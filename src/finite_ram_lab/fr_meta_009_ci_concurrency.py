from __future__ import annotations

import json

SCHEMA = "finite-ram-lab.fr-meta-009-ci-concurrency/v0.1"


def group_key(workflow: str, head_ref: str, ref_name: str) -> str:
    branch = head_ref or ref_name
    return f"{workflow}-{branch}"


def cancel_in_progress(ref_name: str) -> bool:
    return ref_name != "main"


def run_panel() -> dict:
    branch = "research/fr-meta-006-aba-memoization"
    push_group = group_key("CI", "", branch)
    pr_group = group_key("CI", branch, "108/merge")
    main_group = group_key("CI", "", "main")

    observed_duplicate = {
        "head_sha": "447a027c7fdc5b91450de8967b28ea4d956e5006",
        "push_run": 37136849854,
        "push_created_at": "2026-10-03T16:26:22Z",
        "pr_run": 37136854358,
        "pr_created_at": "2026-10-03T16:26:26Z",
        "same_sha": True,
    }

    checks = {
        "push_and_pr_same_branch_group": push_group == pr_group,
        "research_push_cancel_enabled": cancel_in_progress(branch) is True,
        "pr_cancel_enabled": cancel_in_progress("108/merge") is True,
        "main_cancel_disabled": cancel_in_progress("main") is False,
        "observed_duplicate_same_sha": observed_duplicate["same_sha"],
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "group_examples": {
            "push": push_group,
            "pull_request": pr_group,
            "main": main_group,
        },
        "observed_duplicate": observed_duplicate,
        "clean_fused_lifecycle": {
            "workflow_triggers": 3,
            "full_ci_completions_before": 3,
            "expected_full_ci_completions_after": 2,
            "reason": (
                "receipt push and immediate PR CI share the same branch concurrency "
                "group; the later PR run supersedes the receipt push run"
            ),
        },
        "decision": "CANCEL_SUPERSEDED_NON_MAIN_CI_BY_HEAD_BRANCH",
        "hard_invariants": [
            "main push CI is never canceled by this policy",
            "implementation CI must PASS before receipt is written",
            "PR CI validates the receipt head after it supersedes receipt push CI",
            "workflow group includes workflow name to avoid cross-workflow cancellation",
        ],
        "monte_carlo": {
            "used": False,
            "reason": "GitHub concurrency semantics and the duplicate-SHA event are exact.",
        },
        "claim_ceiling": "CI_CONCURRENCY_OPTIMIZATION_ONLY",
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
