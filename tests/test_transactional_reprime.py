from __future__ import annotations

import unittest

from finite_ram_lab.transactional_reprime import Event, State, Transaction, reduce


Q64 = {
    "page_counter_try_charge_64": True,
    "refill_stock_63": True,
}


class TransactionalReprimeTests(unittest.TestCase):
    def test_release_only_does_not_invalidate_verified_state(self) -> None:
        tx = Transaction()
        tx = reduce(tx, Event.ADMIT)
        tx = reduce(tx, Event.DIRECT_Q64, Q64)
        tx = reduce(tx, Event.RELEASE_ONLY)
        self.assertEqual(tx.state, State.VERIFIED)
        self.assertEqual(tx.expected_residual, 63)
        self.assertEqual(tx.release_only_count, 1)

    def test_unexpected_refill_invalidates_then_reprime_opens_new_epoch(self) -> None:
        tx = Transaction(max_reprimes=2)
        tx = reduce(tx, Event.ADMIT)
        tx = reduce(tx, Event.DIRECT_Q64, Q64)
        tx = reduce(tx, Event.EXPECTED_CONSUME)
        tx = reduce(tx, Event.UNEXPECTED_REFILL)
        self.assertEqual(tx.state, State.INVALIDATED)
        old_epoch = tx.epoch
        tx = reduce(tx, Event.REPRIME)
        self.assertEqual(tx.state, State.NORMALIZING)
        self.assertEqual(tx.epoch, old_epoch + 1)
        self.assertFalse(tx.direct_q64_seen)

    def test_success_requires_verified_receipt_chain(self) -> None:
        tx = Transaction()
        tx = reduce(tx, Event.ADMIT)
        tx = reduce(tx, Event.DIRECT_Q64, Q64)
        tx = reduce(tx, Event.EXPECTED_CONSUME)
        tx = reduce(tx, Event.TARGET_MATCH)
        tx = reduce(tx, Event.COMMIT)
        self.assertEqual(tx.state, State.SUCCESS)

    def test_target_mismatch_is_failure_only_when_state_is_valid(self) -> None:
        tx = Transaction()
        tx = reduce(tx, Event.ADMIT)
        tx = reduce(tx, Event.DIRECT_Q64, Q64)
        tx = reduce(tx, Event.TARGET_MISMATCH)
        self.assertEqual(tx.state, State.TARGET_FAIL)

    def test_invalidated_attempt_cannot_be_called_target_failure(self) -> None:
        tx = Transaction()
        tx = reduce(tx, Event.ADMIT)
        tx = reduce(tx, Event.DIRECT_Q64, Q64)
        tx = reduce(tx, Event.PTE_GROWTH)
        self.assertEqual(tx.state, State.INVALIDATED)
        with self.assertRaises(ValueError):
            reduce(tx, Event.TARGET_MISMATCH)

    def test_missing_direct_q64_receipt_fails_closed(self) -> None:
        tx = reduce(Transaction(), Event.ADMIT)
        with self.assertRaises(ValueError):
            reduce(
                tx,
                Event.DIRECT_Q64,
                {
                    "page_counter_try_charge_64": True,
                    "refill_stock_63": False,
                },
            )

    def test_reprime_budget_aborts_without_false_failure(self) -> None:
        tx = Transaction(max_reprimes=1)
        tx = reduce(tx, Event.ADMIT)
        tx = reduce(tx, Event.NORMALIZE_EXHAUSTED)
        tx = reduce(tx, Event.REPRIME)
        tx = reduce(tx, Event.NORMALIZE_EXHAUSTED)
        tx = reduce(tx, Event.REPRIME)
        self.assertEqual(tx.state, State.ABORTED)

    def test_memory_current_is_not_an_event(self) -> None:
        self.assertFalse(hasattr(Event, "MEMORY_CURRENT_Q64"))


if __name__ == "__main__":
    unittest.main()
