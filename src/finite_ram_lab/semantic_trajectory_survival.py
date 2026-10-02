from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json


SCHEMA = "finite-ram-lab.semantic-trajectory-survival/v0.1"
SEED = 20261002
ERROR_PROBABILITY = 0.01
REPLICATES = 2048
BUDGETS = (2, 4, 6)
LENGTHS = (1, 2, 4, 7, 8, 9, 15, 16, 17, 31, 32)
MAX_LENGTH = max(LENGTHS)
REFRESH_INTERVAL = 8
DISTRACTORS_PER_STEP = 2
QUERY_KEYS = ("goal", "constraint")
HASH_DOMAIN = "TRAJECTORY_SCORE_FLIP"
MAX_BIOPSIES = 8


@dataclass(frozen=True)
class TrajectoryEvent:
    serial: int
    key: str
    value: str


def _uniform01(*parts: object) -> float:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def _latest_by_key(
    events: list[TrajectoryEvent],
) -> dict[str, TrajectoryEvent]:
    out: dict[str, TrajectoryEvent] = {}
    for event in events:
        out[event.key] = event
    return out


def _select_resident(
    candidates: list[TrajectoryEvent],
    *,
    budget: int,
    replicate: int,
    step: int,
    error_probability: float = ERROR_PROBABILITY,
    seed: int = SEED,
) -> tuple[list[TrajectoryEvent], dict]:
    latest = _latest_by_key(candidates)
    required_serials = {
        latest[key].serial
        for key in QUERY_KEYS
        if key in latest
    }

    ranked: list[tuple[int, int, TrajectoryEvent]] = []
    false_negatives: list[int] = []
    false_positives: list[int] = []

    for event in candidates:
        true_relevant = event.serial in required_serials
        flip = (
            _uniform01(
                seed,
                HASH_DOMAIN,
                error_probability,
                budget,
                replicate,
                step,
                event.serial,
            )
            < error_probability
        )
        predicted_relevant = (
            not true_relevant if flip else true_relevant
        )

        if true_relevant and not predicted_relevant:
            false_negatives.append(event.serial)
        elif not true_relevant and predicted_relevant:
            false_positives.append(event.serial)

        ranked.append(
            (
                1 if predicted_relevant else 0,
                event.serial,
                event,
            )
        )

    ranked.sort(
        key=lambda item: (item[0], item[1]),
        reverse=True,
    )
    selected = [
        event
        for _, _, event in ranked[
            : min(budget, len(ranked))
        ]
    ]
    selected.sort(key=lambda event: event.serial)

    return selected, {
        "required_latest_serials": sorted(required_serials),
        "false_negative_required_serials": false_negatives,
        "false_positive_distractor_serials": false_positives,
    }


def _semantic_status(
    resident: list[TrajectoryEvent],
    truth: dict[str, str],
) -> dict:
    latest = _latest_by_key(resident)

    missing = [
        key for key in QUERY_KEYS
        if key not in latest
    ]
    stale = [
        key for key in QUERY_KEYS
        if key in latest and latest[key].value != truth[key]
    ]

    return {
        "exact": not missing and not stale,
        "missing_required_keys": missing,
        "stale_required_keys": stale,
    }


def simulate_trajectory(
    *,
    budget: int,
    replicate: int,
    max_length: int = MAX_LENGTH,
    error_probability: float = ERROR_PROBABILITY,
    seed: int = SEED,
) -> list[dict]:
    if budget not in BUDGETS:
        raise ValueError("unfrozen_budget")
    if max_length <= 0 or max_length > MAX_LENGTH:
        raise ValueError("max_length_out_of_range")
    if not 0.0 <= error_probability <= 1.0:
        raise ValueError("error_probability_out_of_range")

    serial = 0
    truth = {
        "goal": "g0",
        "constraint": "c0",
    }
    resident: list[TrajectoryEvent] = []

    for key in QUERY_KEYS:
        resident.append(
            TrajectoryEvent(
                serial=serial,
                key=key,
                value=truth[key],
            )
        )
        serial += 1

    rows: list[dict] = []
    had_failure = False

    for step in range(1, max_length + 1):
        incoming: list[TrajectoryEvent] = []

        refresh = step % REFRESH_INTERVAL == 0
        if refresh:
            epoch = step // REFRESH_INTERVAL
            truth["goal"] = f"g{epoch}"
            truth["constraint"] = f"c{epoch}"
            for key in QUERY_KEYS:
                incoming.append(
                    TrajectoryEvent(
                        serial=serial,
                        key=key,
                        value=truth[key],
                    )
                )
                serial += 1

        for distractor in range(DISTRACTORS_PER_STEP):
            incoming.append(
                TrajectoryEvent(
                    serial=serial,
                    key=f"d{step}_{distractor}",
                    value=str(step),
                )
            )
            serial += 1

        candidates = resident + incoming
        resident, diagnostics = _select_resident(
            candidates,
            budget=budget,
            replicate=replicate,
            step=step,
            error_probability=error_probability,
            seed=seed,
        )
        semantic = _semantic_status(resident, truth)
        exact = semantic["exact"]
        recovered_this_step = exact and had_failure

        rows.append(
            {
                "step": step,
                "refresh": refresh,
                "exact": exact,
                "recovered_after_prior_failure": (
                    recovered_this_step
                ),
                "resident_serials": [
                    event.serial for event in resident
                ],
                "resident_keys": [
                    event.key for event in resident
                ],
                "truth": dict(truth),
                "missing_required_keys": semantic[
                    "missing_required_keys"
                ],
                "stale_required_keys": semantic[
                    "stale_required_keys"
                ],
                "required_latest_serials": diagnostics[
                    "required_latest_serials"
                ],
                "false_negative_required_serials": diagnostics[
                    "false_negative_required_serials"
                ],
                "false_positive_distractor_serials": diagnostics[
                    "false_positive_distractor_serials"
                ],
            }
        )

        if not exact:
            had_failure = True

    return rows


def _aggregate_budget(budget: int) -> dict:
    trajectories = [
        simulate_trajectory(
            budget=budget,
            replicate=replicate,
        )
        for replicate in range(REPLICATES)
    ]

    cells: list[dict] = []
    first_failure_biopsies: list[dict] = []

    for replicate, rows in enumerate(trajectories):
        first_failure = next(
            (row for row in rows if not row["exact"]),
            None,
        )
        if (
            first_failure is not None
            and len(first_failure_biopsies) < MAX_BIOPSIES
        ):
            first_failure_biopsies.append(
                {
                    "replicate": replicate,
                    **first_failure,
                }
            )

    for length in LENGTHS:
        survival_count = 0
        endpoint_success_count = 0
        exact_steps = 0
        recovered_trajectory_count = 0
        first_failure_histogram: Counter[str] = Counter()

        for rows in trajectories:
            prefix = rows[:length]
            exact_flags = [row["exact"] for row in prefix]
            all_exact = all(exact_flags)
            endpoint_exact = exact_flags[-1]

            survival_count += int(all_exact)
            endpoint_success_count += int(endpoint_exact)
            exact_steps += sum(exact_flags)

            first_failure = next(
                (
                    row["step"]
                    for row in prefix
                    if not row["exact"]
                ),
                None,
            )
            if first_failure is not None:
                first_failure_histogram[str(first_failure)] += 1

            if (
                first_failure is not None
                and endpoint_exact
            ):
                recovered_trajectory_count += 1

        survival_rate = survival_count / REPLICATES
        endpoint_success_rate = (
            endpoint_success_count / REPLICATES
        )
        mean_step_exact_rate = (
            exact_steps / (REPLICATES * length)
        )

        cells.append(
            {
                "budget": budget,
                "length": length,
                "replicates": REPLICATES,
                "trajectory_survival_count": survival_count,
                "trajectory_survival_rate": survival_rate,
                "endpoint_success_count": endpoint_success_count,
                "endpoint_success_rate": endpoint_success_rate,
                "mean_step_exact_rate": mean_step_exact_rate,
                "endpoint_masking_gap": (
                    endpoint_success_rate - survival_rate
                ),
                "recovered_trajectory_count": (
                    recovered_trajectory_count
                ),
                "first_failure_histogram": dict(
                    sorted(
                        first_failure_histogram.items(),
                        key=lambda item: int(item[0]),
                    )
                ),
            }
        )

    one_step = next(
        cell for cell in cells if cell["length"] == 1
    )
    cold_start_rate = one_step["trajectory_survival_rate"]

    for cell in cells:
        cell["cold_start_independent_projection"] = (
            cold_start_rate ** cell["length"]
        )
        cell["cold_start_projection_error"] = (
            cell["cold_start_independent_projection"]
            - cell["trajectory_survival_rate"]
        )

    return {
        "budget": budget,
        "cells": cells,
        "first_failure_biopsies": first_failure_biopsies,
    }


def run_panel() -> dict:
    by_budget = [
        _aggregate_budget(budget)
        for budget in BUDGETS
    ]

    def cell(budget: int, length: int) -> dict:
        block = next(
            row for row in by_budget
            if row["budget"] == budget
        )
        return next(
            row for row in block["cells"]
            if row["length"] == length
        )

    for budget in BUDGETS:
        rates = [
            cell(budget, length)[
                "trajectory_survival_rate"
            ]
            for length in LENGTHS
        ]
        if rates != sorted(rates, reverse=True):
            raise RuntimeError(
                "trajectory_survival_not_monotone"
            )

    if cell(4, 1)["trajectory_survival_rate"] != 1.0:
        raise RuntimeError("budget4_cold_start_not_exact")
    if cell(6, 1)["trajectory_survival_rate"] != 1.0:
        raise RuntimeError("budget6_cold_start_not_exact")

    length32 = {
        budget: cell(budget, 32)
        for budget in BUDGETS
    }

    if not (
        length32[2]["trajectory_survival_rate"]
        < length32[4]["trajectory_survival_rate"]
        < length32[6]["trajectory_survival_rate"]
    ):
        raise RuntimeError(
            "resident_budget_survival_order_unexpected"
        )

    if length32[4]["trajectory_survival_rate"] >= 0.70:
        raise RuntimeError(
            "budget4_long_trajectory_too_high_for_fixture"
        )
    if length32[6]["trajectory_survival_rate"] >= 0.75:
        raise RuntimeError(
            "budget6_long_trajectory_too_high_for_fixture"
        )

    minimum_masking_gap = {
        2: 0.60,
        4: 0.35,
        6: 0.30,
    }
    for budget, minimum_gap in minimum_masking_gap.items():
        if (
            length32[budget]["endpoint_masking_gap"]
            <= minimum_gap
        ):
            raise RuntimeError(
                "endpoint_masking_gap_not_exposed"
            )

    for budget in BUDGETS:
        for refresh_length in (8, 16, 32):
            if (
                cell(budget, refresh_length)[
                    "endpoint_success_rate"
                ]
                < 0.95
            ):
                raise RuntimeError(
                    "refresh_endpoint_recovery_too_low"
                )

    result = {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_TRAJECTORY_SURVIVAL_HARNESS_VALIDATED"
        ),
        "synthetic_only": True,
        "empirical_model_claim": False,
        "seed": SEED,
        "hash_domain": HASH_DOMAIN,
        "selector_error_probability": ERROR_PROBABILITY,
        "replicates": REPLICATES,
        "budgets": list(BUDGETS),
        "lengths": list(LENGTHS),
        "refresh_interval": REFRESH_INTERVAL,
        "distractors_per_step": DISTRACTORS_PER_STEP,
        "by_budget": by_budget,
        "length32_summary": {
            str(budget): {
                "trajectory_survival_rate": length32[
                    budget
                ]["trajectory_survival_rate"],
                "endpoint_success_rate": length32[
                    budget
                ]["endpoint_success_rate"],
                "endpoint_masking_gap": length32[
                    budget
                ]["endpoint_masking_gap"],
                "recovered_trajectory_count": length32[
                    budget
                ]["recovered_trajectory_count"],
                "cold_start_independent_projection": (
                    length32[budget][
                        "cold_start_independent_projection"
                    ]
                ),
            }
            for budget in BUDGETS
        },
        "claim_ceiling": (
            "SYNTHETIC_TRAJECTORY_SURVIVAL_ONLY"
        ),
    }

    return result


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
