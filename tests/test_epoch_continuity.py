from __future__ import annotations

import unittest

from finite_ram_lab.epoch_continuity import scan_interwindow_continuity


BASE_PREFIX = """
x-1 [000] ... 10.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=1 PRE
frltx405-10 [007] ... 10.000000010: frl_pc_try64: counter=0xaaa nr_pages=64 comm="frltx405"
frltx405-10 [007] ... 10.000000020: frl_refill_stock: memcg=0xbbb nr_pages=63 comm="frltx405"
x-1 [000] ... 10.000000030: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=1 POST
"""

BASE_SUFFIX = """
x-1 [000] ... 10.001000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=1 PRE
frltx405-10 [007] ... 10.001000010: some_unrelated_event: foo=1
x-1 [000] ... 10.001000020: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=1 POST
"""


def scan(middle: str) -> dict:
    return scan_interwindow_continuity(
        BASE_PREFIX + middle + BASE_SUFFIX,
        trial_id="0:0",
        epoch=0,
        owner_counter="0xaaa",
        owner_memcg="0xbbb",
        stock_cpu=7,
        verified_at_ns=10_000_000_030,
    )


class EpochContinuityTests(unittest.TestCase):
    def test_owner_filter_no_match_drain_is_not_target_state_change(self) -> None:
        result = scan(
            """
softirq-20 [007] ... 10.000500000: frl_drain_stock: stock=0x111 slot=2 comm="frltx405"
"""
        )
        self.assertTrue(result["gap_clean"])
        self.assertEqual(result["other_counter_drain_count"], 1)
        self.assertEqual(result["target_drain_count"], 0)

    def test_owner_counter_gap_drain_is_state_change(self) -> None:
        result = scan(
            """
softirq-20 [007] ... 10.000500000: frl_drain_stock: stock=0x111 slot=2 comm="frltx405"
softirq-20 [007] ... 10.000500010: frl_pc_uncharge_owner: counter=0xaaa nr_pages=21 comm="frltx405"
"""
        )
        self.assertFalse(result["gap_clean"])
        self.assertEqual(result["target_drain_count"], 1)
        self.assertEqual(result["state_change_count"], 1)

    def test_unpaired_stock_cpu_gap_drain_is_other_when_owner_probe_has_no_match(self) -> None:
        result = scan(
            """
softirq-20 [007] ... 10.000500000: frl_drain_stock: stock=0x111 slot=2 comm="frltx405"
"""
        )
        self.assertTrue(result["gap_clean"])
        self.assertEqual(result["other_counter_drain_count"], 1)
        self.assertEqual(result["unresolved_drain_count"], 0)
        self.assertEqual(result["unknown_count"], 0)

    def test_owner_counter_gap_charge64_is_state_change(self) -> None:
        result = scan(
            """
softirq-20 [007] ... 10.000500000: frl_pc_try64: counter=0xaaa nr_pages=64 comm="ksoftirqd"
"""
        )
        self.assertFalse(result["gap_clean"])
        self.assertEqual(result["target_charge64_count"], 1)
        self.assertEqual(result["state_change_count"], 1)

    def test_other_counter_gap_charge64_is_not_target_state_change(self) -> None:
        result = scan(
            """
softirq-20 [007] ... 10.000500000: frl_pc_try64: counter=0xccc nr_pages=64 comm="ksoftirqd"
"""
        )
        self.assertTrue(result["gap_clean"])
        self.assertEqual(result["target_charge64_count"], 0)

    def test_grounded_owner_release_in_gap_is_state_preserving(self) -> None:
        result = scan(
            """
dotnet-20 [007] ... 10.000500000: frl_pc_uncharge_owner: counter=0xaaa nr_pages=17 comm=".NET TP Worker"
 => page_counter_uncharge
 => folios_put_refs
 => folio_batch_move_lru
 => __folio_batch_add_and_move
"""
        )
        self.assertTrue(result["gap_clean"])
        self.assertEqual(result["grounded_release_only_count"], 1)
        self.assertEqual(result["unknown_owner_uncharge_count"], 0)

    def test_ungrounded_owner_uncharge_in_gap_fails_closed(self) -> None:
        result = scan(
            """
dotnet-20 [007] ... 10.000500000: frl_pc_uncharge_owner: counter=0xaaa nr_pages=17 comm=".NET TP Worker"
 => page_counter_uncharge
 => mystery_path
"""
        )
        self.assertFalse(result["gap_clean"])
        self.assertEqual(result["unknown_owner_uncharge_count"], 1)

    def test_owner_uncharge_without_drain_or_release_is_unknown(self) -> None:
        result = scan(
            """
worker-20 [007] ... 10.000500000: frl_pc_uncharge_owner: counter=0xaaa nr_pages=9 comm="worker"
"""
        )
        self.assertFalse(result["gap_clean"])
        self.assertEqual(result["unknown_owner_uncharge_count"], 1)

    def test_tail_gap_after_last_post_is_scanned(self) -> None:
        text = (
            BASE_PREFIX
            + BASE_SUFFIX
            + """
softirq-20 [007] ... 10.002000000: frl_drain_stock: stock=0x111 slot=2 comm="frltx405"
softirq-20 [007] ... 10.002000010: frl_pc_uncharge_owner: counter=0xaaa nr_pages=21 comm="frltx405"
"""
        )
        result = scan_interwindow_continuity(
            text,
            trial_id="0:0",
            epoch=0,
            owner_counter="0xaaa",
            owner_memcg="0xbbb",
            stock_cpu=7,
            verified_at_ns=10_000_000_030,
        )
        self.assertFalse(result["gap_clean"])
        self.assertEqual(result["target_drain_count"], 1)


if __name__ == "__main__":
    unittest.main()
