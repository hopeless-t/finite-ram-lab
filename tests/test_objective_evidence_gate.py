from __future__ import annotations

import unittest

from finite_ram_lab.historical_dynamic_replay import strata005_observations
from finite_ram_lab.objective_evidence_gate import (
    EvidenceRole,
    ObjectiveEvidence,
    evaluate_objective_evidence_gate,
)


SUMMARY = {
    "cells": {
        "144": {
            "dontneed_48m": {
                "median_max_scan_memory_bytes": 132747264.0,
                "median_memory_high_events": 0.0,
                "median_pgscan": 0.0,
                "median_scan_elapsed_ns": 79322520.0,
            },
            "dontneed_64m": {
                "median_max_scan_memory_bytes": 149536768.0,
                "median_memory_high_events": 0.0,
                "median_pgscan": 0.0,
                "median_scan_elapsed_ns": 72180360.0,
            },
            "dontneed_80m": {
                "median_max_scan_memory_bytes": 150855680.0,
                "median_memory_high_events": 7.0,
                "median_pgscan": 4096.0,
                "median_scan_elapsed_ns": 42382805.5,
            },
        },
        "176": {
            "dontneed_48m": {
                "median_max_scan_memory_bytes": 132759552.0,
                "median_memory_high_events": 0.0,
                "median_pgscan": 0.0,
                "median_scan_elapsed_ns": 80671924.0,
            },
            "dontneed_64m": {
                "median_max_scan_memory_bytes": 149667840.0,
                "median_memory_high_events": 0.0,
                "median_pgscan": 0.0,
                "median_scan_elapsed_ns": 34930647.5,
            },
            "dontneed_80m": {
                "median_max_scan_memory_bytes": 166313984.0,
                "median_memory_high_events": 0.0,
                "median_pgscan": 0.0,
                "median_scan_elapsed_ns": 63095709.0,
            },
        },
    }
}


class ObjectiveEvidenceGateTests(unittest.TestCase):
    def test_strata005_is_projection_fragile(self):
        result = evaluate_objective_evidence_gate(
            strata005_observations(SUMMARY, 144),
            strata005_observations(SUMMARY, 176),
            (
                ObjectiveEvidence(
                    "peak_ram_bytes",
                    EvidenceRole.PRIMARY,
                    "pressure memory observation",
                ),
                ObjectiveEvidence(
                    "memory_high_events",
                    EvidenceRole.PRIMARY,
                    "frozen primary pressure outcome",
                ),
                ObjectiveEvidence(
                    "pgscan",
                    EvidenceRole.PRIMARY,
                    "pressure/reclaim observation",
                ),
                ObjectiveEvidence(
                    "scan_elapsed_ns",
                    EvidenceRole.DESCRIPTIVE,
                    "hosted timing was frozen as noisy/descriptive",
                ),
            ),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["classification"], "PROJECTION_FRAGILE")
        self.assertEqual(
            result["primary_result"]["lost_frontier_ids"],
            (),
        )
        self.assertEqual(
            result["sensitivity_result"]["lost_frontier_ids"],
            ("dontneed_80m",),
        )

    def test_missing_primary_fails_closed(self):
        result = evaluate_objective_evidence_gate(
            strata005_observations(SUMMARY, 144),
            strata005_observations(SUMMARY, 176),
            (
                ObjectiveEvidence("missing", EvidenceRole.PRIMARY),
                ObjectiveEvidence("scan_elapsed_ns", EvidenceRole.DESCRIPTIVE),
            ),
        )
        self.assertEqual(result["status"], "INSTRUMENTATION_HOLD")
        self.assertEqual(
            result["classification"],
            "PRIMARY_OBJECTIVE_MISSING",
        )

    def test_descriptive_missing_does_not_fail_primary(self):
        result = evaluate_objective_evidence_gate(
            strata005_observations(SUMMARY, 144),
            strata005_observations(SUMMARY, 176),
            (
                ObjectiveEvidence("peak_ram_bytes", EvidenceRole.PRIMARY),
                ObjectiveEvidence("not_recorded", EvidenceRole.DESCRIPTIVE),
            ),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["missing_descriptive_objectives"],
            ("not_recorded",),
        )

    def test_excluded_objective_is_never_added_to_sensitivity_projection(self):
        result = evaluate_objective_evidence_gate(
            strata005_observations(SUMMARY, 144),
            strata005_observations(SUMMARY, 176),
            (
                ObjectiveEvidence("peak_ram_bytes", EvidenceRole.PRIMARY),
                ObjectiveEvidence("scan_elapsed_ns", EvidenceRole.EXCLUDED),
            ),
        )
        self.assertEqual(result["descriptive_objectives_used"], ())
        self.assertEqual(
            result["excluded_objectives"],
            ("scan_elapsed_ns",),
        )


if __name__ == "__main__":
    unittest.main()
