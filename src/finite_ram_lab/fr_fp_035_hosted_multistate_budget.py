from __future__ import annotations

import json
import os
import random
import statistics
import tempfile
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_fp_016_restore_size_scaling import (
    _fadvise_dontneed,
    _file_residency,
    _prepare_tier,
    _restore,
    _size_bytes,
)
from finite_ram_lab.fr_fp_030_hosted_reuse_lifecycle import (
    _enforce_tier,
    _proc_read_bytes,
)

SCHEMA = "finite-ram-lab.fr-fp-035-hosted-multistate-budget/v0.1"

STATE_COUNT = 10
STATE_MIB = 8
SIZE_BYTES = _size_bytes(
    STATE_MIB
)
WARM_SLOTS = 5
OPPORTUNITIES = 60
SEED = 20261004
DEADLINE_MS = 10.0

VALUE_WARM_IDS = (
    5,
    6,
    7,
    8,
    9,
)

ANTI_WARM_IDS = (
    0,
    1,
    2,
    3,
    4,
)

EVIDENCE_REUSE_COUNTS = tuple(
    range(10)
)
EVIDENCE_OBSERVATIONS = 35


def _reuse_counts() -> list[int]:
    return [
        round(
            OPPORTUNITIES
            * count
            / EVIDENCE_OBSERVATIONS
        )
        for count in (
            EVIDENCE_REUSE_COUNTS
        )
    ]


def _schedules() -> dict[int, list[bool]]:
    counts = _reuse_counts()
    out = {}

    for state_id, count in enumerate(
        counts
    ):
        rng = random.Random(
            SEED
            + state_id
            * 1009
        )
        positions = set(
            rng.sample(
                range(
                    OPPORTUNITIES
                ),
                count,
            )
        )
        out[state_id] = [
            index in positions
            for index in range(
                OPPORTUNITIES
            )
        ]

    return out


def _resident_total_mib(
    paths: dict[int, Path],
) -> float:
    return sum(
        _file_residency(
            path
        )[
            "resident_fraction"
        ]
        * STATE_MIB
        for path in paths.values()
    )


def _run_arm(
    *,
    root: Path,
    arm: str,
    warm_ids: tuple[int, ...],
    schedules: dict[int, list[bool]],
) -> dict[str, Any]:
    warm_set = set(
        warm_ids
    )
    paths = {}
    prepared = []

    arm_root = root / arm.lower()
    arm_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    for state_id in range(
        STATE_COUNT
    ):
        path = arm_root / (
            f"state-{state_id}.bin"
        )
        row = _prepare_tier(
            path,
            size_bytes=SIZE_BYTES,
            marker=(
                100
                + state_id
            ),
            cold=(
                state_id
                not in warm_set
            ),
        )

        if not row[
            "verified"
        ]:
            raise RuntimeError(
                f"prepare_failed:{arm}:{state_id}"
            )

        paths[state_id] = path
        prepared.append(
            row
        )

    for state_id, path in (
        paths.items()
    ):
        _enforce_tier(
            path,
            tier=(
                "WARM"
                if state_id
                in warm_set
                else "COLD"
            ),
        )

    restore_rows = []
    residency_trace = []
    post_enforcement_trace = []

    try:
        for opportunity in range(
            OPPORTUNITIES
        ):
            before_total = (
                _resident_total_mib(
                    paths
                )
            )
            residency_trace.append(
                before_total
            )

            for state_id, path in (
                paths.items()
            ):
                if not schedules[
                    state_id
                ][
                    opportunity
                ]:
                    continue

                tier = (
                    "WARM"
                    if state_id
                    in warm_set
                    else "COLD"
                )
                pre_resident = (
                    _file_residency(
                        path
                    )[
                        "resident_fraction"
                    ]
                )
                io_before = (
                    _proc_read_bytes()
                )
                restored = _restore(
                    path,
                    size_bytes=SIZE_BYTES,
                    marker=(
                        100
                        + state_id
                    ),
                )
                io_after = (
                    _proc_read_bytes()
                )

                if not restored[
                    "verified"
                ]:
                    raise RuntimeError(
                        f"restore_failed:{arm}:{state_id}:{opportunity}"
                    )

                restore_rows.append(
                    {
                        **restored,
                        "state_id": state_id,
                        "opportunity": (
                            opportunity
                            + 1
                        ),
                        "tier": tier,
                        "pre_resident_fraction": (
                            pre_resident
                        ),
                        "read_bytes_delta": (
                            None
                            if (
                                io_before
                                is None
                                or io_after
                                is None
                            )
                            else (
                                io_after
                                - io_before
                            )
                        ),
                    }
                )

            for state_id, path in (
                paths.items()
            ):
                _enforce_tier(
                    path,
                    tier=(
                        "WARM"
                        if state_id
                        in warm_set
                        else "COLD"
                    ),
                )

            post_enforcement_trace.append(
                _resident_total_mib(
                    paths
                )
            )

    finally:
        for path in paths.values():
            try:
                _fadvise_dontneed(
                    path
                )
            except Exception:
                pass

            try:
                path.unlink()
            except FileNotFoundError:
                pass

    warm_restores = [
        row
        for row in restore_rows
        if row[
            "tier"
        ]
        == "WARM"
    ]
    cold_restores = [
        row
        for row in restore_rows
        if row[
            "tier"
        ]
        == "COLD"
    ]

    deadline_misses = [
        row
        for row in cold_restores
        if (
            row[
                "read_ns"
            ]
            / 1_000_000.0
        )
        > DEADLINE_MS
    ]

    return {
        "arm": arm,
        "warm_ids": sorted(
            warm_set
        ),
        "cold_ids": sorted(
            set(
                range(
                    STATE_COUNT
                )
            )
            - warm_set
        ),
        "warm_mib": (
            len(
                warm_set
            )
            * STATE_MIB
        ),
        "restore_count": len(
            restore_rows
        ),
        "warm_restores": len(
            warm_restores
        ),
        "cold_restores": len(
            cold_restores
        ),
        "all_restores_verified": all(
            row[
                "verified"
            ]
            for row in restore_rows
        ),
        "warm_restore_pre_residency_median": (
            None
            if not warm_restores
            else statistics.median(
                row[
                    "pre_resident_fraction"
                ]
                for row
                in warm_restores
            )
        ),
        "cold_restore_pre_residency_median": (
            None
            if not cold_restores
            else statistics.median(
                row[
                    "pre_resident_fraction"
                ]
                for row
                in cold_restores
            )
        ),
        "resident_mib_opportunity_integral": sum(
            residency_trace
        ),
        "mean_resident_mib": (
            statistics.fmean(
                residency_trace
            )
        ),
        "max_post_enforcement_resident_mib": max(
            post_enforcement_trace
        ),
        "min_post_enforcement_resident_mib": min(
            post_enforcement_trace
        ),
        "total_restore_ns": sum(
            row[
                "read_ns"
            ]
            for row
            in restore_rows
        ),
        "total_storage_read_bytes": sum(
            (
                row[
                    "read_bytes_delta"
                ]
                or 0
            )
            for row
            in restore_rows
        ),
        "cold_deadline_miss_count": len(
            deadline_misses
        ),
        "cold_restore_median_ns": (
            None
            if not cold_restores
            else statistics.median(
                row[
                    "read_ns"
                ]
                for row
                in cold_restores
            )
        ),
        "warm_restore_median_ns": (
            None
            if not warm_restores
            else statistics.median(
                row[
                    "read_ns"
                ]
                for row
                in warm_restores
            )
        ),
        "rows": restore_rows,
    }


def run_panel() -> dict[str, Any]:
    schedules = _schedules()
    reuse_counts = [
        sum(
            schedules[
                state_id
            ]
        )
        for state_id
        in range(
            STATE_COUNT
        )
    ]

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-035-"
    ) as tmp:
        root = Path(tmp)

        value = _run_arm(
            root=root,
            arm=(
                "VALUE_RISK_ALLOCATOR"
            ),
            warm_ids=(
                VALUE_WARM_IDS
            ),
            schedules=schedules,
        )

        anti = _run_arm(
            root=root,
            arm=(
                "ANTI_VALUE_CONTROL"
            ),
            warm_ids=(
                ANTI_WARM_IDS
            ),
            schedules=schedules,
        )

    expected_value_cold = sum(
        reuse_counts[
            state_id
        ]
        for state_id in range(
            STATE_COUNT
        )
        if state_id
        not in set(
            VALUE_WARM_IDS
        )
    )
    expected_anti_cold = sum(
        reuse_counts[
            state_id
        ]
        for state_id in range(
            STATE_COUNT
        )
        if state_id
        not in set(
            ANTI_WARM_IDS
        )
    )

    storage_accounting_available = (
        anti[
            "total_storage_read_bytes"
        ]
        > 0
    )

    checks = {
        "frozen_schedule_counts_match": (
            reuse_counts
            == [
                0,
                2,
                3,
                5,
                7,
                9,
                10,
                12,
                14,
                15,
            ]
        ),
        "same_total_reuse_count": (
            value[
                "restore_count"
            ]
            == anti[
                "restore_count"
            ]
            == sum(
                reuse_counts
            )
            == 77
        ),
        "same_warm_capacity": (
            value[
                "warm_mib"
            ]
            == anti[
                "warm_mib"
            ]
            == 40
        ),
        "all_restore_integrity_passes": (
            value[
                "all_restores_verified"
            ]
            and anti[
                "all_restores_verified"
            ]
        ),
        "warm_tiers_are_physically_resident_on_reuse": (
            value[
                "warm_restore_pre_residency_median"
            ]
            >= 0.95
            and anti[
                "warm_restore_pre_residency_median"
            ]
            >= 0.95
        ),
        "cold_tiers_are_physically_nonresident_on_reuse": (
            value[
                "cold_restore_pre_residency_median"
            ]
            <= 0.10
            and anti[
                "cold_restore_pre_residency_median"
            ]
            <= 0.10
        ),
        "value_allocator_cold_restore_count_matches_schedule": (
            value[
                "cold_restores"
            ]
            == expected_value_cold
            == 17
        ),
        "anti_value_cold_restore_count_matches_schedule": (
            anti[
                "cold_restores"
            ]
            == expected_anti_cold
            == 60
        ),
        "value_allocator_uses_fewer_cold_restores": (
            value[
                "cold_restores"
            ]
            < anti[
                "cold_restores"
            ]
        ),
        "both_arms_hold_the_same_physical_resident_budget": (
            value[
                "max_post_enforcement_resident_mib"
            ]
            <= 40.5
            and anti[
                "max_post_enforcement_resident_mib"
            ]
            <= 40.5
            and value[
                "min_post_enforcement_resident_mib"
            ]
            >= 39.0
            and anti[
                "min_post_enforcement_resident_mib"
            ]
            >= 39.0
        ),
        "residency_integrals_are_capacity_matched": (
            abs(
                value[
                    "resident_mib_opportunity_integral"
                ]
                - anti[
                    "resident_mib_opportunity_integral"
                ]
            )
            <= (
                0.02
                * max(
                    value[
                        "resident_mib_opportunity_integral"
                    ],
                    anti[
                        "resident_mib_opportunity_integral"
                    ],
                )
            )
        ),
        "storage_reads_improve_when_accounting_is_available": (
            (
                not storage_accounting_available
            )
            or (
                value[
                    "total_storage_read_bytes"
                ]
                < anti[
                    "total_storage_read_bytes"
                ]
            )
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
            "HOSTED_PHYSICAL_EQUAL_CAPACITY_MULTI_STATE_RESIDENCY_ALLOCATION_PILOT"
        ),
        "fixture": {
            "state_count": STATE_COUNT,
            "state_mib": STATE_MIB,
            "warm_slots": WARM_SLOTS,
            "warm_mib": (
                WARM_SLOTS
                * STATE_MIB
            ),
            "opportunities": (
                OPPORTUNITIES
            ),
            "seed": SEED,
            "reuse_counts": (
                reuse_counts
            ),
            "deadline_ms": (
                DEADLINE_MS
            ),
        },
        "value_risk_allocator": (
            value
        ),
        "anti_value_control": (
            anti
        ),
        "derived": {
            "cold_restore_reduction_fraction": (
                1.0
                - value[
                    "cold_restores"
                ]
                / anti[
                    "cold_restores"
                ]
            ),
            "storage_read_reduction_fraction": (
                None
                if not (
                    storage_accounting_available
                )
                else (
                    1.0
                    - value[
                        "total_storage_read_bytes"
                    ]
                    / anti[
                        "total_storage_read_bytes"
                    ]
                )
            ),
            "restore_latency_reduction_fraction_observed": (
                1.0
                - value[
                    "total_restore_ns"
                ]
                / anti[
                    "total_restore_ns"
                ]
            ),
        },
        "checks": checks,
        "decision": (
            "ALLOCATE_EQUAL_RESIDENT_BYTES_TO_THE_STATES_WITH_HIGHEST_CONSERVATIVE_AVOIDED_COLD_COST_SUBJECT_TO_DEADLINE_GUARDS"
        ),
        "evidence_boundary": (
            "The reuse trace is synthetic and frozen. File residency, DONTNEED, "
            "restore latency, storage-read accounting and byte integrity are hosted "
            "physical Linux observations. Both arms use exactly the same 40 MiB WARM "
            "capacity."
        ),
        "next": (
            "MAKE_THE_WARM_SET_ADAPT_ONLINE_AS_REUSE_EVIDENCE_AND_AVAILABLE_CAPACITY_CHANGE"
        ),
        "claim_ceiling": (
            "HOSTED_PHYSICAL_TEN_STATE_EQUAL_SIZE_SAME_CAPACITY_ALLOCATION_ON_ONE_SYNTHETIC_REUSE_TRACE_ONLY"
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
