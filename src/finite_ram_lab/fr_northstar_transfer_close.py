from __future__ import annotations

import json

from finite_ram_lab.fr_gap_selector import (
    classify_gap,
)
from finite_ram_lab.fr_primitive_registry import (
    PRIMITIVES,
    eligible,
)


SCHEMA = "finite-ram-lab.fr-northstar-005-close-transfer-gap/v0.1"

BUDGET_MIB = 600.0
CURRENT_RESIDENT_MIB = 560.0

SOURCE_PSS_KIB = 32772
DIRECT_PSS_KIB = 65544
STAGED_PSS_KIB = 98316
SHARED_VIEW_PSS_KIB = 32772


def _primitive(
    primitive_id: str,
) -> dict:
    for row in PRIMITIVES:
        if row["id"] == primitive_id:
            return row

    raise KeyError(
        primitive_id
    )


def _facts_for(
    primitive_ids: list[str],
) -> list[str]:
    facts = set()

    for primitive_id in (
        primitive_ids
    ):
        facts.update(
            _primitive(
                primitive_id
            )["requires"]
        )

    return sorted(
        facts
    )


def _peak_from_increment(
    held_pss_kib: int,
) -> float:
    incremental_kib = (
        held_pss_kib
        - SOURCE_PSS_KIB
    )

    return (
        CURRENT_RESIDENT_MIB
        + incremental_kib
        / 1024.0
    )


def transfer_effect_model() -> dict:
    staged_peak = (
        _peak_from_increment(
            STAGED_PSS_KIB
        )
    )

    direct_peak = (
        _peak_from_increment(
            DIRECT_PSS_KIB
        )
    )

    shared_peak = (
        _peak_from_increment(
            SHARED_VIEW_PSS_KIB
        )
    )

    return {
        "current_resident_mib": (
            CURRENT_RESIDENT_MIB
        ),
        "budget_mib": (
            BUDGET_MIB
        ),
        "source_pss_kib": (
            SOURCE_PSS_KIB
        ),
        "arms": {
            "STAGED_COPY": {
                "held_pss_kib": (
                    STAGED_PSS_KIB
                ),
                "incremental_over_source_kib": (
                    STAGED_PSS_KIB
                    - SOURCE_PSS_KIB
                ),
                "predicted_peak_mib": (
                    staged_peak
                ),
                "fits_budget": (
                    staged_peak
                    <= BUDGET_MIB
                ),
            },
            "DIRECT_TRANSFER_NO_STAGING": {
                "held_pss_kib": (
                    DIRECT_PSS_KIB
                ),
                "incremental_over_source_kib": (
                    DIRECT_PSS_KIB
                    - SOURCE_PSS_KIB
                ),
                "predicted_peak_mib": (
                    direct_peak
                ),
                "fits_budget": (
                    direct_peak
                    <= BUDGET_MIB
                ),
            },
            "ZERO_COPY_SHARED_VIEW": {
                "held_pss_kib": (
                    SHARED_VIEW_PSS_KIB
                ),
                "incremental_over_source_kib": (
                    SHARED_VIEW_PSS_KIB
                    - SOURCE_PSS_KIB
                ),
                "predicted_peak_mib": (
                    shared_peak
                ),
                "fits_budget": (
                    shared_peak
                    <= BUDGET_MIB
                ),
            },
        },
        "best_if_zero_copy_legal": (
            "ZERO_COPY_SHARED_VIEW"
        ),
        "best_if_copy_required": (
            "DIRECT_TRANSFER_NO_STAGING"
        ),
    }


def run_panel() -> dict:
    transfer_primitives = [
        row["id"]
        for row in eligible(
            failure_domain=(
                "TRANSFER_STAGING_PRESSURE"
            ),
            min_evidence_class=(
                "HOSTED_PHYSICAL"
            ),
        )
    ]

    all_transfer_facts = (
        _facts_for(
            transfer_primitives
        )
    )

    after_registry = (
        classify_gap(
            workload_name=(
                "OUT_OF_CORE"
            ),
            budget_mib=600.0,
            failure_domains=[
                "TRANSFER_STAGING_PRESSURE"
            ],
            facts=(
                all_transfer_facts
            ),
        )
    )

    effect = (
        transfer_effect_model()
    )

    staged = effect[
        "arms"
    ]["STAGED_COPY"]

    direct = effect[
        "arms"
    ][
        "DIRECT_TRANSFER_NO_STAGING"
    ]

    shared = effect[
        "arms"
    ][
        "ZERO_COPY_SHARED_VIEW"
    ]

    if staged[
        "fits_budget"
    ]:
        raise RuntimeError(
            "staged_copy_should_cross_budget"
        )

    if not direct[
        "fits_budget"
    ]:
        raise RuntimeError(
            "direct_transfer_should_fit"
        )

    if not shared[
        "fits_budget"
    ]:
        raise RuntimeError(
            "shared_view_should_fit"
        )

    after_effect_model = {
        "classification": (
            "FRONTIER_REACHED"
        ),
        "next_step": (
            "STOP_TRANSFER_MECHANISM_RESEARCH_AND_MOVE_TO_HOST_BOUND_VALIDATION"
        ),
        "selected_if_copy_required": (
            "DIRECT_TRANSFER_NO_STAGING"
        ),
        "selected_if_zero_copy_legal": (
            "ZERO_COPY_SHARED_VIEW"
        ),
        "live_promotion_allowed": (
            False
        ),
    }

    frozen = {
        "previous_gap": (
            "CAPABILITY_GAP"
        ),
        "after_registry_gap": (
            "MODEL_GAP"
        ),
        "after_effect_model_gap": (
            "FRONTIER_REACHED"
        ),
        "transfer_primitives": [
            "DIRECT_TRANSFER_NO_STAGING",
            "ZERO_COPY_SHARED_VIEW",
        ],
        "staged_peak_mib": (
            624.0078125
        ),
        "direct_peak_mib": (
            592.00390625
        ),
        "shared_peak_mib": 560.0,
    }

    actual = {
        "previous_gap": (
            "CAPABILITY_GAP"
        ),
        "after_registry_gap": (
            after_registry[
                "classification"
            ]
        ),
        "after_effect_model_gap": (
            after_effect_model[
                "classification"
            ]
        ),
        "transfer_primitives": (
            transfer_primitives
        ),
        "staged_peak_mib": (
            staged[
                "predicted_peak_mib"
            ]
        ),
        "direct_peak_mib": (
            direct[
                "predicted_peak_mib"
            ]
        ),
        "shared_peak_mib": (
            shared[
                "predicted_peak_mib"
            ]
        ),
    }

    if actual != frozen:
        raise RuntimeError(
            "frozen_transfer_loop_changed:"
            f"{actual}"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "NORTH_STAR_GAP_CLOSURE_LOOP_VALIDATED"
        ),
        "gap_lifecycle": {
            "before_FR_XFER_001": (
                "CAPABILITY_GAP"
            ),
            "after_registry_update": (
                after_registry
            ),
            "after_effect_model": (
                after_effect_model
            ),
        },
        "transfer_primitives": (
            transfer_primitives
        ),
        "effect_model": effect,
        "research_policy": {
            "open_new_transfer_mechanism_lane": (
                False
            ),
            "reason": (
                "The frozen transfer capability gap is closed in the hosted proxy model."
            ),
            "next": (
                "Host-bound qualification if a real workload needs this primitive; otherwise return to the gap selector."
            ),
        },
        "governance": {
            "hosted_physical_is_not_live_authority": (
                True
            ),
            "live_actions_executed": 0,
            "live_promotion_candidates": 0,
        },
        "primary_findings": [
            "THE_RESEARCH_LOOP_CAN_MOVE_CAPABILITY_GAP_TO_MODEL_GAP_TO_FRONTIER_REACHED",
            "PHYSICAL_MEASUREMENT_IS_NOT_COMPLETE_UNTIL_IT_IS_REGISTERED_AND_REEVALUATED",
            "TRANSFER_RESEARCH_SHOULD_STOP_ONCE_THE_MEASURED_GAP_CLOSES",
            "ZERO_COPY_IS_AN_APPLICABILITY_CONSTRAINED_OPTIMUM_NOT_A_UNIVERSAL_DEFAULT",
            "HOSTED_PHYSICAL_GAP_CLOSURE_DOES_NOT_GRANT_LIVE_EXECUTION_AUTHORITY",
        ],
        "claim_ceiling": (
            "HOSTED_PROXY_NORTH_STAR_LOOP_CLOSURE_ONLY"
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
    raise SystemExit(
        main()
    )
