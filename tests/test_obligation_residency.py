from __future__ import annotations

import random
import unittest

from finite_ram_lab.obligation_residency import (
    FidelityClass,
    compare_crt_residency,
    software_panel,
    unified_contracts,
)


class ObligationResidencyTests(unittest.TestCase):
    def test_three_lane_crt_stream_preserves_exact_result_with_lower_logical_peak(self):
        a = ((3, 5), (-2, 7))
        b = ((11, -4), (6, 9))
        result = compare_crt_residency(a, b, (127, 125, 121))

        self.assertEqual(result.streamed.output, ((63, 33), (20, 71)))
        self.assertTrue(result.all_resident.exact_match)
        self.assertTrue(result.streamed.exact_match)
        self.assertEqual(result.all_resident.logical_peak_intermediate_bytes, 24)
        self.assertEqual(result.streamed.logical_peak_intermediate_bytes, 16)
        self.assertAlmostEqual(result.peak_reduction_fraction, 1 / 3)

    def test_uniqueness_gate_fails_closed(self):
        a = ((3, 5), (-2, 7))
        b = ((11, -4), (6, 9))
        with self.assertRaisesRegex(ValueError, "crt_uniqueness_not_proven"):
            compare_crt_residency(a, b, (127,))

    def test_non_coprime_moduli_fail_closed(self):
        a = ((1, 2), (3, 4))
        b = ((5, 6), (7, 8))
        with self.assertRaisesRegex(ValueError, "moduli_not_pairwise_coprime"):
            compare_crt_residency(a, b, (125, 25))

    def test_random_exact_replay(self):
        rng = random.Random(46101)
        for _ in range(40):
            a = tuple(
                tuple(rng.randint(-8, 8) for _ in range(4))
                for _ in range(4)
            )
            b = tuple(
                tuple(rng.randint(-8, 8) for _ in range(4))
                for _ in range(4)
            )
            result = compare_crt_residency(a, b, (127, 125, 121))
            self.assertTrue(result.streamed.exact_match)
            self.assertEqual(result.all_resident.output, result.streamed.output)

    def test_panel_exact_and_streamed_peak_lower(self):
        panel = software_panel(seed=461, size=8)
        self.assertEqual(
            panel["claim_ceiling"],
            "SOFTWARE_EXACT_LOGICAL_RESIDENCY_ONLY",
        )
        rows = panel["rows"]
        self.assertEqual([row["lane_count"] for row in rows], [2, 3, 4, 5, 6, 7])
        self.assertTrue(all(row["exact_match"] for row in rows))
        self.assertTrue(
            all(
                row["streamed_peak_bytes"] < row["all_resident_peak_bytes"]
                for row in rows
            )
        )

    def test_cross_domain_contracts_do_not_overclaim_exactness(self):
        contracts = {item.domain: item for item in unified_contracts()}
        self.assertIs(contracts["ozaki_crt"].fidelity_class, FidelityClass.EXACT)
        self.assertIs(
            contracts["ternary_model"].fidelity_class,
            FidelityClass.EMPIRICAL_CAPABILITY,
        )
        self.assertIs(
            contracts["kitten_review"].fidelity_class,
            FidelityClass.EMPIRICAL_CAPABILITY,
        )


if __name__ == "__main__":
    unittest.main()
