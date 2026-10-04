from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_024_post_training_validation import (
    run_panel,
)


class PostTrainingValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_024_RESULT="
            + json.dumps(
                cls.result,
                sort_keys=True,
            ),
            flush=True,
        )

    def test_panel_passes(self) -> None:
        self.assertEqual(
            self.result["status"],
            "PASS",
        )
        self.assertTrue(
            all(
                self.result[
                    "checks"
                ].values()
            )
        )

    def test_one_probe_is_not_overclaimed(self) -> None:
        one = self.result[
            "one_probe_first"
        ]
        self.assertFalse(
            one[
                "improves_every_deadline"
            ]
        )
        self.assertLessEqual(
            one[
                "deadline_brier"
            ][
                "25"
            ][
                "relative_improvement"
            ],
            0.0,
        )

    def test_two_probe_min_repairs_validation(self) -> None:
        two = self.result[
            "two_probe_min"
        ]
        self.assertTrue(
            two[
                "improves_every_deadline"
            ]
        )
        self.assertGreater(
            two[
                "deadline_brier"
            ][
                "25"
            ][
                "relative_improvement"
            ],
            0.0,
        )

    def test_claim_ceiling_is_holdout_only(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "EIGHT_POST_TRAINING_UNIQUE_HEAD_GITHUB_HOSTED_CI_RUNS_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
