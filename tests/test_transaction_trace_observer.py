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
        self.assertEqual(p0["elapsed_ns_since_verified"], 0)
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


    def test_off_cpu_drain_does_not_invalidate_target_stock(self) -> None:
        trace = """
x-1 [000] ... 15.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=5 PRE
python-1 [000] ... 15.000000010: frl_drain_stock: stock=0x111 slot=2 comm="python"
x-1 [000] ... 15.000000020: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=5 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "CONSUME", 5)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter="0xaaa",
            stock_cpu=7,
            phase="CONSUME",
        )
        self.assertEqual(receipt["drain_stock_count"], 0)
        self.assertEqual(receipt["off_cpu_drain_stock_count"], 1)

    def test_stock_cpu_consume_drain_remains_invalidating(self) -> None:
        trace = """
x-1 [000] ... 16.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=6 PRE
kworker-4 [007] ... 16.000000010: frl_drain_stock: stock=0x111 slot=2 comm="kworker"
kworker-4 [007] ... 16.000000011: frl_memcg_uncharge: memcg=0xbbb nr_pages=21 comm="kworker"
x-1 [000] ... 16.000000020: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=6 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "CONSUME", 6)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter="0xaaa",
            owner_memcg="0xbbb",
            stock_cpu=7,
            phase="CONSUME",
        )
        self.assertEqual(receipt["drain_stock_count"], 1)
        self.assertEqual(receipt["off_cpu_drain_stock_count"], 0)

    def test_normalize_internal_slot_drain_is_not_new_residual_loss(self) -> None:
        trace = """
x-1 [000] ... 17.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=1 PRE
frltx-10 [007] ... 17.000000010: frl_pc_try64: counter=0xaaa nr_pages=64 comm="frltx"
frltx-10 [007] ... 17.000000020: frl_drain_stock: stock=0x111 slot=3 comm="frltx"
frltx-10 [007] ... 17.000000021: frl_memcg_uncharge: memcg=0xccc nr_pages=9 comm="frltx"
frltx-10 [007] ... 17.000000030: frl_refill_stock: memcg=0xbbb nr_pages=63 comm="frltx"
x-1 [000] ... 17.000000040: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=1 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "NORMALIZE", 1)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter=None,
            stock_cpu=7,
            phase="NORMALIZE",
        )
        self.assertEqual(receipt["drain_stock_count"], 0)
        self.assertEqual(receipt["normalization_internal_drain_count"], 1)
        self.assertEqual(receipt["other_memcg_drain_count"], 0)
        self.assertEqual(receipt["unresolved_drain_count"], 0)
        self.assertEqual(receipt["discovered_owner_counter"], "0xaaa")
        self.assertEqual(receipt["discovered_owner_memcg"], "0xbbb")

    def test_owner_release_can_be_grounded_by_uncharge_stack(self) -> None:
        trace = """
x-1 [000] ... 18.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=12 PRE
dotnet-20 [002] ... 18.000000010: frl_pc_uncharge17: counter=0xaaa nr_pages=17 comm=".NET TP Worker"
 => page_counter_uncharge
 => folios_put_refs
 => folio_batch_move_lru
 => __folio_batch_add_and_move
x-1 [000] ... 18.000000020: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=12 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "CONSUME", 12)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter="0xaaa",
            stock_cpu=7,
            phase="CONSUME",
        )
        self.assertEqual(receipt["classified_release_only_count"], 1)
        self.assertEqual(receipt["unknown_emission_count"], 0)


    def test_same_cpu_other_memcg_drain_is_not_target_invalidator(self) -> None:
        trace = """
x-1 [000] ... 19.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=13 PRE
softirq-10 [007] ... 19.000000010: frl_drain_stock: stock=0x111 slot=2 comm="frltx405"
softirq-10 [007] ... 19.000000011: frl_memcg_uncharge: memcg=0xccc nr_pages=21 comm="frltx405"
x-1 [000] ... 19.000000020: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=13 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "CONSUME", 13)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter="0xaaa",
            owner_memcg="0xbbb",
            stock_cpu=7,
            phase="CONSUME",
        )
        self.assertEqual(receipt["drain_stock_count"], 0)
        self.assertEqual(receipt["other_memcg_drain_count"], 1)
        self.assertEqual(receipt["unknown_emission_count"], 0)

    def test_unpaired_same_cpu_drain_fails_closed_as_unknown(self) -> None:
        trace = """
x-1 [000] ... 20.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=14 PRE
softirq-10 [007] ... 20.000000010: frl_drain_stock: stock=0x111 slot=2 comm="frltx405"
x-1 [000] ... 20.000000020: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=14 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "CONSUME", 14)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter="0xaaa",
            owner_memcg="0xbbb",
            stock_cpu=7,
            phase="CONSUME",
        )
        self.assertEqual(receipt["drain_stock_count"], 0)
        self.assertEqual(receipt["unresolved_drain_count"], 1)
        self.assertEqual(receipt["unknown_emission_count"], 1)



    def test_all_counter_probe_can_ground_17_page_release(self) -> None:
        trace = """
x-1 [000] ... 21.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=15 PRE
worker-20 [007] ... 21.000000010: frl_pc_uncharge_owner: counter=0xaaa nr_pages=17 comm="worker"
 => page_counter_uncharge
 => folios_put_refs
 => folio_batch_move_lru
 => __folio_batch_add_and_move
x-1 [000] ... 21.000000020: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=15 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "CONSUME", 15)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter="0xaaa",
            owner_memcg="0xbbb",
            stock_cpu=7,
            phase="CONSUME",
        )
        self.assertEqual(len(w["pc_uncharge_any"]), 1)
        self.assertEqual(len(w["pc_uncharge17"]), 1)
        self.assertEqual(receipt["classified_release_only_count"], 1)
        self.assertEqual(receipt["unknown_emission_count"], 0)


    def test_global_q64_noise_is_projected_away_from_target_receipt(self) -> None:
        trace = """
x-1 [000] ... 22.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=1 PRE
bg-20 [003] ... 22.000000005: frl_pc_try64: counter=0xccc nr_pages=64 comm="background"
frltx-10 [007] ... 22.000000010: frl_pc_try64: counter=0xaaa nr_pages=64 comm="frltx405"
frltx-10 [007] ... 22.000000020: frl_refill_stock: memcg=0xbbb nr_pages=63 comm="frltx405"
x-1 [000] ... 22.000000030: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=1 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "NORMALIZE", 1)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter=None,
            owner_memcg=None,
            stock_cpu=7,
            phase="NORMALIZE",
        )
        self.assertEqual(receipt["page_counter_try_charge_64_count"], 1)
        self.assertEqual(receipt["refill_stock_63_count"], 1)
        self.assertEqual(receipt["discovered_owner_counter"], "0xaaa")
        self.assertEqual(receipt["discovered_owner_memcg"], "0xbbb")

    def test_verified_owner_filters_background_q64_in_consume_window(self) -> None:
        trace = """
x-1 [000] ... 23.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=2 PRE
bg-20 [003] ... 23.000000005: frl_pc_try64: counter=0xccc nr_pages=64 comm="background"
x-1 [000] ... 23.000000030: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=2 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "CONSUME", 2)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter="0xaaa",
            owner_memcg="0xbbb",
            stock_cpu=7,
            phase="CONSUME",
        )
        self.assertEqual(receipt["page_counter_try_charge_64_count"], 0)
        self.assertEqual(receipt["refill_stock_63_count"], 0)


    def test_target_comm_filters_background_q64_before_owner_exists(self) -> None:
        trace = """
x-1 [000] ... 24.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=7 PRE
python-20 [000] ... 24.000000010: frl_pc_try64: counter=0xccc nr_pages=64 comm="python"
python-20 [000] ... 24.000000020: frl_pc_try64: counter=0xddd nr_pages=64 comm="python"
x-1 [000] ... 24.000000030: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=7 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "NORMALIZE", 7)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter=None,
            owner_memcg=None,
            stock_cpu=7,
            phase="NORMALIZE",
            target_comm="frltx405",
        )
        self.assertEqual(receipt["page_counter_try_charge_64_count"], 0)
        self.assertEqual(receipt["refill_stock_63_count"], 0)
        self.assertIsNone(receipt["discovered_owner_counter"])


    def test_owner_filtered_drain_match_is_target_invalidator(self) -> None:
        trace = """
x-1 [000] ... 25.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=9 PRE
worker-20 [007] ... 25.000000010: frl_drain_stock: stock=0x111 slot=2 comm="worker"
worker-20 [007] ... 25.000000011: frl_pc_uncharge_owner: counter=0xaaa nr_pages=38 comm="worker"
x-1 [000] ... 25.000000020: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=9 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "CONSUME", 9)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter="0xaaa",
            owner_memcg="0xbbb",
            stock_cpu=7,
            phase="CONSUME",
            owner_probe_filtered=True,
        )
        self.assertEqual(receipt["drain_stock_count"], 1)
        self.assertEqual(receipt["other_memcg_drain_count"], 0)
        self.assertEqual(receipt["unknown_emission_count"], 0)

    def test_owner_filtered_no_match_marks_drain_other_stock(self) -> None:
        trace = """
x-1 [000] ... 26.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=10 PRE
worker-20 [007] ... 26.000000010: frl_drain_stock: stock=0x111 slot=3 comm="worker"
x-1 [000] ... 26.000000020: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=10 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "CONSUME", 10)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter="0xaaa",
            owner_memcg="0xbbb",
            stock_cpu=7,
            phase="CONSUME",
            owner_probe_filtered=True,
        )
        self.assertEqual(receipt["drain_stock_count"], 0)
        self.assertEqual(receipt["other_memcg_drain_count"], 1)
        self.assertEqual(receipt["unresolved_drain_count"], 0)
        self.assertEqual(receipt["unknown_emission_count"], 0)


    def test_owner_stack_detects_target_drain_when_drain_probe_is_missing(self) -> None:
        trace = """
x-1 [000] ... 27.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=11 PRE
worker-20 [007] ... 27.000000010: frl_pc_uncharge_owner: counter=0xaaa nr_pages=38 comm="worker"
 => page_counter_uncharge
 => memcg_uncharge
 => drain_stock
x-1 [000] ... 27.000000020: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=CONSUME touch=11 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "CONSUME", 11)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter="0xaaa",
            owner_memcg="0xbbb",
            stock_cpu=7,
            phase="CONSUME",
            owner_probe_filtered=True,
        )
        self.assertEqual(receipt["drain_stock_count"], 1)
        self.assertEqual(receipt["unknown_emission_count"], 0)
        self.assertEqual(
            receipt["target_drain_events"][0]["ownership"],
            "OWNER_STACK_DRAIN_STOCK",
        )


    def test_one_owner_uncharge_is_not_reused_for_two_drains(self) -> None:
        trace = """
x-1 [000] ... 27.500000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=OBSERVE touch=99 PRE
helper-20 [007] ... 27.500000010: frl_drain_stock: stock=0x111 slot=6 comm="systemd"
helper-20 [007] ... 27.500000020: frl_drain_stock: stock=0x111 slot=1 comm="systemd"
helper-20 [007] ... 27.500000021: frl_pc_uncharge_owner: counter=0xaaa nr_pages=31 comm="systemd"
 => page_counter_uncharge
 => drain_stock
x-1 [000] ... 27.500000030: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=OBSERVE touch=99 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "OBSERVE", 99)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter="0xaaa",
            owner_memcg="0xbbb",
            stock_cpu=7,
            phase="OBSERVE",
            owner_probe_filtered=True,
        )
        self.assertEqual(receipt["drain_stock_count"], 1)
        self.assertEqual(receipt["other_memcg_drain_count"], 1)
        event = receipt["target_drain_events"][0]
        self.assertIn("slot=1", event["line"])
        self.assertEqual(
            event["paired_page_counter_uncharge"]["nr_pages"],
            31,
        )


    def test_owner_refill_any_retains_small_verified_refill(self) -> None:
        trace = """
x-1 [000] ... 28.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=OBSERVE touch=1 PRE
systemd-1 [007] ... 28.000000010: frl_refill_stock: memcg=0xbbb nr_pages=1 comm="systemd"
x-1 [000] ... 28.000000020: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=OBSERVE touch=1 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "OBSERVE", 1)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter="0xaaa",
            owner_memcg="0xbbb",
            stock_cpu=7,
            phase="OBSERVE",
        )
        self.assertEqual(len(w["refill_any"]), 1)
        self.assertEqual(receipt["owner_refill_any_count"], 1)
        self.assertEqual(receipt["owner_refill_non63_count"], 1)
        self.assertEqual(receipt["refill_stock_63_count"], 0)

    def test_off_cpu_owner_refill_does_not_change_target_stock_cpu(self) -> None:
        trace = """
x-1 [000] ... 29.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=OBSERVE touch=2 PRE
systemd-1 [003] ... 29.000000010: frl_refill_stock: memcg=0xbbb nr_pages=1 comm="systemd"
x-1 [000] ... 29.000000020: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=OBSERVE touch=2 POST
"""
        w = parse_transaction_trace(trace)[("0:0", 0, "OBSERVE", 2)]
        receipt = observer_receipt_for_window(
            w,
            owner_counter="0xaaa",
            owner_memcg="0xbbb",
            stock_cpu=7,
            phase="OBSERVE",
        )
        self.assertEqual(receipt["owner_refill_any_count"], 0)
        self.assertEqual(receipt["off_cpu_owner_refill_count"], 1)

if __name__ == "__main__":
    unittest.main()
