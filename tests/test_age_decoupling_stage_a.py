from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.age_decoupling_stage_a import (
    _classify,
    aggregate,
)
from finite_ram_lab.transaction_epoch_archive import EpochArchive
from finite_ram_lab.transactional_reprime import (
    Event,
    State,
    Transaction,
    reduce,
)


def archive_in_state(
    state: State,
    *,
    invalidation_reason: str | None = None,
) -> EpochArchive:
    archive = EpochArchive.start(max_reprimes=0)
    archive.owner_counter = "0xaaa"
    archive.owner_memcg = "0xbbb"
    archive.verified_at_ns = 100

    if state is State.VERIFIED:
        archive.tx = Transaction(
            state=State.VERIFIED,
            max_reprimes=0,
            expected_residual=63,
            direct_q64_seen=True,
        )
    elif state is State.SUCCESS:
        archive.tx = Transaction(
            state=State.SUCCESS,
            max_reprimes=0,
            expected_residual=1,
            direct_q64_seen=True,
            target_result="MATCH",
        )
    elif state is State.TARGET_FAIL:
        archive.tx = Transaction(
            state=State.TARGET_FAIL,
            max_reprimes=0,
            expected_residual=1,
            direct_q64_seen=True,
            target_result="MISMATCH",
        )
    elif state is State.INVALIDATED:
        archive.tx = Transaction(
            state=State.INVALIDATED,
            max_reprimes=0,
            expected_residual=None,
            direct_q64_seen=True,
            invalidation_reason=invalidation_reason,
        )
    else:
        archive.tx = Transaction(
            state=state,
            max_reprimes=0,
        )
    return archive


CLEAN_CONTINUITY = {
    "gap_clean": True,
    "unknown_count": 0,
    "target_drain_count": 0,
    "target_charge64_count": 0,
    "target_refill_count": 0,
    "target_refill_non63_count": 0,
}


class AgeDecouplingStageATests(unittest.TestCase):
    def test_canonical_success(self) -> None:
        classification, detail = _classify(
            archive=archive_in_state(State.SUCCESS),
            normalized=True,
            coverage_ok=True,
            continuity=CLEAN_CONTINUITY,
            dwell=None,
            first_q64={"T": 64},
            late_scan=None,
        )
        self.assertEqual(classification, "CANONICAL_SUCCESS")
        self.assertIsNone(detail)

    def test_clean_early_boundary_is_unexplained(self) -> None:
        classification, detail = _classify(
            archive=archive_in_state(State.TARGET_FAIL),
            normalized=True,
            coverage_ok=True,
            continuity=CLEAN_CONTINUITY,
            dwell=None,
            first_q64={"T": 63},
            late_scan=None,
        )
        self.assertEqual(
            classification,
            "UNEXPLAINED_BOUNDARY_DEVIATION",
        )
        self.assertEqual(detail, "LATE_OR_EARLY_BOUNDARY")

    def test_clean_canonical_mismatch_is_true_target_fail(self) -> None:
        classification, detail = _classify(
            archive=archive_in_state(State.TARGET_FAIL),
            normalized=True,
            coverage_ok=True,
            continuity=CLEAN_CONTINUITY,
            dwell=None,
            first_q64={"T": 64},
            late_scan=None,
        )
        self.assertEqual(classification, "TRUE_TARGET_FAIL")
        self.assertEqual(
            detail,
            "TARGET_MISMATCH_AT_CANONICAL_T",
        )

    def test_owner_refill1_is_known_state_change(self) -> None:
        continuity = {
            **CLEAN_CONTINUITY,
            "gap_clean": False,
            "target_refill_count": 1,
            "target_refill_non63_count": 1,
        }
        classification, detail = _classify(
            archive=archive_in_state(State.TARGET_FAIL),
            normalized=True,
            coverage_ok=True,
            continuity=continuity,
            dwell=None,
            first_q64={"T": 65},
            late_scan=None,
        )
        self.assertEqual(classification, "KNOWN_STATE_CHANGE")
        self.assertEqual(detail, "OWNER_REFILL_NON63")

    def test_probe_miss_has_precedence(self) -> None:
        classification, detail = _classify(
            archive=archive_in_state(State.SUCCESS),
            normalized=True,
            coverage_ok=False,
            continuity=CLEAN_CONTINUITY,
            dwell=None,
            first_q64={"T": 64},
            late_scan=None,
        )
        self.assertEqual(classification, "INSTRUMENTATION_HOLD")
        self.assertEqual(detail, "CRITICAL_PROBE_MISS")

    def test_aggregate_preserves_stage_b_trigger_policy(self) -> None:
        spec = {
            "experiment_id": "TX-AGE-DECOUPLING-STAGE-A-v2",
            "stage_a": {"total_identities": 2},
            "timing_reference": {
                "nominal_total_exposure_factor": 16
            },
        }
        rows = [
            {
                "trial_id": "0:0",
                "arm": "FAST",
                "classification": "CANONICAL_SUCCESS",
                "T_first_post_primer_direct_q64": 64,
                "elapsed_ns_verified_to_q64": 100,
                "dwell": {"observed_ns": 1},
                "known_hazard_kind": None,
                "critical_probe_coverage_ok": True,
            },
            {
                "trial_id": "0:1",
                "arm": "HOLD32",
                "classification":
                    "UNEXPLAINED_BOUNDARY_DEVIATION",
                "T_first_post_primer_direct_q64": 33,
                "elapsed_ns_verified_to_q64": 1600,
                "dwell": {"observed_ns": 1500},
                "known_hazard_kind": None,
                "critical_probe_coverage_ok": True,
            },
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i, row in enumerate(rows):
                (root / f"trial-{i}.json").write_text(
                    json.dumps(row),
                    encoding="utf-8",
                )
            result = aggregate(spec, root)

        self.assertTrue(result["stage_b_trigger"])
        self.assertFalse(
            result["known_hold_hazard_requires_council"]
        )
        self.assertEqual(result["true_target_fail_count"], 0)

    def test_known_hold_hazard_requires_council_not_stage_b(self) -> None:
        spec = {
            "experiment_id": "TX-AGE-DECOUPLING-STAGE-A-v2",
            "stage_a": {"total_identities": 1},
            "timing_reference": {
                "nominal_total_exposure_factor": 16
            },
        }
        row = {
            "trial_id": "0:0",
            "arm": "HOLD32",
            "classification": "KNOWN_STATE_CHANGE",
            "T_first_post_primer_direct_q64": None,
            "elapsed_ns_verified_to_q64": None,
            "dwell": {"observed_ns": 1500},
            "known_hazard_kind": "TARGET_STOCK_EVICTION",
            "critical_probe_coverage_ok": True,
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "trial-0.json").write_text(
                json.dumps(row),
                encoding="utf-8",
            )
            result = aggregate(spec, root)

        self.assertFalse(result["stage_b_trigger"])
        self.assertTrue(
            result["known_hold_hazard_requires_council"]
        )


if __name__ == "__main__":
    unittest.main()
