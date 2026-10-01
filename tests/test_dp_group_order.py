from __future__ import annotations

import random
import unittest

from finite_ram_lab.bounded_frontier_controller import StateOption
from finite_ram_lab.dp_group_order import (
    evaluate_order,
    search_orders,
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


class DPGroupOrderTests(unittest.TestCase):
    def test_b436_plus_b447_optimal_order_preserves_frontier_and_costs_no_more(self):
        groups = mixed_option_groups() + (
            cadence_state_options(memory_high_mib=144),
        )
        result = search_orders(
            groups,
            {"RAM": 50000, "VRAM": 50000},
        )
        self.assertEqual(
            result.original.final_frontier_vectors,
            result.optimal.final_frontier_vectors,
        )
        self.assertLessEqual(
            result.optimal.total_expanded_states,
            result.original.total_expanded_states,
        )
        self.assertLessEqual(
            result.greedy.total_expanded_states,
            result.original.total_expanded_states,
        )

    def test_100_random_four_group_systems_keep_frontier_under_reordering(self):
        rng = random.Random(459)
        capacities = {"RAM": 50, "VRAM": 50}

        for case in range(100):
            groups = []
            for group_index in range(4):
                state = f"s{case}_{group_index}"
                group = tuple(
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
                groups.append(group)

            result = search_orders(tuple(groups), capacities)
            self.assertEqual(
                result.original.final_frontier_vectors,
                result.greedy.final_frontier_vectors,
            )
            self.assertEqual(
                result.original.final_frontier_vectors,
                result.optimal.final_frontier_vectors,
            )
            self.assertLessEqual(
                result.optimal.total_expanded_states,
                result.greedy.total_expanded_states,
            )

    def test_explicit_order_evaluation_is_permutation_invariant_in_result(self):
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
        left = evaluate_order(groups, capacities, (0, 1, 2))
        right = evaluate_order(groups, capacities, (2, 1, 0))
        self.assertEqual(
            left.final_frontier_vectors,
            right.final_frontier_vectors,
        )


if __name__ == "__main__":
    unittest.main()
