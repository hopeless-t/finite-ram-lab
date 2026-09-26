from __future__ import annotations

import argparse
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from finite_ram_lab.gate001_policy import _block_arrays, load_input
from finite_ram_lab.sig001_design_mc import (
    _cost_ratio_summary,
    clopper_pearson_lower,
)


PROTOCOL_ID = "SIG-001-CAL-PROTOCOL-v1"

FROZEN_PROTOCOL: dict[str, Any] = {
    "protocol_id": PROTOCOL_ID,
    "action_cost_input_json": (
        "analysis/inputs/GATE-001-EXP003-policy-primitives.json"
    ),
    "source_trials_sha256": (
        "29aa46c700b817785bdc67ae4a6eb3c3330887ff5a06efd1f7516aa6ed53ba66"
    ),
    "primary_metric": "log_total_work",
    "secondary_metric": "arithmetic_total_work",
    "action_cost_bootstrap_resamples": 100000,
    "action_cost_bootstrap_seed": 2026092702,
    "familywise_alpha": 0.05,
    "bonferroni_components": 4,
    "abstain_semantics": "NO_ACT",
    "independence_policy": "one_event_per_independence_unit",
    "decision_outputs": ["CERTIFIED", "NOT_CERTIFIED"],
}

_MANIFEST_KEYS = {
    "schema_version",
    "protocol_id",
    "provider_id",
    "provider_version",
    "decision_rule_id",
    "epoch_id",
    "environment_digest",
    "prediction_horizon_id",
    "predictions_sha256",
    "external_seal_ref",
}

_PREDICTION_REQUIRED = {
    "schema_version",
    "event_id",
    "independence_unit_id",
    "decision",
    "prediction_time_ns",
}
_PREDICTION_ALLOWED = _PREDICTION_REQUIRED | {"score"}

_OUTCOME_KEYS = {
    "schema_version",
    "event_id",
    "true_state",
    "outcome_time_ns",
}

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ENV_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def _read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text())


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    text = Path(path).read_text()
    if not text:
        raise ValueError("JSONL artifact is empty")
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            raise ValueError(f"blank JSONL line at {lineno}")
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"JSONL line {lineno} is not an object")
        rows.append(value)
    return rows


def _sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _nonempty_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _nonnegative_int(value: Any, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _validate_frozen_protocol(protocol: Any) -> dict[str, Any]:
    if protocol != FROZEN_PROTOCOL:
        raise ValueError("protocol does not exactly match frozen v1 contract")
    return protocol


def _validate_manifest(manifest: Any) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    if set(manifest) != _MANIFEST_KEYS:
        raise ValueError("manifest keys do not match frozen schema")
    if manifest["schema_version"] != 1:
        raise ValueError("unsupported manifest schema_version")
    if manifest["protocol_id"] != PROTOCOL_ID:
        raise ValueError("manifest protocol_id mismatch")

    for key in (
        "provider_id",
        "provider_version",
        "decision_rule_id",
        "epoch_id",
        "prediction_horizon_id",
        "external_seal_ref",
    ):
        _nonempty_string(manifest[key], key)

    if not isinstance(manifest["environment_digest"], str) or not (
        _ENV_DIGEST.fullmatch(manifest["environment_digest"])
    ):
        raise ValueError("invalid environment_digest")
    if not isinstance(manifest["predictions_sha256"], str) or not (
        _HEX64.fullmatch(manifest["predictions_sha256"])
    ):
        raise ValueError("invalid predictions_sha256")

    return manifest


def _validate_predictions(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    by_event: dict[str, dict[str, Any]] = {}
    independence_units: set[str] = set()

    for row in rows:
        keys = set(row)
        if not _PREDICTION_REQUIRED <= keys <= _PREDICTION_ALLOWED:
            raise ValueError("prediction keys do not match frozen schema")
        if row["schema_version"] != 1:
            raise ValueError("unsupported prediction schema_version")

        event_id = _nonempty_string(row["event_id"], "event_id")
        unit_id = _nonempty_string(
            row["independence_unit_id"],
            "independence_unit_id",
        )
        if event_id in by_event:
            raise ValueError(f"duplicate prediction event_id: {event_id}")
        if unit_id in independence_units:
            raise ValueError(
                f"duplicate independence_unit_id: {unit_id}"
            )

        decision = row["decision"]
        if decision not in {"ACT", "NO_ACT", "ABSTAIN"}:
            raise ValueError(f"invalid decision: {decision}")
        _nonnegative_int(row["prediction_time_ns"], "prediction_time_ns")

        if "score" in row and row["score"] is not None:
            score = row["score"]
            if isinstance(score, bool) or not isinstance(
                score, (int, float)
            ):
                raise ValueError("score must be numeric or null")
            if not 0.0 <= float(score) <= 1.0:
                raise ValueError("score must be in [0,1]")

        by_event[event_id] = row
        independence_units.add(unit_id)

    return by_event


def _validate_outcomes(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    by_event: dict[str, dict[str, Any]] = {}
    for row in rows:
        if set(row) != _OUTCOME_KEYS:
            raise ValueError("outcome keys do not match frozen schema")
        if row["schema_version"] != 1:
            raise ValueError("unsupported outcome schema_version")

        event_id = _nonempty_string(row["event_id"], "event_id")
        if event_id in by_event:
            raise ValueError(f"duplicate outcome event_id: {event_id}")
        if row["true_state"] not in {"misaligned", "aligned"}:
            raise ValueError("invalid true_state")
        _nonnegative_int(row["outcome_time_ns"], "outcome_time_ns")
        by_event[event_id] = row
    return by_event


@lru_cache(maxsize=4)
def _canonical_cost_summary(
    input_path: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    data = load_input(input_path)
    if (
        data["provenance"]["source_trials_sha256"]
        != FROZEN_PROTOCOL["source_trials_sha256"]
    ):
        raise ValueError("action-cost source trials digest mismatch")

    arithmetic = _block_arrays(data, "mean_work_ms")
    logv = _block_arrays(data, "mean_log_work")
    if len(arithmetic["blocks"]) != 16:
        raise ValueError("frozen action-cost input requires 16 blocks")

    alpha_component = (
        FROZEN_PROTOCOL["familywise_alpha"]
        / FROZEN_PROTOCOL["bonferroni_components"]
    )
    resamples = FROZEN_PROTOCOL["action_cost_bootstrap_resamples"]
    seed = FROZEN_PROTOCOL["action_cost_bootstrap_seed"]

    primary = _cost_ratio_summary(
        logv,
        resamples=resamples,
        seed=seed,
        alpha=alpha_component,
    )
    secondary = _cost_ratio_summary(
        arithmetic,
        resamples=resamples,
        seed=seed + 1,
        alpha=alpha_component,
    )

    if (
        primary["lower_ratio"] <= 0.0
        or secondary["lower_ratio"] <= 0.0
    ):
        raise ValueError("non-positive fail-closed action-cost ratio")

    return primary, secondary, data["provenance"]


def _lower_bound(successes: int, trials: int, alpha: float) -> float:
    return float(clopper_pearson_lower(successes, trials, alpha))


def _required_specificity(q_l: float, t_l: float, ratio_l: float) -> float:
    if not 0.0 <= q_l < 1.0:
        return float("inf")
    if not 0.0 <= t_l <= 1.0:
        return float("inf")
    if ratio_l <= 0.0:
        return float("inf")
    return 1.0 - q_l * t_l * ratio_l / (1.0 - q_l)


def calibrate(
    *,
    protocol_path: str | Path,
    manifest_path: str | Path,
    predictions_path: str | Path,
    outcomes_path: str | Path,
) -> dict[str, Any]:
    protocol = _validate_frozen_protocol(_read_json(protocol_path))
    manifest = _validate_manifest(_read_json(manifest_path))

    actual_prediction_digest = _sha256(predictions_path)
    if actual_prediction_digest != manifest["predictions_sha256"]:
        raise ValueError("prediction artifact SHA-256 mismatch")

    predictions = _validate_predictions(_read_jsonl(predictions_path))
    outcomes = _validate_outcomes(_read_jsonl(outcomes_path))

    if set(predictions) != set(outcomes):
        raise ValueError("prediction/outcome event-set mismatch")

    n = len(predictions)
    if n == 0:
        raise ValueError("no calibration evidence")

    misaligned = 0
    aligned = 0
    act_misaligned = 0
    noact_aligned = 0
    abstain_count = 0

    for event_id, pred in predictions.items():
        outcome = outcomes[event_id]
        if outcome["outcome_time_ns"] <= pred["prediction_time_ns"]:
            raise ValueError(
                f"outcome not later than prediction: {event_id}"
            )

        decision = pred["decision"]
        state = outcome["true_state"]
        if decision == "ABSTAIN":
            abstain_count += 1

        if state == "misaligned":
            misaligned += 1
            if decision == "ACT":
                act_misaligned += 1
        else:
            aligned += 1
            if decision in {"NO_ACT", "ABSTAIN"}:
                noact_aligned += 1

    if misaligned == 0 or aligned == 0:
        raise ValueError(
            "both misaligned and aligned independent evidence are required"
        )

    alpha_component = (
        protocol["familywise_alpha"]
        / protocol["bonferroni_components"]
    )
    q_l = _lower_bound(misaligned, n, alpha_component)
    t_l = _lower_bound(
        act_misaligned,
        misaligned,
        alpha_component,
    )
    s_l = _lower_bound(
        noact_aligned,
        aligned,
        alpha_component,
    )

    primary_cost, secondary_cost, source = _canonical_cost_summary(
        protocol["action_cost_input_json"]
    )

    primary_required = _required_specificity(
        q_l,
        t_l,
        float(primary_cost["lower_ratio"]),
    )
    secondary_required = _required_specificity(
        q_l,
        t_l,
        float(secondary_cost["lower_ratio"]),
    )

    primary_margin = s_l - primary_required
    secondary_margin = s_l - secondary_required
    decision = (
        "CERTIFIED" if primary_margin > 0.0 else "NOT_CERTIFIED"
    )

    return {
        "analysis_id": PROTOCOL_ID,
        "validation_status": "PASS",
        "decision": decision,
        "manifest_binding": {
            "provider_id": manifest["provider_id"],
            "provider_version": manifest["provider_version"],
            "decision_rule_id": manifest["decision_rule_id"],
            "epoch_id": manifest["epoch_id"],
            "environment_digest": manifest["environment_digest"],
            "prediction_horizon_id": manifest["prediction_horizon_id"],
            "external_seal_ref": manifest["external_seal_ref"],
            "predictions_sha256": actual_prediction_digest,
        },
        "counts": {
            "independent_units": n,
            "misaligned": misaligned,
            "aligned": aligned,
            "act_when_misaligned": act_misaligned,
            "noact_or_abstain_when_aligned": noact_aligned,
            "abstain_total": abstain_count,
        },
        "lower_bounds": {
            "q": q_l,
            "sensitivity": t_l,
            "specificity": s_l,
            "alpha_component": alpha_component,
        },
        "primary": {
            "metric": protocol["primary_metric"],
            "action_cost_ratio_lower": primary_cost["lower_ratio"],
            "required_specificity": primary_required,
            "observed_specificity_lower": s_l,
            "margin": primary_margin,
            "certified": primary_margin > 0.0,
        },
        "secondary": {
            "metric": protocol["secondary_metric"],
            "action_cost_ratio_lower": secondary_cost["lower_ratio"],
            "required_specificity": secondary_required,
            "observed_specificity_lower": s_l,
            "margin": secondary_margin,
            "certified": secondary_margin > 0.0,
        },
        "action_cost_provenance": source,
        "authority_boundary": (
            "Offline observational certification only. CERTIFIED does "
            "not execute ACT. NOT_CERTIFIED maps to NO-ACT at any "
            "future authority boundary."
        ),
    }


def _failure(error: Exception) -> dict[str, Any]:
    return {
        "analysis_id": PROTOCOL_ID,
        "validation_status": "FAIL",
        "decision": "NOT_CERTIFIED",
        "error": f"{type(error).__name__}: {error}",
        "authority_boundary": (
            "Validation failure is fail-closed and cannot authorize ACT."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--protocol",
        default="specs/SIG-001-CAL-PROTOCOL-v1.json",
    )
    p.add_argument("--manifest", required=True)
    p.add_argument("--predictions", required=True)
    p.add_argument("--outcomes", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    try:
        result = calibrate(
            protocol_path=args.protocol,
            manifest_path=args.manifest,
            predictions_path=args.predictions,
            outcomes_path=args.outcomes,
        )
        exit_code = 0
    except Exception as exc:
        result = _failure(exc)
        exit_code = 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
