from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math


SCHEMA = "finite-ram-lab.semantic-temporal-error-shape/v0.1"
SEED = 20261002
MARGINAL_FLIP_RATE = 0.01
REPLICATES = 8192
BUDGET = 4
LENGTH = 64
REFRESH_INTERVAL = 8
DISTRACTORS_PER_STEP = 2
QUERY_KEYS = ("goal", "constraint")
ARMS = ("IID_EVENT", "STEP_SHARED", "MARKOV_BURST")
MARKOV_BAD_PERSISTENCE = 0.75
MARKOV_GOOD_TO_BAD = (
    MARGINAL_FLIP_RATE
    * (1.0 - MARKOV_BAD_PERSISTENCE)
    / (1.0 - MARGINAL_FLIP_RATE)
)


@dataclass(frozen=True)
class Event:
    serial: int
    key: str
    value: str


def _uniform01(*parts: object) -> float:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def _latest_by_key(events: list[Event]) -> dict[str, Event]:
    out: dict[str, Event] = {}
    for event in events:
        out[event.key] = event
    return out


def _markov_bad_states(
    *,
    replicate: int,
    length: int = LENGTH,
    seed: int = SEED,
) -> list[bool]:
    bad = (
        _uniform01(seed, "MARKOV_INIT", replicate)
        < MARGINAL_FLIP_RATE
    )
    states: list[bool] = []

    for step in range(1, length + 1):
        states.append(bad)
        draw = _uniform01(
            seed,
            "MARKOV_TRANSITION",
            replicate,
            step,
        )
        if bad:
            bad = draw < MARKOV_BAD_PERSISTENCE
        else:
            bad = draw < MARKOV_GOOD_TO_BAD

    return states


def _event_flip(
    *,
    arm: str,
    replicate: int,
    step: int,
    event_serial: int,
    markov_bad: bool | None,
    seed: int = SEED,
) -> bool:
    if arm == "IID_EVENT":
        return (
            _uniform01(
                seed,
                "IID_EVENT",
                replicate,
                step,
                event_serial,
            )
            < MARGINAL_FLIP_RATE
        )

    if arm == "STEP_SHARED":
        return (
            _uniform01(
                seed,
                "STEP_SHARED",
                replicate,
                step,
            )
            < MARGINAL_FLIP_RATE
        )

    if arm == "MARKOV_BURST":
        if markov_bad is None:
            raise RuntimeError("markov_state_missing")
        return markov_bad

    raise ValueError(f"unknown_arm:{arm}")


def _max_failure_run(exact_flags: list[bool]) -> int:
    maximum = 0
    current = 0
    for exact in exact_flags:
        if exact:
            current = 0
        else:
            current += 1
            maximum = max(maximum, current)
    return maximum


def simulate_trajectory(
    *,
    arm: str,
    replicate: int,
    seed: int = SEED,
) -> dict:
    if arm not in ARMS:
        raise ValueError(f"unknown_arm:{arm}")

    serial = 0
    truth = {
        "goal": "g0",
        "constraint": "c0",
    }
    resident: list[Event] = []

    for key in QUERY_KEYS:
        resident.append(
            Event(
                serial=serial,
                key=key,
                value=truth[key],
            )
        )
        serial += 1

    markov_states = (
        _markov_bad_states(
            replicate=replicate,
            seed=seed,
        )
        if arm == "MARKOV_BURST"
        else None
    )

    exact_flags: list[bool] = []
    first_failure_step: int | None = None
    label_flips = 0
    label_decisions = 0
    bad_steps = 0

    for step in range(1, LENGTH + 1):
        incoming: list[Event] = []

        if step % REFRESH_INTERVAL == 0:
            epoch = step // REFRESH_INTERVAL
            truth["goal"] = f"g{epoch}"
            truth["constraint"] = f"c{epoch}"
            for key in QUERY_KEYS:
                incoming.append(
                    Event(
                        serial=serial,
                        key=key,
                        value=truth[key],
                    )
                )
                serial += 1

        for distractor in range(DISTRACTORS_PER_STEP):
            incoming.append(
                Event(
                    serial=serial,
                    key=f"d{step}_{distractor}",
                    value=str(step),
                )
            )
            serial += 1

        candidates = resident + incoming
        latest = _latest_by_key(candidates)
        required_serials = {
            latest[key].serial
            for key in QUERY_KEYS
            if key in latest
        }

        markov_bad = (
            markov_states[step - 1]
            if markov_states is not None
            else None
        )
        if (
            arm == "MARKOV_BURST"
            and markov_bad
        ):
            bad_steps += 1
        elif arm == "STEP_SHARED":
            if _event_flip(
                arm=arm,
                replicate=replicate,
                step=step,
                event_serial=-1,
                markov_bad=None,
                seed=seed,
            ):
                bad_steps += 1

        ranked: list[tuple[int, int, Event]] = []

        if arm == "STEP_SHARED":
            shared_flip = (
                _uniform01(
                    seed,
                    "STEP_SHARED",
                    replicate,
                    step,
                )
                < MARGINAL_FLIP_RATE
            )
        else:
            shared_flip = None

        for event in candidates:
            true_relevant = event.serial in required_serials

            if arm == "STEP_SHARED":
                flip = bool(shared_flip)
            else:
                flip = _event_flip(
                    arm=arm,
                    replicate=replicate,
                    step=step,
                    event_serial=event.serial,
                    markov_bad=markov_bad,
                    seed=seed,
                )

            label_decisions += 1
            label_flips += int(flip)

            predicted_relevant = (
                not true_relevant
                if flip
                else true_relevant
            )

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
        resident = [
            event
            for _, _, event in ranked[:BUDGET]
        ]
        resident.sort(key=lambda event: event.serial)

        resident_latest = _latest_by_key(resident)
        exact = all(
            (
                key in resident_latest
                and resident_latest[key].value == truth[key]
            )
            for key in QUERY_KEYS
        )
        exact_flags.append(exact)

        if not exact and first_failure_step is None:
            first_failure_step = step

    failed_steps = sum(not exact for exact in exact_flags)

    return {
        "arm": arm,
        "exact_flags": exact_flags,
        "trajectory_survived": all(exact_flags),
        "endpoint_exact": exact_flags[-1],
        "first_failure_step": first_failure_step,
        "failed_steps": failed_steps,
        "max_failure_run": _max_failure_run(exact_flags),
        "label_flips": label_flips,
        "label_decisions": label_decisions,
        "bad_steps": bad_steps,
    }


def _nearest_rank_p95(values: list[int]) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = math.ceil(0.95 * len(ordered)) - 1
    return ordered[index]


def evaluate_arm(arm: str) -> dict:
    rows = [
        simulate_trajectory(
            arm=arm,
            replicate=replicate,
        )
        for replicate in range(REPLICATES)
    ]

    survived = sum(
        row["trajectory_survived"]
        for row in rows
    )
    endpoint = sum(
        row["endpoint_exact"]
        for row in rows
    )
    exact_steps = sum(
        sum(row["exact_flags"])
        for row in rows
    )
    label_flips = sum(
        row["label_flips"]
        for row in rows
    )
    label_decisions = sum(
        row["label_decisions"]
        for row in rows
    )
    bad_steps = sum(
        row["bad_steps"]
        for row in rows
    )

    affected = [
        row for row in rows
        if not row["trajectory_survived"]
    ]
    max_runs = [
        row["max_failure_run"]
        for row in affected
    ]
    failed_steps = [
        row["failed_steps"]
        for row in affected
    ]
    first_failure_histogram: Counter[str] = Counter(
        str(row["first_failure_step"])
        for row in affected
    )

    return {
        "arm": arm,
        "replicates": REPLICATES,
        "length": LENGTH,
        "budget": BUDGET,
        "expected_marginal_flip_rate": MARGINAL_FLIP_RATE,
        "observed_label_flip_rate": (
            label_flips / label_decisions
        ),
        "observed_bad_step_rate": (
            bad_steps / (REPLICATES * LENGTH)
            if arm != "IID_EVENT"
            else None
        ),
        "trajectory_survival_rate": (
            survived / REPLICATES
        ),
        "affected_trajectory_rate": (
            1.0 - survived / REPLICATES
        ),
        "endpoint_success_rate": (
            endpoint / REPLICATES
        ),
        "mean_step_exact_rate": (
            exact_steps / (REPLICATES * LENGTH)
        ),
        "conditional_mean_max_failure_run": (
            sum(max_runs) / len(max_runs)
            if max_runs
            else 0.0
        ),
        "conditional_p95_max_failure_run": (
            _nearest_rank_p95(max_runs)
        ),
        "conditional_mean_failed_steps": (
            sum(failed_steps) / len(failed_steps)
            if failed_steps
            else 0.0
        ),
        "first_failure_histogram": dict(
            sorted(
                first_failure_histogram.items(),
                key=lambda item: int(item[0]),
            )
        ),
    }


def run_panel() -> dict:
    arms = [
        evaluate_arm(arm)
        for arm in ARMS
    ]
    by_name = {
        row["arm"]: row
        for row in arms
    }

    for row in arms:
        if not (
            0.009
            <= row["observed_label_flip_rate"]
            <= 0.011
        ):
            raise RuntimeError(
                "marginal_flip_rate_not_matched"
            )
        if row["endpoint_success_rate"] < 0.98:
            raise RuntimeError(
                "endpoint_success_too_low_for_fixture"
            )

    survival = [
        by_name[arm]["trajectory_survival_rate"]
        for arm in ARMS
    ]
    if not (
        survival[0] < survival[1] < survival[2]
    ):
        raise RuntimeError(
            "temporal_dependence_survival_order_unexpected"
        )

    if (
        by_name["IID_EVENT"]["affected_trajectory_rate"]
        <= 0.60
    ):
        raise RuntimeError("iid_affected_rate_too_low")
    if not (
        0.40
        < by_name["STEP_SHARED"][
            "affected_trajectory_rate"
        ]
        < 0.60
    ):
        raise RuntimeError(
            "step_shared_affected_rate_unexpected"
        )
    if (
        by_name["MARKOV_BURST"][
            "affected_trajectory_rate"
        ]
        >= 0.25
    ):
        raise RuntimeError(
            "markov_affected_rate_too_high"
        )

    if (
        by_name["MARKOV_BURST"][
            "conditional_p95_max_failure_run"
        ]
        < 12
    ):
        raise RuntimeError(
            "markov_failure_tail_not_exposed"
        )
    if (
        by_name["MARKOV_BURST"][
            "conditional_mean_max_failure_run"
        ]
        <= by_name["IID_EVENT"][
            "conditional_mean_max_failure_run"
        ]
    ):
        raise RuntimeError(
            "markov_failure_severity_not_higher"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "MATCHED_MARGINAL_TEMPORAL_ERROR_SHAPE_VALIDATED"
        ),
        "synthetic_only": True,
        "empirical_model_claim": False,
        "seed": SEED,
        "marginal_flip_rate": MARGINAL_FLIP_RATE,
        "replicates": REPLICATES,
        "budget": BUDGET,
        "length": LENGTH,
        "refresh_interval": REFRESH_INTERVAL,
        "markov_bad_persistence": MARKOV_BAD_PERSISTENCE,
        "markov_good_to_bad": MARKOV_GOOD_TO_BAD,
        "arms": arms,
        "claim_ceiling": (
            "SYNTHETIC_TEMPORAL_ERROR_SHAPE_ONLY"
        ),
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
