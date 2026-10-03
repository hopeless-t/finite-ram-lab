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
from finite_ram_lab.fr_fp_012_hosted_cold_spill import (
    HOT_STATE_BUDGET,
    RSS_BUDGET_KIB,
    SAFE_STEP,
    WRITE_CHUNK_BYTES,
    _memory_current_bytes,
)

SCHEMA = "finite-ram-lab.fr-fp-013-cold-spill-dontneed/v0.1"

ARMS = (
    "PLAIN_FSYNC",
    "DONTNEED_AFTER_FSYNC",
)


def _verify_fd(
    fd: int,
    *,
    marker: int,
) -> bool:
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


def _spill(
    region: mmap.mmap,
    *,
    path: Path,
    marker: int,
    dontneed: bool,
) -> dict[str, Any]:
    start = time.perf_counter_ns()
    fd = os.open(
        path,
        os.O_RDWR
        | os.O_CREAT
        | os.O_TRUNC,
        0o600,
    )

    written = 0

    try:
        while written < STATE_BYTES:
            end = min(
                written
                + WRITE_CHUNK_BYTES,
                STATE_BYTES,
            )
            chunk = region[
                written:end
            ]
            offset = 0

            while offset < len(chunk):
                count = os.write(
                    fd,
                    chunk[
                        offset:
                    ],
                )

                if count <= 0:
                    raise RuntimeError(
                        "short_spill_write"
                    )

                offset += count
                written += count

        os.fsync(fd)

        after_fsync_current = (
            _memory_current_bytes()
        )

        verified = _verify_fd(
            fd,
            marker=marker,
        )

        region.close()

        after_unmap_current = (
            _memory_current_bytes()
        )

        advice_called = False
        advice_error = None

        if dontneed:
            if (
                not hasattr(
                    os,
                    "posix_fadvise",
                )
                or not hasattr(
                    os,
                    "POSIX_FADV_DONTNEED",
                )
            ):
                advice_error = (
                    "POSIX_FADV_DONTNEED unavailable"
                )
            else:
                try:
                    os.posix_fadvise(
                        fd,
                        0,
                        STATE_BYTES,
                        os.POSIX_FADV_DONTNEED,
                    )
                    advice_called = True
                except OSError as exc:
                    advice_error = (
                        f"{type(exc).__name__}: {exc}"
                    )

        if advice_called:
            time.sleep(
                0.01
            )

        after_advice_current = (
            _memory_current_bytes()
        )

    finally:
        os.close(fd)

    return {
        "bytes_written": (
            written
        ),
        "verified": verified,
        "duration_ns": (
            time.perf_counter_ns()
            - start
        ),
        "after_fsync_memory_current_bytes": (
            after_fsync_current
        ),
        "after_unmap_memory_current_bytes": (
            after_unmap_current
        ),
        "after_advice_memory_current_bytes": (
            after_advice_current
        ),
        "advice_called": (
            advice_called
        ),
        "advice_error": (
            advice_error
        ),
    }


def run_arm(
    arm: str,
) -> dict[str, Any]:
    if arm not in ARMS:
        raise ValueError(
            f"unknown_arm:{arm}"
        )

    dontneed = (
        arm
        == "DONTNEED_AFTER_FSYNC"
    )

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
    peak_current = (
        baseline_current
    )
    peak_hot_states = 0
    peak_cold_bytes = 0
    spill_rows = []

    with tempfile.TemporaryDirectory(
        prefix=(
            "fr-fp-013-"
            + arm.lower()
            + "-"
        )
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
                    row = _spill(
                        region,
                        path=path,
                        marker=marker,
                        dontneed=dontneed,
                    )
                    cold.append(path)
                    spill_rows.append(
                        {
                            "step": step,
                            "marker": marker,
                            **row,
                        }
                    )

                    for key in (
                        "after_fsync_memory_current_bytes",
                        "after_unmap_memory_current_bytes",
                        "after_advice_memory_current_bytes",
                    ):
                        value = row[key]

                        if value is not None:
                            peak_current = (
                                value
                                if peak_current
                                is None
                                else max(
                                    peak_current,
                                    value,
                                )
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

            final_status = (
                _status_kib()
            )
            final_current = (
                _memory_current_bytes()
            )

            return {
                "arm": arm,
                "baseline_memory_current_bytes": (
                    baseline_current
                ),
                "peak_memory_current_delta_bytes": (
                    None
                    if (
                        baseline_current
                        is None
                        or peak_current
                        is None
                    )
                    else (
                        peak_current
                        - baseline_current
                    )
                ),
                "final_memory_current_delta_bytes": (
                    None
                    if (
                        baseline_current
                        is None
                        or final_current
                        is None
                    )
                    else (
                        final_current
                        - baseline_current
                    )
                ),
                "peak_rss_delta_kib": (
                    peak_rss
                    - baseline_status[
                        "vmrss_kib"
                    ]
                ),
                "final_rss_delta_kib": (
                    final_status[
                        "vmrss_kib"
                    ]
                    - baseline_status[
                        "vmrss_kib"
                    ]
                ),
                "peak_hot_states": (
                    peak_hot_states
                ),
                "peak_cold_bytes": (
                    peak_cold_bytes
                ),
                "spill_rows": (
                    spill_rows
                ),
                "final_hot_states": (
                    len(hot)
                ),
                "final_cold_files": (
                    len(cold)
                ),
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
    plain = run_arm(
        "PLAIN_FSYNC"
    )
    time.sleep(0.05)
    dontneed = run_arm(
        "DONTNEED_AFTER_FSYNC"
    )

    plain_peak = plain[
        "peak_memory_current_delta_bytes"
    ]
    dontneed_peak = dontneed[
        "peak_memory_current_delta_bytes"
    ]

    ratio = (
        None
        if (
            plain_peak is None
            or dontneed_peak is None
            or plain_peak <= 0
        )
        else (
            dontneed_peak
            / plain_peak
        )
    )

    advice_rows = (
        dontneed[
            "spill_rows"
        ]
    )

    checks = {
        "cgroup_accounting_available": (
            plain_peak is not None
            and dontneed_peak is not None
        ),
        "both_arms_respect_hot_state_budget": (
            plain[
                "peak_hot_states"
            ]
            <= HOT_STATE_BUDGET
            and dontneed[
                "peak_hot_states"
            ]
            <= HOT_STATE_BUDGET
        ),
        "both_arms_respect_process_rss_budget_margin": (
            plain[
                "peak_rss_delta_kib"
            ]
            <= RSS_BUDGET_KIB
            + 4096
            and dontneed[
                "peak_rss_delta_kib"
            ]
            <= RSS_BUDGET_KIB
            + 4096
        ),
        "both_arms_spill_five_exact_states": (
            len(
                plain[
                    "spill_rows"
                ]
            )
            == 5
            and len(
                dontneed[
                    "spill_rows"
                ]
            )
            == 5
            and plain[
                "peak_cold_bytes"
            ]
            == 5 * STATE_BYTES
            and dontneed[
                "peak_cold_bytes"
            ]
            == 5 * STATE_BYTES
        ),
        "all_spills_verify": all(
            row[
                "verified"
            ]
            for row in (
                plain[
                    "spill_rows"
                ]
                + dontneed[
                    "spill_rows"
                ]
            )
        ),
        "dontneed_applied_five_times": (
            len(
                advice_rows
            )
            == 5
            and all(
                row[
                    "advice_called"
                ]
                and row[
                    "advice_error"
                ]
                is None
                for row
                in advice_rows
            )
        ),
        "dontneed_materially_reduces_cgroup_peak": (
            ratio is not None
            and ratio < 0.75
        ),
        "both_arms_end_one_hot_zero_cold": (
            plain[
                "final_hot_states"
            ]
            == 1
            and dontneed[
                "final_hot_states"
            ]
            == 1
            and plain[
                "final_cold_files"
            ]
            == 0
            and dontneed[
                "final_cold_files"
            ]
            == 0
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
            "HOSTED_LINUX_COLD_SPILL_PAGE_CACHE_RELEASE_COMPARISON"
        ),
        "fixture": {
            "state_mib": (
                STATE_MIB
            ),
            "hot_state_budget": (
                HOT_STATE_BUDGET
            ),
            "rss_budget_kib": (
                RSS_BUDGET_KIB
            ),
            "safe_step": (
                SAFE_STEP
            ),
        },
        "plain": plain,
        "dontneed": (
            dontneed
        ),
        "cgroup_peak_ratio_dontneed_over_plain": (
            ratio
        ),
        "checks": checks,
        "decision": (
            "ADVISE_DURABLE_COLD_FILES_DONTNEED_WHEN_THE_GOAL_INCLUDES_SAME_CGROUP_MEMORY_PRESSURE"
        ),
        "evidence_boundary": (
            "The safe-step semantics are synthetic. File writes/fsync, "
            "POSIX_FADV_DONTNEED, mmap unmapping, process RSS and cgroup "
            "memory.current are hosted physical."
        ),
        "claim_ceiling": (
            "HOSTED_LINUX_CGROUP_PAGE_CACHE_RELEASE_FOR_THIS_COLD_SPILL_FIXTURE_ONLY"
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
