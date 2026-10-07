from __future__ import annotations

import unittest

from finite_ram_lab.fr_p9_018_service_curve_deadline_admission import ADMIT
from finite_ram_lab.fr_p9_022_stage_release_service_composition import (
    INSUFFICIENT_CPU,
    first_completion_index,
    post_release_service,
    release_order_adversary,
    run_panel,
)
from finite_ram_lab.fr_p9_018_service_curve_deadline_admission import curve_from_increments


class StageReleaseServiceCompositionTests(unittest.TestCase):
    def test_completion_and_post_release_service(self) -> None:
        transfer = curve_from_increments((0, 2, 2, 0), epoch=1)
        cpu = curve_from_increments((3, 0, 0, 4), epoch=1)
        release = first_completion_index(transfer, 4, deadline_index=4)
        self.assertEqual(release, 3)
        self.assertEqual(post_release_service(cpu, release_index=3, deadline_index=4), 4)

    def test_front_loaded_cpu_service_is_not_bankable_before_release(self) -> None:
        result = release_order_adversary()
        self.assertTrue(result["naive_front_admit"])
        self.assertEqual(result["stage_aware_front_status"], INSUFFICIENT_CPU)
        self.assertEqual(result["front_usable_cpu_service"], 0)
        self.assertEqual(result["stage_aware_back_status"], ADMIT)

    def test_frozen_panel_passes(self) -> None:
        result = run_panel(seed=20261008, trials=1000)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["exhaustive"]["mismatches"], 0)
        self.assertGreater(result["monte_carlo"]["naive_independent_false_admits"], 0)
        self.assertEqual(result["monte_carlo"]["stage_aware_false_admits"], 0)
        self.assertIsNone(result["scalar_gain"])


if __name__ == "__main__":
    unittest.main()
