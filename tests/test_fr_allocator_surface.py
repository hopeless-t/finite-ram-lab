from __future__ import annotations

import unittest

from finite_ram_lab.fr_allocator_surface import (
    block_granularity_panel,
    run_panel,
)


class FrAllocatorSurfaceTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()

    def test_external_fragmentation_dominates_contiguous_rejects(self):
        self.assertGreater(
            self.result[
                "derived"
            ][
                "contiguous_rejects_due_to_external_fragmentation_fraction"
            ],
            0.95,
        )

    def test_paging_improves_admission(self):
        p = self.result[
            "policies"
        ]

        self.assertGreater(
            p["PAGED"]["admitted"],
            p[
                "CONTIG_FIRST_FIT"
            ]["admitted"],
        )

    def test_prefix_sharing_improves_paged_admission(self):
        p = self.result[
            "policies"
        ]

        self.assertGreater(
            p[
                "PAGED_PREFIX_SHARE"
            ]["admitted"],
            p[
                "PAGED"
            ]["admitted"],
        )

    def test_smaller_blocks_reduce_internal_waste(self):
        panel = (
            block_granularity_panel()
        )

        self.assertLess(
            panel["16"][
                "waste_fraction"
            ],
            panel["128"][
                "waste_fraction"
            ],
        )

    def test_claim_ceiling(self):
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SOURCE_GROUNDED_SYNTHETIC_ALLOCATOR_GEOMETRY_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
