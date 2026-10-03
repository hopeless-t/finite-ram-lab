from __future__ import annotations

import itertools
import json
import math


SCHEMA = "finite-ram-lab.fr-northstar-001-qualified-survival-frontier/v0.1"

CONTRACT = {
    "max_p99_latency_ms": 85.0,
    "min_quality": 0.97,
    "min_reliability": 0.999,
    "max_extra_cpu_units": 35.0,
    "max_extra_io_mib": 400.0,
}

WORKLOADS = {
    "MULTIWORKER_LLM": {
        "base_ram_mib": 1000.0,
        "base_p99_latency_ms": 45.0,
        "quality": 1.0,
        "reliability": 0.9995,
        "atoms": {
            "Q": 0.30,
            "D": 0.38,
            "F": 0.05,
            "G": 0.05,
            "P": 0.07,
            "Z": 0.10,
        },
    },
    "LONG_CONTEXT": {
        "base_ram_mib": 1200.0,
        "base_p99_latency_ms": 55.0,
        "quality": 1.0,
        "reliability": 0.9995,
        "atoms": {
            "Q": 0.42,
            "D": 0.06,
            "F": 0.10,
            "G": 0.12,
            "P": 0.08,
            "Z": 0.12,
        },
    },
    "SERVING_FRAGMENTED": {
        "base_ram_mib": 900.0,
        "base_p99_latency_ms": 50.0,
        "quality": 1.0,
        "reliability": 0.9994,
        "atoms": {
            "Q": 0.15,
            "D": 0.18,
            "F": 0.28,
            "G": 0.08,
            "P": 0.06,
            "Z": 0.10,
        },
    },
    "OUT_OF_CORE": {
        "base_ram_mib": 1100.0,
        "base_p99_latency_ms": 60.0,
        "quality": 1.0,
        "reliability": 0.9994,
        "atoms": {
            "Q": 0.18,
            "D": 0.05,
            "F": 0.06,
            "G": 0.12,
            "P": 0.34,
            "Z": 0.12,
        },
    },
    "COMPRESSIBLE_CACHE": {
        "base_ram_mib": 800.0,
        "base_p99_latency_ms": 40.0,
        "quality": 1.0,
        "reliability": 0.9996,
        "atoms": {
            "Q": 0.08,
            "D": 0.10,
            "F": 0.05,
            "G": 0.12,
            "P": 0.10,
            "Z": 0.45,
        },
    },
    "REBUILDABLE_PIPELINE": {
        "base_ram_mib": 1000.0,
        "base_p99_latency_ms": 42.0,
        "quality": 1.0,
        "reliability": 0.9995,
        "atoms": {
            "Q": 0.10,
            "D": 0.08,
            "F": 0.05,
            "G": 0.45,
            "P": 0.10,
            "Z": 0.12,
        },
    },
}

ACTIONS = {
    "QUANTIZE": {
        "atom": "Q",
        "retain_fraction": 0.45,
        "latency_ms": 5.0,
        "quality_delta": -0.015,
        "reliability_delta": -0.00005,
        "cpu_units": 8.0,
        "io_mib": 0.0,
    },
    "SHARE": {
        "atom": "D",
        "retain_fraction": 0.18,
        "latency_ms": 1.0,
        "quality_delta": 0.0,
        "reliability_delta": 0.0,
        "cpu_units": 1.0,
        "io_mib": 0.0,
    },
    "PAGING": {
        "atom": "F",
        "retain_fraction": 0.15,
        "latency_ms": 2.0,
        "quality_delta": 0.0,
        "reliability_delta": -0.00002,
        "cpu_units": 2.0,
        "io_mib": 0.0,
    },
    "REMATERIALIZE": {
        "atom": "G",
        "retain_fraction": 0.25,
        "latency_ms": 12.0,
        "quality_delta": 0.0,
        "reliability_delta": -0.00015,
        "cpu_units": 18.0,
        "io_mib": 0.0,
    },
    "RECLAIM_PAGECACHE": {
        "atom": "P",
        "retain_fraction": 0.20,
        "latency_ms": 8.0,
        "quality_delta": 0.0,
        "reliability_delta": -0.00005,
        "cpu_units": 4.0,
        "io_mib": 220.0,
    },
    "COMPRESS": {
        "atom": "Z",
        "retain_fraction": 0.45,
        "latency_ms": 6.0,
        "quality_delta": 0.0,
        "reliability_delta": -0.00003,
        "cpu_units": 12.0,
        "io_mib": 0.0,
    },
}

BUDGETS_MIB = (
    350,
    400,
    450,
    500,
    550,
    600,
    650,
    700,
    750,
    800,
    850,
    900,
    950,
    1000,
    1100,
    1200,
)


def evaluate(
    workload: dict,
    actions: tuple[str, ...],
) -> dict:
    ram = float(
        workload[
            "base_ram_mib"
        ]
    )

    latency = float(
        workload[
            "base_p99_latency_ms"
        ]
    )

    quality = float(
        workload[
            "quality"
        ]
    )

    reliability = float(
        workload[
            "reliability"
        ]
    )

    cpu = 0.0
    io = 0.0

    for name in actions:
        action = ACTIONS[name]
        atom_fraction = (
            workload[
                "atoms"
            ][
                action[
                    "atom"
                ]
            ]
        )

        ram -= (
            workload[
                "base_ram_mib"
            ]
            * atom_fraction
            * (
                1.0
                - action[
                    "retain_fraction"
                ]
            )
        )

        latency += action[
            "latency_ms"
        ]

        quality += action[
            "quality_delta"
        ]

        reliability += action[
            "reliability_delta"
        ]

        cpu += action[
            "cpu_units"
        ]

        io += action[
            "io_mib"
        ]

    qualified = (
        latency
        <= CONTRACT[
            "max_p99_latency_ms"
        ]
        and quality
        >= CONTRACT[
            "min_quality"
        ]
        and reliability
        >= CONTRACT[
            "min_reliability"
        ]
        and cpu
        <= CONTRACT[
            "max_extra_cpu_units"
        ]
        and io
        <= CONTRACT[
            "max_extra_io_mib"
        ]
    )

    return {
        "resident_ram_mib": ram,
        "p99_latency_ms": latency,
        "quality": quality,
        "reliability": reliability,
        "extra_cpu_units": cpu,
        "extra_io_mib": io,
        "qualified": qualified,
    }


def best_for_mode(
    workload: dict,
    *,
    mode: str,
) -> dict:
    names = tuple(
        ACTIONS
    )

    best = {
        "actions": [],
        **evaluate(
            workload,
            (),
        ),
    }

    for width in range(
        len(names) + 1
    ):
        for combo in itertools.combinations(
            names,
            width,
        ):
            if (
                mode == "BASELINE"
                and combo
            ):
                continue

            if (
                mode == "SINGLE_ATOM"
                and len(combo)
                > 1
            ):
                continue

            result = evaluate(
                workload,
                combo,
            )

            if not result[
                "qualified"
            ]:
                continue

            if (
                result[
                    "resident_ram_mib"
                ]
                < best[
                    "resident_ram_mib"
                ]
            ):
                best = {
                    "actions": list(
                        combo
                    ),
                    **result,
                }

    return best


def geometric_mean(
    values: list[float],
) -> float:
    return math.exp(
        sum(
            math.log(
                value
            )
            for value in values
        )
        / len(values)
    )


def run_panel() -> dict:
    policies = {}

    for mode in (
        "BASELINE",
        "SINGLE_ATOM",
        "JOINT",
    ):
        policies[
            mode
        ] = {
            name: best_for_mode(
                workload,
                mode=mode,
            )
            for name, workload
            in WORKLOADS.items()
        }

    curves = {}

    for mode, rows in (
        policies.items()
    ):
        curves[
            mode
        ] = {
            str(budget): sum(
                (
                    row[
                        "qualified"
                    ]
                    and row[
                        "resident_ram_mib"
                    ]
                    <= budget
                )
                for row
                in rows.values()
            )
            for budget
            in BUDGETS_MIB
        }

    single_gain = geometric_mean(
        [
            policies[
                "BASELINE"
            ][name][
                "resident_ram_mib"
            ]
            / policies[
                "SINGLE_ATOM"
            ][name][
                "resident_ram_mib"
            ]
            for name
            in WORKLOADS
        ]
    )

    joint_gain = geometric_mean(
        [
            policies[
                "BASELINE"
            ][name][
                "resident_ram_mib"
            ]
            / policies[
                "JOINT"
            ][name][
                "resident_ram_mib"
            ]
            for name
            in WORKLOADS
        ]
    )

    frozen = {
        "single_gain": (
            1.377449471796244
        ),
        "joint_gain": (
            2.2625893036493747
        ),
        "qualified_at_600": {
            "BASELINE": 0,
            "SINGLE_ATOM": 0,
            "JOINT": 6,
        },
        "joint_min_ram": {
            "MULTIWORKER_LLM": 369.9,
            "LONG_CONTEXT": 576.96,
            "SERVING_FRAGMENTED": 381.50999999999993,
            "OUT_OF_CORE": 518.1,
            "COMPRESSIBLE_CACHE": 400.4,
            "REBUILDABLE_PIPELINE": 419.4,
        },
        "single_winners": {
            "MULTIWORKER_LLM": [
                "SHARE"
            ],
            "LONG_CONTEXT": [
                "QUANTIZE"
            ],
            "SERVING_FRAGMENTED": [
                "PAGING"
            ],
            "OUT_OF_CORE": [
                "RECLAIM_PAGECACHE"
            ],
            "COMPRESSIBLE_CACHE": [
                "COMPRESS"
            ],
            "REBUILDABLE_PIPELINE": [
                "REMATERIALIZE"
            ],
        },
    }

    actual_single_winners = {
        name: policies[
            "SINGLE_ATOM"
        ][name][
            "actions"
        ]
        for name
        in WORKLOADS
    }

    actual_joint_min = {
        name: policies[
            "JOINT"
        ][name][
            "resident_ram_mib"
        ]
        for name
        in WORKLOADS
    }

    if abs(
        single_gain
        - frozen[
            "single_gain"
        ]
    ) > 1e-12:
        raise RuntimeError(
            "single_gain_changed"
        )

    if abs(
        joint_gain
        - frozen[
            "joint_gain"
        ]
    ) > 1e-12:
        raise RuntimeError(
            "joint_gain_changed"
        )

    if {
        mode: curves[
            mode
        ]["600"]
        for mode in curves
    } != frozen[
        "qualified_at_600"
    ]:
        raise RuntimeError(
            "budget_curve_changed"
        )

    if (
        actual_single_winners
        != frozen[
            "single_winners"
        ]
    ):
        raise RuntimeError(
            "single_winner_map_changed:"
            f"{actual_single_winners}"
        )

    if (
        actual_joint_min
        != frozen[
            "joint_min_ram"
        ]
    ):
        raise RuntimeError(
            "joint_min_ram_changed:"
            f"{actual_joint_min}"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_QUALIFIED_TASK_SURVIVAL_FRONTIER_VALIDATED"
        ),
        "north_star": {
            "name": (
                "QUALIFIED_TASK_SURVIVAL_FRONTIER"
            ),
            "definition": (
                "Minimize resident RAM required to complete a task while semantic/quality, p99 latency, reliability, CPU, IO, and network-style resource contracts remain satisfied."
            ),
            "anti_cheat_rule": (
                "RAM savings do not qualify if they violate another frozen task/resource contract."
            ),
        },
        "contract": CONTRACT,
        "workloads": WORKLOADS,
        "actions": ACTIONS,
        "policies": policies,
        "budget_curve": curves,
        "summary": {
            "single_atom_geomean_memory_gain": (
                single_gain
            ),
            "joint_geomean_memory_gain": (
                joint_gain
            ),
            "qualified_workloads_at_600_mib": {
                mode: curves[
                    mode
                ]["600"]
                for mode
                in curves
            },
        },
        "strategy": {
            "stop_condition_for_atom_first_research": (
                "A new atom is not prioritized merely because it exists; it must improve the qualified survival frontier or close a measured failure-domain gap."
            ),
            "next_system": (
                "North-Star compiler: observe failure domain -> enumerate allowed primitives -> search qualified combinations -> shadow replay -> host-bound promotion."
            ),
        },
        "primary_findings": [
            "NO_SINGLE_MEMORY_PRIMITIVE_DOMINATES_ALL_FAILURE_DOMAINS",
            "THE_NORTH_STAR_IS_A_QUALIFIED_FRONTIER_NOT_RAW_RAM_REDUCTION",
            "JOINT_COMPOSITION_CAN_DOMINATE_SINGLE_AXIS_OPTIMIZATION",
            "RESOURCE_SHIFTING_IS_NOT_A_WIN_UNLESS_ALL_TASK_CONTRACTS_STILL_PASS",
            "FUTURE_RESEARCH_SHOULD_BE_PRIORITY_DRIVEN_BY_FRONTIER_GAIN",
            "EXISTING_ATOMS_BECOME_COMPILER_PRIMITIVES_NOT_SEPARATE_END_GOALS",
        ],
        "boundaries": {
            "fixture": (
                "All workload fractions and action costs are synthetic controls."
            ),
            "physical_claim": False,
            "ranking_claim": (
                "No real method or implementation is ranked by this synthetic panel."
            ),
        },
        "claim_ceiling": (
            "SYNTHETIC_NORTH_STAR_CONTRACT_AND_JOINT_POLICY_TOPOLOGY_ONLY"
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
