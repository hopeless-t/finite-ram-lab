from __future__ import annotations

import json
import random
import statistics

SCHEMA = "finite-ram-lab.fr-meta-004-loop-speed-governor/v0.2"

OBSERVED = (
    {"pr": 103, "commits": 6, "push_runs": 8, "pr_runs": 2, "total_runs": 10},
    {"pr": 104, "commits": 6, "push_runs": 8, "pr_runs": 2, "total_runs": 10},
    {"pr": 105, "commits": 6, "push_runs": 8, "pr_runs": 2, "total_runs": 10},
)

# Full qualified lifecycle:
# initial atomic bundle -> CI + dedicated qualification (2 push runs)
# qualification receipt -> ordinary CI only (1 push run)
# open PR after receipt -> ordinary PR CI (1 PR run)
BUNDLED_EXPECTATION = {
    "commits": 2,
    "push_runs": 3,
    "pr_runs": 1,
    "total_runs": 4,
}


def exact_fanout() -> dict:
    mean_commits = statistics.fmean(row["commits"] for row in OBSERVED)
    mean_runs = statistics.fmean(row["total_runs"] for row in OBSERVED)
    mean_push = statistics.fmean(row["push_runs"] for row in OBSERVED)
    return {
        "observed_prs": [row["pr"] for row in OBSERVED],
        "baseline_mean_commits": mean_commits,
        "baseline_mean_total_runs": mean_runs,
        "baseline_mean_push_runs": mean_push,
        "bundled_expected_commits": BUNDLED_EXPECTATION["commits"],
        "bundled_expected_total_runs": BUNDLED_EXPECTATION["total_runs"],
        "bundled_expected_push_runs": BUNDLED_EXPECTATION["push_runs"],
        "commit_reduction_fraction": 1.0 - BUNDLED_EXPECTATION["commits"] / mean_commits,
        "workflow_run_reduction_fraction": 1.0 - BUNDLED_EXPECTATION["total_runs"] / mean_runs,
        "push_run_reduction_fraction": 1.0 - BUNDLED_EXPECTATION["push_runs"] / mean_push,
    }


def monte_carlo_rework_sensitivity(*, trials: int = 20000, seed: int = 20261004) -> dict:
    rng = random.Random(seed)
    scenarios = []
    for defect_p in (0.05, 0.15, 0.30):
        for diagnosis_penalty in (1.0, 3.0, 6.0):
            wins = 0
            deltas = []
            for _ in range(trials):
                baseline = 10.0
                candidate = 4.0
                if rng.random() < defect_p:
                    candidate += diagnosis_penalty
                delta = baseline - candidate
                deltas.append(delta)
                wins += delta > 0.0
            scenarios.append({
                "defect_probability": defect_p,
                "diagnosis_penalty_run_units": diagnosis_penalty,
                "candidate_win_rate": wins / trials,
                "mean_run_unit_savings": statistics.fmean(deltas),
            })
    return {
        "trials_per_scenario": trials,
        "seed": seed,
        "scenarios": scenarios,
        "all_mean_savings_positive": all(
            row["mean_run_unit_savings"] > 0.0 for row in scenarios
        ),
        "claim": "SYNTHETIC_REWORK_SENSITIVITY_ONLY",
    }


def governor_decision() -> dict:
    exact = exact_fanout()
    mc = monte_carlo_rework_sensitivity()
    checks = {
        "observed_baseline_has_redundant_fanout": exact["baseline_mean_total_runs"] > 4.0,
        "commit_reduction_ge_60pct": exact["commit_reduction_fraction"] >= 0.60,
        "workflow_reduction_ge_50pct": exact["workflow_run_reduction_fraction"] >= 0.50,
        "mc_mean_savings_positive": mc["all_mean_savings_positive"],
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "decision": "ASSEMBLE_DETACHED_ATOMIC_COMMIT_THEN_PUBLISH_BRANCH",
        "receipt_rule": "QUALIFY_FIRST_THEN_ONE_RECEIPT_COMMIT_THEN_OPEN_PR",
        "fallback": "IF_QUALIFICATION_FAILS_CREATE_ONE_EXPLICIT_FIX_COMMIT",
        "forbidden": [
            "force_push_over_evidence",
            "skip_tests_to_gain_speed",
            "collapse_unknown_to_success",
            "expand_execution_authority",
        ],
        "exact": exact,
        "monte_carlo": mc,
    }


def main() -> int:
    print(json.dumps({
        "schema": SCHEMA,
        **governor_decision(),
        "claim_ceiling": "REPOSITORY_WORKFLOW_FANOUT_OPTIMIZATION_ONLY",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
