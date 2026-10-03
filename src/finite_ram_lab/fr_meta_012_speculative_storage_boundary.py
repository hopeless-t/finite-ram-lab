from __future__ import annotations

import json

SCHEMA = "finite-ram-lab.fr-meta-012-speculative-storage-boundary/v0.1"

OBSERVED_FAILURE = {
    "prepared_commit": "5f8b37de4694652064eeef7f468294de5f4c5fb0",
    "contents_api": "404_NO_COMMIT_FOUND_FOR_REF",
    "git_commit_api": "404_NOT_FOUND",
}


def classify_prepared_storage(kind: str) -> dict:
    if kind == "UNREFERENCED_GIT_OBJECT":
        return {
            "durable": False,
            "canonical": False,
            "allowed_role": "EPHEMERAL_OPTIMIZATION_ONLY",
        }
    if kind == "ACTIVE_TURN_DRAFT":
        return {
            "durable": False,
            "canonical": False,
            "allowed_role": "EPHEMERAL_BUILD_AHEAD",
        }
    if kind == "POST_RECEIPT_COMMIT":
        return {
            "durable": True,
            "canonical": True,
            "allowed_role": "FINAL_CANDIDATE",
        }
    raise ValueError(f"unknown_storage_kind:{kind}")


def run_panel() -> dict:
    unreferenced = classify_prepared_storage("UNREFERENCED_GIT_OBJECT")
    draft = classify_prepared_storage("ACTIVE_TURN_DRAFT")
    final = classify_prepared_storage("POST_RECEIPT_COMMIT")

    checks = {
        "unreferenced_not_durable": unreferenced["durable"] is False,
        "unreferenced_not_canonical": unreferenced["canonical"] is False,
        "draft_not_canonical": draft["canonical"] is False,
        "final_is_durable": final["durable"] is True,
        "final_is_canonical": final["canonical"] is True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "observed_failure": OBSERVED_FAILURE,
        "decision": "EPHEMERAL_BUILD_AHEAD_DURABLE_MATERIALIZATION_AFTER_RECEIPT",
        "protocol": {
            "build_ahead": (
                "Reasoning/source drafting may happen while parent CI runs, "
                "but no durability claim is made."
            ),
            "unreferenced_git_objects": (
                "May be used opportunistically inside one active operation, "
                "but are not a durable handoff/cache contract."
            ),
            "canonical_materialization": (
                "Create the final Git commit only after the parent receipt is frozen."
            ),
            "speculative_depth": 1,
        },
        "hard_invariants": [
            "no child branch before parent receipt",
            "no authority from ephemeral drafts",
            "no recovery assumption from unreferenced Git object SHA",
            "repository state wins over remembered speculative state",
        ],
        "claim_ceiling": "SPECULATIVE_STORAGE_RELIABILITY_BOUNDARY_ONLY",
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
