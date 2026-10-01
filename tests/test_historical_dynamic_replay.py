from __future__ import annotations

import unittest

from finite_ram_lab.historical_dynamic_replay import (
    STRATA005_OBJECTIVES,
    ProjectedObservation,
    changed_objectives,
    compare_projected_pair,
    projected_frontier,
    strata005_observations,
)


SUMMARY = {
    "cells": {
        "144": {
            "buffered": {
                "median_max_scan_memory_bytes": 150927360.0,
                "median_memory_high_events": 14.0,
                "median_pgscan": 7680.0,
                "median_scan_elapsed_ns": 119107334.5,
            },
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
            "dontneed_96m": {
                "median_max_scan_memory_bytes": 150857728.0,
                "median_memory_high_events": 14.0,
                "median_pgscan": 7680.0,
                "median_scan_elapsed_ns": 76379837.5,
            },
        },
        "176": {
            "buffered": {
                "median_max_scan_memory_bytes": 181125120.0,
                "median_memory_high_events": 0.0,
                "median_pgscan": 0.0,
                "median_scan_elapsed_ns": 90262944.0,
            },
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
            "dontneed_96m": {
                "median_max_scan_memory_bytes": 181127168.0,
                "median_memory_high_events": 0.0,
                "median_pgscan": 0.0,
                "median_scan_elapsed_ns": 226512842.5,
            },
        },
    }
}


class HistoricalDynamicReplayTests(unittest.TestCase):
    def test_strata005_frontiers(self):
        h144 = strata005_observations(SUMMARY, 144)
        h176 = strata005_observations(SUMMARY, 176)
        self.assertEqual(
            {p.plan_id for p in projected_frontier(h144, STRATA005_OBJECTIVES)},
            {"dontneed_48m", "dontneed_64m", "dontneed_80m"},
        )
        self.assertEqual(
            {p.plan_id for p in projected_frontier(h176, STRATA005_OBJECTIVES)},
            {"dontneed_48m", "dontneed_64m"},
        )

    def test_dontneed_80_is_lost_with_both_cost_shifts(self):
        result = compare_projected_pair(
            strata005_observations(SUMMARY, 144),
            strata005_observations(SUMMARY, 176),
            STRATA005_OBJECTIVES,
        )
        self.assertEqual(result["lost_frontier_ids"], ("dontneed_80m",))
        explanation = result["explanations"][0]
        self.assertEqual(
            explanation["classification"],
            "LOST_WITH_SELF_AND_DOMINATOR_COST_SHIFT",
        )
        self.assertEqual(explanation["dominators"], ("dontneed_64m",))

    def test_dontneed_80_observed_changes_are_exact(self):
        h144 = {p.plan_id: p for p in strata005_observations(SUMMARY, 144)}
        h176 = {p.plan_id: p for p in strata005_observations(SUMMARY, 176)}
        self.assertEqual(
            dict(
                changed_objectives(
                    h144["dontneed_80m"],
                    h176["dontneed_80m"],
                    STRATA005_OBJECTIVES,
                )
            ),
            {
                "peak_ram_bytes": 15458304.0,
                "memory_high_events": -7.0,
                "pgscan": -4096.0,
                "scan_elapsed_ns": 20712903.5,
            },
        )

    def test_dontneed_64_dominator_changes_are_exact(self):
        h144 = {p.plan_id: p for p in strata005_observations(SUMMARY, 144)}
        h176 = {p.plan_id: p for p in strata005_observations(SUMMARY, 176)}
        self.assertEqual(
            dict(
                changed_objectives(
                    h144["dontneed_64m"],
                    h176["dontneed_64m"],
                    STRATA005_OBJECTIVES,
                )
            ),
            {
                "peak_ram_bytes": 131072.0,
                "scan_elapsed_ns": -37249712.5,
            },
        )

    def test_projection_mismatch_fails_closed(self):
        p = ProjectedObservation("p", (("a", 1.0),))
        with self.assertRaisesRegex(ValueError, "objective_projection_mismatch"):
            p.vector(("a", "b"))


if __name__ == "__main__":
    unittest.main()
