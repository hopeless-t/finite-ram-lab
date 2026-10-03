from __future__ import annotations

import json
import mmap
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_fp_010_hosted_residency import (
    STATE_BYTES,
    STATE_MIB,
    STEPS,
    _close_all,
    _fault_state,
    _status_kib,
)
from finite_ram_lab.fr_fp_011_hosted_rss_calibration import (
    STATE_KIB,
)

SCHEMA = "finite-ram-lab.fr-fp-012-hosted-cold-spill/v0.1"

RSS_BUDGET_MIB = 32
RSS_BUDGET_KIB = RSS_BUDGET_MIB * 1024
HOT_STATE_BUDGET = RSS_BUDGET_KIB // STATE_KIB
SAFE_STEP = 9
WRITE_CHUNK_BYTES = 1024 * 1024


def _self_cgroup_dir() -> Path | None:
    path = Path("/proc/self/cgroup")

    if not path.exists():
        return None

    for line in path.read_text(
        encoding="utf-8"
    ).splitlines():
        if line.startswith("0::"):
            relative = line.split(
                "::",
                1,
            )[1].lstrip(
                "/"
            )

            return (
                Path("/sys/fs/cgroup")
                / relative
            )

    return None


def _memory_current_bytes() -> int | None:
    directory = _self_cgroup_dir()

    if directory is None:
        return None

    path = directory / "memory.current"

    if not path.exists():
        return None

    try:
        return int(
            path.read_text(
                encoding="utf-8"
            ).strip()
        )
    except (
        OSError,
        ValueError,
    ):
        return None


def _verify_spill(
    path: Path,
    *,
    marker: int,
) -> bool:
    if path.stat().st_size != STATE_BYTES:
        return False

    expected = bytes(
        [
            marker
            % 251
            + 1
        ]
    )
    page_size = os.sysconf(
        "SC_PAGE_SIZE"
    )
    offsets = (
        0,
        (
            STATE_BYTES // 2
            // page_size
        )
        * page_size,
        STATE_BYTES
        - page_size,
    )

    fd = os.open(
        path,
        os.O_RDONLY,
    )

    try:
        return all(
            os.pread(
                fd,
                1,
                offset,
            )
            == expected
            for offset
            in offsets
        )
    finally:
        os.close(fd)


def _spill_region(
    region: mmap.mmap,
    *,
    path: Path,
    marker: int,
) -> dict[str, Any]:
    start = time.perf_counter_ns()

    fd = os.open(
        path,
        os.O_WRONLY
        | os.O_CREAT
        | os.O_TRUNC,
        0o600,
    )

    view = memoryview(
        region
    )
    written = 0

    try:
        while written < STATE_BYTES:
            end = min(
                written
                + WRITE_CHUNK_BYTES,
                STATE_BYTES,
            )
            chunk = view[
                written:end
            ]

            while chunk:
                count = os.write(
                    fd,
                    chunk,
                )

                if count <= 0:
                    raise RuntimeError(
                        "short_spill_write"
                    )

                written += count
                chunk = chunk[
                    count:
                ]

        os.fsync(fd)
    finally:
        view.release()
        os.close(fd)

    verified = _verify_spill(
        path,
        marker=marker,
    )

    region.close()

    end = time.perf_counter_ns()

    return {
        "bytes_written": (
            written
        ),
        "duration_ns": (
            end - start
        ),
        "verified": (
            verified
        ),
    }


def run_spill_arm() -> dict[str, Any]:
    hot: list[
        tuple[int, mmap.mmap]
    ] = []
    cold: list[
        Path
    ] = []

    baseline_status = (
        _status_kib()
    )
    baseline_current = (
        _memory_current_bytes()
    )

    peak_rss = baseline_status[
        "vmrss_kib"
    ]
    peak_anon = baseline_status[
        "rssanon_kib"
    ]
    peak_current = (
        baseline_current
    )
    peak_hot_states = 0
    peak_cold_bytes = 0
    spill_rows = []
    trace = []

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-012-"
    ) as tmp:
        root = Path(tmp)

        try:
            for step in range(
                1,
                STEPS + 1,
            ):
                if (
                    len(hot)
                    >= HOT_STATE_BUDGET
                ):
                    marker, region = (
                        hot.pop(0)
                    )
                    path = root / (
                        f"state-{marker:02d}.bin"
                    )
                    spill = _spill_region(
                        region,
                        path=path,
                        marker=marker,
                    )
                    cold.append(
                        path
                    )
                    spill_rows.append(
                        {
                            "step": step,
                            "marker": marker,
                            **spill,
                        }
                    )

                hot.append(
                    (
                        step,
                        _fault_state(
                            step
                        ),
                    )
                )

                status = _status_kib()
                current = (
                    _memory_current_bytes()
                )

                peak_rss = max(
                    peak_rss,
                    status[
                        "vmrss_kib"
                    ],
                )
                peak_anon = max(
                    peak_anon,
                    status[
                        "rssanon_kib"
                    ],
                )

                if current is not None:
                    peak_current = (
                        current
                        if peak_current
                        is None
                        else max(
                            peak_current,
                            current,
                        )
                    )

                peak_hot_states = max(
                    peak_hot_states,
                    len(hot),
                )
                peak_cold_bytes = max(
                    peak_cold_bytes,
                    sum(
                        path.stat().st_size
                        for path
                        in cold
                        if path.exists()
                    ),
                )

                action = "HOT"

                if step >= SAFE_STEP:
                    current_item = hot[-1]
                    old = hot[:-1]
                    hot = [
                        current_item
                    ]

                    for _marker, region in old:
                        region.close()

                    for path in cold:
                        try:
                            path.unlink()
                        except FileNotFoundError:
                            pass

                    cold.clear()
                    action = (
                        "SAFE_COLLAPSE"
                    )

                post_status = (
                    _status_kib()
                )
                post_current = (
                    _memory_current_bytes()
                )

                trace.append(
                    {
                        "step": step,
                        "action": action,
                        "hot_states": len(hot),
                        "cold_files": len(cold),
                        "vmrss_delta_kib": (
                            post_status[
                                "vmrss_kib"
                            ]
                            - baseline_status[
                                "vmrss_kib"
                            ]
                        ),
                        "rssanon_delta_kib": (
                            post_status[
                                "rssanon_kib"
                            ]
                            - baseline_status[
                                "rssanon_kib"
                            ]
                        ),
                        "memory_current_delta_bytes": (
                            None
                            if (
                                post_current
                                is None
                                or baseline_current
                                is None
                            )
                            else (
                                post_current
                                - baseline_current
                            )
                        ),
                    }
                )

            final_status = (
                _status_kib()
            )
            final_current = (
                _memory_current_bytes()
            )

            return {
                "baseline": {
                    "status": (
                        baseline_status
                    ),
                    "memory_current_bytes": (
                        baseline_current
                    ),
                },
                "peak_hot_states": (
                    peak_hot_states
                ),
                "peak_cold_bytes": (
                    peak_cold_bytes
                ),
                "peak_rss_delta_kib": (
                    peak_rss
                    - baseline_status[
                        "vmrss_kib"
                    ]
                ),
                "peak_rssanon_delta_kib": (
                    peak_anon
                    - baseline_status[
                        "rssanon_kib"
                    ]
                ),
                "peak_memory_current_delta_bytes": (
                    None
                    if (
                        peak_current
                        is None
                        or baseline_current
                        is None
                    )
                    else (
                        peak_current
                        - baseline_current
                    )
                ),
                "final_rss_delta_kib": (
                    final_status[
                        "vmrss_kib"
                    ]
                    - baseline_status[
                        "vmrss_kib"
                    ]
                ),
                "final_rssanon_delta_kib": (
                    final_status[
                        "rssanon_kib"
                    ]
                    - baseline_status[
                        "rssanon_kib"
                    ]
                ),
                "final_memory_current_delta_bytes": (
                    None
                    if (
                        final_current
                        is None
                        or baseline_current
                        is None
                    )
                    else (
                        final_current
                        - baseline_current
                    )
                ),
                "final_hot_states": (
                    len(hot)
                ),
                "final_cold_files": (
                    len(cold)
                ),
                "spill_rows": (
                    spill_rows
                ),
                "trace": trace,
            }

        finally:
            _close_all(
                [
                    region
                    for _marker, region
                    in hot
                ]
            )


def run_panel() -> dict[str, Any]:
    spill = run_spill_arm()

    spilled_states = len(
        spill[
            "spill_rows"
        ]
    )
    spilled_bytes = sum(
        row[
            "bytes_written"
        ]
        for row
        in spill[
            "spill_rows"
        ]
    )
    verified = all(
        row[
            "verified"
        ]
        for row
        in spill[
            "spill_rows"
        ]
    )

    checks = {
        "calibration_maps_32mib_to_four_hot_states": (
            HOT_STATE_BUDGET
            == 4
        ),
        "hot_state_budget_never_exceeded": (
            spill[
                "peak_hot_states"
            ]
            <= HOT_STATE_BUDGET
        ),
        "process_rss_respects_budget_with_small_noise_margin": (
            spill[
                "peak_rss_delta_kib"
            ]
            <= RSS_BUDGET_KIB
            + 4096
        ),
        "five_states_physically_spilled_before_safe_collapse": (
            spilled_states
            == 5
        ),
        "spill_bytes_are_exact": (
            spilled_bytes
            == 5 * STATE_BYTES
        ),
        "spill_sentinels_verified_before_unmap": (
            verified
        ),
        "cold_peak_is_five_states": (
            spill[
                "peak_cold_bytes"
            ]
            == 5 * STATE_BYTES
        ),
        "safe_collapse_ends_one_hot_state": (
            spill[
                "final_hot_states"
            ]
            == 1
        ),
        "safe_collapse_removes_cold_files": (
            spill[
                "final_cold_files"
            ]
            == 0
        ),
        "final_process_rss_is_one_state_scale": (
            spill[
                "final_rss_delta_kib"
            ]
            <= STATE_KIB
            + 4096
        ),
    }

    accounting = {
        "cgroup_memory_current_available": (
            spill[
                "baseline"
            ][
                "memory_current_bytes"
            ]
            is not None
        ),
        "peak_memory_current_delta_bytes": (
            spill[
                "peak_memory_current_delta_bytes"
            ]
        ),
        "final_memory_current_delta_bytes": (
            spill[
                "final_memory_current_delta_bytes"
            ]
        ),
        "interpretation": (
            "Process RSS and cgroup memory.current are reported separately. "
            "File-backed cold spill may leave page-cache charges in memory.current "
            "even after hot anonymous mappings are unmapped."
        ),
    }

    return {
        "schema": SCHEMA,
        "status": (
            "PASS"
            if all(
                checks.values()
            )
            else "FAIL"
        ),
        "classification": (
            "HOSTED_LINUX_CALIBRATED_HOT_BUDGET_WITH_DURABLE_FILE_COLD_SPILL"
        ),
        "fixture": {
            "state_mib": (
                STATE_MIB
            ),
            "rss_budget_mib": (
                RSS_BUDGET_MIB
            ),
            "calibrated_hot_state_budget": (
                HOT_STATE_BUDGET
            ),
            "trajectory_steps": (
                STEPS
            ),
            "synthetic_safe_step": (
                SAFE_STEP
            ),
        },
        "spill": spill,
        "spilled_states": (
            spilled_states
        ),
        "spilled_bytes": (
            spilled_bytes
        ),
        "checks": checks,
        "accounting": accounting,
        "decision": (
            "CONVERT_CALIBRATED_RSS_BUDGET_TO_HOT_STATE_BUDGET_AND_SPILL_LIVE_HISTORY_BEFORE_ALLOCATING_THE_NEXT_STATE"
        ),
        "evidence_boundary": (
            "Safe-step semantics remain synthetic. mmap faults, process RSS, "
            "file writes/fsync, unmapping, sentinel verification and cgroup "
            "memory.current observations are hosted physical."
        ),
        "claim_ceiling": (
            "HOSTED_LINUX_PROCESS_RSS_BUDGET_AND_FILE_COLD_SPILL_ONLY"
        ),
    }


def main() -> int:
    print(
        json.dumps(
            run_panel(),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
