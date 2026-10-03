from __future__ import annotations

import unittest

from finite_ram_lab.fr_memory_atoms import (
    run_panel,
)


class FrMemoryAtomsTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()

    def test_foundational_quantization_is_present(self):
        q = self.result[
            "quantization_coverage"
        ]

        for key in (
            "AWQ",
            "GPTQ",
            "NF4",
            "GGUF",
            "BITNET_B1_58",
        ):
            self.assertIn(
                key,
                q,
            )

    def test_gguf_is_not_quantizer(self):
        self.assertEqual(
            self.result[
                "quantization_coverage"
            ]["GGUF"],
            "CONTAINER_AXIS_NOT_QUANTIZER",
        )

    def test_duplication_is_top_gap(self):
        self.assertEqual(
            self.result[
                "immediate_priorities"
            ][0]["atom"],
            "DUPLICATION_FACTOR",
        )

    def test_allocator_fragmentation_is_gap(self):
        self.assertIn(
            "ALLOCATOR_FRAGMENTATION",
            self.result[
                "coverage_summary"
            ]["gap"],
        )

    def test_observation_is_in_equation(self):
        self.assertEqual(
            self.result[
                "equation"
            ]["terms"]["O"],
            "observation/control overhead",
        )

    def test_claim_ceiling(self):
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SOURCE_GROUNDED_ATOMIC_INVENTORY_AND_RESEARCH_PRIORITIZATION_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
