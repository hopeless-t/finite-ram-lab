from __future__ import annotations

import random
import unittest

from finite_ram_lab.static_dynamic_frontier import (
    changed_coordinates,
    compare_measured_capacity_pair,
    observed_frontier,
    synthetic_observation,
)


class StaticDynamicFrontierTests(unittest.TestCase):
    TIERS = ("RAM", "VRAM")

    def test_static_observations_preserve_frontier(self):
        observations = (
            synthetic_observation("a", ram=8, vram=4, latency=2),
            synthetic_observation("b", ram=10, vram=3, latency=1),
        )
        result = compare_measured_capacity_pair(
            observations,
            observations,
            self.TIERS,
        )
        self.assertFalse(result["monotonicity_violation"])
        self.assertEqual(result["lost_frontier_ids"], ())

    def test_self_cost_shift_explains_lost_plan(self):
        small = (
            synthetic_observation("p", ram=8, vram=4, latency=1),
            synthetic_observation("q", ram=8, vram=4, latency=2),
        )
        large = (
            synthetic_observation("p", ram=8, vram=4, latency=3),
            synthetic_observation("q", ram=8, vram=4, latency=2),
        )
        result = compare_measured_capacity_pair(
            small,
            large,
            self.TIERS,
        )
        self.assertTrue(result["monotonicity_violation"])
        self.assertEqual(result["lost_frontier_ids"], ("p",))
        explanation = result["explanations"][0]
        self.assertEqual(
            explanation["classification"],
            "LOST_WITH_SELF_COST_SHIFT",
        )
        self.assertIn(("latency", 2.0), explanation["changed_coordinates"])
        self.assertEqual(explanation["dominators"], ("q",))

    def test_dominator_cost_shift_explains_lost_plan(self):
        small = (
            synthetic_observation("p", ram=8, vram=4, latency=2),
            synthetic_observation("q", ram=8, vram=4, latency=3),
        )
        large = (
            synthetic_observation("p", ram=8, vram=4, latency=2),
            synthetic_observation("q", ram=8, vram=4, latency=1),
        )
        result = compare_measured_capacity_pair(
            small,
            large,
            self.TIERS,
        )
        explanation = result["explanations"][0]
        self.assertEqual(
            explanation["classification"],
            "LOST_WITH_DOMINATOR_COST_SHIFT",
        )
        self.assertIn(
            ("latency", -2.0),
            explanation["dominator_changes"]["q"],
        )

    def test_new_unobserved_dominator_is_distinguished(self):
        small = (
            synthetic_observation("p", ram=8, vram=4, latency=2),
        )
        large = (
            synthetic_observation("p", ram=8, vram=4, latency=2),
            synthetic_observation("q", ram=8, vram=4, latency=1),
        )
        result = compare_measured_capacity_pair(
            small,
            large,
            self.TIERS,
        )
        explanation = result["explanations"][0]
        self.assertEqual(
            explanation["classification"],
            "LOST_WITH_NEW_OR_PREVIOUSLY_UNOBSERVED_DOMINATOR",
        )

    def test_missing_larger_observation_is_not_invented(self):
        small = (
            synthetic_observation("p", ram=8, vram=4, latency=1),
            synthetic_observation("q", ram=9, vram=5, latency=2),
        )
        large = (
            synthetic_observation("q", ram=9, vram=5, latency=2),
        )
        result = compare_measured_capacity_pair(
            small,
            large,
            self.TIERS,
        )
        explanation = result["explanations"][0]
        self.assertEqual(
            explanation["classification"],
            "MISSING_LARGER_OBSERVATION",
        )

    def test_changed_coordinates_tolerance(self):
        before = synthetic_observation("p", ram=8, vram=4, latency=1.0)
        after = synthetic_observation("p", ram=8, vram=4, latency=1.0001)
        self.assertEqual(
            changed_coordinates(
                before,
                after,
                self.TIERS,
                tolerance=0.001,
            ),
            (),
        )

    def test_5000_random_static_replays_have_no_violation(self):
        rng = random.Random(439)
        for case in range(5000):
            observations = []
            for i in range(rng.randint(1, 8)):
                observations.append(
                    synthetic_observation(
                        f"p{case}_{i}",
                        ram=rng.randint(0, 30),
                        vram=rng.randint(0, 30),
                        ram_area=rng.randint(0, 100),
                        vram_area=rng.randint(0, 100),
                        traffic=rng.randint(0, 30),
                        compute=rng.randint(0, 30),
                        latency=rng.randint(0, 30),
                        error=rng.random(),
                    )
                )

            result = compare_measured_capacity_pair(
                observations,
                tuple(reversed(observations)),
                self.TIERS,
            )
            self.assertFalse(result["monotonicity_violation"])

    def test_observed_frontier_removes_dominated_plan(self):
        plans = (
            synthetic_observation("good", ram=1, vram=1, latency=1),
            synthetic_observation("bad", ram=2, vram=2, latency=2),
        )
        self.assertEqual(
            [p.plan_id for p in observed_frontier(plans, self.TIERS)],
            ["good"],
        )


if __name__ == "__main__":
    unittest.main()
