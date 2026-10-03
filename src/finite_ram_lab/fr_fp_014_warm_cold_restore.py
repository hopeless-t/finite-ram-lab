from __future__ import annotations

import json
import mmap
import os
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_fp_010_hosted_residency import (
    STATE_BYTES,
    STATE_MIB,
    _fault_state,
    _status_kib,
)
from finite_ram_lab.fr_fp_013_cold_spill_dontneed import (
    _spill,
)
from finite_ram_lab.strata001_probe import (
    _fadvise_dontneed,
    _file_residency,
)

SCHEMA = "finite-ram-lab.fr-fp-014-warm-cold-restore/v0.1"

BLOCKS = 8
ARMS = (
    "WARM_PAGECACHE",
    "COLD_DONTNEED",
)


def _verify_mapping(
    region: mmap.mmap,
    *,
    marker: int,
) -> bool:
    expected = (
        marker
        % 251
        + 1
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
        region[
            offset
        ]
        == expected
        for offset
        in offsets
    )


def _restore(
    path: Path,
    *,
    marker: int,
) -> dict[str, Any]:
    baseline = _status_kib()

    start_total = (
        time.perf_counter_ns()
    )

    region = mmap.mmap(
        -1,
        STATE_BYTES,
        flags=(
            mmap.MAP_PRIVATE
            | mmap.MAP_ANONYMOUS
        ),
        prot=(
            mmap.PROT_READ
            | mmap.PROT_WRITE
        ),
    )

    after_map = (
        time.perf_counter_ns()
    )

    fd = os.open(
        path,
        os.O_RDONLY,
    )
    view = memoryview(
        region
    )

    try:
        start_read = (
            time.perf_counter_ns()
        )
        got = os.preadv(
            fd,
            [view],
            0,
        )
        end_read = (
            time.perf_counter_ns()
        )
    finally:
        view.release()
        os.close(fd)

    after = _status_kib()

    verified = (
        got == STATE_BYTES
        and _verify_mapping(
            region,
            marker=marker,
        )
    )

    region.close()

    return {
        "bytes_read": got,
        "verified": verified,
        "map_ns": (
            after_map
            - start_total
        ),
        "read_ns": (
            end_read
            - start_read
        ),
        "total_restore_ns": (
            end_read
            - start_total
        ),
        "rss_delta_kib": (
            after[
                "vmrss_kib"
            ]
            - baseline[
                "vmrss_kib"
            ]
        ),
        "rssanon_delta_kib": (
            after[
                "rssanon_kib"
            ]
            - baseline[
                "rssanon_kib"
            ]
        ),
    }


def run_trial(
    *,
    block: int,
    arm: str,
    root: Path,
) -> dict[str, Any]:
    marker = (
        block
        + 1
    )
    source = _fault_state(
        marker
    )
    path = root / (
        f"block-{block:02d}-{arm}.bin"
    )

    spill = _spill(
        source,
        path=path,
        marker=marker,
        dontneed=(
            arm
            == "COLD_DONTNEED"
        ),
    )

    pre = _file_residency(
        path
    )

    restore = _restore(
        path,
        marker=marker,
    )

    post = _file_residency(
        path
    )

    _fadvise_dontneed(
        path
    )
    path.unlink()
    time.sleep(
        0.005
    )

    return {
        "block": block,
        "arm": arm,
        "spill_verified": (
            spill[
                "verified"
            ]
        ),
        "spill_advice_called": (
            spill[
                "advice_called"
            ]
        ),
        "pre_restore_residency": (
            pre
        ),
        "restore": restore,
        "post_restore_residency": (
            post
        ),
    }


def run_panel() -> dict[str, Any]:
    rows = []

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-014-"
    ) as tmp:
        root = Path(tmp)

        for block in range(
            BLOCKS
        ):
            order = (
                ARMS
                if block % 2 == 0
                else tuple(
                    reversed(
                        ARMS
                    )
                )
            )

            for arm in order:
                rows.append(
                    run_trial(
                        block=block,
                        arm=arm,
                        root=root,
                    )
                )

    by_arm = {
        arm: [
            row
            for row in rows
            if row[
                "arm"
            ]
            == arm
        ]
        for arm in ARMS
    }

    summary = {}

    for arm, arm_rows in (
        by_arm.items()
    ):
        summary[arm] = {
            "trials": len(
                arm_rows
            ),
            "median_pre_restore_resident_fraction": (
                statistics.median(
                    row[
                        "pre_restore_residency"
                    ][
                        "resident_fraction"
                    ]
                    for row
                    in arm_rows
                )
            ),
            "median_post_restore_resident_fraction": (
                statistics.median(
                    row[
                        "post_restore_residency"
                    ][
                        "resident_fraction"
                    ]
                    for row
                    in arm_rows
                )
            ),
            "median_read_ns": (
                statistics.median(
                    row[
                        "restore"
                    ][
                        "read_ns"
                    ]
                    for row
                    in arm_rows
                )
            ),
            "median_total_restore_ns": (
                statistics.median(
                    row[
                        "restore"
                    ][
                        "total_restore_ns"
                    ]
                    for row
                    in arm_rows
                )
            ),
            "median_rss_delta_kib": (
                statistics.median(
                    row[
                        "restore"
                    ][
                        "rss_delta_kib"
                    ]
                    for row
                    in arm_rows
                )
            ),
        }

    paired_ratios = []

    for block in range(
        BLOCKS
    ):
        warm = next(
            row
            for row in rows
            if (
                row[
                    "block"
                ]
                == block
                and row[
                    "arm"
                ]
                == "WARM_PAGECACHE"
            )
        )
        cold = next(
            row
            for row in rows
            if (
                row[
                    "block"
                ]
                == block
                and row[
                    "arm"
                ]
                == "COLD_DONTNEED"
            )
        )

        warm_ns = warm[
            "restore"
        ][
            "read_ns"
        ]
        cold_ns = cold[
            "restore"
        ][
            "read_ns"
        ]

        paired_ratios.append(
            cold_ns
            / warm_ns
        )

    median_paired_ratio = (
        statistics.median(
            paired_ratios
        )
    )

    checks = {
        "eight_paired_blocks": (
            len(
                by_arm[
                    "WARM_PAGECACHE"
                ]
            )
            == BLOCKS
            and len(
                by_arm[
                    "COLD_DONTNEED"
                ]
            )
            == BLOCKS
        ),
        "all_spills_verify": all(
            row[
                "spill_verified"
            ]
            for row in rows
        ),
        "all_restores_read_full_state": all(
            row[
                "restore"
            ][
                "bytes_read"
            ]
            == STATE_BYTES
            for row in rows
        ),
        "all_restores_verify": all(
            row[
                "restore"
            ][
                "verified"
            ]
            for row in rows
        ),
        "warm_is_resident_before_restore": all(
            row[
                "pre_restore_residency"
            ][
                "resident_fraction"
            ]
            >= 0.95
            for row in by_arm[
                "WARM_PAGECACHE"
            ]
        ),
        "cold_is_nonresident_before_restore": all(
            row[
                "pre_restore_residency"
            ][
                "resident_fraction"
            ]
            <= 0.10
            for row in by_arm[
                "COLD_DONTNEED"
            ]
        ),
        "cold_advice_was_applied": all(
            row[
                "spill_advice_called"
            ]
            for row in by_arm[
                "COLD_DONTNEED"
            ]
        ),
        "restore_materializes_state_in_rss": all(
            row[
                "restore"
            ][
                "rss_delta_kib"
            ]
            >= 0.80
            * STATE_MIB
            * 1024
            for row in rows
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
            "HOSTED_LINUX_WARM_VS_COLD_RESTORE_PILOT"
        ),
        "blocks": (
            BLOCKS
        ),
        "state_mib": (
            STATE_MIB
        ),
        "rows": rows,
        "summary": (
            summary
        ),
        "paired_cold_over_warm_read_ratios": (
            paired_ratios
        ),
        "median_paired_cold_over_warm_read_ratio": (
            median_paired_ratio
        ),
        "observed_latency_direction": (
            "COLD_SLOWER"
            if median_paired_ratio
            > 1.0
            else (
                "COLD_FASTER"
                if median_paired_ratio
                < 1.0
                else "EQUAL"
            )
        ),
        "checks": checks,
        "decision": (
            "MEASURE_RESTORE_COST_SEPARATELY_FROM_RESIDENCY_BENEFIT_BEFORE_TIER_POLICY_SELECTION"
        ),
        "claim_ceiling": (
            "HOSTED_LINUX_WARM_COLD_RESTORE_PILOT_ONLY"
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
