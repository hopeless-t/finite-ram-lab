from __future__ import annotations

import json
import random
import statistics
from typing import Any, Iterable

SCHEMA = "finite-ram-lab.fr-meta-002-method-telemetry/v0.1"
CALL_BUDGET = 6
REHYDRATE_FILE_BUDGET = 5

NUMERIC_FIELDS = (
    "external_tool_calls",
    "max_calls_between_updates",
    "rehydrate_files",
    "rehydrate_bytes",
    "durable_transitions",
    "mc_trials",
    "failure_specimens",
    "branches_opened",
    "branches_closed",
    "frontier_gap_before",
    "frontier_gap_after",
)


def _known(value: Any) -> bool:
    return value is not None


def normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    required = ("event_id", "bounce_id", "protocol", "gap_class")
    missing = [key for key in required if key not in event]
    if missing:
        raise ValueError(f"missing_required:{','.join(missing)}")

    row = dict(event)
    for field in NUMERIC_FIELDS:
        row.setdefault(field, None)
    row.setdefault("authority_expanded", None)
    row.setdefault("stop_reason", None)
    row.setdefault("claim_class", None)
    return row


def assess_event(event: dict[str, Any]) -> dict[str, Any]:
    row = normalize_event(event)

    call_budget = (
        None
        if not _known(row["external_tool_calls"])
        else row["external_tool_calls"] <= CALL_BUDGET
    )
    update_budget = (
        None
        if not _known(row["max_calls_between_updates"])
        else row["max_calls_between_updates"] <= 3
    )
    rehydrate_budget = (
        None
        if not _known(row["rehydrate_files"])
        else row["rehydrate_files"] <= REHYDRATE_FILE_BUDGET
    )
    atomic_transition = (
        None
        if not _known(row["durable_transitions"])
        else row["durable_transitions"] == 1
    )
    authority_ok = (
        None
        if row["authority_expanded"] is None
        else not bool(row["authority_expanded"])
    )

    branch_delta = None
    if _known(row["branches_opened"]) and _known(row["branches_closed"]):
        branch_delta = row["branches_opened"] - row["branches_closed"]

    frontier_movement = None
    if _known(row["frontier_gap_before"]) and _known(row["frontier_gap_after"]):
        frontier_movement = row["frontier_gap_before"] - row["frontier_gap_after"]

    violations: list[str] = []
    if call_budget is False:
        violations.append("EXTERNAL_CALL_BUDGET_EXCEEDED")
    if update_budget is False:
        violations.append("PROGRESS_UPDATE_BUDGET_EXCEEDED")
    if rehydrate_budget is False:
        violations.append("REHYDRATE_FILE_BUDGET_EXCEEDED")
    if atomic_transition is False:
        violations.append("NON_ATOMIC_DURABLE_TRANSITION")
    if authority_ok is False:
        violations.append("METHOD_TELEMETRY_AUTHORITY_EXPANSION")
    if branch_delta is not None and branch_delta > 2:
        violations.append("BRANCH_SPRAWL_SIGNAL")

    critical_known = (
        row["external_tool_calls"],
        row["rehydrate_files"],
        row["durable_transitions"],
        row["authority_expanded"],
    )
    critical_coverage = sum(_known(value) for value in critical_known) / len(
        critical_known
    )

    if authority_ok is False:
        risk = "CRITICAL"
    elif violations:
        risk = "REVIEW"
    elif critical_coverage < 0.75:
        risk = "INSUFFICIENT_TELEMETRY"
    else:
        risk = "OK"

    return {
        "event_id": row["event_id"],
        "bounce_id": row["bounce_id"],
        "risk": risk,
        "violations": violations,
        "checks": {
            "call_budget": call_budget,
            "progress_update_budget": update_budget,
            "rehydrate_file_budget": rehydrate_budget,
            "atomic_transition": atomic_transition,
            "authority_ok": authority_ok,
        },
        "branch_delta": branch_delta,
        "frontier_movement": frontier_movement,
        "critical_coverage": critical_coverage,
    }


def _observed_mean(events: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = [row[field] for row in events if _known(row[field])]
    return {
        "value": None if not values else statistics.fmean(values),
        "observed": len(values),
        "total": len(events),
        "coverage": 0.0 if not events else len(values) / len(events),
    }


def aggregate(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = [normalize_event(row) for row in events]
    assessments = [assess_event(row) for row in rows]

    branch_deltas = [
        assessment["branch_delta"]
        for assessment in assessments
        if assessment["branch_delta"] is not None
    ]
    frontier_moves = [
        assessment["frontier_movement"]
        for assessment in assessments
        if assessment["frontier_movement"] is not None
    ]

    return {
        "events": len(rows),
        "means": {
            field: _observed_mean(rows, field)
            for field in (
                "external_tool_calls",
                "max_calls_between_updates",
                "rehydrate_files",
                "rehydrate_bytes",
                "durable_transitions",
                "mc_trials",
                "failure_specimens",
            )
        },
        "branch_delta": {
            "value": None if not branch_deltas else sum(branch_deltas),
            "observed": len(branch_deltas),
            "total": len(rows),
        },
        "frontier_movement": {
            "value": None if not frontier_moves else sum(frontier_moves),
            "observed": len(frontier_moves),
            "total": len(rows),
        },
        "risk_counts": {
            risk: sum(a["risk"] == risk for a in assessments)
            for risk in ("OK", "REVIEW", "CRITICAL", "INSUFFICIENT_TELEMETRY")
        },
        "assessments": assessments,
    }


def monte_carlo_call_budget_sensitivity(
    *,
    trials: int = 20000,
    seed: int = 20261004,
) -> dict[str, Any]:
    """Synthetic sensitivity only. It is not authority to change CALL_BUDGET."""
    rng = random.Random(seed)

    samples = []
    for _ in range(trials):
        safe_calls = max(1, min(12, round(rng.gauss(3.8, 1.15))))
        stall_calls = max(1, min(12, round(rng.gauss(8.1, 1.65))))
        samples.append((safe_calls, stall_calls))

    rows = []
    for threshold in range(4, 9):
        false_positive = sum(safe > threshold for safe, _ in samples) / trials
        false_negative = sum(stall <= threshold for _, stall in samples) / trials
        rows.append(
            {
                "threshold": threshold,
                "safe_flag_rate": false_positive,
                "stall_miss_rate": false_negative,
                "balanced_loss": false_positive + false_negative,
                "checkpoint_cost_weighted_loss": 2.0 * false_positive + false_negative,
                "stall_cost_weighted_loss": false_positive + 2.0 * false_negative,
            }
        )

    return {
        "trials": trials,
        "seed": seed,
        "rows": rows,
        "current_policy_threshold": CALL_BUDGET,
        "decision": "NO_THRESHOLD_CHANGE_FROM_SYNTHETIC_ONLY",
        "reason": (
            "The preferred threshold changes with the assumed false-positive versus "
            "stall-miss cost. Real dogfood telemetry is required before policy revision."
        ),
    }


def synthetic_fixtures() -> list[dict[str, Any]]:
    return [
        {
            "event_id": "LEAN-001",
            "bounce_id": "LEAN-001",
            "protocol": "MIXED_V3",
            "gap_class": "EVIDENCE_GAP",
            "external_tool_calls": 4,
            "max_calls_between_updates": 2,
            "rehydrate_files": 3,
            "rehydrate_bytes": 12000,
            "durable_transitions": 1,
            "mc_trials": 0,
            "failure_specimens": 0,
            "branches_opened": 0,
            "branches_closed": 1,
            "frontier_gap_before": 0.40,
            "frontier_gap_after": 0.25,
            "authority_expanded": False,
            "stop_reason": "DURABLE_TRANSITION_COMPLETE",
            "claim_class": "SYNTHETIC",
        },
        {
            "event_id": "MC-001",
            "bounce_id": "MC-001",
            "protocol": "FIXED_V1",
            "gap_class": "CAPABILITY_GAP",
            "external_tool_calls": 6,
            "max_calls_between_updates": 3,
            "rehydrate_files": 4,
            "rehydrate_bytes": 22000,
            "durable_transitions": 1,
            "mc_trials": 5000,
            "failure_specimens": 2,
            "branches_opened": 1,
            "branches_closed": 0,
            "frontier_gap_before": 0.60,
            "frontier_gap_after": 0.35,
            "authority_expanded": False,
            "stop_reason": "EXPERIMENT_FROZEN",
            "claim_class": "SYNTHETIC",
        },
        {
            "event_id": "STALL-001",
            "bounce_id": "STALL-001",
            "protocol": "FIXED_V1",
            "gap_class": "MODEL_GAP",
            "external_tool_calls": 8,
            "max_calls_between_updates": 5,
            "rehydrate_files": 7,
            "rehydrate_bytes": 120000,
            "durable_transitions": 0,
            "mc_trials": None,
            "failure_specimens": None,
            "branches_opened": 3,
            "branches_closed": 0,
            "frontier_gap_before": 0.40,
            "frontier_gap_after": None,
            "authority_expanded": False,
            "stop_reason": "RUNTIME_LOSS",
            "claim_class": "SYNTHETIC",
        },
        {
            "event_id": "UNKNOWN-001",
            "bounce_id": "UNKNOWN-001",
            "protocol": "MIXED_V3",
            "gap_class": "CONTRACT_GAP",
            "external_tool_calls": None,
            "max_calls_between_updates": None,
            "rehydrate_files": None,
            "rehydrate_bytes": None,
            "durable_transitions": 1,
            "mc_trials": None,
            "failure_specimens": None,
            "branches_opened": None,
            "branches_closed": None,
            "frontier_gap_before": None,
            "frontier_gap_after": None,
            "authority_expanded": False,
            "stop_reason": "PARTIAL_LEGACY_RECORD",
            "claim_class": "SYNTHETIC",
        },
    ]


def run_panel() -> dict[str, Any]:
    fixtures = synthetic_fixtures()
    summary = aggregate(fixtures)
    sensitivity = monte_carlo_call_budget_sensitivity()

    by_id = {
        row["event_id"]: row
        for row in summary["assessments"]
    }

    invariants = {
        "lean_ok": by_id["LEAN-001"]["risk"] == "OK",
        "mc_ok": by_id["MC-001"]["risk"] == "OK",
        "stall_review": by_id["STALL-001"]["risk"] == "REVIEW",
        "unknown_not_zero": (
            summary["means"]["external_tool_calls"]["observed"] == 3
            and summary["means"]["external_tool_calls"]["total"] == 4
        ),
        "unknown_explicit": by_id["UNKNOWN-001"]["risk"] == "INSUFFICIENT_TELEMETRY",
        "synthetic_mc_cannot_change_policy": (
            sensitivity["decision"] == "NO_THRESHOLD_CHANGE_FROM_SYNTHETIC_ONLY"
        ),
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(invariants.values()) else "FAIL",
        "purpose": (
            "Observe research-method friction using durable operational metadata "
            "without collecting private reasoning content."
        ),
        "invariants": invariants,
        "summary": summary,
        "call_budget_sensitivity": sensitivity,
        "data_boundary": {
            "allowed": [
                "repository commits and handoffs",
                "explicit tool-call counts",
                "workflow/run receipts",
                "explicit experiment budgets and results",
                "explicit stop reasons",
                "frontier-gap values already present in durable artifacts",
            ],
            "forbidden": [
                "private chain-of-thought",
                "hidden reasoning tokens",
                "invented zero values for missing telemetry",
            ],
        },
        "next": (
            "Dogfood the schema on future canonical bounces, then fit L1/L2 "
            "cost-and-gain distributions from observed records."
        ),
        "claim_ceiling": "SYNTHETIC_METHOD_TELEMETRY_SCHEMA_AND_ALERT_LOGIC_ONLY",
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
