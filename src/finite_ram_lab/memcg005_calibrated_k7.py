from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _predicted_absent(m: int, k: int) -> bool:
    return m >= k


def _state_bit(state: str) -> int | None:
    if state == "PRESENT":
        return 0
    if state == "ABSENT":
        return 1
    return None


def _equivalence_classes(tested_m: list[int], candidates: list[int]) -> list[dict[str, Any]]:
    groups: dict[tuple[int, ...], list[int]] = {}
    for k in candidates:
        signature = tuple(int(_predicted_absent(m, k)) for m in tested_m)
        groups.setdefault(signature, []).append(k)
    return [
        {"candidate_k": ks, "signature": list(sig)}
        for sig, ks in sorted(groups.items(), key=lambda item: item[1][0])
    ]


def analyze_trials(spec: dict[str, Any], trials: list[dict[str, Any]]) -> dict[str, Any]:
    tested_m = [int(x) for x in spec["tested_m"]]
    blocks_n = int(spec["runner_blocks"])
    expected = {(b, m) for b in range(blocks_n) for m in tested_m}
    got = {(int(t["block"]), int(t["m"])) for t in trials}
    if got != expected:
        raise ValueError("incomplete replica matrix")

    source_signature = {0: "PRESENT", 5: "PRESENT", 6: "PRESENT", 7: "ABSENT", 8: "ABSENT"}

    blocks = []
    support_blocks = 0
    complete_valid_blocks = 0
    invalid_by_m = {str(m): 0 for m in tested_m}

    for b in range(blocks_n):
        rows = {int(t["m"]): t for t in trials if int(t["block"]) == b}
        all_valid = all(bool(rows[m]["valid_state"]) for m in tested_m)
        if all_valid:
            complete_valid_blocks += 1
        for m in tested_m:
            if not bool(rows[m]["valid_state"]):
                invalid_by_m[str(m)] += 1

        states = {str(m): rows[m]["target_state"] for m in tested_m}
        exact = all_valid and all(rows[m]["target_state"] == source_signature[m] for m in tested_m)
        support_blocks += int(exact)

        blocks.append({
            "block": b,
            "all_replicas_valid": all_valid,
            "states": states,
            "supports_calibrated_k7": exact,
            "invalid_reasons": {
                str(m): rows[m].get("invalid_reason")
                for m in tested_m
                if not bool(rows[m]["valid_state"])
            },
        })

    candidates = [int(x) for x in spec["candidate_k"]]
    eps = float(spec["model_error_floor"])
    model_rows = {}
    for k in candidates:
        errors = 0
        n = 0
        for t in trials:
            bit = _state_bit(t["target_state"])
            if not bool(t["valid_state"]) or bit is None:
                continue
            pred = int(_predicted_absent(int(t["m"]), k))
            errors += int(pred != bit)
            n += 1
        log_loss_bits = (
            (n - errors) * -math.log2(1.0 - eps)
            + errors * -math.log2(eps)
        )
        exception_bits = 0.0 if errors == 0 else math.log2(math.comb(n, errors))
        mdl_bits = math.log2(len(candidates)) + exception_bits
        model_rows[str(k)] = {
            "valid_observations": n,
            "classification_errors": errors,
            "log_loss_bits": log_loss_bits,
            "mdl_bits": mdl_bits,
        }

    min_errors = min(v["classification_errors"] for v in model_rows.values())
    best_error_ks = [int(k) for k, v in model_rows.items() if v["classification_errors"] == min_errors]

    min_ll = min(v["log_loss_bits"] for v in model_rows.values())
    best_logloss_ks = [int(k) for k, v in model_rows.items() if abs(v["log_loss_bits"] - min_ll) < 1e-12]

    min_mdl = min(v["mdl_bits"] for v in model_rows.values())
    best_mdl_ks = [int(k) for k, v in model_rows.items() if abs(v["mdl_bits"] - min_mdl) < 1e-12]

    lobo = []
    for held in range(blocks_n):
        train = [t for t in trials if int(t["block"]) != held and bool(t["valid_state"]) and _state_bit(t["target_state"]) is not None]
        held_rows = [t for t in trials if int(t["block"]) == held and bool(t["valid_state"]) and _state_bit(t["target_state"]) is not None]
        train_err = {}
        for k in candidates:
            train_err[k] = sum(
                int(int(_predicted_absent(int(t["m"]), k)) != _state_bit(t["target_state"]))
                for t in train
            )
        e = min(train_err.values())
        selected = [k for k in candidates if train_err[k] == e]
        accuracies = {}
        for k in selected:
            if not held_rows:
                accuracies[str(k)] = None
            else:
                ok = sum(
                    int(int(_predicted_absent(int(t["m"]), k)) == _state_bit(t["target_state"]))
                    for t in held_rows
                )
                accuracies[str(k)] = ok / len(held_rows)
        lobo.append({
            "heldout_block": held,
            "selected_k": selected,
            "train_errors": e,
            "heldout_accuracy_by_k": accuracies,
        })

    systematic_invalid = any(v >= 2 for v in invalid_by_m.values())
    required = int(spec["required_support_blocks"])

    if support_blocks >= required and not systematic_invalid:
        decision = "SUPPORT_CALIBRATED_K7"
    elif complete_valid_blocks >= 3 and support_blocks <= 1 and 7 not in best_error_ks:
        decision = "REJECT_CALIBRATED_K7"
    else:
        decision = "INCONCLUSIVE"

    return {
        "experiment_id": spec["experiment_id"],
        "decision": decision,
        "support_blocks": support_blocks,
        "complete_valid_blocks": complete_valid_blocks,
        "invalid_by_m": invalid_by_m,
        "systematic_invalid": systematic_invalid,
        "tested_m": tested_m,
        "source_signature": {str(k): v for k, v in source_signature.items()},
        "blocks": blocks,
        "model_by_k": model_rows,
        "best_k_by_errors": best_error_ks,
        "best_k_by_log_loss": best_logloss_ks,
        "best_k_by_mdl": best_mdl_ks,
        "candidate_equivalence_classes": _equivalence_classes(tested_m, candidates),
        "leave_one_block_out": lobo,
        "trials": trials,
        "inference_boundary": (
            "Hosted calibrated memcg slot-boundary probe; "
            "not a hardware-memory law and not local-substrate replicated."
        ),
    }
