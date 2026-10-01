from __future__ import annotations

import random
import unittest

from finite_ram_lab.frontier_compiler import compile_frontier
from finite_ram_lab.strata_physical_frontier import (
    borrowed_cache_plan,
    expert_complement_plan,
    idle_unload_byte_seconds,
    kv_bytes_per_cell,
    kv_tier_plan,
    ownership_partition_bytes,
    strata_trace_states,
)
from finite_ram_lab.tiered_frontier import (
    TierTraceState,
    capacity_ratios,
    compile_tiered_frontier,
)


class StrataPhysicalFrontierTests(unittest.TestCase):
    def test_source_backed_kv_cell_sizes(self):
        self.assertEqual(kv_bytes_per_cell("fp16"), 2048)
        self.assertEqual(kv_bytes_per_cell("int8"), 1056)
        self.assertEqual(kv_bytes_per_cell("q4_0"), 576)
        self.assertEqual(kv_bytes_per_cell("k8v4"), 816)

    def test_int8_131k_32k_resident_12_layers(self):
        p = kv_tier_plan(
            mode="int8",
            max_cells=131072,
            resident_cells=32768,
            layers=12,
        )
        self.assertEqual(p.full_vram_bytes, 1_660_944_384)
        self.assertEqual(p.gpu_resident_bytes, 415_236_096)
        self.assertEqual(p.host_authoritative_bytes, 1_660_944_384)
        self.assertEqual(p.freed_vram_bytes, 1_245_708_288)

    def test_k8v4_streaming_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "k8v4_streaming_not_supported"):
            kv_tier_plan(
                mode="k8v4",
                max_cells=131072,
                resident_cells=32768,
                layers=12,
            )

    def test_expert_complement_has_one_logical_copy(self):
        p = expert_complement_plan(
            logical_expert_bytes=1000,
            gpu_resident_bytes=400,
            ram_budget_bytes=300,
        )
        self.assertEqual(p.gpu_resident_bytes, 400)
        self.assertEqual(p.ram_complement_bytes, 300)
        self.assertEqual(p.file_fallback_bytes, 300)
        self.assertEqual(
            p.gpu_resident_bytes + p.ram_complement_bytes + p.file_fallback_bytes,
            p.logical_expert_bytes,
        )

    def test_prompt_borrow_reuses_cache_allocation(self):
        p = borrowed_cache_plan(
            cache_bytes=1000,
            borrowed_bytes=400,
            prompt_scratch_bytes=350,
        )
        self.assertEqual(p.steady_peak_bytes, 1000)
        self.assertEqual(p.prompt_peak_bytes, 1000)
        self.assertEqual(p.temporary_expert_capacity_bytes, 600)

    def test_ownership_partition_avoids_unowned_layer_state(self):
        p = ownership_partition_bytes(
            total_layers=48,
            owned_layers=12,
            per_layer_state_bytes=1000,
        )
        self.assertEqual(p["whole_model_copy_bytes"], 48000)
        self.assertEqual(p["carved_state_bytes"], 12000)
        self.assertEqual(p["avoided_duplicate_bytes"], 36000)

    def test_idle_unload_reduces_byte_seconds_not_loaded_peak(self):
        p = idle_unload_byte_seconds(
            resident_bytes=100,
            horizon_seconds=10,
            active_seconds=4,
        )
        self.assertEqual(p["always_loaded_byte_seconds"], 1000.0)
        self.assertEqual(p["idle_unload_byte_seconds"], 400.0)
        self.assertEqual(p["saved_byte_seconds"], 600.0)

    def test_b428_adapter_counts_semantics_once_and_excludes_file_backing(self):
        kv = kv_tier_plan(
            mode="int8", max_cells=100, resident_cells=25, layers=1
        )
        experts = expert_complement_plan(
            logical_expert_bytes=1000,
            gpu_resident_bytes=400,
            ram_budget_bytes=300,
        )
        states = strata_trace_states(
            kv_plan=kv,
            expert_plan=experts,
            session_state_bytes=50,
        )
        names = {s.name for s in states}
        self.assertNotIn("strata-expert-file-fallback", names)
        r = compile_frontier(states)
        self.assertEqual(
            r["logical_peak_bytes"],
            kv.full_vram_bytes + experts.logical_expert_bytes + 50,
        )

    def test_tiered_compiler_separates_vram_and_ram(self):
        states = [
            TierTraceState("gpu", 0, 2, "VRAM", 8, logical_bytes=10),
            TierTraceState("host", 0, 2, "RAM", 12, logical_bytes=0),
        ]
        r = compile_tiered_frontier(states)
        self.assertEqual(r["total_resident_peak_bytes"], 20)
        self.assertEqual(r["tier_peak_bytes"], {"RAM": 12, "VRAM": 8})
        self.assertEqual(
            capacity_ratios(r["tier_peak_bytes"], {"VRAM": 10, "RAM": 24}),
            {"RAM": 0.5, "VRAM": 0.8},
        )

    def test_20000_random_tier_invariants(self):
        rng = random.Random(432)
        for case in range(20_000):
            states = []
            for i in range(rng.randint(0, 8)):
                start = rng.randint(0, 8)
                end = rng.randint(start + 1, 10)
                states.append(
                    TierTraceState(
                        f"s{case}_{i}",
                        start,
                        end,
                        rng.choice(("VRAM", "RAM")),
                        rng.randint(0, 1000),
                        logical_bytes=rng.randint(0, 1000),
                    )
                )
            r = compile_tiered_frontier(states)
            self.assertEqual(
                r["total_resident_peak_bytes"],
                max(
                    [sum(w["resident_by_tier"].values()) for w in r["windows"]]
                    or [0]
                ),
            )
            for tier, peak in r["tier_peak_bytes"].items():
                self.assertEqual(
                    peak,
                    max(
                        [w["resident_by_tier"][tier] for w in r["windows"]]
                        or [0]
                    ),
                )


if __name__ == "__main__":
    unittest.main()
