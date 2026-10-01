from __future__ import annotations

import unittest

from finite_ram_lab.bounded_frontier_controller import exact_pareto_controller
from finite_ram_lab.mixed_capacity_cliff import (
    EXPERT_LOGICAL_PROXY_MIB,
    PROMPT_BORROW_PROXY_MIB,
    STRATA_INT8_KV_FULL_MIB,
    STRATA_INT8_KV_HOST_MIB,
    STRATA_INT8_KV_RESIDENT_MIB,
    capacity_sweep,
    frontier_option_sets,
    minimum_vram_for_ram,
    mixed_option_groups,
)


class MixedCapacityCliffTests(unittest.TestCase):
    def test_source_anchors(self):
        self.assertEqual(STRATA_INT8_KV_FULL_MIB, 1584)
        self.assertEqual(STRATA_INT8_KV_RESIDENT_MIB, 396)
        self.assertEqual(STRATA_INT8_KV_HOST_MIB, 1584)
        self.assertEqual(EXPERT_LOGICAL_PROXY_MIB, 34 * 1024)
        self.assertEqual(PROMPT_BORROW_PROXY_MIB, 4731)

    def test_tight_ram_cliff_requires_full_kv(self):
        self.assertEqual(minimum_vram_for_ram(8192), 10544)
        self.assertEqual(minimum_vram_for_ram(9775), 10544)

    def test_streaming_opens_lower_vram_region_once_ram_can_hold_host_kv(self):
        self.assertEqual(minimum_vram_for_ram(9776), 9356)
        self.assertEqual(minimum_vram_for_ram(16384), 9356)

    def test_exact_threshold_plan_is_fully_squeezed(self):
        exact = exact_pareto_controller(
            mixed_option_groups(),
            {"RAM": 8192, "VRAM": 10544},
        )
        self.assertEqual(len(exact), 2)
        options = frontier_option_sets(exact)
        self.assertEqual(options["strata_kv"], ["full_int8_vram"])
        self.assertEqual(
            options["strata_experts"],
            ["gpu8_ram8_file_backing"],
        )
        self.assertEqual(
            options["strata_prefill"],
            ["borrow_expert_cache"],
        )
        self.assertEqual(
            options["semantic_reduction"],
            ["future_sufficient_summary"],
        )
        self.assertEqual(
            options["temporalization"],
            ["blocked_frontier"],
        )
        self.assertEqual(
            options["idle_lifetime"],
            ["always_loaded", "idle_unload"],
        )

    def test_one_mib_below_tight_cliff_is_infeasible(self):
        exact = exact_pareto_controller(
            mixed_option_groups(),
            {"RAM": 8192, "VRAM": 10543},
        )
        self.assertEqual(exact, ())

    def test_streaming_cliff_is_exact(self):
        self.assertEqual(
            exact_pareto_controller(
                mixed_option_groups(),
                {"RAM": 9776, "VRAM": 9355},
            ),
            (),
        )
        exact = exact_pareto_controller(
            mixed_option_groups(),
            {"RAM": 9776, "VRAM": 9356},
        )
        self.assertTrue(exact)
        self.assertEqual(
            frontier_option_sets(exact)["strata_kv"],
            ["stream_int8"],
        )

    def test_capacity_relaxation_adds_frontier_arms(self):
        low = exact_pareto_controller(
            mixed_option_groups(),
            {"RAM": 8192, "VRAM": 10544},
        )
        high = exact_pareto_controller(
            mixed_option_groups(),
            {"RAM": 32768, "VRAM": 32768},
        )
        self.assertGreater(len(high), len(low))
        high_options = frontier_option_sets(high)
        self.assertEqual(
            high_options["strata_experts"],
            [
                "gpu12_ram22",
                "gpu20_ram14",
                "gpu8_ram26",
                "gpu8_ram8_file_backing",
            ],
        )
        self.assertEqual(
            high_options["strata_prefill"],
            ["borrow_expert_cache", "dedicated_prompt_scratch"],
        )

    def test_grid_beam64_is_conservative_high_coverage(self):
        rows = capacity_sweep(
            vram_capacities_mib=(
                9216, 9728, 10240, 10752, 11264,
                12288, 13312, 14336, 16384, 18432,
                20480, 22528, 24576, 28672, 32768,
            ),
            ram_capacities_mib=(
                8192, 9216, 10240, 12288, 14336,
                16384, 20480, 24576, 28672, 32768, 40960,
            ),
            beam_width=64,
        )
        feasible = [row for row in rows if row["feasible"]]
        self.assertEqual(len(feasible), 150)
        coverages = [row["beam_exact_point_coverage"] for row in feasible]
        self.assertGreaterEqual(min(coverages), 0.8)
        self.assertGreaterEqual(sum(coverages) / len(coverages), 0.99)
        self.assertTrue(
            all(row["beam_dominated_fraction"] == 0.0 for row in feasible)
        )

    def test_grid_beam96_matches_exact(self):
        rows = capacity_sweep(
            vram_capacities_mib=(
                9216, 9728, 10240, 10752, 11264,
                12288, 13312, 14336, 16384, 18432,
                20480, 22528, 24576, 28672, 32768,
            ),
            ram_capacities_mib=(
                8192, 9216, 10240, 12288, 14336,
                16384, 20480, 24576, 28672, 32768, 40960,
            ),
            beam_width=96,
        )
        feasible = [row for row in rows if row["feasible"]]
        self.assertTrue(
            all(row["beam_exact_point_coverage"] == 1.0 for row in feasible)
        )
        self.assertTrue(
            all(row["beam_dominated_fraction"] == 0.0 for row in feasible)
        )


if __name__ == "__main__":
    unittest.main()
