from __future__ import annotations

import json
from pathlib import Path
import unittest

from finite_ram_lab.semantic_oom_shadow import (
    compare_snapshot,
)


FIXTURE = Path("fixtures/FR-SOOM-002-snapshot.json")


class SemanticOomShadowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(
            FIXTURE.read_text(encoding="utf-8")
        )
        cls.result = compare_snapshot(
            cls.snapshot,
            2048,
        )

    def test_shadow_mode_has_no_control_effects(self):
        self.assertTrue(
            self.result["observation_only"]
        )
        self.assertEqual(
            self.result["signals_sent"],
            0,
        )
        self.assertEqual(
            self.result["control_changes"],
            0,
        )
        self.assertEqual(
            self.result["authority_effect"],
            "NONE",
        )

    def test_oom_score_and_semantic_rankings_disagree(self):
        self.assertTrue(
            self.result["ranking_disagreement"]
        )
        baseline = self.result["policies"][
            "EARLYOOM_LIKE_OOM_SCORE"
        ]
        semantic = self.result["policies"][
            "SEMANTIC_MIN_LOSS"
        ]
        self.assertEqual(
            [v["name"] for v in baseline["victims"]],
            ["chrome-active"],
        )
        self.assertEqual(
            [v["name"] for v in semantic["victims"]],
            [
                "batch-compressor",
                "background-indexer",
            ],
        )

    def test_semantic_shadow_preserves_current_task(self):
        baseline = self.result["policies"][
            "EARLYOOM_LIKE_OOM_SCORE"
        ]
        semantic = self.result["policies"][
            "SEMANTIC_MIN_LOSS"
        ]
        self.assertFalse(
            baseline["current_task_survives"]
        )
        self.assertTrue(
            semantic["current_task_survives"]
        )
        self.assertTrue(
            self.result[
                "current_task_survival_changed"
            ]
        )

    def test_semantic_loss_delta_is_frozen(self):
        self.assertEqual(
            self.result[
                "semantic_loss_delta_vs_oom_score"
            ],
            262,
        )

    def test_claim_ceiling_is_read_only(self):
        self.assertEqual(
            self.result["claim_ceiling"],
            "READ_ONLY_SHADOW_RANKING_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
