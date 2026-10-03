from __future__ import annotations

import unittest

from finite_ram_lab.representation_placement_graph import (
    CONTAINERS,
    run_panel,
)


class RepresentationPlacementGraphTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.selected = cls.result[
            "selected_plans"
        ]
        cls.cloud = cls.result[
            "forced_cloud_counterfactual"
        ]

    def test_taxonomy_keeps_gguf_out_of_quantizer_axis(self):
        self.assertFalse(
            CONTAINERS["GGUF"][
                "is_quantizer"
            ]
        )
        self.assertEqual(
            CONTAINERS["GGUF"][
                "size_ratio"
            ],
            1.0,
        )

    def test_hot_conventional_state_stays_local(self):
        row = self.selected[
            "HOT_WEIGHT_SHARD"
        ]

        self.assertEqual(
            row["representation"],
            "AWQ4",
        )
        self.assertEqual(
            row["placement"],
            "RAM",
        )
        self.assertLessEqual(
            row["latency_ms"],
            row["deadline_ms"],
        )

    def test_warm_state_can_use_ssd(self):
        row = self.selected[
            "WARM_EXPERT_SHARD"
        ]

        self.assertEqual(
            row["representation"],
            "AWQ4",
        )
        self.assertEqual(
            row["placement"],
            "SSD",
        )
        self.assertEqual(
            row["volatile_resident_mib"],
            0.0,
        )

    def test_cold_state_can_use_cloud(self):
        row = self.selected[
            "COLD_MODEL_SHARD"
        ]

        self.assertEqual(
            row["representation"],
            "AWQ4",
        )
        self.assertEqual(
            row["placement"],
            "CLOUD_OBJECT",
        )
        self.assertEqual(
            row["volatile_resident_mib"],
            0.0,
        )
        self.assertEqual(
            row["local_storage_mib"],
            0.0,
        )

    def test_force_cloud_fails_hot_and_warm_deadlines(self):
        self.assertFalse(
            self.cloud[
                "HOT_WEIGHT_SHARD"
            ][
                "counterfactual_deadline_success"
            ]
        )
        self.assertFalse(
            self.cloud[
                "WARM_EXPERT_SHARD"
            ][
                "counterfactual_deadline_success"
            ]
        )
        self.assertTrue(
            self.cloud[
                "COLD_MODEL_SHARD"
            ][
                "counterfactual_deadline_success"
            ]
        )

    def test_bitnet_is_native_compatibility_class(self):
        probe = self.result[
            "bitnet_compatibility_probe"
        ]

        self.assertFalse(
            probe["compatible"]
        )
        self.assertFalse(
            probe["feasible"]
        )

        native = self.selected[
            "BITNET_NATIVE_SHARD"
        ]

        self.assertEqual(
            native["representation"],
            "BITNET_B1_58",
        )

    def test_claim_ceiling_is_synthetic(self):
        self.assertTrue(
            self.result["synthetic_only"]
        )
        self.assertFalse(
            self.result["live_control_claim"]
        )
        self.assertEqual(
            self.result["claim_ceiling"],
            "SYNTHETIC_REPRESENTATION_PLACEMENT_GRAPH_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
