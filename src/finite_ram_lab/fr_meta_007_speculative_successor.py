from __future__ import annotations

import json

SCHEMA = "finite-ram-lab.fr-meta-007-speculative-successor/v0.3"


def transition(parent_state: str, child_state: str) -> dict:
    if child_state != "DETACHED_PROVISIONAL":
        raise ValueError("child_must_begin_detached_provisional")

    if parent_state == "RECEIPT_FROZEN":
        return {
            "decision": "MATERIALIZE_DELTA_ON_RECEIPT_THEN_PUBLISH",
            "child_authority": "PROVISIONAL_UNTIL_MATERIALIZED",
            "workflow_allowed_after_materialization": True,
            "direct_publish_pre_receipt_commit": False,
        }

    if parent_state == "QUALIFIED_PASS":
        return {
            "decision": "WAIT_FOR_PARENT_RECEIPT",
            "child_authority": "PROVISIONAL_ONLY",
            "workflow_allowed_after_materialization": False,
            "direct_publish_pre_receipt_commit": False,
        }

    if parent_state in ("FAIL", "UNKNOWN", "IN_PROGRESS"):
        return {
            "decision": "DO_NOT_PUBLISH_CHILD",
            "child_authority": "PROVISIONAL_ONLY",
            "workflow_allowed_after_materialization": False,
            "direct_publish_pre_receipt_commit": False,
        }

    raise ValueError(f"unknown_parent_state:{parent_state}")


def run_panel() -> dict:
    receipt_case = transition("RECEIPT_FROZEN", "DETACHED_PROVISIONAL")
    pass_case = transition("QUALIFIED_PASS", "DETACHED_PROVISIONAL")
    fail_case = transition("FAIL", "DETACHED_PROVISIONAL")
    unknown_case = transition("UNKNOWN", "DETACHED_PROVISIONAL")
    in_progress_case = transition("IN_PROGRESS", "DETACHED_PROVISIONAL")

    checks = {
        "receipt_requires_materialization": (
            receipt_case["decision"]
            == "MATERIALIZE_DELTA_ON_RECEIPT_THEN_PUBLISH"
        ),
        "pre_receipt_sha_never_directly_published": (
            receipt_case["direct_publish_pre_receipt_commit"] is False
        ),
        "pass_waits_for_receipt": pass_case["decision"] == "WAIT_FOR_PARENT_RECEIPT",
        "fail_cannot_publish": fail_case["decision"] == "DO_NOT_PUBLISH_CHILD",
        "unknown_cannot_publish": unknown_case["decision"] == "DO_NOT_PUBLISH_CHILD",
        "in_progress_cannot_publish": (
            in_progress_case["decision"] == "DO_NOT_PUBLISH_CHILD"
        ),
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "protocol": {
            "max_speculative_depth": 1,
            "build_surface": "UNREFERENCED_GIT_OBJECTS_AS_PREPARED_DELTA",
            "publish_gate": "PARENT_RECEIPT_FROZEN_ONLY",
            "publication": (
                "REAPPLY_PREPARED_CHILD_DELTA_ON_PARENT_RECEIPT_TREE_"
                "THEN_CREATE_FINAL_CHILD_COMMIT_AND_REF"
            ),
            "qualified_without_receipt": "KEEP_DETACHED_PROVISIONAL",
            "failed_or_unknown_parent": "NO_BRANCH_REF_NO_WORKFLOW_NO_AUTHORITY",
        },
        "decision": "BUILD_AHEAD_DELTA_MATERIALIZE_AFTER_RECEIPT",
        "claim_ceiling": "SPECULATIVE_DETACHED_BUILD_PROTOCOL_ONLY",
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
