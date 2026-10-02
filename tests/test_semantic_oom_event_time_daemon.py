from __future__ import annotations

import unittest

from finite_ram_lab.semantic_oom_event_time_daemon import (
    run_panel,
)


class SemanticOomEventTimeDaemonTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.s = cls.result["strategies"]

    def test_static_underreacts(self):
        row = self.s[
            "STATIC_COOPERATIVE"
        ]
        self.assertEqual(
            row["current_task_loss_count"],
            6,
        )
        self.assertEqual(
            row["switch_count"],
            0,
        )

    def test_sticky_overprotects(self):
        row = self.s[
            "STICKY_EVER_DEPENDENCE"
        ]
        self.assertEqual(
            row["current_task_loss_count"],
            0,
        )
        self.assertEqual(
            row[
                "unnecessary_protection_count"
            ],
            6,
        )
        self.assertEqual(
            row["switch_count"],
            1,
        )

    def test_raw_churns_and_overreacts(self):
        row = self.s[
            "RAW_LAST_EVIDENCE"
        ]
        self.assertEqual(
            row["current_task_loss_count"],
            1,
        )
        self.assertEqual(
            row[
                "unnecessary_protection_count"
            ],
            3,
        )
        self.assertEqual(
            row["switch_count"],
            6,
        )
        self.assertEqual(
            row[
                "release_delay_to_cooperative_pressure_s"
            ],
            75,
        )

    def test_decay_hysteresis_reduces_overreaction(self):
        row = self.s[
            "DECAY_HYSTERESIS_COOLDOWN"
        ]
        self.assertEqual(
            row["current_task_loss_count"],
            1,
        )
        self.assertEqual(
            row[
                "unnecessary_protection_count"
            ],
            0,
        )
        self.assertEqual(
            row["switch_count"],
            2,
        )
        self.assertEqual(
            row[
                "detection_delay_to_protected_pressure_s"
            ],
            10,
        )
        self.assertEqual(
            row[
                "release_delay_to_cooperative_pressure_s"
            ],
            40,
        )

    def test_cooldown_blocks_one_contradictory_exit(self):
        row = self.s[
            "DECAY_HYSTERESIS_COOLDOWN"
        ]
        self.assertEqual(
            row[
                "cooldown_blocked_exit_events"
            ],
            1,
        )

        switches = row["switches"]
        self.assertEqual(
            switches[0]["time_s"],
            113,
        )
        self.assertEqual(
            switches[0]["to"],
            "PROTECTIVE",
        )
        self.assertEqual(
            switches[1]["time_s"],
            280,
        )
        self.assertEqual(
            switches[1]["to"],
            "COOPERATIVE",
        )

    def test_decay_hysteresis_has_lower_mean_cost_than_raw(self):
        decay = self.s[
            "DECAY_HYSTERESIS_COOLDOWN"
        ]
        raw = self.s[
            "RAW_LAST_EVIDENCE"
        ]

        self.assertLess(
            decay["mean_semantic_loss"],
            raw["mean_semantic_loss"],
        )
        self.assertLess(
            decay["switch_count"],
            raw["switch_count"],
        )

    def test_claim_ceiling_is_synthetic(self):
        self.assertTrue(
            self.result["synthetic_only"]
        )
        self.assertFalse(
            self.result[
                "live_control_claim"
            ]
        )
        self.assertEqual(
            self.result["claim_ceiling"],
            "SYNTHETIC_EVENT_TIME_DAEMON_STATE_MACHINE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
