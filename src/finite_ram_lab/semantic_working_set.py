from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable


SCHEMA = "finite-ram-lab.semantic-working-set/v0.1"
BUDGETS = (1, 2, 4, 6, 8)


@dataclass(frozen=True)
class Event:
    key: str
    value: str


@dataclass(frozen=True)
class Case:
    name: str
    events: tuple[Event, ...]
    query_keys: tuple[str, ...]


def corpus() -> tuple[Case, ...]:
    return (
        Case(
            "early-single",
            (
                Event("goal", "alpha"),
                Event("d1", "1"),
                Event("d2", "2"),
                Event("d3", "3"),
                Event("d4", "4"),
                Event("d5", "5"),
                Event("d6", "6"),
                Event("d7", "7"),
            ),
            ("goal",),
        ),
        Case(
            "superseded-two-key",
            (
                Event("a", "old"),
                Event("d1", "1"),
                Event("b", "bee"),
                Event("d2", "2"),
                Event("a", "new"),
                Event("d3", "3"),
                Event("d4", "4"),
                Event("d5", "5"),
            ),
            ("a", "b"),
        ),
        Case(
            "two-separated",
            (
                Event("x", "ex"),
                Event("y", "why"),
                Event("d1", "1"),
                Event("d2", "2"),
                Event("z", "zee"),
                Event("d3", "3"),
                Event("d4", "4"),
                Event("d5", "5"),
            ),
            ("x", "z"),
        ),
        Case(
            "late-single",
            (
                Event("d1", "1"),
                Event("d2", "2"),
                Event("d3", "3"),
                Event("d4", "4"),
                Event("d5", "5"),
                Event("d6", "6"),
                Event("d7", "7"),
                Event("answer", "omega"),
            ),
            ("answer",),
        ),
    )


def _latest_map(events: Iterable[Event]) -> dict[str, str]:
    out: dict[str, str] = {}
    for event in events:
        out[event.key] = event.value
    return out


def truth(case: Case) -> dict[str, str]:
    latest = _latest_map(case.events)
    return {key: latest[key] for key in case.query_keys}


def full_indices(case: Case, budget: int) -> tuple[int, ...]:
    del budget
    return tuple(range(len(case.events)))


def append_truncate_indices(case: Case, budget: int) -> tuple[int, ...]:
    if budget <= 0:
        return ()
    start = max(0, len(case.events) - budget)
    return tuple(range(start, len(case.events)))


def key_aware_indices(case: Case, budget: int) -> tuple[int, ...]:
    if budget <= 0:
        return ()

    selected: list[int] = []
    needed = set(case.query_keys)

    for index in range(len(case.events) - 1, -1, -1):
        event = case.events[index]
        if event.key in needed:
            selected.append(index)
            needed.remove(event.key)
            if len(selected) >= budget:
                return tuple(sorted(selected))

    if len(selected) < budget:
        selected_set = set(selected)
        for index in range(len(case.events) - 1, -1, -1):
            if index in selected_set:
                continue
            selected.append(index)
            if len(selected) >= budget:
                break

    return tuple(sorted(selected))


POLICIES = {
    "FULL": full_indices,
    "APPEND_TRUNCATE": append_truncate_indices,
    "KEY_AWARE": key_aware_indices,
}


def evaluate_case(case: Case, indices: tuple[int, ...]) -> dict:
    resident = tuple(case.events[index] for index in indices)
    resident_latest = _latest_map(resident)
    expected = truth(case)

    missing = [
        key for key in case.query_keys
        if key not in resident_latest
    ]
    stale = [
        key for key in case.query_keys
        if key in resident_latest and resident_latest[key] != expected[key]
    ]

    contributing_indices: set[int] = set()
    for key, value in expected.items():
        for index in reversed(indices):
            event = case.events[index]
            if event.key == key and event.value == value:
                contributing_indices.add(index)
                break

    interference = len(indices) - len(contributing_indices)
    success = not missing and not stale

    return {
        "case": case.name,
        "success": success,
        "resident_count": len(indices),
        "resident_indices": list(indices),
        "missing_required_keys": missing,
        "stale_required_keys": stale,
        "interference_events": interference,
    }


def evaluate_policy(policy: str, budget: int) -> dict:
    if policy not in POLICIES:
        raise ValueError(f"unknown_policy:{policy}")
    rows = []
    for case in corpus():
        indices = POLICIES[policy](case, budget)
        rows.append(evaluate_case(case, indices))

    successes = sum(row["success"] for row in rows)
    return {
        "policy": policy,
        "budget": budget,
        "case_count": len(rows),
        "success_count": successes,
        "exact_rate": successes / len(rows),
        "mean_resident_count": sum(
            row["resident_count"] for row in rows
        ) / len(rows),
        "mean_interference_events": sum(
            row["interference_events"] for row in rows
        ) / len(rows),
        "failures": [row for row in rows if not row["success"]],
    }


def _corpus_sha256() -> str:
    payload = [
        {
            "name": case.name,
            "events": [
                {"key": event.key, "value": event.value}
                for event in case.events
            ],
            "query_keys": list(case.query_keys),
        }
        for case in corpus()
    ]
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def first_full_success_budget(policy: str) -> int | None:
    for budget in BUDGETS:
        if evaluate_policy(policy, budget)["exact_rate"] == 1.0:
            return budget
    return None


def run_panel() -> dict:
    rows = [
        evaluate_policy(policy, budget)
        for policy in ("APPEND_TRUNCATE", "KEY_AWARE")
        for budget in BUDGETS
    ]
    full = evaluate_policy("FULL", max(BUDGETS))

    result = {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": "SYNTHETIC_SEMANTIC_WORKING_SET_HARNESS_VALIDATED",
        "empirical_model_claim": False,
        "synthetic_only": True,
        "corpus_sha256": _corpus_sha256(),
        "case_count": len(corpus()),
        "budgets": list(BUDGETS),
        "reference": full,
        "rows": rows,
        "knees": {
            "APPEND_TRUNCATE": first_full_success_budget("APPEND_TRUNCATE"),
            "KEY_AWARE": first_full_success_budget("KEY_AWARE"),
        },
        "claim_ceiling": "SYNTHETIC_SEMANTIC_WORKING_SET_HARNESS_ONLY",
    }

    if not full["exact_rate"] == 1.0:
        raise RuntimeError("full_reference_failed")
    if result["knees"]["APPEND_TRUNCATE"] != 8:
        raise RuntimeError("append_knee_unexpected")
    if result["knees"]["KEY_AWARE"] != 2:
        raise RuntimeError("key_aware_knee_unexpected")

    return result


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
