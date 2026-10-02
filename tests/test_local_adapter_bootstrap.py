from __future__ import annotations

import unittest

from finite_ram_lab.local_adapter_bootstrap import (
    FINGERPRINT_SCHEMA,
    build_local_bootstrap_plan,
    fingerprint_sha256,
    minimum_samples_for_rank_max_coverage,
)


def fingerprint() -> dict:
    return {
        "schema": FINGERPRINT_SCHEMA,
        "system": "Linux",
        "kernel_release": "test-kernel",
        "machine": "x86_64",
        "python_version": "3.12.0",
        "page_size_bytes": 4096,
        "cpu_model": "test-cpu",
        "mem_total": "16384000 kB",
        "libc": {"name": "glibc", "version": "2.39"},
        "cgroup_v2_present": True,
    }


class LocalAdapterBootstrapTests(unittest.TestCase):
    def test_95_percent_target_requires_n19(self):
        self.assertEqual(minimum_samples_for_rank_max_coverage(0.95), 19)

    def test_bootstrap_restores_all_four_q_candidates(self):
        plan = build_local_bootstrap_plan(
            target_coverage=0.95,
            exploration_samples_per_q=8,
            fingerprint=fingerprint(),
        )
        self.assertEqual(plan["candidate_q"], [1,2,4,7])
        self.assertFalse(plan["hosted_threshold_import_allowed"])
        self.assertEqual(
            plan["initial_exploration"]["physical_observations"],
            32,
        )
        self.assertEqual(
            plan["promotion_target"]["required_sample_count_per_promoted_q"],
            19,
        )
        self.assertEqual(
            plan["promotion_target"][
                "additional_samples_after_exploration_per_promoted_q"
            ],
            11,
        )

    def test_fingerprint_digest_is_deterministic(self):
        first = fingerprint_sha256(fingerprint())
        second = fingerprint_sha256(dict(reversed(list(fingerprint().items()))))
        self.assertEqual(first, second)

    def test_plan_contains_no_hosted_breakpoints(self):
        plan = build_local_bootstrap_plan(
            fingerprint=fingerprint(),
        )
        encoded = str(plan)
        for hosted in ("50696192","58941440","71512064"):
            self.assertNotIn(hosted, encoded)
        self.assertEqual(
            plan["promotion_target"]["pareto_q"],
            "UNKNOWN_UNTIL_LOCAL_EXPLORATION",
        )


if __name__=="__main__":
    unittest.main()
