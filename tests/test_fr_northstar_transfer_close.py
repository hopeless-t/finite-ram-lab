from __future__ import annotations

import unittest

from finite_ram_lab.fr_northstar_transfer_close import (
    run_panel,
)


class FrNorthStarTransferCloseTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()

    def test_gap_lifecycle_closes(self):
        life = self.result[
            "gap_lifecycle"
        ]

        self.assertEqual(
            life[
                "before_FR_XFER_001"
            ],
            "CAPABILITY_GAP",
        )

        self.assertEqual(
            life[
                "after_registry_update"
            ]["classification"],
            "MODEL_GAP",
        )

        self.assertEqual(
            life[
                "after_effect_model"
            ]["classification"],
            "FRONTIER_REACHED",
        )

    def test_staged_crosses_budget(self):
        self.assertFalse(
            self.result[
                "effect_model"
            ]["arms"][
                "STAGED_COPY"
            ]["fits_budget"]
        )

    def test_direct_and_shared_fit(self):
        arms = self.result[
            "effect_model"
        ]["arms"]

        self.assertTrue(
            arms[
                "DIRECT_TRANSFER_NO_STAGING"
            ]["fits_budget"]
        )

        self.assertTrue(
            arms[
                "ZERO_COPY_SHARED_VIEW"
            ]["fits_budget"]
        )

    def test_transfer_research_stops(self):
        self.assertFalse(
            self.result[
                "research_policy"
            ][
                "open_new_transfer_mechanism_lane"
            ]
        )

    def test_no_live_authority(self):
        self.assertEqual(
            self.result[
                "governance"
            ][
                "live_actions_executed"
            ],
            0,
        )

    def test_claim_ceiling(self):
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_PROXY_NORTH_STAR_LOOP_CLOSURE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
