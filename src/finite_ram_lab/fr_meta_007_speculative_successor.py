from __future__ import annotations

import json

SCHEMA = "finite-ram-lab.fr-meta-007-speculative-successor/v0.2"


def transition(parent_state: str, child_state: str) -> dict:
    if child_state != "DETACHED_PROVISIONAL":
        raise ValueError("child_must_begin_detached_provisional")

    if parent_state == "RECEIPT_FROZEN":
        return {
            "decision": "PUBLISH_CHILD_REF",
            "child_authority": "CANDIDATE",
            "workflow_allowed": True,
        }

    if parent_state == "QUALIFIED_PASS":
        return {
            "decision": "WAIT_FOR_PARENT_RECEIPT",
            "child_authority": "PROVISIONAL_ONLY",
            "workflow_allowed": False,
        }

    if parent_state in ("FAIL", "UNKNOWN", "IN_PROGRESS"):
        return {
            "decision": "DO_NOT_PUBLISH_CHILD_REF",
            "child_authority": "PROVISIONAL_ONLY",
            "workflow_allowed": False,
        }

    raise ValueError(f"unknown_parent_state:{parent_state}")


def run_panel() -> dict:
    receipt_case = transition("RECEIPT_FROZEN", "DETACHED_PROVISIONAL")
    pass_case = transition("QUALIFIED_PASS", "DETACHED_PROVISIONAL")
    fail_case = transition("FAIL", "DETACHED_PROVISIONAL")
    unknown_case = transition("UNKNOWN", "DETACHED_PROVISIONAL")
    in_progress_case = transition("IN_PROGRESS", "DETACHED_PROVISIONAL")

    checks = {
        "receipt_can_publish": receipt_case["workflow_allowed"] is True,
        "pass_waits_for_receipt": pass_case["decision"] == "WAIT_FOR_PARENT_RECEIPT",
        "fail_cannot_publish": fail_case["workflow_allowed"] is False,
        "unknown_cannot_publish": unknown_case["workflow_allowed"] is False,
        "in_progress_cannot_publish": in_progress_case["workflow_allowed"] is False,
        "unknown_is_not_receipt": unknown_case["decision"] != receipt_case["decision"],
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "protocol": {
            "max_speculative_depth": 1,
            "build_surface": "UNREFERENCED_GIT_OBJECTS_ONLY",
            "publish_gate": "PARENT_RECEIPT_FROZEN_ONLY",
            "qualified_without_receipt": "KEEP_DETACHED_PROVISIONAL",
            "failed_or_unknown_parent": "NO_BRANCH_REF_NO_WORKFLOW_NO_AUTHORITY",
        },
        "decision": "BUILD_AHEAD_DETACHED_PUBLISH_AFTER_RECEIPT",
        "claim_ceiling": "SPECULATIVE_DETACHED_BUILD_PROTOCOL_ONLY",
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
