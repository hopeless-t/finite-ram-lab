from __future__ import annotations

import unittest

from finite_ram_lab.transaction_epoch_archive import EpochArchive
from finite_ram_lab.transaction_trace_observer import parse_transaction_trace
from finite_ram_lab.transactional_reprime import State


def touch(*, cpu: int = 7, pte: int = 0, worker_error: int = 0) -> dict:
    return {
        "observed_cpu": cpu,
        "vmpte_delta_kib": pte,
        "worker_error": worker_error,
    }


def one_window(
    *,
    trial: str,
    epoch: int,
    phase: str,
    touch_no: int,
    start_s: int,
    events: list[str],
) -> dict:
    lines = [
        (
            f'x-1 [000] ... {start_s}.000000000: tracing_mark_write: '
            f'FRL_TX trial={trial} epoch={epoch} phase={phase} '
            f'touch={touch_no} PRE'
        )
    ]
    for i, event in enumerate(events, start=1):
        lines.append(
            f'worker-10 [007] ... {start_s}.0000000{i:02d}: {event}'
        )
    lines.append(
        (
            f'x-1 [000] ... {start_s}.000000900: tracing_mark_write: '
            f'FRL_TX trial={trial} epoch={epoch} phase={phase} '
            f'touch={touch_no} POST'
        )
    )
    parsed = parse_transaction_trace("\n".join(lines))
    return parsed[(trial, epoch, phase, touch_no)]


class EpochArchiveTests(unittest.TestCase):
    def test_release_only_preserves_epoch_owner_and_residual_math(self) -> None:
        archive = EpochArchive.start(max_reprimes=2)
        normalize = one_window(
            trial="0:0",
            epoch=0,
            phase="NORMALIZE",
            touch_no=1,
            start_s=10,
            events=[
                'frl_pc_try64: counter=0xaaa nr_pages=64 comm="frltx"',
                'frl_refill_stock: memcg=0xbbb nr_pages=63 comm="frltx"',
            ],
        )
        p0 = archive.apply_touch(
            epoch=0,
            phase="NORMALIZE",
            touch_number=1,
            touch=touch(),
            window=normalize,
            stock_cpu=7,
        )
        self.assertEqual(archive.tx.state, State.VERIFIED)
        self.assertEqual(archive.owner_counter, "0xaaa")
        self.assertEqual(p0["elapsed_ns_since_verified"], 0)

        release = one_window(
            trial="0:0",
            epoch=0,
            phase="CONSUME",
            touch_no=2,
            start_s=11,
            events=[
                'frl_lru_flush: nr=31 comm="other"',
                'frl_folios_put: nr=31 comm="other"',
                'frl_pc_uncharge17: counter=0xaaa nr_pages=17 comm="other"',
            ],
        )
        p1 = archive.apply_touch(
            epoch=0,
            phase="CONSUME",
            touch_number=2,
            touch=touch(),
            window=release,
            stock_cpu=7,
        )
        self.assertEqual(archive.tx.state, State.EXECUTING)
        self.assertEqual(archive.tx.expected_residual, 62)
        self.assertEqual(p1["classified_release_only_count"], 1)
        self.assertEqual(p1["expected_residual_before"], 63)
        self.assertEqual(p1["expected_residual_after"], 62)
        self.assertEqual(archive.owner_counter, "0xaaa")

    def test_forced_unexpected_refill_then_hard_reprime_requires_new_owner(self) -> None:
        archive = EpochArchive.start(max_reprimes=2)

        q0 = one_window(
            trial="0:1",
            epoch=0,
            phase="NORMALIZE",
            touch_no=1,
            start_s=20,
            events=[
                'frl_pc_try64: counter=0xaaa nr_pages=64 comm="frltx"',
                'frl_refill_stock: memcg=0x111 nr_pages=63 comm="frltx"',
            ],
        )
        archive.apply_touch(
            epoch=0,
            phase="NORMALIZE",
            touch_number=1,
            touch=touch(),
            window=q0,
            stock_cpu=7,
        )
        self.assertEqual(archive.owner_counter, "0xaaa")

        unexpected = one_window(
            trial="0:1",
            epoch=0,
            phase="CONSUME",
            touch_no=2,
            start_s=21,
            events=[
                'frl_pc_try64: counter=0xaaa nr_pages=64 comm="frltx"',
                'frl_refill_stock: memcg=0x111 nr_pages=63 comm="frltx"',
            ],
        )
        archive.apply_touch(
            epoch=0,
            phase="CONSUME",
            touch_number=2,
            touch=touch(),
            window=unexpected,
            stock_cpu=7,
        )
        self.assertEqual(archive.tx.state, State.INVALIDATED)
        self.assertEqual(archive.tx.invalidation_reason, "UNEXPECTED_REFILL")

        archive.reprime()
        self.assertEqual(archive.tx.state, State.NORMALIZING)
        self.assertEqual(archive.tx.epoch, 1)
        self.assertIsNone(archive.owner_counter)
        self.assertIsNone(archive.verified_at_ns)
        self.assertIsNone(archive.next_touch_index_since_verified)

        with self.assertRaises(ValueError):
            archive.apply_touch(
                epoch=0,
                phase="NORMALIZE",
                touch_number=3,
                touch=touch(),
                window=q0,
                stock_cpu=7,
            )

        q1 = one_window(
            trial="0:1",
            epoch=1,
            phase="NORMALIZE",
            touch_no=1,
            start_s=30,
            events=[
                'frl_pc_try64: counter=0xbbb nr_pages=64 comm="frltx"',
                'frl_refill_stock: memcg=0x222 nr_pages=63 comm="frltx"',
            ],
        )
        archive.apply_touch(
            epoch=1,
            phase="NORMALIZE",
            touch_number=1,
            touch=touch(),
            window=q1,
            stock_cpu=7,
        )
        self.assertEqual(archive.tx.state, State.VERIFIED)
        self.assertEqual(archive.owner_counter, "0xbbb")

        target = one_window(
            trial="0:1",
            epoch=1,
            phase="TARGET",
            touch_no=64,
            start_s=31,
            events=[
                'frl_pc_try64: counter=0xbbb nr_pages=64 comm="frltx"',
                'frl_refill_stock: memcg=0x222 nr_pages=63 comm="frltx"',
            ],
        )
        archive.apply_target_bundle(
            epoch=1,
            arm_id="b64",
            touch_number=64,
            touches=[touch()],
            windows=[target],
            stock_cpu=7,
        )
        self.assertEqual(archive.tx.state, State.COMMIT_READY)
        archive.commit()
        self.assertEqual(archive.tx.state, State.SUCCESS)

        frozen = archive.as_dict()
        self.assertEqual(frozen["reprimes"], 1)
        self.assertEqual(
            frozen["control_events"][0]["mode"],
            "HARD_NEW_WORKER_CGROUP",
        )

    def test_pte_growth_invalidates_before_matching_b64_can_commit(self) -> None:
        archive = EpochArchive.start()
        normalize = one_window(
            trial="0:2",
            epoch=0,
            phase="NORMALIZE",
            touch_no=1,
            start_s=40,
            events=[
                'frl_pc_try64: counter=0xaaa nr_pages=64 comm="frltx"',
                'frl_refill_stock: memcg=0x111 nr_pages=63 comm="frltx"',
            ],
        )
        archive.apply_touch(
            epoch=0,
            phase="NORMALIZE",
            touch_number=1,
            touch=touch(),
            window=normalize,
            stock_cpu=7,
        )

        target = one_window(
            trial="0:2",
            epoch=0,
            phase="TARGET",
            touch_no=64,
            start_s=41,
            events=[
                'frl_pc_try64: counter=0xaaa nr_pages=64 comm="frltx"',
                'frl_refill_stock: memcg=0x111 nr_pages=63 comm="frltx"',
            ],
        )
        packet = archive.apply_target_bundle(
            epoch=0,
            arm_id="b64",
            touch_number=64,
            touches=[touch(pte=4)],
            windows=[target],
            stock_cpu=7,
        )
        self.assertTrue(packet["target_match"])
        self.assertEqual(archive.tx.state, State.INVALIDATED)
        self.assertEqual(archive.tx.invalidation_reason, "PTE_GROWTH")


if __name__ == "__main__":
    unittest.main()
