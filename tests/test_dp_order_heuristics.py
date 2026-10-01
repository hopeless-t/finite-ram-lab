from __future__ import annotations

import random
import unittest

from finite_ram_lab.bounded_frontier_controller import StateOption
from finite_ram_lab.dp_order_heuristics import (
    compare_heuristics,
    frontier_size_greedy_order,
    rollout_order,
)
from finite_ram_lab.mixed_capacity_cliff import mixed_option_groups
from finite_ram_lab.stateoption_quotient import cadence_state_options


def option(state: str, name: str, values: tuple[int, ...]) -> StateOption:
    ram, vram, traffic, compute, latency = values
    return StateOption(
        state_name=state,
        option_name=name,
        resident_by_tier=(("RAM", ram), ("VRAM", vram)),
        byte_seconds_by_tier=(("RAM", float(ram)), ("VRAM", float(vram))),
        traffic_bytes=float(traffic),
        compute_cost=float(compute),
        latency_cost=float(latency),
        error_cost=0.0,
    )


class DPOrderHeuristicTests(unittest.TestCase):
    def test_fixed_mixed_heuristics_preserve_frontier(self):
        groups = mixed_option_groups() + (
            cadence_state_options(memory_high_mib=144),
        )
        result = compare_heuristics(
            groups,
            {"RAM": 50000, "VRAM": 50000},
        )
        vectors = result.original.final_frontier_vectors
        self.assertEqual(result.rollout.final_frontier_vectors, vectors)
        self.assertEqual(result.frontier_greedy.final_frontier_vectors, vectors)
        self.assertLessEqual(
            result.optimal.total_expanded_states,
            result.rollout.total_expanded_states,
        )

    def test_orders_are_valid_permutations(self):
        groups = (
            (
                option("a", "a0", (1, 4, 3, 1, 2)),
                option("a", "a1", (4, 1, 1, 3, 2)),
            ),
            (
                option("b", "b0", (2, 2, 2, 2, 1)),
                option("b", "b1", (3, 3, 1, 1, 3)),
            ),
            (
                option("c", "c0", (1, 5, 2, 1, 4)),
                option("c", "c1", (5, 1, 1, 2, 1)),
            ),
        )
        capacities = {"RAM": 20, "VRAM": 20}
        self.assertEqual(
            sorted(frontier_size_greedy_order(groups, capacities)),
            [0, 1, 2],
        )
        self.assertEqual(
            sorted(rollout_order(groups, capacities)),
            [0, 1, 2],
        )

    def test_20_random_five_group_systems_preserve_frontier(self):
        rng = random.Random(460)
        capacities = {"RAM": 60, "VRAM": 60}

        for case in range(20):
            groups = []
            for group_index in range(5):
                state = f"s{case}_{group_index}"
                groups.append(
                    tuple(
                        option(
                            state,
                            f"o{option_index}",
                            (
                                rng.randint(0, 20),
                                rng.randint(0, 20),
                                rng.randint(0, 10),
                                rng.randint(0, 10),
                                rng.randint(0, 10),
                            ),
                        )
                        for option_index in range(rng.randint(2, 4))
                    )
                )

            result = compare_heuristics(tuple(groups), capacities)
            self.assertEqual(
                result.original.final_frontier_vectors,
                result.rollout.final_frontier_vectors,
            )
            self.assertLessEqual(
                result.optimal.total_expanded_states,
                result.rollout.total_expanded_states,
            )


if __name__ == "__main__":
    unittest.main()
