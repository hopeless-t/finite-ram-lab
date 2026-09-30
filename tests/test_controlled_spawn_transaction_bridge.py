from __future__ import annotations

import unittest

from finite_ram_lab.controlled_spawn_transaction_bridge import (
    observer_receipt,
    packet_from_touch,
    target_bundle_packet,
    transition_token,
)
from finite_ram_lab.transactional_receipt_adapter import apply_packet
from finite_ram_lab.transactional_reprime import Event, State, Transaction, reduce


def touch(*, cpu: int = 7, worker_error: int = 0, pte: int = 0) -> dict:
    return {
        "observed_cpu": cpu,
        "worker_error": worker_error,
        "vmpte_delta_kib": pte,
    }


class ControlledSpawnTransactionBridgeTests(unittest.TestCase):
    def _normalizing(self) -> Transaction:
        return reduce(Transaction(), Event.ADMIT)

    def _verified(self) -> Transaction:
        tx = self._normalizing()
        packet = packet_from_touch(
            epoch=0,
            phase="NORMALIZE",
            touch_number=1,
            touch=touch(),
            observer=observer_receipt(charge64=1, refill63=1),
            stock_cpu=7,
        )
        return apply_packet(tx, packet)

    def test_masked_q64_release_still_verifies(self) -> None:
        tx = self._normalizing()
        packet = packet_from_touch(
            epoch=0,
            phase="NORMALIZE",
            touch_number=1,
            touch=touch(),
            observer=observer_receipt(
                charge64=1,
                refill63=1,
                releases=1,
            ),
            stock_cpu=7,
        )
        tx = apply_packet(tx, packet)
        self.assertEqual(tx.state, State.VERIFIED)
        self.assertEqual(tx.expected_residual, 63)
        self.assertEqual(tx.release_only_count, 1)

    def test_release_only_consume_preserves_state_and_consumes_once(self) -> None:
        tx = self._verified()
        packet = packet_from_touch(
            epoch=0,
            phase="CONSUME",
            touch_number=2,
            touch=touch(),
            observer=observer_receipt(releases=1),
            stock_cpu=7,
        )
        tx = apply_packet(tx, packet)
        self.assertEqual(tx.state, State.EXECUTING)
        self.assertEqual(tx.expected_residual, 62)
        self.assertEqual(tx.release_only_count, 1)

    def test_unexpected_q64_during_bait_invalidates(self) -> None:
        tx = self._verified()
        packet = packet_from_touch(
            epoch=0,
            phase="CONSUME",
            touch_number=2,
            touch=touch(),
            observer=observer_receipt(charge64=1, refill63=1),
            stock_cpu=7,
        )
        tx = apply_packet(tx, packet)
        self.assertEqual(tx.state, State.INVALIDATED)
        self.assertEqual(tx.invalidation_reason, "UNEXPECTED_REFILL")

    def test_unknown_emission_fails_closed(self) -> None:
        tx = self._normalizing()
        packet = packet_from_touch(
            epoch=0,
            phase="NORMALIZE",
            touch_number=1,
            touch=touch(),
            observer=observer_receipt(unknown=1),
            stock_cpu=7,
        )
        tx = apply_packet(tx, packet)
        self.assertEqual(tx.state, State.INVALIDATED)
        self.assertEqual(tx.invalidation_reason, "TRACE_GAP")

    def test_transition_token_marks_non63_owner_refill_noncanonical(self) -> None:
        self.assertEqual(
            transition_token(observer_receipt(refill_non63=1)),
            "OTHER",
        )

    def test_transition_token_ignores_release_only(self) -> None:
        self.assertEqual(
            transition_token(observer_receipt(releases=1)),
            "ZERO",
        )
        self.assertEqual(
            transition_token(
                observer_receipt(charge64=1, refill63=1, releases=1)
            ),
            "Q64",
        )

    def test_b63_direct_terminal_pattern_matches(self) -> None:
        packet = target_bundle_packet(
            epoch=0,
            arm_id="b63",
            touches=[touch(), touch()],
            observers=[
                observer_receipt(),
                observer_receipt(charge64=1, refill63=1),
            ],
            stock_cpu=7,
            touch_number=65,
        )
        self.assertTrue(packet["target_match"])
        tx = apply_packet(self._verified(), packet)
        self.assertEqual(tx.state, State.COMMIT_READY)
        tx = reduce(tx, Event.COMMIT)
        self.assertEqual(tx.state, State.SUCCESS)

    def test_b62_release_contamination_does_not_break_pattern(self) -> None:
        packet = target_bundle_packet(
            epoch=0,
            arm_id="b62",
            touches=[touch(), touch(), touch()],
            observers=[
                observer_receipt(releases=1),
                observer_receipt(),
                observer_receipt(charge64=1, refill63=1),
            ],
            stock_cpu=7,
            touch_number=66,
        )
        self.assertTrue(packet["target_match"])
        self.assertEqual(packet["classified_release_only_count"], 1)

    def test_early_q64_is_genuine_target_mismatch(self) -> None:
        packet = target_bundle_packet(
            epoch=0,
            arm_id="b63",
            touches=[touch(), touch()],
            observers=[
                observer_receipt(charge64=1, refill63=1),
                observer_receipt(),
            ],
            stock_cpu=7,
            touch_number=65,
        )
        self.assertFalse(packet["target_match"])
        tx = apply_packet(self._verified(), packet)
        self.assertEqual(tx.state, State.TARGET_FAIL)

    def test_partial_terminal_q64_is_trace_gap_not_target_fail(self) -> None:
        packet = target_bundle_packet(
            epoch=0,
            arm_id="b64",
            touches=[touch()],
            observers=[observer_receipt(charge64=1, refill63=0)],
            stock_cpu=7,
            touch_number=64,
        )
        self.assertFalse(packet["trace_complete"])
        self.assertIsNone(packet["target_match"])
        tx = apply_packet(self._verified(), packet)
        self.assertEqual(tx.state, State.INVALIDATED)
        self.assertEqual(tx.invalidation_reason, "TRACE_GAP")

    def test_pte_growth_has_precedence_over_matching_pattern(self) -> None:
        packet = target_bundle_packet(
            epoch=0,
            arm_id="b64",
            touches=[touch(pte=4)],
            observers=[observer_receipt(charge64=1, refill63=1)],
            stock_cpu=7,
            touch_number=64,
        )
        self.assertTrue(packet["target_match"])
        tx = apply_packet(self._verified(), packet)
        self.assertEqual(tx.state, State.INVALIDATED)
        self.assertEqual(tx.invalidation_reason, "PTE_GROWTH")


if __name__ == "__main__":
    unittest.main()
