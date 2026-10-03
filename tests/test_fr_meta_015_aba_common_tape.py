from __future__ import annotations

from statistics import mean
import unittest

from finite_ram_lab.fr_gfx_observer_aba import (
    ARMS,
    ARM_SETTING_INDEX,
    _b_arm_means,
    _segment,
)
from finite_ram_lab.fr_meta_015_aba_common_tape import (
    run_panel,
)


class AbaCommonTapeTests(unittest.TestCase):
    def test_skill_routed_panel(self) -> None:
        result = run_panel()
        self.assertEqual(
            result["status"],
            "PASS",
        )
        self.assertEqual(
            result["skill_route"][
                "primary_action"
            ],
            "REUSE_EXACT_COMPUTATION",
        )
        self.assertFalse(
            result["monte_carlo"][
                "used_for_optimization_decision"
            ]
        )

    def test_common_tape_is_exact_for_reference_episodes(self) -> None:
        for episode in (
            0,
            1,
            137,
            8191,
        ):
            combined = _b_arm_means(
                episode
            )

            for settings in (
                ARMS.values()
            ):
                constant_ms = settings[
                    "constant_overhead_ms"
                ]
                tail_ms = settings[
                    "tail_overhead_ms"
                ]
                index = ARM_SETTING_INDEX[
                    (
                        constant_ms,
                        tail_ms,
                    )
                ]

                original = mean(
                    _segment(
                        episode,
                        1,
                        observer_constant_ms=(
                            constant_ms
                        ),
                        observer_tail_ms=(
                            tail_ms
                        ),
                    )
                )

                self.assertEqual(
                    combined[index],
                    original,
                )


if __name__ == "__main__":
    unittest.main()
