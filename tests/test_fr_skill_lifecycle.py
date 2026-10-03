from __future__ import annotations

import unittest

from finite_ram_lab.fr_skill_lifecycle import (
    apply_maturity,
    classify_evidence,
    resident_allowed,
    run_panel,
)


def evidence(
    *,
    positive: int = 0,
    independent: int = 0,
    negative: int = 0,
    contradictions: int = 0,
    invalidated: bool = False,
    scope: bool = True,
    invariants: bool = True,
    authority: bool = False,
):
    return {
        "positive_replays": positive,
        "independent_examples": independent,
        "negative_observations": negative,
        "contradictions": contradictions,
        "invalidated": invalidated,
        "scope_explicit": scope,
        "invariants_pass": invariants,
        "authority_expanded": authority,
    }


class SkillLifecycleTests(unittest.TestCase):
    def test_panel(self) -> None:
        result = run_panel()
        self.assertEqual(
            result["status"],
            "PASS",
        )
        self.assertTrue(
            all(
                result["checks"].values()
            )
        )

    def test_two_replays_promote_stable(self) -> None:
        self.assertEqual(
            classify_evidence(
                evidence(
                    positive=2,
                    independent=2,
                )
            ),
            "STABLE",
        )

    def test_direct_negative_is_scoped_guard(self) -> None:
        self.assertEqual(
            classify_evidence(
                evidence(
                    negative=1,
                    independent=1,
                )
            ),
            "QUALIFIED_NEGATIVE",
        )
        self.assertTrue(
            resident_allowed(
                "QUALIFIED_NEGATIVE"
            )
        )

    def test_contradiction_retires_without_deleting(self) -> None:
        self.assertEqual(
            classify_evidence(
                evidence(
                    positive=4,
                    independent=4,
                    contradictions=1,
                )
            ),
            "RETIRED",
        )
        self.assertFalse(
            resident_allowed(
                "RETIRED"
            )
        )

    def test_unknown_evidence_fails_closed(self) -> None:
        self.assertEqual(
            classify_evidence(
                {"positive_replays": 1}
            ),
            "INSUFFICIENT_EVIDENCE",
        )

    def test_governor_only_mutates_maturity(self) -> None:
        skill = {
            "id": "EXAMPLE",
            "when": {"x": True},
            "action": "DO_X",
            "mc": "SKIP",
            "evidence_prs": [1],
            "invalidate_on": ["x_changed"],
            "maturity": "QUALIFIED",
        }

        result = apply_maturity(
            skill,
            evidence(
                positive=2,
                independent=2,
            ),
        )

        self.assertEqual(
            result["maturity"],
            "STABLE",
        )
        for key in (
            "id",
            "when",
            "action",
            "mc",
            "evidence_prs",
            "invalidate_on",
        ):
            self.assertEqual(
                result[key],
                skill[key],
            )


if __name__ == "__main__":
    unittest.main()
