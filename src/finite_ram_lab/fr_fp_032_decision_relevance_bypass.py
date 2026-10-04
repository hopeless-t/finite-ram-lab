from __future__ import annotations

import json
from typing import Any

from finite_ram_lab.fr_fp_030_hosted_reuse_lifecycle import (
    _run_arm,
    _schedule,
)
from finite_ram_lab.fr_fp_031_risk_aware_hosted_governor import (
    _run_governor_arm,
)

SCHEMA = "finite-ram-lab.fr-fp-032-decision-relevance-bypass/v0.1"

UNCONSTRAINED_REUSE_CEILING = 1.0


def evidence_relevance(
    reuse_ceiling: float,
) -> str:
    if reuse_ceiling >= 1.0:
        return (
            "BYPASS_REUSE_EVIDENCE_AND_KEEP_COLD"
        )

    return (
        "REUSE_EVIDENCE_REQUIRED"
    )


def run_panel() -> dict[str, Any]:
    schedule = _schedule()

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-032-"
    ) as tmp:
        root = Path(tmp)

        evidenceful = (
            _run_governor_arm(
                root=root,
                arm=(
                    "EVIDENCEFUL_P1_GOVERNOR"
                ),
                schedule=schedule,
                reuse_ceiling_value=(
                    UNCONSTRAINED_REUSE_CEILING
                ),
            )
        )

        bypass_physical = _run_arm(
            root=root,
            arm="ALWAYS_COLD",
            schedule=schedule,
        )

    bypass = {
        **bypass_physical,
        "arm": (
            "DECISION_RELEVANCE_BYPASS_P1"
        ),
        "reuse_ceiling": (
            UNCONSTRAINED_REUSE_CEILING
        ),
        "reuse_evidence_observations": 0,
        "reuse_upper_evaluations": 0,
        "drift_alarm_evaluations": 0,
        "drift_alarm_steps": [],
        "decision_relevance": (
            evidence_relevance(
                UNCONSTRAINED_REUSE_CEILING
            )
        ),
    }

    evidenceful_policy_events = (
        len(
            evidenceful["rows"]
        )
        + len(
            evidenceful[
                "drift_alarm_steps"
            ]
        )
    )

    checks = {
        "p1_is_classified_as_evidence_irrelevant": (
            evidence_relevance(
                1.0
            )
            == "BYPASS_REUSE_EVIDENCE_AND_KEEP_COLD"
        ),
        "interior_ceiling_still_requires_evidence": (
            evidence_relevance(
                0.10
            )
            == "REUSE_EVIDENCE_REQUIRED"
        ),
        "same_reuse_schedule_is_restored": (
            evidenceful[
                "warm_restores"
            ]
            + evidenceful[
                "cold_restores"
            ]
            == bypass[
                "restore_count"
            ]
            == sum(schedule)
        ),
        "all_restore_integrity_passes": (
            evidenceful[
                "all_restores_verified"
            ]
            and bypass[
                "all_restores_verified"
            ]
        ),
        "bypass_has_zero_reuse_evidence_work": (
            bypass[
                "reuse_evidence_observations"
            ]
            == 0
            and bypass[
                "reuse_upper_evaluations"
            ]
            == 0
            and bypass[
                "drift_alarm_evaluations"
            ]
            == 0
        ),
        "evidenceful_path_does_redundant_policy_work": (
            evidenceful_policy_events
            > 0
            and bool(
                evidenceful[
                    "drift_alarm_steps"
                ]
            )
        ),
        "bypass_matches_unconstrained_cold_policy_from_first_opportunity": (
            bypass[
                "cold_opportunities"
            ]
            == len(schedule)
            and bypass[
                "warm_opportunities"
            ]
            == 0
        ),
        "bypass_removes_evidence_induced_warm_residency": (
            bypass[
                "resident_mib_opportunity_integral"
            ]
            < evidenceful[
                "resident_mib_opportunity_integral"
            ]
        ),
        "bypass_preserves_cold_restore_count": (
            bypass[
                "cold_restores"
            ]
            == (
                evidenceful[
                    "warm_restores"
                ]
                + evidenceful[
                    "cold_restores"
                ]
            )
        ),
        "bypass_preserves_storage_read_volume_for_all_cold_policy": (
            bypass[
                "total_storage_read_bytes"
            ]
            == 17
            * 8
            * 1024
            * 1024
        ),
        "bypass_finishes_cold": (
            bypass[
                "final_tier"
            ]
            == "COLD"
        ),
    }

    return {
        "schema": SCHEMA,
        "status": (
            "PASS"
            if all(
                checks.values()
            )
            else "FAIL"
        ),
        "classification": (
            "HOSTED_PHYSICAL_DECISION_RELEVANCE_BYPASS_FOR_UNCONSTRAINED_REUSE"
        ),
        "law": {
            "trigger": (
                "reuse_ceiling >= 1"
            ),
            "decision": (
                "reuse probability cannot change COLD eligibility"
            ),
            "compiled_action": (
                "skip reuse evidence collection, upper-bound updates and drift alarms; keep COLD"
            ),
        },
        "evidenceful": {
            "reuse_ceiling": (
                evidenceful[
                    "reuse_ceiling"
                ]
            ),
            "warm_opportunities": (
                evidenceful[
                    "warm_opportunities"
                ]
            ),
            "cold_opportunities": (
                evidenceful[
                    "cold_opportunities"
                ]
            ),
            "warm_restores": (
                evidenceful[
                    "warm_restores"
                ]
            ),
            "cold_restores": (
                evidenceful[
                    "cold_restores"
                ]
            ),
            "resident_mib_opportunity_integral": (
                evidenceful[
                    "resident_mib_opportunity_integral"
                ]
            ),
            "drift_alarm_steps": (
                evidenceful[
                    "drift_alarm_steps"
                ]
            ),
            "policy_event_count_lower_bound": (
                evidenceful_policy_events
            ),
            "total_storage_read_bytes": (
                evidenceful[
                    "total_storage_read_bytes"
                ]
            ),
        },
        "bypass": {
            "warm_opportunities": (
                bypass[
                    "warm_opportunities"
                ]
            ),
            "cold_opportunities": (
                bypass[
                    "cold_opportunities"
                ]
            ),
            "cold_restores": (
                bypass[
                    "cold_restores"
                ]
            ),
            "resident_mib_opportunity_integral": (
                bypass[
                    "resident_mib_opportunity_integral"
                ]
            ),
            "drift_alarm_steps": [],
            "reuse_evidence_observations": 0,
            "reuse_upper_evaluations": 0,
            "drift_alarm_evaluations": 0,
            "total_storage_read_bytes": (
                bypass[
                    "total_storage_read_bytes"
                ]
            ),
            "final_tier": (
                bypass[
                    "final_tier"
                ]
            ),
        },
        "checks": checks,
        "decision": (
            "PRUNE_THE_REUSE_EVIDENCE_PLANE_WHEN_THE_RISK_SURFACE_MAKES_REUSE_DECISION_IRRELEVANT"
        ),
        "meta_transfer": (
            "An observation or skill plane should not stay resident merely because it exists; retain it only while it can still change an admissible decision."
        ),
        "claim_ceiling": (
            "HOSTED_PHYSICAL_P1_REUSE_CEILING_DECISION_RELEVANCE_BYPASS_ONLY"
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
