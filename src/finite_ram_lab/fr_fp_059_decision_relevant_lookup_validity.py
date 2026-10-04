from __future__ import annotations

import copy
import json
import math
import sys
from typing import Any

from finite_ram_lab.fr_fp_058_compiled_rent_lookup import (
    COMPILED_PATHS,
    COMPILED_THRESHOLDS,
    SCORE_TIE_ULPS,
    _load,
)

SCHEMA = "finite-ram-lab.fr-fp-059-decision-relevant-lookup-validity/v0.1"

BOUNDARY_EQUIVALENCE_ULPS = SCORE_TIE_ULPS * 4


def _line(row: dict[str, Any]) -> tuple[str, float, float]:
    return (
        str(row["path_id"]),
        float(row["resident_mib_round"]),
        float(row["semantic_service_ms"])
        + float(row["physical_actuation_ms"]),
    )


def derive_scalar_surface(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Derive the exact lower envelope used by the scalar memory-rent policy."""

    # For equal resident slopes, only the line with the lowest intercept can win.
    # Stable path ID resolves an exact intercept tie.
    by_slope: dict[float, tuple[str, float, float]] = {}

    for row in rows:
        path_id, slope, intercept = _line(row)
        incumbent = by_slope.get(slope)

        if incumbent is None:
            by_slope[slope] = (
                path_id,
                slope,
                intercept,
            )
            continue

        incumbent_key = (
            incumbent[2],
            incumbent[0],
        )
        candidate_key = (
            intercept,
            path_id,
        )

        if candidate_key < incumbent_key:
            by_slope[slope] = (
                path_id,
                slope,
                intercept,
            )

    lines = sorted(
        by_slope.values(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    )

    hull: list[tuple[str, float, float]] = []
    starts: list[float] = []

    for candidate in lines:
        path_id, slope, intercept = candidate

        while hull:
            _prev_id, prev_slope, prev_intercept = hull[-1]
            crossover = (
                (intercept - prev_intercept)
                / (prev_slope - slope)
            )

            if crossover <= starts[-1]:
                hull.pop()
                starts.pop()
                continue

            break

        if not hull:
            hull.append(candidate)
            starts.append(-math.inf)
            continue

        _prev_id, prev_slope, prev_intercept = hull[-1]
        crossover = (
            (intercept - prev_intercept)
            / (prev_slope - slope)
        )
        hull.append(candidate)
        starts.append(crossover)

    if not hull:
        raise ValueError("empty_policy_family")

    active_at_zero = max(
        index
        for index, start
        in enumerate(starts)
        if start <= 0.0
    )

    active = hull[active_at_zero:]
    active_starts = starts[active_at_zero:]

    return {
        "paths": [
            item[0]
            for item in active
        ],
        "thresholds": [
            float(value)
            for value in active_starts[1:]
        ],
    }


def _float_equivalent(
    left: float,
    right: float,
) -> bool:
    scale = max(
        1.0,
        abs(left),
        abs(right),
    )
    tolerance = (
        BOUNDARY_EQUIVALENCE_ULPS
        * sys.float_info.epsilon
        * scale
    )

    return abs(left - right) <= tolerance


def surfaces_equivalent(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    if left["paths"] != right["paths"]:
        return False

    left_thresholds = left["thresholds"]
    right_thresholds = right["thresholds"]

    if len(left_thresholds) != len(right_thresholds):
        return False

    return all(
        _float_equivalent(
            float(a),
            float(b),
        )
        for a, b
        in zip(
            left_thresholds,
            right_thresholds,
        )
    )


def validity_action(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    current = derive_scalar_surface(rows)
    compiled = {
        "paths": list(COMPILED_PATHS),
        "thresholds": list(COMPILED_THRESHOLDS),
    }
    equivalent = surfaces_equivalent(
        current,
        compiled,
    )

    return {
        "action": (
            "KEEP_HOT_LOOKUP"
            if equivalent
            else "INVALIDATE_AND_RECOMPILE_LOOKUP"
        ),
        "equivalent": equivalent,
        "candidate_surface": current,
    }


def _mutations(
    rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    cases: dict[str, list[dict[str, Any]]] = {}

    metadata_only = copy.deepcopy(rows)
    metadata_only[0]["representative_rent"] = 0.03125
    metadata_only[0]["shadow_rents"] = [
        0.0,
        0.03125,
    ]
    metadata_only[0]["evidence"] = "METADATA_REFRESH_ONLY"
    cases["metadata_only"] = metadata_only

    common_semantic_offset = copy.deepcopy(rows)
    for row in common_semantic_offset:
        row["semantic_service_ms"] = (
            float(row["semantic_service_ms"])
            + 100.0
        )
    cases["common_semantic_offset"] = common_semantic_offset

    common_actuation_offset = copy.deepcopy(rows)
    for row in common_actuation_offset:
        row["physical_actuation_ms"] = (
            float(row["physical_actuation_ms"])
            + 7.0
        )
    cases["common_actuation_offset"] = common_actuation_offset

    common_resident_offset = copy.deepcopy(rows)
    for row in common_resident_offset:
        row["resident_mib_round"] = (
            float(row["resident_mib_round"])
            + 128.0
        )
    cases["common_resident_offset"] = common_resident_offset

    unsupported_path_more_expensive = copy.deepcopy(rows)
    for row in unsupported_path_more_expensive:
        if row["path_id"] == "P1":
            row["semantic_service_ms"] = (
                float(row["semantic_service_ms"])
                + 25.0
            )
    cases["unsupported_path_more_expensive"] = (
        unsupported_path_more_expensive
    )

    supported_path_service_change = copy.deepcopy(rows)
    for row in supported_path_service_change:
        if row["path_id"] == "P3":
            row["semantic_service_ms"] = (
                float(row["semantic_service_ms"])
                + 5.0
            )
    cases["supported_path_service_change"] = (
        supported_path_service_change
    )

    supported_path_actuation_change = copy.deepcopy(rows)
    for row in supported_path_actuation_change:
        if row["path_id"] == "P5":
            row["physical_actuation_ms"] = (
                float(row["physical_actuation_ms"])
                + 3.0
            )
    cases["supported_path_actuation_change"] = (
        supported_path_actuation_change
    )

    supported_path_resident_change = copy.deepcopy(rows)
    for row in supported_path_resident_change:
        if row["path_id"] == "P6":
            row["resident_mib_round"] = (
                float(row["resident_mib_round"])
                + 32.0
            )
    cases["supported_path_resident_change"] = (
        supported_path_resident_change
    )

    remove_supported_path = [
        copy.deepcopy(row)
        for row in rows
        if row["path_id"] != "P4"
    ]
    cases["remove_supported_path"] = remove_supported_path

    return cases


def run_panel() -> dict[str, Any]:
    data = _load()
    rows = data["points"]

    compiled_surface = {
        "paths": list(COMPILED_PATHS),
        "thresholds": list(COMPILED_THRESHOLDS),
    }
    derived = derive_scalar_surface(rows)
    baseline_equivalent = surfaces_equivalent(
        derived,
        compiled_surface,
    )

    cases = {}

    for name, mutated_rows in _mutations(rows).items():
        cases[name] = validity_action(
            mutated_rows
        )

    keep_cases = (
        "metadata_only",
        "common_semantic_offset",
        "common_actuation_offset",
        "common_resident_offset",
        "unsupported_path_more_expensive",
    )
    invalidate_cases = (
        "supported_path_service_change",
        "supported_path_actuation_change",
        "supported_path_resident_change",
        "remove_supported_path",
    )

    hot_validity_capsule = {
        "paths": list(COMPILED_PATHS),
        "thresholds": list(COMPILED_THRESHOLDS),
        "boundary_equivalence_ulps": (
            BOUNDARY_EQUIVALENCE_ULPS
        ),
        "rule": (
            "KEEP_LOOKUP_IFF_REDERIVED_SCALAR_SURFACE_IS_EQUIVALENT"
        ),
    }
    raw_evidence_contract = {
        "points": [
            {
                "path_id": row["path_id"],
                "resident_mib_round": row["resident_mib_round"],
                "semantic_service_ms": row["semantic_service_ms"],
                "physical_actuation_ms": row["physical_actuation_ms"],
                "representative_rent": row["representative_rent"],
                "shadow_rents": row["shadow_rents"],
                "evidence": row["evidence"],
            }
            for row in rows
        ],
        "source": data["source"],
    }

    capsule_chars = len(
        json.dumps(
            hot_validity_capsule,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    raw_chars = len(
        json.dumps(
            raw_evidence_contract,
            sort_keys=True,
            separators=(",", ":"),
        )
    )

    checks = {
        "baseline_rederives_fp058_surface": (
            baseline_equivalent
        ),
        "decision_irrelevant_updates_keep_lookup": all(
            cases[name]["action"]
            == "KEEP_HOT_LOOKUP"
            for name in keep_cases
        ),
        "decision_surface_updates_invalidate_lookup": all(
            cases[name]["action"]
            == "INVALIDATE_AND_RECOMPILE_LOOKUP"
            for name in invalidate_cases
        ),
        "unsupported_scalar_path_can_change_without_invalidating_hot_lookup": (
            cases[
                "unsupported_path_more_expensive"
            ]["action"]
            == "KEEP_HOT_LOOKUP"
        ),
        "common_score_offsets_are_pruned_as_decision_irrelevant": (
            cases[
                "common_semantic_offset"
            ]["action"]
            == "KEEP_HOT_LOOKUP"
            and cases[
                "common_actuation_offset"
            ]["action"]
            == "KEEP_HOT_LOOKUP"
            and cases[
                "common_resident_offset"
            ]["action"]
            == "KEEP_HOT_LOOKUP"
        ),
        "validity_capsule_is_smaller_than_raw_evidence_contract": (
            capsule_chars < raw_chars
        ),
    }

    return {
        "schema": SCHEMA,
        "status": (
            "PASS"
            if all(checks.values())
            else "FAIL"
        ),
        "classification": (
            "DECISION_RELEVANT_VALIDITY_GATE_FOR_COMPILED_PHYSICAL_RENT_LOOKUP"
        ),
        "source": data["source"],
        "baseline_surface": derived,
        "mutation_cases": cases,
        "keep_cases": list(keep_cases),
        "invalidate_cases": list(invalidate_cases),
        "resident_surface": {
            "validity_capsule_chars": capsule_chars,
            "raw_evidence_contract_chars": raw_chars,
            "validity_fraction": (
                capsule_chars / raw_chars
            ),
        },
        "checks": checks,
        "decision": (
            "INVALIDATE_THE_COMPILED_LOOKUP_ONLY_WHEN_THE_REDERIVED_DECISION_SURFACE_CHANGES"
        ),
        "meta_transfer": (
            "evidence mutation is not itself an invalidation event; invalidate resident compiled state only when the mutation can change an admissible decision"
        ),
        "claim_ceiling": (
            "DECISION_SURFACE_VALIDITY_GATE_FOR_THE_FP058_SCALAR_MEMORY_RENT_LOOKUP_ONLY"
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
