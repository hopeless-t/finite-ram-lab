from __future__ import annotations

import copy
import unittest
from pathlib import Path

from finite_ram_lab.local_execution_admission import (
    build_request,
    load_spec,
    validate_spec,
)


SPEC = Path("specs/B501-LOCAL-EXECUTION-ADMISSION-v0.1.json")


class LocalExecutionAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = load_spec(SPEC)

    def test_frozen_budget_is_bounded(self):
        budget = self.spec["budget"]
        self.assertEqual(budget["candidate_q"], [1, 2, 4, 7])
        self.assertEqual(budget["initial_physical_observations"], 32)
        self.assertEqual(
            budget["required_sample_count_per_promoted_q"],
            19,
        )
        self.assertEqual(
            budget["maximum_total_physical_observations"],
            76,
        )

    def test_request_is_bound_to_run_id_and_commit(self):
        request = build_request(
            self.spec,
            run_id="b501-local-001",
            repo_commit="a" * 40,
        )
        self.assertEqual(request["run_id"], "b501-local-001")
        self.assertEqual(request["repo_commit"], "a" * 40)
        self.assertEqual(
            request["out_dir"],
            "runs/local-governor/b501-local-001",
        )
        self.assertIn(
            "runs/local-governor/b501-local-001",
            request["argv"],
        )
        self.assertEqual(
            request["retry_on_unknown_delivery"],
            "DO_NOT_RETRY",
        )

    def test_network_or_external_effect_widening_fails_closed(self):
        for field in ("network_allowed", "external_effects_allowed"):
            mutated = copy.deepcopy(self.spec)
            mutated["execution"][field] = True
            with self.subTest(field=field):
                with self.assertRaises(RuntimeError):
                    validate_spec(mutated)

    def test_unknown_delivery_retry_widening_fails_closed(self):
        mutated = copy.deepcopy(self.spec)
        mutated["retry"]["unknown_delivery"] = "RETRY"
        with self.assertRaisesRegex(
            RuntimeError,
            "admission_unknown_delivery_policy_invalid",
        ):
            validate_spec(mutated)

    def test_invalid_run_id_or_commit_rejected(self):
        with self.assertRaises(ValueError):
            build_request(
                self.spec,
                run_id="../escape",
                repo_commit="a" * 40,
            )
        with self.assertRaises(ValueError):
            build_request(
                self.spec,
                run_id="ok",
                repo_commit="not-a-commit",
            )


if __name__ == "__main__":
    unittest.main()
