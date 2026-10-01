from __future__ import annotations

import random
import unittest

from finite_ram_lab.live_state_exemplars import (
    EXEMPLARS,
    deduplicated_bytes,
    naive_attention_score_bytes,
    ozaki_i_symbolic,
    ozaki_ii_symbolic,
    phase_value_density,
    tiled_attention_score_bytes,
)


class LiveStateExemplarTests(unittest.TestCase):
    def test_ozaki_i_peak_grows_with_slice_count(self):
        prev = 0
        for k in range(1, 20):
            now = ozaki_i_symbolic(
                slices=k,
                a_slice_bytes=100,
                b_slice_bytes=100,
                accumulator_bytes=80,
            )["peak_live_bytes"]
            self.assertGreater(now, prev)
            prev = now

    def test_ozaki_i_gemm_count_is_triangular(self):
        self.assertEqual(
            ozaki_i_symbolic(
                slices=8,
                a_slice_bytes=1,
                b_slice_bytes=1,
                accumulator_bytes=1,
            )["gemm_count"],
            36,
        )

    def test_ozaki_ii_streaming_peak_is_independent_of_modulus_count(self):
        peaks = {
            ozaki_ii_symbolic(
                moduli=s,
                a_residue_bytes=100,
                b_residue_bytes=100,
                accumulator_bytes=80,
            )["peak_live_bytes"]
            for s in range(1, 50)
        }
        self.assertEqual(len(peaks), 1)

    def test_ozaki_ii_compute_grows_linearly_in_moduli(self):
        for s in range(1, 50):
            self.assertEqual(
                ozaki_ii_symbolic(
                    moduli=s,
                    a_residue_bytes=1,
                    b_residue_bytes=1,
                    accumulator_bytes=1,
                )["gemm_count"],
                s,
            )

    def test_tiled_attention_avoidable_score_state_is_smaller(self):
        n = 4096
        full = naive_attention_score_bytes(n, 2)
        tile = tiled_attention_score_bytes(128, 128, 2)
        self.assertLess(tile, full)
        self.assertEqual(full // tile, 1024)

    def test_shared_arena_saves_replica_bytes_when_metadata_is_small(self):
        r = deduplicated_bytes(
            object_bytes=10_000,
            replicas=4,
            metadata_bytes_per_replica=100,
        )
        self.assertEqual(r["before_bytes"], 40_000)
        self.assertEqual(r["after_bytes"], 10_400)
        self.assertEqual(r["saved_bytes"], 29_600)

    def test_phase_value_density_can_reverse_hotset(self):
        expert_a = phase_value_density(
            size_bytes=100,
            accesses={"prefill": 100, "decode": 2},
            fast_access_cost=1,
            slow_access_cost=10,
        )
        expert_b = phase_value_density(
            size_bytes=100,
            accesses={"prefill": 10, "decode": 50},
            fast_access_cost=1,
            slow_access_cost=10,
        )
        self.assertGreater(expert_a["prefill"], expert_b["prefill"])
        self.assertLess(expert_a["decode"], expert_b["decode"])

    def test_10000_random_ozaki_invariants(self):
        rng = random.Random(427)
        for _ in range(10_000):
            k = rng.randint(1, 128)
            s = rng.randint(1, 128)
            a = rng.randint(1, 1_000_000)
            b = rng.randint(1, 1_000_000)
            acc = rng.randint(1, 1_000_000)
            oi = ozaki_i_symbolic(
                slices=k,
                a_slice_bytes=a,
                b_slice_bytes=b,
                accumulator_bytes=acc,
            )
            oii = ozaki_ii_symbolic(
                moduli=s,
                a_residue_bytes=a,
                b_residue_bytes=b,
                accumulator_bytes=acc,
            )
            self.assertEqual(oi["gemm_count"], k * (k + 1) // 2)
            self.assertEqual(oii["gemm_count"], s)
            self.assertEqual(oii["peak_live_bytes"], a + b + acc)

    def test_exemplar_names_unique(self):
        names = [x.name for x in EXEMPLARS]
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
