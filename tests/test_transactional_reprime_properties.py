from __future__ import annotations

import unittest

from finite_ram_lab.transactional_reprime import (
    Event,
    INVALIDATING_EVENTS,
    State,
    Transaction,
    reduce,
)


Q64 = {
    "page_counter_try_charge_64": True,
    "refill_stock_63": True,
}


class TransactionalReprimePropertyTests(unittest.TestCase):
    def _verified(self) -> Transaction:
        tx = reduce(Transaction(max_reprimes=2), Event.ADMIT)
        return reduce(tx, Event.DIRECT_Q64, Q64)

    def test_every_invalidator_blocks_success_in_current_epoch(self) -> None:
        for event in INVALIDATING_EVENTS:
            with self.subTest(event=event):
                tx = self._verified()
                tx = reduce(tx, Event.EXPECTED_CONSUME)
                epoch = tx.epoch
                tx = reduce(tx, event)
                self.assertEqual(tx.state, State.INVALIDATED)
                self.assertEqual(tx.epoch, epoch)
                for forbidden in (Event.TARGET_MATCH, Event.TARGET_MISMATCH, Event.COMMIT):
                    with self.assertRaises(ValueError):
                        reduce(tx, forbidden)

    def test_reprime_requires_fresh_q64_before_success(self) -> None:
        for event in INVALIDATING_EVENTS:
            with self.subTest(event=event):
                tx = self._verified()
                tx = reduce(tx, event)
                tx = reduce(tx, Event.REPRIME)
                self.assertEqual(tx.state, State.NORMALIZING)
                self.assertFalse(tx.direct_q64_seen)
                with self.assertRaises(ValueError):
                    reduce(tx, Event.TARGET_MATCH)

                tx = reduce(tx, Event.DIRECT_Q64, Q64)
                tx = reduce(tx, Event.TARGET_MATCH)
                tx = reduce(tx, Event.COMMIT)
                self.assertEqual(tx.state, State.SUCCESS)
                self.assertEqual(tx.epoch, 1)

    def test_release_only_is_orthogonal_to_stock_residual(self) -> None:
        tx = self._verified()
        before = tx.expected_residual
        for _ in range(50):
            tx = reduce(tx, Event.RELEASE_ONLY)
        self.assertEqual(tx.state, State.VERIFIED)
        self.assertEqual(tx.expected_residual, before)
        self.assertEqual(tx.release_only_count, 50)

    def test_valid_target_mismatch_is_terminal_and_not_reprimed(self) -> None:
        tx = self._verified()
        tx = reduce(tx, Event.EXPECTED_CONSUME)
        tx = reduce(tx, Event.TARGET_MISMATCH)
        self.assertEqual(tx.state, State.TARGET_FAIL)
        with self.assertRaises(ValueError):
            reduce(tx, Event.REPRIME)

    def test_abort_is_no_result_not_target_fail(self) -> None:
        tx = Transaction(max_reprimes=0)
        tx = reduce(tx, Event.ADMIT)
        tx = reduce(tx, Event.NORMALIZE_EXHAUSTED)
        tx = reduce(tx, Event.REPRIME)
        self.assertEqual(tx.state, State.ABORTED)
        self.assertNotEqual(tx.state, State.TARGET_FAIL)


if __name__ == "__main__":
    unittest.main()
