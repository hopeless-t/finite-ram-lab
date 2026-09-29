from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.transactional_spawn_pilot import (
    ARM_ORDER,
    BAIT_COUNT,
    TARGET_LEN,
    _tag_touch_sequence,
    aggregate,
)


def spec() -> dict:
    return {
        "experiment_id": "TRANSACTIONAL-SPAWN-PILOT-v1",
        "normal_lane": {"raw_identities": 12},
    }


def normal(block: int, identity: int, arm: str, *, state: str = "SUCCESS") -> dict:
    return {
        "experiment_id": "TRANSACTIONAL-SPAWN-PILOT-v1",
        "kind": "NORMAL",
        "block": block,
        "identity": identity,
        "trial_id": f"{block}:{identity}",
        "arm_id": arm,
        "epochs": [
            {
                "epoch": 0,
                "state_after": state,
                "invalidation_reason": None,
            }
        ],
        "archive": {},
        "final_state": state,
        "reprimes": 0,
        "invalidation_reason": None,
        "target_result": "MATCH" if state == "SUCCESS" else None,
    }


def sentinel(*, ok: bool = True) -> dict:
    return {
        "experiment_id": "TRANSACTIONAL-SPAWN-PILOT-v1",
        "kind": "SENTINEL",
        "block": 0,
        "identity": 99,
        "trial_id": "0:99",
        "epochs": [
            {
                "epoch": 0,
                "state_after": "INVALIDATED",
                "invalidation_reason": "UNEXPECTED_REFILL",
            },
            {
                "epoch": 1,
                "state_after": "SUCCESS" if ok else "INVALIDATED",
                "invalidation_reason": None if ok else "TRACE_GAP",
            },
        ],
        "archive": {},
        "epoch0_expected_unexpected_refill": True,
        "epoch1_fresh_q64": ok,
        "final_state": "SUCCESS" if ok else "INVALIDATED",
        "reprimes": 1,
    }


class TransactionalSpawnPilotTests(unittest.TestCase):
    def test_arm_geometry_is_frozen(self) -> None:
        self.assertEqual(ARM_ORDER, ("b62", "b63", "b64"))
        self.assertEqual(BAIT_COUNT, {"b62": 61, "b63": 62, "b64": 63})
        self.assertEqual(TARGET_LEN, {"b62": 3, "b63": 2, "b64": 1})

    def test_touch_sequence_mismatch_becomes_worker_error(self) -> None:
        row = _tag_touch_sequence(
            {"worker_error": 0, "worker_touched": 7},
            8,
        )
        self.assertEqual(row["worker_error"], 9001)
        self.assertEqual(
            row["runner_error"],
            "WORKER_TOUCH_SEQUENCE_MISMATCH",
        )

    def test_complete_12_plus_sentinel_is_protocol_pass(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for block in range(4):
                for identity, arm in enumerate(ARM_ORDER):
                    row = normal(block, identity, arm)
                    (root / f"trial-{block}-{identity}.json").write_text(
                        json.dumps(row),
                        encoding="utf-8",
                    )
            (root / "trial-0-99-sentinel.json").write_text(
                json.dumps(sentinel()),
                encoding="utf-8",
            )

            result = aggregate(spec(), root)

        self.assertEqual(result["normal_count"], 12)
        self.assertEqual(result["normal_success"], 12)
        self.assertEqual(result["sentinel_count"], 1)
        self.assertTrue(result["sentinel_pass"])
        self.assertTrue(result["protocol_smoke_pass"])
        self.assertEqual(result["by_arm"]["b62"]["n"], 4)
        self.assertEqual(result["by_arm"]["b63"]["n"], 4)
        self.assertEqual(result["by_arm"]["b64"]["n"], 4)

    def test_target_fail_prevents_protocol_pass(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for block in range(4):
                for identity, arm in enumerate(ARM_ORDER):
                    state = (
                        "TARGET_FAIL"
                        if block == 2 and identity == 1
                        else "SUCCESS"
                    )
                    row = normal(block, identity, arm, state=state)
                    (root / f"trial-{block}-{identity}.json").write_text(
                        json.dumps(row),
                        encoding="utf-8",
                    )
            (root / "trial-0-99-sentinel.json").write_text(
                json.dumps(sentinel()),
                encoding="utf-8",
            )

            result = aggregate(spec(), root)

        self.assertEqual(result["target_fail"], 1)
        self.assertFalse(result["protocol_smoke_pass"])


if __name__ == "__main__":
    unittest.main()
