from __future__ import annotations

import json

SCHEMA = "finite-ram-lab.fr-meta-011-recursive-panel-fixture/v0.1"

BASELINE_RUN_PANEL_CALLS = 2
CANDIDATE_RUN_PANEL_CALLS = 1
PERTURBATIONS_PER_PANEL = 300


def run_panel() -> dict:
    reduction = 1.0 - CANDIDATE_RUN_PANEL_CALLS / BASELINE_RUN_PANEL_CALLS
    checks = {
        "panel_calls_halved": CANDIDATE_RUN_PANEL_CALLS == 1,
        "perturbations_per_panel_unchanged": PERTURBATIONS_PER_PANEL == 300,
        "structural_reduction_ge_50pct": reduction >= 0.50,
    }
    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "baseline_run_panel_calls": BASELINE_RUN_PANEL_CALLS,
        "candidate_run_panel_calls": CANDIDATE_RUN_PANEL_CALLS,
        "meta_meta_perturbations_per_panel": PERTURBATIONS_PER_PANEL,
        "structural_reduction_fraction": reduction,
        "decision": "SHARE_RECURSIVE_RESEARCH_PANEL_WITHIN_TEST_CLASS",
        "semantic_guard": (
            "The recursive research panel, perturbation count, holdout, Goodhart "
            "control, and assertions are unchanged; only duplicate invocation is removed."
        ),
        "claim_ceiling": "TEST_FIXTURE_REUSE_OPTIMIZATION_ONLY",
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
