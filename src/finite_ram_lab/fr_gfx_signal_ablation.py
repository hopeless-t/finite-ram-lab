from __future__ import annotations

import json

from finite_ram_lab.fr_gfx_observation_plane import (
    EPISODES,
    _sample,
    _target_action,
)


SCHEMA = "finite-ram-lab.fr-gfx-003-signal-ablation/v0.1"

SIGNAL_SETS = {
    "FRAME": {
        "cost": 1.0,
        "signals": (
            "frame_ms",
        ),
    },
    "FRAME_MEM": {
        "cost": 1.2,
        "signals": (
            "frame_ms",
            "mem_available",
            "memory_psi",
        ),
    },
    "FRAME_GPU": {
        "cost": 1.8,
        "signals": (
            "frame_ms",
            "gpu_busy",
        ),
    },
    "FRAME_CPU": {
        "cost": 1.2,
        "signals": (
            "frame_ms",
            "cpu_busy",
            "compiler_active",
        ),
    },
    "FRAME_GPU_MEM": {
        "cost": 2.0,
        "signals": (
            "frame_ms",
            "gpu_busy",
            "mem_available",
            "memory_psi",
        ),
    },
    "FULL": {
        "cost": 2.2,
        "signals": (
            "frame_ms",
            "gpu_busy",
            "mem_available",
            "memory_psi",
            "cpu_busy",
            "compiler_active",
        ),
    },
}


def _predict(
    row,
    signal_set: str,
) -> str:
    if row.frame_ms <= 33.3:
        return "OBSERVE"

    if signal_set == "FRAME":
        return "DOWNSCALE_RENDER"

    if signal_set == "FRAME_MEM":
        if (
            row.mem_available_mib
            < 800.0
            or row.psi_some_avg10
            > 5.0
        ):
            return "DROP_RESIDENCY"

        return "DOWNSCALE_RENDER"

    if signal_set == "FRAME_GPU":
        if row.gpu_busy > 88.0:
            return "DOWNSCALE_RENDER"

        return "OBSERVE"

    if signal_set == "FRAME_CPU":
        if (
            row.cpu_busy > 90.0
            or row.compiler_active
        ):
            return "CPU_DRIVER_OBSERVE"

        return "DOWNSCALE_RENDER"

    if signal_set == "FRAME_GPU_MEM":
        if (
            row.mem_available_mib
            < 800.0
            or row.psi_some_avg10
            > 5.0
        ):
            return "DROP_RESIDENCY"

        if row.gpu_busy > 88.0:
            return "DOWNSCALE_RENDER"

        return "OBSERVE"

    if signal_set == "FULL":
        if (
            row.mem_available_mib
            < 800.0
            or row.psi_some_avg10
            > 5.0
        ):
            return "DROP_RESIDENCY"

        if row.gpu_busy > 88.0:
            return "DOWNSCALE_RENDER"

        if (
            row.cpu_busy > 90.0
            or row.compiler_active
        ):
            return "CPU_DRIVER_OBSERVE"

        return "OBSERVE"

    raise ValueError(
        f"unknown_signal_set:{signal_set}"
    )


def _score(signal_set: str) -> dict:
    samples = [
        _sample(index)
        for index in range(
            EPISODES
        )
    ]

    correct = 0
    gpu_total = 0
    gpu_detected = 0
    non_gpu_total = 0
    non_gpu_downscale = 0

    for row in samples:
        prediction = _predict(
            row,
            signal_set,
        )

        if (
            prediction
            == _target_action(
                row.state
            )
        ):
            correct += 1

        if row.state == "GPU_BOUND":
            gpu_total += 1

            if (
                prediction
                == "DOWNSCALE_RENDER"
            ):
                gpu_detected += 1
        else:
            non_gpu_total += 1

            if (
                prediction
                == "DOWNSCALE_RENDER"
            ):
                non_gpu_downscale += 1

    return {
        "action_accuracy": (
            correct
            / len(samples)
        ),
        "gpu_bound_recall": (
            gpu_detected
            / gpu_total
        ),
        "gpu_downscale_false_positive_rate": (
            non_gpu_downscale
            / non_gpu_total
        ),
        "abstract_acquisition_cost": (
            SIGNAL_SETS[
                signal_set
            ]["cost"]
        ),
        "signals": list(
            SIGNAL_SETS[
                signal_set
            ]["signals"]
        ),
    }


def run_panel() -> dict:
    rows = {
        signal_set: _score(
            signal_set
        )
        for signal_set in (
            SIGNAL_SETS
        )
    }

    frozen = {
        "FRAME": (
            0.71197509765625,
            0.9284548422198041,
            0.32522820270695624,
        ),
        "FRAME_MEM": (
            0.88385009765625,
            0.9284548422198041,
            0.10363550519357885,
        ),
        "FRAME_GPU": (
            0.69696044921875,
            0.8615342763873776,
            0.023371104815864022,
        ),
        "FRAME_CPU": (
            0.7923583984375,
            0.9284548422198041,
            0.2215926975133774,
        ),
        "FRAME_GPU_MEM": (
            0.86883544921875,
            0.8615342763873776,
            0.0,
        ),
        "FULL": (
            0.94921875,
            0.8615342763873776,
            0.0,
        ),
    }

    for name, expected in (
        frozen.items()
    ):
        row = rows[
            name
        ]

        actual = (
            row[
                "action_accuracy"
            ],
            row[
                "gpu_bound_recall"
            ],
            row[
                "gpu_downscale_false_positive_rate"
            ],
        )

        if actual != expected:
            raise RuntimeError(
                (
                    "frozen_signal_ablation_"
                    f"changed:{name}:{actual}"
                )
            )

    safe_candidates = [
        (
            row[
                "abstract_acquisition_cost"
            ],
            name,
        )
        for name, row
        in rows.items()
        if (
            row[
                "action_accuracy"
            ] >= 0.85
            and row[
                "gpu_downscale_false_positive_rate"
            ] <= 0.01
        )
    ]

    safe_candidates.sort()

    minimum_safe = (
        safe_candidates[0][1]
    )

    high_accuracy_candidates = [
        (
            row[
                "abstract_acquisition_cost"
            ],
            name,
        )
        for name, row
        in rows.items()
        if (
            row[
                "action_accuracy"
            ] >= 0.90
            and row[
                "gpu_downscale_false_positive_rate"
            ] <= 0.01
        )
    ]

    high_accuracy_candidates.sort()

    minimum_high_accuracy = (
        high_accuracy_candidates[
            0
        ][1]
    )

    if (
        minimum_safe
        != "FRAME_GPU_MEM"
    ):
        raise RuntimeError(
            "minimum_safe_signal_set_changed"
        )

    if (
        minimum_high_accuracy
        != "FULL"
    ):
        raise RuntimeError(
            "minimum_high_accuracy_signal_set_changed"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_SIGNAL_ABLATION_VALIDATED"
        ),
        "episodes": EPISODES,
        "signal_sets": rows,
        "selection_rules": {
            "minimum_safe": {
                "accuracy_floor": 0.85,
                "gpu_false_positive_ceiling": 0.01,
                "selected": (
                    minimum_safe
                ),
            },
            "minimum_high_accuracy": {
                "accuracy_floor": 0.90,
                "gpu_false_positive_ceiling": 0.01,
                "selected": (
                    minimum_high_accuracy
                ),
            },
        },
        "cost_semantics": (
            "abstract acquisition units only; not measured CPU overhead"
        ),
        "primary_findings": [
            "MEMORY_SIGNALS_REMOVE_MANY_FALSE_GPU_TREATMENTS",
            "GPU_BUSY_IS_NEEDED_FOR_A_ZERO_FALSE_DOWNSCALE_GATE_IN_THE_FROZEN_FIXTURE",
            "CPU_DRIVER_SIGNALS_ARE_REQUIRED_TO_CROSS_THE_90_PERCENT_ACTION_ACCURACY_FLOOR",
            "THE_CHEAPEST_SAFE_SIGNAL_SET_NEED_NOT_BE_THE_MOST_ACCURATE_SET",
            "LIVE_INSTRUMENTATION_COST_MUST_BE_MEASURED_SEPARATELY",
        ],
        "claim_ceiling": (
            "SYNTHETIC_SIGNAL_ABLATION_ONLY"
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
