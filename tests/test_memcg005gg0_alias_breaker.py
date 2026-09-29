from __future__ import annotations

import json
import unittest
from collections import defaultdict
from pathlib import Path

from finite_ram_lab.memcg005gg0_alias_breaker import (
    analyze,
    arm_for,
    classify_biopsy,
)


ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads(
    (
        ROOT
        / "specs/MEMCG-005G-G0-MINIMAL-ARGV-PTE-ALIAS-BREAKER-v1.json"
    ).read_text(encoding="utf-8")
)


def row(
    block: int,
    identity: int,
    *,
    zero: bool,
    vmpte_delta: int = 0,
) -> dict:
    arm = arm_for(SPEC, block, identity)
    return {
        "block": block,
        "identity": identity,
        "arm_id": arm["id"],
        "stratum": "LOW",
        "valid": True,
        "zero_capture": zero,
        "first_q64_pass": not zero,
        "first_vmpte_delta_kib": vmpte_delta,
        "biopsy_performed": zero,
        "biopsy_valid": True if zero else None,
        "biopsy_class": "R1_CANDIDATE" if zero else None,
        "cpu_match": True,
    }


class G0AliasBreakerTests(unittest.TestCase):
    def test_arm_balance_and_zero_padding(self) -> None:
        expected = {
            "C8": ("8", 8),
            "P8": ("08", 8),
            "C9": ("9", 9),
            "P9": ("09", 9),
            "H10": ("10", 10),
            "H32": ("32", 32),
        }
        for block in range(SPEC["runner_blocks"]):
            arms = [
                arm_for(SPEC, block, identity)
                for identity in range(
                    SPEC["identities_per_block"]
                )
            ]
            ids = [arm["id"] for arm in arms]
            for arm_id, (token, capacity) in expected.items():
                self.assertEqual(ids.count(arm_id), 10)
                sample = next(
                    arm for arm in arms
                    if arm["id"] == arm_id
                )
                self.assertEqual(sample["token"], token)
                self.assertEqual(
                    sample["capacity_pages"],
                    capacity,
                )

    def _synthetic(
        self,
        zeros_per_block: dict[str, int],
    ) -> list[dict]:
        seen: defaultdict[tuple[int, str], int] = defaultdict(int)
        rows: list[dict] = []
        for block in range(SPEC["runner_blocks"]):
            for identity in range(
                SPEC["identities_per_block"]
            ):
                arm = arm_for(SPEC, block, identity)
                key = (block, arm["id"])
                seen[key] += 1
                zero = (
                    seen[key]
                    <= zeros_per_block[arm["id"]]
                )
                rows.append(
                    row(
                        block,
                        identity,
                        zero=zero,
                    )
                )
        return rows

    def test_argv_like_world_is_identified(self) -> None:
        rows = self._synthetic(
            {
                "C8": 1,
                "C9": 1,
                "P8": 4,
                "P9": 4,
                "H10": 4,
                "H32": 4,
            }
        )
        result = analyze(SPEC, rows)
        self.assertEqual(
            result["interpretation"],
            "ARGV_LIKE_DIRECTION",
        )
        self.assertGreater(
            result["pooled"]["padded_8_9"]["zero_rate"],
            result["pooled"]["canonical_8_9"]["zero_rate"],
        )

    def test_capacity_like_world_is_identified(self) -> None:
        rows = self._synthetic(
            {
                "C8": 1,
                "C9": 1,
                "P8": 1,
                "P9": 1,
                "H10": 4,
                "H32": 4,
            }
        )
        result = analyze(SPEC, rows)
        self.assertEqual(
            result["interpretation"],
            "CAPACITY_LIKE_DIRECTION",
        )
        self.assertGreater(
            result["pooled"]["high_10_32"]["zero_rate"],
            result["pooled"]["padded_8_9"]["zero_rate"],
        )

    def test_biopsy_classifier(self) -> None:
        base = {
            "biopsy_performed": True,
            "biopsy_valid": True,
            "second_q64_pass": True,
            "second_vmpte_delta_kib": 0,
        }
        self.assertEqual(
            classify_biopsy(
                {**base, "first_vmpte_delta_kib": 0}
            ),
            "R1_CANDIDATE",
        )
        self.assertEqual(
            classify_biopsy(
                {**base, "first_vmpte_delta_kib": 4}
            ),
            "R2_CANDIDATE",
        )
        self.assertEqual(
            classify_biopsy(
                {
                    **base,
                    "first_vmpte_delta_kib": 0,
                    "second_vmpte_delta_kib": 4,
                }
            ),
            "PTE_BOUNDARY",
        )


if __name__ == "__main__":
    unittest.main()
