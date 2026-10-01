from __future__ import annotations

import unittest

from finite_ram_lab.active_experiment_runtime import (
    CandidatePlan,
    DatasetPartition,
    ProbeEnvelope,
    RuntimeConstraints,
    RuntimeMode,
    select_runtime_plan,
)


def plan(
    plan_id: str,
    *,
    strategy: str = "STREAMED_FOLD",
    lanes: int = 7,
    tile_rows: int = 64,
    peak: int = 40,
    latency: float = 1.0,
    useful: float = 1.0,
    info: float = 0.0,
    fidelity: bool = True,
) -> CandidatePlan:
    return CandidatePlan(
        plan_id=plan_id,
        variables=(
            ("lane_count", lanes),
            ("strategy", strategy),
            ("tile_rows", tile_rows),
        ),
        fidelity_gate=fidelity,
        predicted_peak_bytes=peak,
        predicted_latency_seconds=latency,
        useful_work=useful,
        expected_information_gain=info,
    )


class ActiveExperimentRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.baseline = plan("baseline", peak=60, latency=1.0)
        self.constraints = RuntimeConstraints(
            max_peak_bytes=100,
            max_latency_seconds=2.0,
            min_useful_work=0.9,
        )

    def test_observe_never_intervenes(self):
        receipt = select_runtime_plan(
            mode=RuntimeMode.OBSERVE,
            baseline=self.baseline,
            candidates=(self.baseline, plan("other", lanes=5, peak=30)),
            constraints=self.constraints,
        )
        self.assertEqual(receipt.selected_plan_id, "baseline")
        self.assertFalse(receipt.intervention)
        self.assertEqual(receipt.changed_variables, ())
        self.assertIs(receipt.dataset_partition, DatasetPartition.OBSERVATIONAL)

    def test_optimize_chooses_min_peak_subject_to_constraints(self):
        low_peak = plan("low_peak", lanes=5, peak=30, latency=1.4)
        too_slow = plan("too_slow", lanes=3, peak=20, latency=3.0)
        receipt = select_runtime_plan(
            mode=RuntimeMode.OPTIMIZE,
            baseline=self.baseline,
            candidates=(self.baseline, low_peak, too_slow),
            constraints=self.constraints,
        )
        self.assertEqual(receipt.selected_plan_id, "low_peak")
        self.assertIs(receipt.dataset_partition, DatasetPartition.OPTIMIZATION)

    def test_probe_selects_information_per_second_inside_envelope(self):
        lanes5 = plan("lanes5", lanes=5, peak=40, latency=1.0, info=0.9)
        tile32 = plan("tile32", tile_rows=32, peak=42, latency=0.5, info=0.6)
        envelope = ProbeEnvelope(
            allowed_variables=("lane_count", "tile_rows"),
            numeric_bounds=(
                ("lane_count", 3, 7),
                ("tile_rows", 32, 128),
            ),
        )
        receipt = select_runtime_plan(
            mode=RuntimeMode.PROBE,
            baseline=self.baseline,
            candidates=(self.baseline, lanes5, tile32),
            constraints=self.constraints,
            hypothesis_id="H-PROBE",
            probe_envelope=envelope,
        )
        self.assertEqual(receipt.selected_plan_id, "tile32")
        self.assertTrue(receipt.intervention)
        self.assertEqual(receipt.hypothesis_id, "H-PROBE")
        self.assertIs(
            receipt.dataset_partition,
            DatasetPartition.EXPERIMENTAL_INTERVENTION,
        )
        self.assertEqual(
            receipt.changed_variables,
            (("tile_rows", 64, 32),),
        )

    def test_probe_rejects_disallowed_strategy_change(self):
        changed_strategy = plan(
            "other_strategy",
            strategy="ALL_RESIDENT",
            peak=50,
            latency=1.0,
            info=10.0,
        )
        envelope = ProbeEnvelope(
            allowed_variables=("lane_count",),
            numeric_bounds=(("lane_count", 3, 7),),
        )
        with self.assertRaisesRegex(RuntimeError, "no_safe_probe_candidate"):
            select_runtime_plan(
                mode=RuntimeMode.PROBE,
                baseline=self.baseline,
                candidates=(self.baseline, changed_strategy),
                constraints=self.constraints,
                hypothesis_id="H-PROBE",
                probe_envelope=envelope,
            )

    def test_probe_requires_hypothesis(self):
        with self.assertRaisesRegex(ValueError, "probe_hypothesis_required"):
            select_runtime_plan(
                mode=RuntimeMode.PROBE,
                baseline=self.baseline,
                candidates=(self.baseline, plan("lanes5", lanes=5, info=1.0)),
                constraints=self.constraints,
                probe_envelope=ProbeEnvelope(
                    allowed_variables=("lane_count",),
                    numeric_bounds=(("lane_count", 3, 7),),
                ),
            )

    def test_fidelity_fail_candidate_is_not_eligible(self):
        unsafe = plan("unsafe", lanes=5, peak=1, fidelity=False, info=100.0)
        good = plan("good", lanes=6, peak=40, latency=1.0, info=0.5)
        receipt = select_runtime_plan(
            mode=RuntimeMode.OPTIMIZE,
            baseline=self.baseline,
            candidates=(self.baseline, unsafe, good),
            constraints=self.constraints,
        )
        self.assertEqual(receipt.selected_plan_id, "good")


if __name__ == "__main__":
    unittest.main()
