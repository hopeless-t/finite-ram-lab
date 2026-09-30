from __future__ import annotations

import unittest

from finite_ram_lab.transactional_receipt_adapter import apply_packet
from finite_ram_lab.transactional_reprime import Event, State, Transaction, reduce


def packet(
    *,
    epoch: int = 0,
    phase: str,
    charge64: int = 0,
    refill63: int = 0,
    releases: int = 0,
    drain: int = 0,
    pte: int = 0,
    cpu: bool = True,
    worker: bool = True,
    trace: bool = True,
    target_match: bool | None = None,
    refill_non63: int = 0,
) -> dict:
    return {
        "schema_version": "transaction-receipt-packet-v1",
        "epoch": epoch,
        "phase": phase,
        "touch": 1,
        "trace_complete": trace,
        "cpu_match": cpu,
        "worker_ok": worker,
        "vmpte_delta_kib": pte,
        "page_counter_try_charge_64_count": charge64,
        "refill_stock_63_count": refill63,
        "owner_refill_non63_count": refill_non63,
        "drain_stock_count": drain,
        "classified_release_only_count": releases,
        "target_match": target_match,
    }


class ReceiptAdapterTests(unittest.TestCase):
    def _normalizing(self) -> Transaction:
        return reduce(Transaction(), Event.ADMIT)

    def test_masked_q64_plus_release_opens_verified_state(self) -> None:
        tx = apply_packet(
            self._normalizing(),
            packet(
                phase="NORMALIZE",
                charge64=1,
                refill63=1,
                releases=1,
            ),
        )
        self.assertEqual(tx.state, State.VERIFIED)
        self.assertEqual(tx.expected_residual, 63)
        self.assertEqual(tx.release_only_count, 1)

    def test_release_plus_consume_decrements_only_once(self) -> None:
        tx = apply_packet(
            self._normalizing(),
            packet(phase="NORMALIZE", charge64=1, refill63=1),
        )
        tx = apply_packet(
            tx,
            packet(phase="CONSUME", releases=1),
        )
        self.assertEqual(tx.state, State.EXECUTING)
        self.assertEqual(tx.expected_residual, 62)
        self.assertEqual(tx.release_only_count, 1)

    def test_partial_q64_pair_fails_closed(self) -> None:
        tx = apply_packet(
            self._normalizing(),
            packet(phase="NORMALIZE", charge64=1, refill63=0),
        )
        self.assertEqual(tx.state, State.INVALIDATED)
        self.assertEqual(tx.invalidation_reason, "TRACE_GAP")

    def test_drain_has_precedence_over_target_match(self) -> None:
        tx = apply_packet(
            self._normalizing(),
            packet(phase="NORMALIZE", charge64=1, refill63=1),
        )
        tx = apply_packet(
            tx,
            packet(phase="TARGET", drain=1, target_match=True),
        )
        self.assertEqual(tx.state, State.INVALIDATED)

    def test_valid_target_mismatch_remains_visible(self) -> None:
        tx = apply_packet(
            self._normalizing(),
            packet(phase="NORMALIZE", charge64=1, refill63=1),
        )
        tx = apply_packet(
            tx,
            packet(phase="TARGET", target_match=False),
        )
        self.assertEqual(tx.state, State.TARGET_FAIL)

    def test_owner_non63_refill_invalidates_verified_consume(self) -> None:
        tx = apply_packet(
            self._normalizing(),
            packet(phase="NORMALIZE", charge64=1, refill63=1),
        )
        tx = apply_packet(
            tx,
            packet(phase="CONSUME", refill_non63=1),
        )
        self.assertEqual(tx.state, State.INVALIDATED)
        self.assertEqual(tx.invalidation_reason, "UNEXPECTED_REFILL")

    def test_stale_epoch_cannot_authorize_current_state(self) -> None:
        tx = self._normalizing()
        tx = reduce(tx, Event.NORMALIZE_EXHAUSTED)
        tx = reduce(tx, Event.REPRIME)
        with self.assertRaises(ValueError):
            apply_packet(
                tx,
                packet(
                    epoch=0,
                    phase="NORMALIZE",
                    charge64=1,
                    refill63=1,
                ),
            )


if __name__ == "__main__":
    unittest.main()
