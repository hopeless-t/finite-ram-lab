from __future__ import annotations

import json
import os
import random
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_fp_012_hosted_cold_spill import (
    _memory_current_bytes,
)
from finite_ram_lab.fr_fp_016_restore_size_scaling import (
    _fadvise_dontneed,
    _file_residency,
    _prepare_tier,
    _restore,
    _size_bytes,
)
from finite_ram_lab.fr_fp_027_reuse_evidence_budget import (
    clopper_pearson_upper,
)

SCHEMA = "finite-ram-lab.fr-fp-030-hosted-reuse-lifecycle/v0.1"

STATE_MIB = 8
SIZE_BYTES = _size_bytes(
    STATE_MIB
)
MARKER = 30

SEED = 20261004
PRE_REUSE_P = 0.02
POST_REUSE_P = 0.25
PRE_OBSERVATIONS = 60
POST_OBSERVATIONS = 60

CONFIDENCE = 0.95
REUSE_CEILING = 0.10
RECENT_WINDOW = 35
DRIFT_THRESHOLD = 4

ARMS = (
    "ALWAYS_WARM",
    "ALWAYS_COLD",
    "LIFECYCLE_GOVERNOR",
)


def _proc_read_bytes() -> int | None:
    path = Path(
        "/proc/self/io"
    )

    if not path.exists():
        return None

    for line in path.read_text(
        encoding="utf-8"
    ).splitlines():
        if line.startswith(
            "read_bytes:"
        ):
            try:
                return int(
                    line.split(
                        ":",
                        1,
                    )[1].strip()
                )
            except ValueError:
                return None

    return None


def _schedule() -> list[bool]:
    rng = random.Random(
        SEED
    )

    return [
        rng.random()
        < PRE_REUSE_P
        for _ in range(
            PRE_OBSERVATIONS
        )
    ] + [
        rng.random()
        < POST_REUSE_P
        for _ in range(
            POST_OBSERVATIONS
        )
    ]


def _warm_file(
    path: Path,
) -> int:
    fd = os.open(
        path,
        os.O_RDONLY,
    )
    read = 0
    chunk = 1024 * 1024

    try:
        while read < SIZE_BYTES:
            data = os.pread(
                fd,
                min(
                    chunk,
                    SIZE_BYTES
                    - read,
                ),
                read,
            )

            if not data:
                raise RuntimeError(
                    "unexpected_prefetch_eof"
                )

            read += len(
                data
            )

        return read
    finally:
        os.close(fd)


def _enforce_tier(
    path: Path,
    *,
    tier: str,
) -> dict[str, Any]:
    if tier == "COLD":
        _fadvise_dontneed(
            path
        )
        time.sleep(
            0.01
        )
        action = (
            "DONTNEED"
        )
        prefetch_bytes = 0
    elif tier == "WARM":
        before = _file_residency(
            path
        )[
            "resident_fraction"
        ]

        if before < 0.95:
            prefetch_bytes = (
                _warm_file(
                    path
                )
            )
            time.sleep(
                0.005
            )
            action = (
                "PREFETCH"
            )
        else:
            prefetch_bytes = 0
            action = (
                "KEEP_WARM"
            )
    else:
        raise ValueError(
            f"unknown_tier:{tier}"
        )

    after = _file_residency(
        path
    )[
        "resident_fraction"
    ]

    return {
        "action": action,
        "prefetch_bytes": (
            prefetch_bytes
        ),
        "resident_fraction": (
            after
        ),
    }


def _upper(
    history: list[bool],
) -> float:
    if not history:
        return 1.0

    return (
        clopper_pearson_upper(
            reused=sum(
                history
            ),
            observations=len(
                history
            ),
            confidence=(
                CONFIDENCE
            ),
        )
    )


def _next_governor_state(
    *,
    history: list[bool],
    recent: list[bool],
    ever_qualified: bool,
    opportunity: int,
    drift_alarm_steps: list[int],
) -> tuple[
    str,
    list[bool],
    list[bool],
    bool,
    float,
]:
    recent = recent[
        -RECENT_WINDOW:
    ]

    if (
        ever_qualified
        and sum(
            recent
        )
        >= DRIFT_THRESHOLD
    ):
        drift_alarm_steps.append(
            opportunity
        )

        return (
            "WARM",
            [],
            [],
            False,
            1.0,
        )

    upper = _upper(
        history
    )

    if upper <= REUSE_CEILING:
        return (
            "COLD",
            history,
            recent,
            True,
            upper,
        )

    return (
        "WARM",
        history,
        recent,
        ever_qualified,
        upper,
    )


def _run_arm(
    *,
    root: Path,
    arm: str,
    schedule: list[bool],
) -> dict[str, Any]:
    path = root / (
        arm.lower()
        + ".bin"
    )
    initial_cold = (
        arm
        == "ALWAYS_COLD"
    )

    prepared = _prepare_tier(
        path,
        size_bytes=SIZE_BYTES,
        marker=MARKER,
        cold=initial_cold,
    )

    if not prepared[
        "verified"
    ]:
        raise RuntimeError(
            "prepare_verify_failed"
        )

    tier = (
        "COLD"
        if initial_cold
        else "WARM"
    )
    history: list[bool] = []
    recent: list[bool] = []
    ever_qualified = False
    drift_alarm_steps: list[int] = []

    rows = []
    restore_rows = []
    resident_integral_mib = 0.0
    peak_memory_current_delta = 0
    baseline_current = (
        _memory_current_bytes()
    )

    for opportunity, reused in enumerate(
        schedule,
        start=1,
    ):
        tier_before = tier

        pre_resident = (
            _file_residency(
                path
            )[
                "resident_fraction"
            ]
        )
        resident_integral_mib += (
            pre_resident
            * STATE_MIB
        )

        current = (
            _memory_current_bytes()
        )

        if (
            current is not None
            and baseline_current
            is not None
        ):
            peak_memory_current_delta = max(
                peak_memory_current_delta,
                current
                - baseline_current,
            )

        restore = None

        if reused:
            io_before = (
                _proc_read_bytes()
            )
            restored = _restore(
                path,
                size_bytes=SIZE_BYTES,
                marker=MARKER,
            )
            io_after = (
                _proc_read_bytes()
            )

            if not restored[
                "verified"
            ]:
                raise RuntimeError(
                    "restore_verify_failed"
                )

            restore = {
                **restored,
                "tier_before": (
                    tier_before
                ),
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
            restore_rows.append(
                restore
            )

        if arm == "ALWAYS_WARM":
            tier = "WARM"
            upper = None
        elif arm == "ALWAYS_COLD":
            tier = "COLD"
            upper = None
        elif arm == "LIFECYCLE_GOVERNOR":
            history.append(
                reused
            )
            recent.append(
                reused
            )

            (
                tier,
                history,
                recent,
                ever_qualified,
                upper,
            ) = _next_governor_state(
                history=history,
                recent=recent,
                ever_qualified=(
                    ever_qualified
                ),
                opportunity=(
                    opportunity
                ),
                drift_alarm_steps=(
                    drift_alarm_steps
                ),
            )
        else:
            raise ValueError(
                f"unknown_arm:{arm}"
            )

        enforcement = (
            _enforce_tier(
                path,
                tier=tier,
            )
        )

        rows.append(
            {
                "opportunity": (
                    opportunity
                ),
                "phase": (
                    "LOW_REUSE"
                    if opportunity
                    <= PRE_OBSERVATIONS
                    else "HIGH_REUSE"
                ),
                "reused": (
                    reused
                ),
                "tier_before": (
                    tier_before
                ),
                "tier_after": tier,
                "reuse_upper": (
                    upper
                ),
                "pre_resident_fraction": (
                    pre_resident
                ),
                "post_resident_fraction": (
                    enforcement[
                        "resident_fraction"
                    ]
                ),
                "enforcement_action": (
                    enforcement[
                        "action"
                    ]
                ),
                "prefetch_bytes": (
                    enforcement[
                        "prefetch_bytes"
                    ]
                ),
                "restore": restore,
            }
        )

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

    warm_opportunities = sum(
        row[
            "tier_before"
        ]
        == "WARM"
        for row in rows
    )
    cold_opportunities = sum(
        row[
            "tier_before"
        ]
        == "COLD"
        for row in rows
    )
    warm_restores = sum(
        row[
            "tier_before"
        ]
        == "WARM"
        for row in restore_rows
    )
    cold_restores = sum(
        row[
            "tier_before"
        ]
        == "COLD"
        for row in restore_rows
    )

    warm_restore_latencies = [
        row[
            "read_ns"
        ]
        for row in restore_rows
        if row[
            "tier_before"
        ]
        == "WARM"
    ]
    cold_restore_latencies = [
        row[
            "read_ns"
        ]
        for row in restore_rows
        if row[
            "tier_before"
        ]
        == "COLD"
    ]

    return {
        "arm": arm,
        "prepared": prepared,
        "opportunities": len(
            rows
        ),
        "warm_opportunities": (
            warm_opportunities
        ),
        "cold_opportunities": (
            cold_opportunities
        ),
        "warm_restores": (
            warm_restores
        ),
        "cold_restores": (
            cold_restores
        ),
        "restore_count": len(
            restore_rows
        ),
        "all_restores_verified": all(
            row[
                "verified"
            ]
            for row in restore_rows
        ),
        "resident_mib_opportunity_integral": (
            resident_integral_mib
        ),
        "mean_pre_resident_fraction": (
            statistics.fmean(
                row[
                    "pre_resident_fraction"
                ]
                for row in rows
            )
        ),
        "warm_restore_pre_residency_median": (
            None
            if not warm_restore_latencies
            else statistics.median(
                row[
                    "pre_resident_fraction"
                ]
                for row in restore_rows
                if row[
                    "tier_before"
                ]
                == "WARM"
            )
        ),
        "cold_restore_pre_residency_median": (
            None
            if not cold_restore_latencies
            else statistics.median(
                row[
                    "pre_resident_fraction"
                ]
                for row in restore_rows
                if row[
                    "tier_before"
                ]
                == "COLD"
            )
        ),
        "warm_restore_median_ns": (
            None
            if not warm_restore_latencies
            else statistics.median(
                warm_restore_latencies
            )
        ),
        "cold_restore_median_ns": (
            None
            if not cold_restore_latencies
            else statistics.median(
                cold_restore_latencies
            )
        ),
        "total_restore_ns": sum(
            row[
                "read_ns"
            ]
            for row in restore_rows
        ),
        "total_storage_read_bytes": sum(
            (
                row[
                    "read_bytes_delta"
                ]
                or 0
            )
            for row in restore_rows
        ),
        "prefetch_bytes": sum(
            row[
                "prefetch_bytes"
            ]
            for row in rows
        ),
        "peak_memory_current_delta_bytes": (
            peak_memory_current_delta
        ),
        "drift_alarm_steps": (
            drift_alarm_steps
        ),
        "final_tier": tier,
        "rows": rows,
    }


def run_panel() -> dict[str, Any]:
    schedule = _schedule()

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-030-"
    ) as tmp:
        root = Path(tmp)
        arms = {
            arm: _run_arm(
                root=root,
                arm=arm,
                schedule=schedule,
            )
            for arm in ARMS
        }

    warm = arms[
        "ALWAYS_WARM"
    ]
    cold = arms[
        "ALWAYS_COLD"
    ]
    governor = arms[
        "LIFECYCLE_GOVERNOR"
    ]

    checks = {
        "frozen_schedule_has_17_reuses": (
            sum(schedule)
            == 17
        ),
        "all_arms_restore_every_reuse": all(
            row[
                "restore_count"
            ]
            == sum(
                schedule
            )
            for row in arms.values()
        ),
        "all_restore_integrity_passes": all(
            row[
                "all_restores_verified"
            ]
            for row in arms.values()
        ),
        "warm_control_is_physically_warm_on_reuse": (
            warm[
                "warm_restore_pre_residency_median"
            ]
            is not None
            and warm[
                "warm_restore_pre_residency_median"
            ]
            >= 0.95
        ),
        "cold_control_is_physically_cold_on_reuse": (
            cold[
                "cold_restore_pre_residency_median"
            ]
            is not None
            and cold[
                "cold_restore_pre_residency_median"
            ]
            <= 0.10
        ),
        "governor_uses_both_tiers": (
            governor[
                "warm_opportunities"
            ]
            > 0
            and governor[
                "cold_opportunities"
            ]
            > 0
        ),
        "governor_uses_fewer_cold_restores_than_always_cold": (
            0
            < governor[
                "cold_restores"
            ]
            < cold[
                "cold_restores"
            ]
        ),
        "governor_reduces_residency_integral_vs_always_warm": (
            governor[
                "resident_mib_opportunity_integral"
            ]
            < warm[
                "resident_mib_opportunity_integral"
            ]
        ),
        "governor_keeps_more_residency_than_always_cold": (
            governor[
                "resident_mib_opportunity_integral"
            ]
            > cold[
                "resident_mib_opportunity_integral"
            ]
        ),
        "governor_alarm_occurs_after_drift": (
            bool(
                governor[
                    "drift_alarm_steps"
                ]
            )
            and governor[
                "drift_alarm_steps"
            ][0]
            > PRE_OBSERVATIONS
        ),
        "governor_alarm_is_timely_in_frozen_trace": (
            governor[
                "drift_alarm_steps"
            ][0]
            <= (
                PRE_OBSERVATIONS
                + 20
            )
        ),
        "governor_finishes_warm_after_high_reuse_phase": (
            governor[
                "final_tier"
            ]
            == "WARM"
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
            "HOSTED_PHYSICAL_REUSE_EVIDENCE_LIFECYCLE_GOVERNOR_PILOT"
        ),
        "fixture": {
            "state_mib": (
                STATE_MIB
            ),
            "seed": SEED,
            "pre_reuse_probability": (
                PRE_REUSE_P
            ),
            "post_reuse_probability": (
                POST_REUSE_P
            ),
            "pre_observations": (
                PRE_OBSERVATIONS
            ),
            "post_observations": (
                POST_OBSERVATIONS
            ),
            "reuse_ceiling": (
                REUSE_CEILING
            ),
            "confidence": (
                CONFIDENCE
            ),
            "recent_window": (
                RECENT_WINDOW
            ),
            "drift_threshold": (
                DRIFT_THRESHOLD
            ),
            "reuse_count": sum(
                schedule
            ),
        },
        "arms": arms,
        "checks": checks,
        "decision": (
            "CONNECT_REUSE_EVIDENCE_LIFECYCLE_TO_REAL_WARM_COLD_PAGECACHE_ACTUATION"
        ),
        "evidence_boundary": (
            "Reuse schedule and reuse semantics are synthetic. File page-cache "
            "residency, POSIX_FADV_DONTNEED, physical restore, anonymous hot "
            "materialization, process I/O counters and integrity checks are "
            "hosted physical Linux observations."
        ),
        "next": (
            "REPLACE_FIXED_10PCT_REUSE_CEILING_WITH_THE_FULL_FR_FP_025_026_RISK_AWARE_DECISION_SURFACE"
        ),
        "claim_ceiling": (
            "HOSTED_PHYSICAL_TIER_ACTUATION_ON_ONE_SYNTHETIC_TWO_PHASE_REUSE_TRACE_ONLY"
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
