from __future__ import annotations

import json
import statistics
from typing import Any, Iterable

from finite_ram_lab.fr_decision_skills import (
    SOURCE_HISTORY_CHARACTERS,
    compile_decision_context,
)

SCHEMA = "finite-ram-lab.fr-meta-017-skill-telemetry/v0.1"
MIN_EVENTS_FOR_EFFECT_CLAIM = 20


def normalize_event(
    event: dict[str, Any],
) -> dict[str, Any]:
    required = (
        "decision_id",
        "skill_ids",
        "primary_action",
        "source_history_characters",
        "resident_context_characters",
        "full_history_fallback",
        "outcome",
        "authority_expanded",
    )

    missing = [
        key
        for key in required
        if key not in event
    ]

    if missing:
        raise ValueError(
            "missing_required:"
            + ",".join(missing)
        )

    row = dict(event)
    row.setdefault(
        "reversal",
        None,
    )
    row.setdefault(
        "invalidation_fired",
        None,
    )
    row.setdefault(
        "evidence_pr",
        None,
    )

    if (
        row["source_history_characters"]
        <= 0
    ):
        raise ValueError(
            "invalid_source_history_characters"
        )

    if (
        row["resident_context_characters"]
        <= 0
    ):
        raise ValueError(
            "invalid_resident_context_characters"
        )

    return row


def assess_event(
    event: dict[str, Any],
) -> dict[str, Any]:
    row = normalize_event(event)

    skill_hit = (
        bool(row["skill_ids"])
        and not row[
            "full_history_fallback"
        ]
    )

    context_reduction = (
        1.0
        - row[
            "resident_context_characters"
        ]
        / row[
            "source_history_characters"
        ]
    )

    qualified = (
        row["outcome"] == "PASS"
        and not row[
            "authority_expanded"
        ]
    )

    if row["authority_expanded"]:
        risk = "CRITICAL"
    elif row["outcome"] == "UNKNOWN":
        risk = "UNKNOWN_OUTCOME"
    elif row["full_history_fallback"]:
        risk = "FALLBACK"
    else:
        risk = "OK"

    return {
        "decision_id": row[
            "decision_id"
        ],
        "skill_hit": skill_hit,
        "qualified": qualified,
        "risk": risk,
        "context_reduction_fraction": (
            context_reduction
        ),
        "reversal": row["reversal"],
        "reversal_observed": (
            row["reversal"]
            is not None
        ),
        "invalidation_fired": (
            row["invalidation_fired"]
        ),
    }


def aggregate(
    events: Iterable[
        dict[str, Any]
    ],
) -> dict[str, Any]:
    rows = [
        normalize_event(event)
        for event in events
    ]
    assessments = [
        assess_event(row)
        for row in rows
    ]

    hits = [
        assessment
        for assessment in assessments
        if assessment["skill_hit"]
    ]

    reversals = [
        assessment["reversal"]
        for assessment in assessments
        if assessment[
            "reversal_observed"
        ]
    ]

    context_chars = [
        row[
            "resident_context_characters"
        ]
        for row in rows
    ]

    reductions = [
        assessment[
            "context_reduction_fraction"
        ]
        for assessment in assessments
    ]

    event_count = len(rows)

    return {
        "events": event_count,
        "skill_hits": len(hits),
        "skill_hit_rate": (
            None
            if not rows
            else len(hits) / event_count
        ),
        "full_history_fallbacks": sum(
            bool(
                row[
                    "full_history_fallback"
                ]
            )
            for row in rows
        ),
        "fallback_rate": (
            None
            if not rows
            else sum(
                bool(
                    row[
                        "full_history_fallback"
                    ]
                )
                for row in rows
            )
            / event_count
        ),
        "qualified_hit_rate": (
            None
            if not hits
            else sum(
                bool(
                    row[
                        "qualified"
                    ]
                )
                for row in hits
            )
            / len(hits)
        ),
        "mean_resident_context_characters": (
            None
            if not context_chars
            else statistics.fmean(
                context_chars
            )
        ),
        "mean_context_reduction_fraction": (
            None
            if not reductions
            else statistics.fmean(
                reductions
            )
        ),
        "reversal": {
            "rate": (
                None
                if not reversals
                else statistics.fmean(
                    bool(value)
                    for value
                    in reversals
                )
            ),
            "observed": len(
                reversals
            ),
            "total": event_count,
            "coverage": (
                0.0
                if not rows
                else len(
                    reversals
                )
                / event_count
            ),
        },
        "effect_claim_ready": (
            event_count
            >= MIN_EVENTS_FOR_EFFECT_CLAIM
            and len(reversals)
            >= MIN_EVENTS_FOR_EFFECT_CLAIM
        ),
        "assessments": assessments,
    }


def fr_meta_015_event() -> dict[str, Any]:
    route = compile_decision_context(
        {
            "deterministic_duplicate_work": True,
            "scientific_contract_unchanged": True,
            "runtime_is_measurement": False,
        }
    )

    return {
        "decision_id": (
            "FR-META-015-ROUTE"
        ),
        "skill_ids": [
            row["id"]
            for row in route["skills"]
        ],
        "primary_action": route[
            "primary_action"
        ],
        "source_history_characters": (
            SOURCE_HISTORY_CHARACTERS
        ),
        "resident_context_characters": (
            route[
                "context_characters"
            ]
        ),
        "full_history_fallback": False,
        "outcome": "PASS",
        "authority_expanded": False,
        "reversal": None,
        "invalidation_fired": False,
        "evidence_pr": 117,
    }


def run_panel() -> dict[str, Any]:
    event = fr_meta_015_event()
    assessment = assess_event(
        event
    )
    summary = aggregate(
        [event]
    )

    checks = {
        "prospective_skill_hit": (
            assessment[
                "skill_hit"
            ]
        ),
        "prospective_outcome_pass": (
            assessment[
                "qualified"
            ]
        ),
        "context_reduction_over_97pct": (
            assessment[
                "context_reduction_fraction"
            ]
            > 0.97
        ),
        "no_full_history_fallback": (
            summary[
                "full_history_fallbacks"
            ]
            == 0
        ),
        "reversal_unknown_not_zero": (
            summary[
                "reversal"
            ]["rate"]
            is None
            and summary[
                "reversal"
            ]["coverage"]
            == 0.0
        ),
        "one_event_not_effect_claim": (
            not summary[
                "effect_claim_ready"
            ]
        ),
    }

    return {
        "schema": SCHEMA,
        "status": (
            "PASS"
            if all(checks.values())
            else "FAIL"
        ),
        "checks": checks,
        "event": event,
        "assessment": assessment,
        "aggregate": summary,
        "promotion_min_events": (
            MIN_EVENTS_FOR_EFFECT_CLAIM
        ),
        "data_boundary": {
            "allowed": [
                "explicit decision facts",
                "selected skill ids",
                "compiled context character count",
                "explicit fallback flag",
                "durable experiment outcome",
                "later explicit reversal or invalidation",
            ],
            "forbidden": [
                "private chain-of-thought",
                "hidden reasoning tokens",
                "invented reversal=false for unobserved future evidence",
            ],
        },
        "decision": (
            "ACCUMULATE_PROSPECTIVE_SKILL_TELEMETRY_BEFORE_EFFECT_CLAIM"
        ),
        "claim_ceiling": (
            "ONE_PROSPECTIVE_SKILL_DOGFOOD_EVENT_AND_TELEMETRY_SCHEMA_ONLY"
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
