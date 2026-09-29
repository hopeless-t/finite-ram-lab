from __future__ import annotations

import unittest

from finite_ram_lab.controlled_spawn_transaction_bridge import packet_from_touch
from finite_ram_lab.transaction_trace_observer import (
    apply_and_enrich_v2,
    direct_q64_owner_counter,
    observer_receipt_for_window,
    parse_transaction_trace,
    window_trace_complete,
)
from finite_ram_lab.transactional_reprime import Event, State, Transaction, reduce


def touch(*, cpu: int = 7, pte: int = 0, worker_error: int = 0) -> dict:
    return {
        "observed_cpu": cpu,
        "vmpte_delta_kib": pte,
        "worker_error": worker_error,
    }


class TransactionTraceObserverTests(unittest.TestCase):
    def test_direct_q64_discovers_epoch_owner_counter(self) -> None:
        trace = """
x-1 [000] ... 10.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=1 PRE
frltx-10 [007] ... 10.000000010: frl_pc_try64: counter=0xaaa nr_pages=64 comm="frltx"
frltx-10 [007] ... 10.000000020: frl_refill_stock: memcg=0xbbb nr_pages=63 comm="frltx"
x-1 [000] ... 10.000000030: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=1 POST
"""
        windows = parse_transaction_trace(trace)
        w = windows[("0:0", 0, "NORMALIZE", 1)]
        self.assertTrue(window_trace_complete(w))
        self.assertEqual(direct_q64_owner_counter(w), "0xaaa")
        receipt = observer_receipt_for_window(w, owner_counter=None)
        self.assertEqual(receipt["page_counter_try_charge_64_count"], 1)
        self.assertEqual(receipt["refill_stock_63_count"], 1)
        self.assertEqual(receipt["owner_counter"], "0xaaa")
        self.assertEqual(receipt["unknown_emission_count"], 0)

    def test_release_only_uses_carried_epoch_owner(self) -> None:
        trace = """
x-1 [000] ... 11.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=9 PRE
other-20 [007] ... 11.000000010: frl_lru_flush: nr=31 comm="other"
other-20 [007] ... 11.000000020: frl_folios_put: nr=31 comm="other"
other-20 [007] ... 11.000000030: frl_pc_uncharge17: counter=0xaaa nr_pages=17 comm="other"
x-1 [000] ... 11.000000040: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=9 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "CONSUME", 9)]
        receipt = observer_receipt_for_window(w, owner_counter="0xaaa")
        self.assertEqual(receipt["classified_release_only_count"], 1)
        self.assertEqual(receipt["unknown_emission_count"], 0)
        self.assertEqual(receipt["page_counter_try_charge_64_count"], 0)
        self.assertEqual(receipt["refill_stock_63_count"], 0)

    def test_owner_uncharge_without_lru_signature_fails_closed(self) -> None:
        trace = """
x-1 [000] ... 12.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=2 PRE
other-20 [007] ... 12.000000010: frl_pc_uncharge17: counter=0xaaa nr_pages=17 comm="other"
x-1 [000] ... 12.000000020: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=2 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "CONSUME", 2)]
        receipt = observer_receipt_for_window(w, owner_counter="0xaaa")
        self.assertEqual(receipt["classified_release_only_count"], 0)
        self.assertEqual(receipt["unknown_emission_count"], 1)

    def test_unrelated_counter_uncharge_is_not_target_release(self) -> None:
        trace = """
x-1 [000] ... 13.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=3 PRE
other-20 [007] ... 13.000000010: frl_lru_flush: nr=31 comm="other"
other-20 [007] ... 13.000000020: frl_folios_put: nr=31 comm="other"
other-20 [007] ... 13.000000030: frl_pc_uncharge17: counter=0xdef nr_pages=17 comm="other"
x-1 [000] ... 13.000000040: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=3 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "CONSUME", 3)]
        receipt = observer_receipt_for_window(w, owner_counter="0xaaa")
        self.assertEqual(receipt["classified_release_only_count"], 0)
        self.assertEqual(receipt["unknown_emission_count"], 0)

    def test_unmatched_marker_makes_trace_incomplete(self) -> None:
        trace = """
x-1 [000] ... 14.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=4 PRE
frltx-10 [007] ... 14.000000010: frl_pc_try64: counter=0xaaa nr_pages=64 comm="frltx"
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "CONSUME", 4)]
        self.assertFalse(window_trace_complete(w))

    def test_v2_archive_tracks_residual_and_state_age(self) -> None:
        tx = reduce(Transaction(max_reprimes=2), Event.ADMIT)

        normalize_observer = {
            "trace_complete": True,
            "page_counter_try_charge_64_count": 1,
            "refill_stock_63_count": 1,
            "drain_stock_count": 0,
            "classified_release_only_count": 0,
            "unknown_emission_count": 0,
        }
        normalize = packet_from_touch(
            epoch=0,
            phase="NORMALIZE",
            touch_number=1,
            touch=touch(),
            observer=normalize_observer,
            stock_cpu=7,
        )
        tx, p0, verified_at, next_index = apply_and_enrich_v2(
            tx,
            normalize,
            owner_counter="0xaaa",
            marker_pre_ns=100,
            marker_post_ns=120,
            verified_at_ns=None,
            touch_index_since_verified=None,
        )
        self.assertEqual(tx.state, State.VERIFIED)
        self.assertEqual(p0["expected_residual_before"], None)
        self.assertEqual(p0["expected_residual_after"], 63)
        self.assertEqual(p0["touch_index_since_verified"], 0)
        self.assertEqual(verified_at, 120)
        self.assertEqual(next_index, 1)

        consume_observer = {
            "trace_complete": True,
            "page_counter_try_charge_64_count": 0,
            "refill_stock_63_count": 0,
            "drain_stock_count": 0,
            "classified_release_only_count": 1,
            "unknown_emission_count": 0,
        }
        consume = packet_from_touch(
            epoch=0,
            phase="CONSUME",
            touch_number=2,
            touch=touch(),
            observer=consume_observer,
            stock_cpu=7,
        )
        tx, p1, verified_at, next_index = apply_and_enrich_v2(
            tx,
            consume,
            owner_counter="0xaaa",
            marker_pre_ns=170,
            marker_post_ns=190,
            verified_at_ns=verified_at,
            touch_index_since_verified=next_index,
        )
        self.assertEqual(tx.state, State.EXECUTING)
        self.assertEqual(p1["expected_residual_before"], 63)
        self.assertEqual(p1["expected_residual_after"], 62)
        self.assertEqual(p1["touch_index_since_verified"], 1)
        self.assertEqual(p1["elapsed_ns_since_verified"], 50)
        self.assertEqual(next_index, 2)

    def test_unknown_emission_is_reflected_in_v2_packet(self) -> None:
        tx = reduce(Transaction(), Event.ADMIT)
        base = packet_from_touch(
            epoch=0,
            phase="NORMALIZE",
            touch_number=1,
            touch=touch(),
            observer={
                "trace_complete": False,
                "page_counter_try_charge_64_count": 0,
                "refill_stock_63_count": 0,
                "drain_stock_count": 0,
                "classified_release_only_count": 0,
                "unknown_emission_count": 1,
            },
            stock_cpu=7,
        )
        tx, packet, _, _ = apply_and_enrich_v2(
            tx,
            base,
            owner_counter=None,
            marker_pre_ns=200,
            marker_post_ns=210,
            verified_at_ns=None,
            touch_index_since_verified=None,
            unknown_emission_count=1,
        )
        self.assertEqual(tx.state, State.INVALIDATED)
        self.assertEqual(packet["unknown_emission_count"], 1)
        self.assertFalse(packet["trace_complete"])


if __name__ == "__main__":
    unittest.main()
