from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_058_compiled_rent_lookup import (
    COMPILED_PATHS,
    compiled_select,
    run_panel,
)


class CompiledRentLookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_058_RESULT="
            + json.dumps(
                cls.result,
                sort_keys=True,
            ),
            flush=True,
        )

    def test_panel_passes(self) -> None:
        self.assertEqual(
            self.result[
                "status"
            ],
            "PASS",
        )
        self.assertTrue(
            all(
                self.result[
                    "checks"
                ].values()
            )
        )

    def test_compiled_paths_are_exact(self) -> None:
        self.assertEqual(
            self.result[
                "validation"
            ][
                "mismatches"
            ],
            0,
        )
        self.assertEqual(
            len(
                COMPILED_PATHS
            ),
            7,
        )

    def test_boundaries_route_forward_on_exact_crossover(self) -> None:
        self.assertEqual(
            compiled_select(
                0.07350214904258025
            ),
            "P2",
        )
        self.assertEqual(
            compiled_select(
                0.32482048730057045
            ),
            "P7",
        )

    def test_negative_rent_fails_closed(self) -> None:
        with self.assertRaises(
            ValueError
        ):
            compiled_select(
                -0.01
            )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "COMPILED_LOOKUP_FOR_THE_EIGHT_FP057_HOSTED_PHYSICAL_POLICY_PATHS_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
