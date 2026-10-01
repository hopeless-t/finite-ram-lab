from __future__ import annotations

import random
import unittest

from finite_ram_lab.bounded_frontier_controller import (
    StateOption,
    dominates,
    exact_candidate_plans,
    exact_pareto_controller,
    option_is_safe,
)


def option(
    state,
    name,
    *,
    vram=0,
    ram=0,
    vram_area=0,
    ram_area=0,
    traffic=0,
    compute=0,
    latency=0,
    error=0,
    release=False,
    release_proven=False,
    merge=False,
    sharing_proven=False,
    error_bound_known=True,
):
    return StateOption(
        state_name=state,
        option_name=name,
        resident_by_tier=(("RAM", ram), ("VRAM", vram)),
        byte_seconds_by_tier=(("RAM", ram_area), ("VRAM", vram_area)),
        traffic_bytes=traffic,
        compute_cost=compute,
        latency_cost=latency,
        error_cost=error,
        releases_semantic_state=release,
        release_proven=release_proven,
        merges_owners=merge,
        sharing_proven=sharing_proven,
        error_bound_known=error_bound_known,
    )


class BoundedFrontierControllerTests(unittest.TestCase):
    def test_unproven_release_is_rejected(self):
        x = option("x", "drop", release=True, release_proven=False)
        self.assertFalse(option_is_safe(x))

    def test_unproven_owner_merge_is_rejected(self):
        x = option("x", "share", merge=True, sharing_proven=False)
        self.assertFalse(option_is_safe(x))

    def test_unknown_lossy_error_bound_is_rejected(self):
        x = option(
            "x",
            "compress",
            error=0.1,
            error_bound_known=False,
        )
        self.assertFalse(option_is_safe(x))

    def test_capacity_is_per_tier(self):
        groups = [
            [
                option("x", "gpu", vram=8, vram_area=8),
                option("x", "ram", ram=8, ram_area=8, latency=1),
            ]
        ]
        plans = exact_candidate_plans(groups, {"VRAM": 4, "RAM": 16})
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0].choices, (("x", "ram"),))

    def test_dominated_plan_is_removed(self):
        groups = [
            [
                option("x", "a", vram=4, vram_area=4, traffic=1),
                option("x", "b", vram=5, vram_area=5, traffic=2),
            ]
        ]
        frontier = exact_pareto_controller(
            groups,
            {"VRAM": 8, "RAM": 8},
        )
        self.assertEqual([p.choices for p in frontier], [(("x", "a"),)])

    def test_memory_exchange_keeps_both_pareto_points(self):
        groups = [
            [
                option("x", "resident", vram=8, vram_area=8),
                option(
                    "x",
                    "offload",
                    vram=2,
                    ram=8,
                    vram_area=2,
                    ram_area=8,
                    traffic=20,
                    latency=3,
                ),
            ]
        ]
        frontier = exact_pareto_controller(
            groups,
            {"VRAM": 8, "RAM": 16},
        )
        self.assertEqual(len(frontier), 2)

    def test_safe_summary_release_can_enter_frontier(self):
        groups = [
            [
                option("x", "retain", vram=10, vram_area=10),
                option(
                    "x",
                    "summary",
                    vram=2,
                    vram_area=2,
                    compute=1,
                    release=True,
                    release_proven=True,
                ),
            ]
        ]
        plans = exact_candidate_plans(groups, {"VRAM": 10, "RAM": 0})
        self.assertEqual(len(plans), 2)

    def test_10000_random_frontiers_contain_no_dominated_points(self):
        rng = random.Random(434)
        for case in range(10_000):
            groups = []
            for state_index in range(rng.randint(1, 4)):
                group = []
                for option_index in range(rng.randint(1, 4)):
                    release = bool(rng.randrange(2))
                    merge = bool(rng.randrange(2))
                    error = rng.random() if rng.randrange(3) == 0 else 0.0
                    group.append(
                        option(
                            f"s{case}_{state_index}",
                            f"o{option_index}",
                            vram=rng.randint(0, 20),
                            ram=rng.randint(0, 20),
                            vram_area=rng.randint(0, 100),
                            ram_area=rng.randint(0, 100),
                            traffic=rng.randint(0, 50),
                            compute=rng.randint(0, 50),
                            latency=rng.randint(0, 50),
                            error=error,
                            release=release,
                            release_proven=(not release) or bool(rng.randrange(2)),
                            merge=merge,
                            sharing_proven=(not merge) or bool(rng.randrange(2)),
                            error_bound_known=(error == 0.0) or bool(rng.randrange(2)),
                        )
                    )
                groups.append(group)

            frontier = exact_pareto_controller(
                groups,
                {"VRAM": 30, "RAM": 30},
            )
            tiers = ("RAM", "VRAM")
            for i, plan in enumerate(frontier):
                self.assertFalse(
                    any(
                        j != i and dominates(other, plan, tiers)
                        for j, other in enumerate(frontier)
                    )
                )


if __name__ == "__main__":
    unittest.main()
