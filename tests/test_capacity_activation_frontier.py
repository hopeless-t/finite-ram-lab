from __future__ import annotations

import unittest

from finite_ram_lab.capacity_activation_frontier import (
    CapacityRequirement,
    activation_antichain,
    capacity_covers,
    option_activation_frontier,
    requirement_dominates,
    scenario_activation_frontier,
    scenario_is_activated,
)
from finite_ram_lab.mixed_capacity_cliff import mixed_option_groups


class CapacityActivationFrontierTests(unittest.TestCase):
    def test_requirement_dominance(self):
        tiers = ("RAM", "VRAM")
        a = CapacityRequirement((("RAM", 8), ("VRAM", 10)))
        b = CapacityRequirement((("RAM", 9), ("VRAM", 10)))
        c = CapacityRequirement((("RAM", 7), ("VRAM", 11)))
        self.assertTrue(requirement_dominates(a, b, tiers))
        self.assertFalse(requirement_dominates(a, c, tiers))

    def test_b436_scenario_has_two_minimal_activation_points(self):
        frontier = scenario_activation_frontier(
            mixed_option_groups(),
            ("RAM", "VRAM"),
        )
        self.assertEqual(
            [p.requirement.vector(("RAM", "VRAM")) for p in frontier],
            [(8192, 10544), (9776, 9356)],
        )

    def test_full_and_streamed_kv_have_distinct_activation_points(self):
        groups = mixed_option_groups()
        full = option_activation_frontier(
            groups,
            state_name="strata_kv",
            option_name="full_int8_vram",
            tiers=("RAM", "VRAM"),
        )
        streamed = option_activation_frontier(
            groups,
            state_name="strata_kv",
            option_name="stream_int8",
            tiers=("RAM", "VRAM"),
        )
        self.assertEqual(
            [p.requirement.vector(("RAM", "VRAM")) for p in full],
            [(8192, 10544)],
        )
        self.assertEqual(
            [p.requirement.vector(("RAM", "VRAM")) for p in streamed],
            [(9776, 9356)],
        )

    def test_materialize_activation_frontier_has_two_tradeoff_points(self):
        frontier = option_activation_frontier(
            mixed_option_groups(),
            state_name="semantic_reduction",
            option_name="materialize",
            tiers=("RAM", "VRAM"),
        )
        self.assertEqual(
            [p.requirement.vector(("RAM", "VRAM")) for p in frontier],
            [(8192, 11312), (9776, 10124)],
        )

    def test_dedicated_prompt_scratch_activation_frontier(self):
        frontier = option_activation_frontier(
            mixed_option_groups(),
            state_name="strata_prefill",
            option_name="dedicated_prompt_scratch",
            tiers=("RAM", "VRAM"),
        )
        self.assertEqual(
            [p.requirement.vector(("RAM", "VRAM")) for p in frontier],
            [(8192, 15275), (9776, 14087)],
        )

    def test_expert_20g_gpu_activation_frontier(self):
        frontier = option_activation_frontier(
            mixed_option_groups(),
            state_name="strata_experts",
            option_name="gpu20_ram14",
            tiers=("RAM", "VRAM"),
        )
        self.assertEqual(
            [p.requirement.vector(("RAM", "VRAM")) for p in frontier],
            [(14336, 22832), (15920, 21644)],
        )

    def test_capacity_cover_matches_two_step_staircase(self):
        frontier = scenario_activation_frontier(
            mixed_option_groups(),
            ("RAM", "VRAM"),
        )
        self.assertFalse(
            scenario_is_activated(
                frontier,
                {"RAM": 8192, "VRAM": 10543},
            )
        )
        self.assertTrue(
            scenario_is_activated(
                frontier,
                {"RAM": 8192, "VRAM": 10544},
            )
        )
        self.assertFalse(
            scenario_is_activated(
                frontier,
                {"RAM": 9776, "VRAM": 9355},
            )
        )
        self.assertTrue(
            scenario_is_activated(
                frontier,
                {"RAM": 9776, "VRAM": 9356},
            )
        )

    def test_10000_random_capacity_checks_match_direct_frontier_cover(self):
        import random

        rng = random.Random(437)
        frontier = scenario_activation_frontier(
            mixed_option_groups(),
            ("RAM", "VRAM"),
        )

        for _ in range(10_000):
            capacity = {
                "RAM": rng.randint(0, 40_000),
                "VRAM": rng.randint(0, 40_000),
            }
            expected = (
                (
                    capacity["RAM"] >= 8192
                    and capacity["VRAM"] >= 10544
                )
                or (
                    capacity["RAM"] >= 9776
                    and capacity["VRAM"] >= 9356
                )
            )
            self.assertEqual(
                scenario_is_activated(frontier, capacity),
                expected,
            )


if __name__ == "__main__":
    unittest.main()
