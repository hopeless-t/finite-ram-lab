from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_p9_001_minimum_sufficient_projection import (
    WORK_UNITS,
    atom_map,
    closure,
    run_panel,
)


class MinimumSufficientProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_P9_001_RESULT="
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

    def test_compiled_projection_preserves_all_contract_planes(self) -> None:
        for row in self.result[
            "work_units"
        ]:
            self.assertTrue(
                all(
                    row[
                        "compiled_contract"
                    ].values()
                )
            )
            self.assertEqual(
                row[
                    "compiled_contract"
                ],
                row[
                    "full_contract"
                ],
            )

    def test_decision_only_projection_is_an_explicit_false_positive(self) -> None:
        self.assertEqual(
            self.result[
                "adversary"
            ][
                "decision_only_false_positive_count"
            ],
            len(WORK_UNITS),
        )
        for row in self.result[
            "work_units"
        ]:
            self.assertTrue(
                row[
                    "decision_only_contract"
                ][
                    "decision"
                ]
            )
            self.assertFalse(
                all(
                    row[
                        "decision_only_contract"
                    ].values()
                )
            )

    def test_compiled_projection_is_inclusion_minimal_on_fixture(self) -> None:
        self.assertEqual(
            self.result[
                "minimality"
            ][
                "failures"
            ],
            [],
        )
        for row in self.result[
            "work_units"
        ]:
            for broken_planes in row[
                "minimality_witnesses"
            ].values():
                self.assertTrue(
                    broken_planes
                )

    def test_fixture_has_large_resident_reduction_without_claiming_physical_gain(self) -> None:
        self.assertGreater(
            self.result[
                "resident_surface"
            ][
                "compiled_savings_fraction"
            ],
            0.80,
        )
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_DECLARED_DEPENDENCY_FIXTURE_ONLY_NO_PHYSICAL_RAM_OR_PCG_PERFORMANCE_CLAIM",
        )

    def test_unknown_atom_fails_closed(self) -> None:
        atoms = atom_map()
        with self.assertRaises(
            ValueError
        ):
            closure(
                ("does-not-exist",),
                atoms=atoms,
            )


if __name__ == "__main__":
    unittest.main()
