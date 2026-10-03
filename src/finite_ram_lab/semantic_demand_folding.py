from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable


SCHEMA = "finite-ram-lab.demand-folding-governor/v0.1"
MAX_CONCURRENCY = 8
MIN_CONCURRENCY = 1


@dataclass(frozen=True)
class ControllerConfig:
    high_threshold: float
    low_threshold: float
    step: int = 1
    min_concurrency: int = MIN_CONCURRENCY
    max_concurrency: int = MAX_CONCURRENCY


@dataclass(frozen=True)
class Sample:
    t: int
    exogenous_pressure: float
    concurrency: int
    pressure: float
    useful_progress: float


def pressure_signal(concurrency: int, exogenous_pressure: float) -> float:
    """Synthetic pressure proxy with a concurrency-amplified component."""
    nonlinear = 0.008 * max(0, concurrency - 5) ** 2
    value = (
        exogenous_pressure * (0.25 + 0.09 * concurrency)
        + 0.01 * concurrency
        + nonlinear
    )
    return min(0.95, max(0.0, value))


def useful_progress(concurrency: int, exogenous_pressure: float) -> float:
    """Synthetic useful work, not CPU utilization or pressure relief."""
    pressure = pressure_signal(concurrency, exogenous_pressure)
    coordination_tax = (
        1.0
        + 0.22
        * exogenous_pressure
        * max(0, concurrency - 4) ** 2
    )
    return (
        concurrency
        * (1.0 - pressure) ** 1.1
        / coordination_tax
    )


def workload_trace() -> list[float]:
    return (
        [0.03] * 15
        + [0.10] * 10
        + [0.20] * 10
        + [0.35] * 10
        + [0.50] * 10
        + [0.65] * 12
        + [0.50] * 8
        + [0.35] * 8
        + [0.20] * 8
        + [0.10] * 10
        + [0.03] * 12
    )


def next_concurrency_hysteresis(
    current: int,
    pressure: float,
    config: ControllerConfig,
) -> int:
    if pressure > config.high_threshold:
        return max(config.min_concurrency, current - config.step)
    if pressure <= config.low_threshold:
        return min(config.max_concurrency, current + config.step)
    return current


def next_concurrency_single_threshold(
    current: int,
    pressure: float,
    *,
    threshold: float,
    step: int = 1,
) -> int:
    if pressure > threshold:
        return max(MIN_CONCURRENCY, current - step)
    return min(MAX_CONCURRENCY, current + step)


def run_policy(
    exogenous_trace: Iterable[float],
    *,
    mode: str,
    initial_concurrency: int = MAX_CONCURRENCY,
    hysteresis: ControllerConfig | None = None,
    single_threshold: float = 0.35,
) -> list[Sample]:
    if hysteresis is None:
        hysteresis = ControllerConfig(
            high_threshold=0.50,
            low_threshold=0.20,
        )

    concurrency = initial_concurrency
    samples: list[Sample] = []

    for t, exogenous in enumerate(exogenous_trace):
        pressure = pressure_signal(concurrency, exogenous)
        progress = useful_progress(concurrency, exogenous)
        samples.append(
            Sample(
                t=t,
                exogenous_pressure=exogenous,
                concurrency=concurrency,
                pressure=pressure,
                useful_progress=progress,
            )
        )

        if mode == "FULL":
            continue
        if mode == "HYSTERESIS":
            concurrency = next_concurrency_hysteresis(
                concurrency,
                pressure,
                hysteresis,
            )
            continue
        if mode == "SINGLE_THRESHOLD":
            concurrency = next_concurrency_single_threshold(
                concurrency,
                pressure,
                threshold=single_threshold,
            )
            continue
        raise ValueError(f"unknown mode: {mode}")

    return samples


def summarize(samples: list[Sample]) -> dict:
    transitions = sum(
        abs(samples[i].concurrency - samples[i - 1].concurrency)
        for i in range(1, len(samples))
    )
    return {
        "total_useful_progress": sum(
            sample.useful_progress for sample in samples
        ),
        "max_pressure": max(sample.pressure for sample in samples),
        "pressure_gt_0_60_samples": sum(
            sample.pressure > 0.60 for sample in samples
        ),
        "control_transitions": transitions,
        "min_concurrency": min(
            sample.concurrency for sample in samples
        ),
        "max_concurrency": max(
            sample.concurrency for sample in samples
        ),
    }


def oracle_summary(exogenous_trace: Iterable[float]) -> dict:
    total = 0.0
    selected: list[int] = []
    for exogenous in exogenous_trace:
        candidates = [
            (
                useful_progress(concurrency, exogenous),
                concurrency,
            )
            for concurrency in range(
                MIN_CONCURRENCY,
                MAX_CONCURRENCY + 1,
            )
        ]
        best_progress, best_concurrency = max(candidates)
        total += best_progress
        selected.append(best_concurrency)
    return {
        "total_useful_progress": total,
        "selected_concurrency_set": sorted(set(selected)),
    }


def build_result() -> dict:
    trace = workload_trace()
    hysteresis = ControllerConfig(
        high_threshold=0.50,
        low_threshold=0.20,
    )

    full = summarize(run_policy(trace, mode="FULL"))
    hys = summarize(
        run_policy(
            trace,
            mode="HYSTERESIS",
            hysteresis=hysteresis,
        )
    )
    single = summarize(
        run_policy(
            trace,
            mode="SINGLE_THRESHOLD",
            single_threshold=0.35,
        )
    )
    oracle = oracle_summary(trace)

    relative_progress = (
        hys["total_useful_progress"]
        / full["total_useful_progress"]
    )
    oracle_capture = (
        hys["total_useful_progress"]
        / oracle["total_useful_progress"]
    )

    invariants = {
        "hysteresis_outprogresses_full": (
            hys["total_useful_progress"]
            > full["total_useful_progress"]
        ),
        "hysteresis_reduces_severe_pressure": (
            hys["pressure_gt_0_60_samples"]
            < full["pressure_gt_0_60_samples"]
        ),
        "hysteresis_reduces_chatter_vs_single_threshold": (
            hys["control_transitions"]
            < single["control_transitions"]
        ),
        "at_least_one_worker_always_retained": (
            hys["min_concurrency"] >= MIN_CONCURRENCY
        ),
        "never_exceeds_declared_max_concurrency": (
            hys["max_concurrency"] <= MAX_CONCURRENCY
        ),
    }

    status = "PASS" if all(invariants.values()) else "FAIL"

    return {
        "schema": SCHEMA,
        "status": status,
        "synthetic_only": True,
        "live_control_claim": False,
        "source_inspiration": "Linux steal_governor v14",
        "controller": {
            "high_threshold": hysteresis.high_threshold,
            "low_threshold": hysteresis.low_threshold,
            "step": hysteresis.step,
            "min_concurrency": hysteresis.min_concurrency,
            "max_concurrency": hysteresis.max_concurrency,
        },
        "arms": {
            "FULL": full,
            "HYSTERESIS": hys,
            "SINGLE_THRESHOLD": single,
            "ORACLE": oracle,
        },
        "derived": {
            "hysteresis_progress_ratio_vs_full": relative_progress,
            "hysteresis_oracle_capture_ratio": oracle_capture,
        },
        "invariants": invariants,
        "primary_finding": (
            "DEMAND_FOLDING_CAN_REDUCE_PRESSURE_AMPLIFICATION_"
            "WITHOUT_SEMANTIC_DESTRUCTION_IN_THIS_SYNTHETIC_FIXTURE"
        ),
        "claim_ceiling": (
            "SOURCE_GROUNDED_STEAL_GOVERNOR_TRANSFER_PLUS_"
            "SYNTHETIC_DEMAND_FOLDING_SHADOW_ONLY"
        ),
    }


def main() -> None:
    print(
        json.dumps(
            build_result(),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
