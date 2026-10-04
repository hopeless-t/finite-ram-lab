from __future__ import annotations

import json
import statistics
from typing import Any

from finite_ram_lab.fr_fp_025_risk_aware_tier_frontier import (
    _build_empirical_priors,
    _load,
)
from finite_ram_lab.fr_fp_026_reuse_ceiling import (
    reuse_ceiling,
)

SCHEMA = "finite-ram-lab.fr-fp-033-calibration-decision-relevance/v0.1"

MEMORY_SHADOW_PRICE_MS_PER_MIB = 1.0
DEADLINE_MS = 25.0
MISS_TOLERANCE = 0.05
EPSILON = 1e-12


def _risk_ceiling(
    baseline_ms: float,
    *,
    training_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    priors = _build_empirical_priors(
        training_rows
    )

    return reuse_ceiling(
        baseline_ms=baseline_ms,
        memory_shadow_price_ms_per_mib=(
            MEMORY_SHADOW_PRICE_MS_PER_MIB
        ),
        deadline_ms=DEADLINE_MS,
        miss_tolerance=MISS_TOLERANCE,
        residuals=priors["residual"],
        warm_ms=priors["warm_ms"],
    )


def run_panel() -> dict[str, Any]:
    data = _load()
    rows = data["rows"]
    results = []

    for index, current in enumerate(
        rows
    ):
        training = [
            row
            for cursor, row
            in enumerate(rows)
            if cursor != index
        ]

        cold = [
            float(value)
            for value
            in current["cold8_ms"]
        ]
        first_baseline = cold[0]
        two_probe_baseline = min(
            cold[0],
            cold[1],
        )

        first = _risk_ceiling(
            first_baseline,
            training_rows=training,
        )
        two = _risk_ceiling(
            two_probe_baseline,
            training_rows=training,
        )

        first_ceiling = (
            first[
                "reuse_probability_ceiling"
            ]
        )
        two_ceiling = (
            two[
                "reuse_probability_ceiling"
            ]
        )

        early_stop = (
            first_ceiling
            >= 1.0
            - EPSILON
        )

        results.append(
            {
                "run_id": (
                    current["run_id"]
                ),
                "first_probe_ms": (
                    first_baseline
                ),
                "second_probe_ms": (
                    cold[1]
                ),
                "two_probe_min_ms": (
                    two_probe_baseline
                ),
                "first_probe_reuse_ceiling": (
                    first_ceiling
                ),
                "two_probe_reuse_ceiling": (
                    two_ceiling
                ),
                "early_stop_after_one_probe": (
                    early_stop
                ),
                "early_stop_preserves_ceiling_one": (
                    (
                        not early_stop
                    )
                    or (
                        two_ceiling
                        >= 1.0
                        - EPSILON
                    )
                ),
                "second_probe_changes_surface": (
                    abs(
                        two_ceiling
                        - first_ceiling
                    )
                    > EPSILON
                ),
                "counterfactual_saved_probe_ms": (
                    cold[1]
                    if early_stop
                    else 0.0
                ),
            }
        )

    early_stop_rows = [
        row
        for row in results
        if row[
            "early_stop_after_one_probe"
        ]
    ]
    changed_rows = [
        row
        for row in results
        if row[
            "second_probe_changes_surface"
        ]
    ]

    saved_probe_ms = [
        row[
            "counterfactual_saved_probe_ms"
        ]
        for row in early_stop_rows
    ]

    checks = {
        "fifteen_runs_leave_one_out": (
            len(results) == 15
        ),
        "early_stop_occurs_in_at_least_one_run": (
            bool(early_stop_rows)
        ),
        "early_stop_never_changes_unconstrained_ceiling": all(
            row[
                "early_stop_preserves_ceiling_one"
            ]
            for row in early_stop_rows
        ),
        "second_probe_is_not_globally_irrelevant": (
            bool(changed_rows)
        ),
        "policy_inputs_are_explicit": (
            MEMORY_SHADOW_PRICE_MS_PER_MIB
            > 0.0
            and DEADLINE_MS > 0.0
            and 0.0
            < MISS_TOLERANCE
            < 1.0
        ),
        "saved_probe_cost_is_positive_when_stopping": (
            all(
                value > 0.0
                for value in saved_probe_ms
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
            "LEAVE_ONE_RUN_OUT_DECISION_RELEVANCE_GATE_FOR_SECOND_COLD_CALIBRATION_PROBE"
        ),
        "source": {
            "runs": len(results),
            "new_physical_runs": 0,
            "state_mib": 8,
        },
        "policy": {
            "memory_shadow_price_ms_per_mib": (
                MEMORY_SHADOW_PRICE_MS_PER_MIB
            ),
            "deadline_ms": (
                DEADLINE_MS
            ),
            "miss_tolerance": (
                MISS_TOLERANCE
            ),
            "baseline_estimator": (
                "TWO_PROBE_MIN"
            ),
        },
        "law": {
            "monotonicity": (
                "TWO_PROBE_MIN can only keep or lower the first-probe baseline"
            ),
            "early_stop_condition": (
                "if first-probe reuse ceiling == 1, the second probe cannot make reuse decision-relevant"
            ),
            "continue_condition": (
                "if first-probe reuse ceiling < 1, retain the second probe because it may change the decision surface"
            ),
        },
        "summary": {
            "early_stop_runs": (
                len(early_stop_rows)
            ),
            "full_two_probe_runs": (
                len(results)
                - len(early_stop_rows)
            ),
            "surface_change_runs": (
                len(changed_rows)
            ),
            "unsafe_early_stops": sum(
                not row[
                    "early_stop_preserves_ceiling_one"
                ]
                for row in early_stop_rows
            ),
            "total_counterfactual_probe_ms_saved": (
                sum(saved_probe_ms)
            ),
            "median_counterfactual_saved_probe_ms": (
                None
                if not saved_probe_ms
                else statistics.median(
                    saved_probe_ms
                )
            ),
        },
        "rows": results,
        "checks": checks,
        "decision": (
            "EARLY_STOP_COLD_CALIBRATION_ONLY_WHEN_THE_FIRST_PROBE_ALREADY_MAKES_REUSE_DECISION_IRRELEVANT"
        ),
        "meta_transfer": (
            "decision-relevance pruning replicated in a second independent plane: calibration measurement rather than reuse monitoring"
        ),
        "claim_ceiling": (
            "LEAVE_ONE_RUN_OUT_EARLY_STOP_BACKTEST_ON_FIFTEEN_8MIB_HOSTED_RESTORE_RUNS_AND_ONE_POLICY_POINT_ONLY"
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
