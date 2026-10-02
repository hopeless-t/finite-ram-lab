from __future__ import annotations

import json
from pathlib import Path
import unittest


SPEC = Path("specs/FR-SOOM-002A.json")


class SemanticOomControllerTaxonomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(
            SPEC.read_text(encoding="utf-8")
        )
        cls.by_name = {
            row["name"]: row
            for row in cls.spec["systems"]
        }

    def test_required_reference_systems_are_present(self):
        required = {
            "earlyoom",
            "nohang",
            "Meta oomd",
            "systemd-oomd",
            "systemd pressure protocol",
            "low-memory-monitor",
            "Android lmkd",
            "Senpai",
            "Intel Memory Usage Analyzer",
        }
        self.assertTrue(
            required.issubset(self.by_name)
        )

    def test_cooperative_and_kill_planes_are_distinct(self):
        self.assertEqual(
            self.by_name["systemd pressure protocol"]["class"],
            "cooperative_pressure_notification",
        )
        self.assertEqual(
            self.by_name["systemd-oomd"]["class"],
            "cgroup_oom_controller",
        )

    def test_importance_aware_precedent_is_recorded(self):
        self.assertEqual(
            self.by_name["Android lmkd"]["semantic_channel"],
            "oom_adj_process_importance",
        )

    def test_working_set_relative_is_recorded(self):
        self.assertEqual(
            self.by_name["Senpai"]["class"],
            "adaptive_working_set_sizer",
        )

    def test_next_hypothesis_is_intra_application(self):
        self.assertIn(
            "intra-application reclaimability",
            self.spec["new_hypothesis"],
        )

    def test_claim_ceiling(self):
        self.assertEqual(
            self.spec["claim_ceiling"],
            "SOURCE_GROUNDED_CONTROLLER_TAXONOMY_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
