from __future__ import annotations

import random
import unittest

from finite_ram_lab.gemmul8_source_trace import (
    BLAS_WORKSPACE_BYTES,
    GROUPED_CRT_MAX_ELEMENTS,
    Gemmul8Int8RealWorkspace,
    int8_real_crt_groups,
    pad,
)


class Gemmul8SourceTraceTests(unittest.TestCase):
    def test_padding_matches_256_alignment(self):
        self.assertEqual(pad(1), 256)
        self.assertEqual(pad(256), 256)
        self.assertEqual(pad(257), 512)

    def test_int8_real_groups_are_four_moduli_until_tail(self):
        self.assertEqual(int8_real_crt_groups(8), ((0, 4), (4, 8)))
        self.assertEqual(
            int8_real_crt_groups(20),
            ((0, 4), (4, 8), (8, 12), (12, 16), (16, 20)),
        )

    def test_4096_cube_num_moduli_8_source_formula(self):
        model = Gemmul8Int8RealWorkspace(4096, 4096, 4096, 8)
        self.assertTrue(model.grouped_crt)
        self.assertEqual(model.work_a_bytes, 134_226_175)
        self.assertEqual(model.work_b_bytes, 134_226_175)
        self.assertEqual(model.work_c_bytes, 402_653_439)
        self.assertEqual(model.total_workspace_bytes, 671_105_789)

    def test_8192_square_output_still_uses_grouped_crt(self):
        model = Gemmul8Int8RealWorkspace(8192, 8192, 8192, 8)
        self.assertEqual(model.size_c, GROUPED_CRT_MAX_ELEMENTS)
        self.assertTrue(model.grouped_crt)
        self.assertEqual(model.total_workspace_bytes, 2_684_388_093)

    def test_16384_square_output_uses_non_grouped_path(self):
        model = Gemmul8Int8RealWorkspace(16384, 16384, 16384, 8)
        self.assertGreater(model.size_c, GROUPED_CRT_MAX_ELEMENTS)
        self.assertFalse(model.grouped_crt)
        self.assertEqual(model.total_workspace_bytes, 7_281_378_045)

    def test_workspace_grows_with_moduli_for_fixed_shape(self):
        previous = 0
        for num_moduli in range(2, 21):
            now = Gemmul8Int8RealWorkspace(
                4096, 4096, 4096, num_moduli
            ).total_workspace_bytes
            self.assertGreaterEqual(now, previous)
            previous = now

    def test_source_trace_does_not_claim_one_residue_pair(self):
        trace = Gemmul8Int8RealWorkspace(
            4096, 4096, 4096, 8
        ).source_trace()
        self.assertEqual(trace["a_low_plane_count"], 8)
        self.assertEqual(trace["b_low_plane_count"], 8)
        self.assertEqual(trace["crt_groups"], [[0, 4], [4, 8]])

    def test_accurate_mode_norm_floor_in_c_workspace(self):
        model = Gemmul8Int8RealWorkspace(
            512, 512, 512, 2, fastmode=False
        )
        self.assertGreaterEqual(
            model.product_workspace_bytes,
            4 * model.size_c + BLAS_WORKSPACE_BYTES,
        )

    def test_20000_random_structural_invariants(self):
        rng = random.Random(429)
        for _ in range(20_000):
            m = rng.randint(1, 20_000)
            n = rng.randint(1, 20_000)
            k = rng.randint(1, 20_000)
            num_moduli = rng.randint(2, 20)
            model = Gemmul8Int8RealWorkspace(m, n, k, num_moduli)
            self.assertGreater(model.work_a_bytes, 0)
            self.assertGreater(model.work_b_bytes, 0)
            self.assertGreater(model.work_c_bytes, 0)
            self.assertEqual(
                model.total_workspace_bytes,
                model.work_a_bytes + model.work_b_bytes + model.work_c_bytes,
            )
            self.assertEqual(
                model.grouped_crt,
                model.size_c <= GROUPED_CRT_MAX_ELEMENTS,
            )


if __name__ == "__main__":
    unittest.main()
