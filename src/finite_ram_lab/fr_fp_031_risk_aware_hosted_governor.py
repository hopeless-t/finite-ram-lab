from __future__ import annotations

import json
import statistics
import tempfile
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_fp_016_restore_size_scaling import (
    _fadvise_dontneed,
    _file_residency,
    _prepare_tier,
    _restore,
)
from finite_ram_lab.fr_fp_025_risk_aware_tier_frontier import (
    _build_empirical_priors,
    _load as _load_restore_evidence,
)
from finite_ram_lab.fr_fp_026_reuse_ceiling import (
    reuse_ceiling,
)
from finite_ram_lab.fr_fp_027_reuse_evidence_budget import (
    clopper_pearson_upper,
)
from finite_ram_lab.fr_fp_030_hosted_reuse_lifecycle import (
    ARMS as CONTROL_ARMS,
    CONFIDENCE,
    DRIFT_THRESHOLD,
    MARKER,
    PRE_OBSERVATIONS,
    RECENT_WINDOW,
    REUSE_CEILING as FIXED_REUSE_CEILING,
    SIZE_BYTES,
    STATE_MIB,
    _enforce_tier,
    _proc_read_bytes,
    _run_arm,
    _schedule,
)

SCHEMA = "finite-ram-lab.fr-fp-031-risk-aware-hosted-governor/v0.1"

MEMORY_SHADOW_PRICE_MS_PER_MIB = 1.0
DEADLINE_MS = 25.0
MISS_TOLERANCE = 0.05
CALIBRATION_PROBES = 2
CALIBRATION_MARKER = 131

POLICY_ARMS = (
    "FIXED_10PCT_GOVERNOR",
    "RISK_AWARE_GOVERNOR",
)


def _current_run_cold_baseline(
    root: Path,
) -> dict[str, Any]:
    path = root / "calibration.bin"

    prepared = _prepare_tier(
        path,
        size_bytes=SIZE_BYTES,
        marker=CALIBRATION_MARKER,
        cold=True,
    )

    if not prepared["verified"]:
        raise RuntimeError(
            "calibration_prepare_failed"
        )

    rows = []

    try:
        for probe in range(
            1,
            CALIBRATION_PROBES + 1,
        ):
            pre = _file_residency(
                path
            )[
                "resident_fraction"
            ]
            restored = _restore(
                path,
                size_bytes=SIZE_BYTES,
                marker=CALIBRATION_MARKER,
            )

            if not restored["verified"]:
                raise RuntimeError(
                    "calibration_restore_failed"
                )

            rows.append(
                {
                    "probe": probe,
                    "pre_resident_fraction": pre,
                    "read_ns": restored[
                        "read_ns"
                    ],
                    "read_ms": (
                        restored[
                            "read_ns"
                        ]
                        / 1_000_000.0
                    ),
                }
            )

            _fadvise_dontneed(
                path
            )

        baseline = min(
            row["read_ms"]
            for row in rows
        )

        return {
            "baseline_estimator": (
                "TWO_PROBE_MIN"
            ),
            "baseline_ms": baseline,
            "rows": rows,
            "all_pre_restore_cold": all(
                row[
                    "pre_resident_fraction"
                ]
                <= 0.10
                for row in rows
            ),
            "total_probe_ms": sum(
                row["read_ms"]
                for row in rows
            ),
        }

    finally:
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


def _upper(
    history: list[bool],
) -> float:
    if not history:
        return 1.0

    return clopper_pearson_upper(
        reused=sum(history),
        observations=len(history),
        confidence=CONFIDENCE,
    )


def _next_state(
    *,
    history: list[bool],
    recent: list[bool],
    ever_qualified: bool,
    opportunity: int,
    drift_alarm_steps: list[int],
    reuse_ceiling_value: float,
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
        and sum(recent)
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

    if (
        upper
        <= reuse_ceiling_value
    ):
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


def _run_governor_arm(
    *,
    root: Path,
    arm: str,
    schedule: list[bool],
    reuse_ceiling_value: float,
) -> dict[str, Any]:
    path = root / (
        arm.lower()
        + ".bin"
    )
    prepared = _prepare_tier(
        path,
        size_bytes=SIZE_BYTES,
        marker=MARKER,
        cold=False,
    )

    if not prepared["verified"]:
        raise RuntimeError(
            "prepare_verify_failed"
        )

    tier = "WARM"
    history: list[bool] = []
    recent: list[bool] = []
    ever_qualified = False
    drift_alarm_steps: list[int] = []
    rows = []
    restore_rows = []
    resident_integral_mib = 0.0

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
        ) = _next_state(
            history=history,
            recent=recent,
            ever_qualified=(
                ever_qualified
            ),
            opportunity=opportunity,
            drift_alarm_steps=(
                drift_alarm_steps
            ),
            reuse_ceiling_value=(
                reuse_ceiling_value
            ),
        )

        enforcement = _enforce_tier(
            path,
            tier=tier,
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
                "reused": reused,
                "tier_before": (
                    tier_before
                ),
                "tier_after": tier,
                "reuse_upper": upper,
                "reuse_ceiling": (
                    reuse_ceiling_value
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

    warm_restores = [
        row
        for row in restore_rows
        if row[
            "tier_before"
        ]
        == "WARM"
    ]
    cold_restores = [
        row
        for row in restore_rows
        if row[
            "tier_before"
        ]
        == "COLD"
    ]

    return {
        "arm": arm,
        "reuse_ceiling": (
            reuse_ceiling_value
        ),
        "warm_opportunities": sum(
            row[
                "tier_before"
            ]
            == "WARM"
            for row in rows
        ),
        "cold_opportunities": sum(
            row[
                "tier_before"
            ]
            == "COLD"
            for row in rows
        ),
        "warm_restores": len(
            warm_restores
        ),
        "cold_restores": len(
            cold_restores
        ),
        "all_restores_verified": all(
            row["verified"]
            for row in restore_rows
        ),
        "resident_mib_opportunity_integral": (
            resident_integral_mib
        ),
        "total_restore_ns": sum(
            row["read_ns"]
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
        "warm_restore_median_ns": (
            None
            if not warm_restores
            else statistics.median(
                row["read_ns"]
                for row in warm_restores
            )
        ),
        "cold_restore_median_ns": (
            None
            if not cold_restores
            else statistics.median(
                row["read_ns"]
                for row in cold_restores
            )
        ),
        "drift_alarm_steps": (
            drift_alarm_steps
        ),
        "final_tier": tier,
        "rows": rows,
    }


def run_panel() -> dict[str, Any]:
    schedule = _schedule()
    evidence = (
        _load_restore_evidence()
    )
    priors = (
        _build_empirical_priors(
            evidence["rows"]
        )
    )

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-031-"
    ) as tmp:
        root = Path(tmp)

        calibration = (
            _current_run_cold_baseline(
                root
            )
        )
        risk = reuse_ceiling(
            baseline_ms=(
                calibration[
                    "baseline_ms"
                ]
            ),
            memory_shadow_price_ms_per_mib=(
                MEMORY_SHADOW_PRICE_MS_PER_MIB
            ),
            deadline_ms=(
                DEADLINE_MS
            ),
            miss_tolerance=(
                MISS_TOLERANCE
            ),
            residuals=(
                priors[
                    "residual"
                ]
            ),
            warm_ms=(
                priors[
                    "warm_ms"
                ]
            ),
        )
        dynamic_ceiling = (
            risk[
                "reuse_probability_ceiling"
            ]
        )

        controls = {
            arm: _run_arm(
                root=root,
                arm=arm,
                schedule=schedule,
            )
            for arm in (
                "ALWAYS_WARM",
                "ALWAYS_COLD",
            )
        }

        fixed = _run_governor_arm(
            root=root,
            arm=(
                "FIXED_10PCT_GOVERNOR"
            ),
            schedule=schedule,
            reuse_ceiling_value=(
                FIXED_REUSE_CEILING
            ),
        )
        adaptive = (
            _run_governor_arm(
                root=root,
                arm=(
                    "RISK_AWARE_GOVERNOR"
                ),
                schedule=schedule,
                reuse_ceiling_value=(
                    dynamic_ceiling
                ),
            )
        )

    warm = controls[
        "ALWAYS_WARM"
    ]
    cold = controls[
        "ALWAYS_COLD"
    ]

    direction_ok = (
        (
            dynamic_ceiling
            >= FIXED_REUSE_CEILING
            and adaptive[
                "cold_opportunities"
            ]
            >= fixed[
                "cold_opportunities"
            ]
        )
        or (
            dynamic_ceiling
            < FIXED_REUSE_CEILING
            and adaptive[
                "cold_opportunities"
            ]
            <= fixed[
                "cold_opportunities"
            ]
        )
    )

    checks = {
        "two_physical_cold_calibration_probes_verify": (
            len(
                calibration[
                    "rows"
                ]
            )
            == 2
            and calibration[
                "all_pre_restore_cold"
            ]
        ),
        "dynamic_reuse_ceiling_is_valid_probability": (
            0.0
            <= dynamic_ceiling
            <= 1.0
        ),
        "all_policy_restores_verify": (
            fixed[
                "all_restores_verified"
            ]
            and adaptive[
                "all_restores_verified"
            ]
        ),
        "risk_aware_policy_moves_in_the_direction_implied_by_its_ceiling": (
            direction_ok
        ),
        "adaptive_residency_is_bounded_by_physical_controls": (
            cold[
                "resident_mib_opportunity_integral"
            ]
            <= adaptive[
                "resident_mib_opportunity_integral"
            ]
            <= warm[
                "resident_mib_opportunity_integral"
            ]
        ),
        "adaptive_cold_restore_count_is_bounded_by_controls": (
            0
            <= adaptive[
                "cold_restores"
            ]
            <= cold[
                "cold_restores"
            ]
        ),
        "adaptive_storage_reads_are_bounded_by_controls": (
            0
            <= adaptive[
                "total_storage_read_bytes"
            ]
            <= cold[
                "total_storage_read_bytes"
            ]
        ),
        "dynamic_policy_inputs_are_explicit": (
            MEMORY_SHADOW_PRICE_MS_PER_MIB
            > 0.0
            and DEADLINE_MS
            > 0.0
            and 0.0
            < MISS_TOLERANCE
            < 1.0
        ),
        "risk_ceiling_reports_binding_constraint": (
            bool(
                risk[
                    "binding_constraints"
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
            "HOSTED_PHYSICAL_RISK_AWARE_WARM_COLD_GOVERNOR_PILOT"
        ),
        "fixture": {
            "state_mib": (
                STATE_MIB
            ),
            "reuse_count": sum(
                schedule
            ),
            "fixed_reuse_ceiling": (
                FIXED_REUSE_CEILING
            ),
            "memory_shadow_price_ms_per_mib": (
                MEMORY_SHADOW_PRICE_MS_PER_MIB
            ),
            "deadline_ms": (
                DEADLINE_MS
            ),
            "miss_tolerance": (
                MISS_TOLERANCE
            ),
            "drift_threshold": (
                DRIFT_THRESHOLD
            ),
            "recent_window": (
                RECENT_WINDOW
            ),
        },
        "calibration": (
            calibration
        ),
        "risk_surface": risk,
        "controls": controls,
        "fixed_governor": fixed,
        "risk_aware_governor": (
            adaptive
        ),
        "checks": checks,
        "decision": (
            "DRIVE_HOSTED_TIER_ACTUATION_FROM_CURRENT_RUN_CALIBRATION_AND_EXPLICIT_RISK_POLICY_INSTEAD_OF_A_FIXED_REUSE_THRESHOLD"
        ),
        "evidence_boundary": (
            "Current-run COLD restore calibration and WARM/COLD page-cache "
            "actuation are hosted physical. Reuse schedule and application policy "
            "inputs are frozen synthetic pilot inputs. Residual/WARM priors are "
            "reused hosted evidence."
        ),
        "next": (
            "SWEEP_EXTERNAL_POLICY_INPUTS_AND_CURRENT_RUN_BASELINES_WITHOUT_HIDING_THEIR_TRADEOFFS_IN_ONE_UTILITY"
        ),
        "claim_ceiling": (
            "HOSTED_PHYSICAL_RISK_AWARE_TIER_ACTUATION_ON_ONE_SYNTHETIC_REUSE_TRACE_AND_ONE_POLICY_POINT_ONLY"
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
