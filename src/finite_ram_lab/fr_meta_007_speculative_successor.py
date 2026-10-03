from __future__ import annotations

import json

SCHEMA = "finite-ram-lab.fr-meta-007-speculative-successor/v0.1"


def transition(parent_state: str, child_state: str) -> dict:
    if child_state != "DETACHED_PROVISIONAL":
        raise ValueError("child_must_begin_detached_provisional")

    if parent_state == "QUALIFIED_PASS":
        return {
            "decision": "PUBLISH_CHILD_REF",
            "child_authority": "CANDIDATE",
            "workflow_allowed": True,
        }

    if parent_state in ("FAIL", "UNKNOWN", "IN_PROGRESS"):
        return {
            "decision": "DO_NOT_PUBLISH_CHILD_REF",
            "child_authority": "PROVISIONAL_ONLY",
            "workflow_allowed": False,
        }

    raise ValueError(f"unknown_parent_state:{parent_state}")


def run_panel() -> dict:
    pass_case = transition("QUALIFIED_PASS", "DETACHED_PROVISIONAL")
    fail_case = transition("FAIL", "DETACHED_PROVISIONAL")
    unknown_case = transition("UNKNOWN", "DETACHED_PROVISIONAL")
    in_progress_case = transition("IN_PROGRESS", "DETACHED_PROVISIONAL")

    checks = {
        "pass_can_publish": pass_case["workflow_allowed"] is True,
        "fail_cannot_publish": fail_case["workflow_allowed"] is False,
        "unknown_cannot_publish": unknown_case["workflow_allowed"] is False,
        "in_progress_cannot_publish": in_progress_case["workflow_allowed"] is False,
        "unknown_is_not_pass": unknown_case["decision"] != pass_case["decision"],
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "protocol": {
            "max_speculative_depth": 1,
            "build_surface": "UNREFERENCED_GIT_OBJECTS_ONLY",
            "publish_gate": "PARENT_QUALIFIED_PASS_ONLY",
            "failed_or_unknown_parent": "NO_BRANCH_REF_NO_WORKFLOW_NO_AUTHORITY",
        },
        "decision": "BUILD_AHEAD_DETACHED_PUBLISH_AFTER_PROOF",
        "claim_ceiling": "SPECULATIVE_DETACHED_BUILD_PROTOCOL_ONLY",
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
