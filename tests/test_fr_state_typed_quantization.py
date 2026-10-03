from __future__ import annotations

import unittest

from finite_ram_lab.fr_state_typed_quantization import (
    grouped_effective_bits,
    kv_cache_mib,
    run_panel,
)


class FrStateTypedQuantizationTests(
    unittest.TestCase
):
    def test_four_bit_payload_has_metadata_tax(self):
        self.assertEqual(
            grouped_effective_bits(
                payload_bits=4.0,
                group_size=32,
                scale_bits=16,
                zero_bits=16,
            ),
            5.0,
        )

    def test_larger_groups_reduce_metadata_tax(self):
        small = grouped_effective_bits(
            payload_bits=4.0,
            group_size=32,
            scale_bits=16,
            zero_bits=16,
        )

        large = grouped_effective_bits(
            payload_bits=4.0,
            group_size=128,
            scale_bits=16,
            zero_bits=16,
        )

        self.assertLess(
            large,
            small,
        )

    def test_kv_long_context_geometry(self):
        self.assertEqual(
            kv_cache_mib(
                layers=32,
                tokens=32768,
                kv_heads=8,
                head_dim=128,
                effective_bits=16.0,
            ),
            4096.0,
        )

    def test_state_classes_select_different_representation_families(self):
        result = run_panel()
        selected = result[
            "synthetic_selections"
        ]

        self.assertEqual(
            selected[
                "weight_quality_0_98"
            ]["name"],
            "SPQR3_OUTLIER_0_5PCT",
        )

        self.assertEqual(
            selected[
                "activation_quality_0_99"
            ]["name"],
            "SMOOTHQUANT_W8A8_ACT",
        )

        self.assertEqual(
            selected[
                "kv_quality_0_98"
            ]["name"],
            "KIVI2_EFFECTIVE",
        )

    def test_claim_ceiling(self):
        result = run_panel()

        self.assertEqual(
            result[
                "claim_ceiling"
            ],
            "SOURCE_GROUNDED_FORMULA_AND_SYNTHETIC_STATE_TYPED_QUANTIZATION_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
