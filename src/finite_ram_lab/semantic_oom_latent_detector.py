from __future__ import annotations

import hashlib
import json
import math


SCHEMA = "finite-ram-lab.semantic-oom-latent-detector/v0.1"
SEED = "FR-SOOM-002E-v0.1"
TOTAL_EPISODES = 8192
TRAIN_EPISODES = 4096
TEST_EPISODES = TOTAL_EPISODES - TRAIN_EPISODES
LATENT_BAD_PROBABILITY = 0.08
TRAIN_RECALL_TARGET = 0.95
FALSE_ESCALATION_SEMANTIC_DELTA = 5


def _uniform(episode: int, field: str) -> float:
    payload = f"{SEED}|{episode}|{field}".encode("utf-8")
    value = int.from_bytes(
        hashlib.sha256(payload).digest()[:8],
        "big",
    )
    return value / 2**64


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _episode(episode: int) -> dict:
    bad = (
        _uniform(episode, "latent")
        < LATENT_BAD_PROBABILITY
    )

    if bad:
        psi_full_avg10 = (
            12.0 + 38.0 * _uniform(episode, "psi")
        )
        psi_slope = (
            0.0 + 10.0 * _uniform(episode, "slope")
        )
        reclaim_progress_mib_50ms = (
            0.0 + 400.0 * _uniform(
                episode,
                "reclaim",
            )
        )
        refault_ratio = (
            0.15 + 0.65 * _uniform(
                episode,
                "refault",
            )
        )
        cooperative_progress_mib_50ms = (
            0.0 + 400.0 * _uniform(
                episode,
                "progress",
            )
        )
        swap_velocity_mib_s = (
            50.0 + 650.0 * _uniform(
                episode,
                "swap",
            )
        )
    else:
        psi_full_avg10 = (
            5.0 + 25.0 * _uniform(episode, "psi")
        )
        psi_slope = (
            -1.0 + 7.0 * _uniform(
                episode,
                "slope",
            )
        )
        reclaim_progress_mib_50ms = (
            100.0 + 550.0 * _uniform(
                episode,
                "reclaim",
            )
        )
        refault_ratio = (
            0.05 + 0.40 * _uniform(
                episode,
                "refault",
            )
        )
        cooperative_progress_mib_50ms = (
            100.0 + 550.0 * _uniform(
                episode,
                "progress",
            )
        )
        swap_velocity_mib_s = (
            0.0 + 300.0 * _uniform(
                episode,
                "swap",
            )
        )

    components = {
        "psi": _clamp01(
            (psi_full_avg10 - 5.0) / 45.0
        ),
        "psi_slope": _clamp01(
            (psi_slope + 1.0) / 11.0
        ),
        "low_reclaim_progress": (
            1.0
            - _clamp01(
                reclaim_progress_mib_50ms / 650.0
            )
        ),
        "refault": _clamp01(
            refault_ratio / 0.8
        ),
        "low_cooperative_progress": (
            1.0
            - _clamp01(
                cooperative_progress_mib_50ms
                / 650.0
            )
        ),
        "swap_velocity": _clamp01(
            swap_velocity_mib_s / 700.0
        ),
    }

    multi_signal_score = (
        sum(components.values())
        / len(components)
    )

    return {
        "episode": episode,
        "latent_bad": bad,
        "observed_by_ms": 50,
        "psi_full_avg10": psi_full_avg10,
        "psi_slope": psi_slope,
        "reclaim_progress_mib_50ms": (
            reclaim_progress_mib_50ms
        ),
        "refault_ratio": refault_ratio,
        "cooperative_progress_mib_50ms": (
            cooperative_progress_mib_50ms
        ),
        "swap_velocity_mib_s": (
            swap_velocity_mib_s
        ),
        "multi_signal_components": components,
        "multi_signal_score": multi_signal_score,
    }


def _fit_recall_threshold(
    rows: list[dict],
    score_key: str,
) -> float:
    bad_scores = sorted(
        (
            row[score_key]
            for row in rows
            if row["latent_bad"]
        ),
        reverse=True,
    )

    required_true_positives = math.ceil(
        TRAIN_RECALL_TARGET * len(bad_scores)
    )

    return bad_scores[
        required_true_positives - 1
    ]


def _evaluate(
    rows: list[dict],
    *,
    score_key: str,
    threshold: float,
) -> dict:
    tp = 0
    fn = 0
    fp = 0
    tn = 0

    first_false_positive: dict | None = None
    first_false_negative: dict | None = None

    for row in rows:
        predicted_bad = row[score_key] >= threshold
        actual_bad = row["latent_bad"]

        if actual_bad and predicted_bad:
            tp += 1
        elif actual_bad and not predicted_bad:
            fn += 1

            if first_false_negative is None:
                first_false_negative = row
        elif not actual_bad and predicted_bad:
            fp += 1

            if first_false_positive is None:
                first_false_positive = row
        else:
            tn += 1

    recall = tp / (tp + fn)
    false_positive_rate = fp / (fp + tn)
    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0.0
    )

    return {
        "threshold": threshold,
        "true_positive": tp,
        "false_negative": fn,
        "false_positive": fp,
        "true_negative": tn,
        "recall": recall,
        "false_positive_rate": false_positive_rate,
        "specificity": 1.0 - false_positive_rate,
        "precision": precision,
        "false_escalation_semantic_delta": (
            fp * FALSE_ESCALATION_SEMANTIC_DELTA
        ),
        "first_false_positive": first_false_positive,
        "first_false_negative": first_false_negative,
    }


def run_panel() -> dict:
    rows = [
        _episode(episode)
        for episode in range(TOTAL_EPISODES)
    ]

    train = rows[:TRAIN_EPISODES]
    test = rows[TRAIN_EPISODES:]

    psi_threshold = _fit_recall_threshold(
        train,
        "psi_full_avg10",
    )
    multi_threshold = _fit_recall_threshold(
        train,
        "multi_signal_score",
    )

    train_psi = _evaluate(
        train,
        score_key="psi_full_avg10",
        threshold=psi_threshold,
    )
    train_multi = _evaluate(
        train,
        score_key="multi_signal_score",
        threshold=multi_threshold,
    )

    test_psi = _evaluate(
        test,
        score_key="psi_full_avg10",
        threshold=psi_threshold,
    )
    test_multi = _evaluate(
        test,
        score_key="multi_signal_score",
        threshold=multi_threshold,
    )

    train_bad = sum(
        int(row["latent_bad"])
        for row in train
    )
    test_bad = sum(
        int(row["latent_bad"])
        for row in test
    )

    if train_bad != 308:
        raise RuntimeError(
            "train_bad_reference_changed"
        )

    if test_bad != 305:
        raise RuntimeError(
            "test_bad_reference_changed"
        )

    if test_psi["true_positive"] != 287:
        raise RuntimeError(
            "psi_test_tp_reference_changed"
        )

    if test_multi["true_positive"] != 287:
        raise RuntimeError(
            "multi_test_tp_reference_changed"
        )

    if test_psi["false_positive"] != 2447:
        raise RuntimeError(
            "psi_test_fp_reference_changed"
        )

    if test_multi["false_positive"] != 152:
        raise RuntimeError(
            "multi_test_fp_reference_changed"
        )

    if not (
        test_multi["false_positive_rate"]
        < 0.05
    ):
        raise RuntimeError(
            "multi_signal_fpr_not_low"
        )

    if not (
        test_psi["false_positive_rate"]
        > 0.60
    ):
        raise RuntimeError(
            "psi_only_fpr_not_high"
        )

    if not (
        test_multi[
            "false_escalation_semantic_delta"
        ]
        < test_psi[
            "false_escalation_semantic_delta"
        ]
    ):
        raise RuntimeError(
            "multi_signal_false_escalation_cost_not_lower"
        )

    if not (
        test_multi["recall"] >= 0.90
    ):
        raise RuntimeError(
            "multi_signal_test_recall_too_low"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_LATENT_SHARED_PRESSURE_DETECTOR_VALIDATED"
        ),
        "synthetic_only": True,
        "live_control_claim": False,
        "seed": SEED,
        "total_episodes": TOTAL_EPISODES,
        "train_episodes": TRAIN_EPISODES,
        "test_episodes": TEST_EPISODES,
        "latent_bad_probability": (
            LATENT_BAD_PROBABILITY
        ),
        "train_recall_target": (
            TRAIN_RECALL_TARGET
        ),
        "train_bad_count": train_bad,
        "test_bad_count": test_bad,
        "detectors": {
            "PSI_ONLY": {
                "score_key": "psi_full_avg10",
                "train": train_psi,
                "test": test_psi,
            },
            "MULTI_SIGNAL": {
                "score_key": "multi_signal_score",
                "train": train_multi,
                "test": test_multi,
            },
        },
        "primary_finding": (
            "MULTI_SIGNAL_REDUCES_FALSE_ESCALATION_AT_MATCHED_HELDOUT_RECALL"
        ),
        "claim_ceiling": (
            "SYNTHETIC_LATENT_PRESSURE_DETECTOR_ONLY"
        ),
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
