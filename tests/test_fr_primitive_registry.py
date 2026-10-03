from __future__ import annotations

import unittest

from finite_ram_lab.fr_primitive_registry import (
    eligible,
    run_panel,
    validate_registry,
)


class FrPrimitiveRegistryTests(
    unittest.TestCase
):
    def test_registry_validates(self):
        validate_registry()

    def test_physical_duplication_query(self):
        rows = eligible(
            failure_domain=(
                "DUPLICATION_HEAVY"
            ),
            min_evidence_class=(
                "HOSTED_PHYSICAL"
            ),
        )

        self.assertEqual(
            [
                row["id"]
                for row in rows
            ],
            [
                "SHARE_IMMUTABLE_MMAP"
            ],
        )

    def test_pagecache_query(self):
        rows = eligible(
            failure_domain=(
                "PAGECACHE_PRESSURE"
            ),
            min_evidence_class=(
                "HOSTED_PHYSICAL"
            ),
        )

        self.assertEqual(
            [
                row["id"]
                for row in rows
            ],
            [
                "RECLAIM_CLEAN_FILE_CACHE"
            ],
        )

    def test_no_live_candidates_yet(self):
        result = run_panel()

        self.assertEqual(
            result[
                "queries"
            ][
                "live_promotion_candidates"
            ],
            [],
        )

    def test_claim_ceiling(self):
        result = run_panel()

        self.assertEqual(
            result[
                "claim_ceiling"
            ],
            "REGISTRY_STRUCTURE_AND_EVIDENCE_ROUTING_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
