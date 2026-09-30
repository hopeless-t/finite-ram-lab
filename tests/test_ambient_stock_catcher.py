from __future__ import annotations

import random
import unittest

from finite_ram_lab.ambient_stock_catcher import (
    AmbientObservation,
    CLASSIFICATIONS,
    classify_ambient_stock,
)


def base(**overrides):
    values = {
        "normalized": True,
        "initial_residual": 31,
        "ambient_target_touch_count": 0,
        "ambient_owner_q64_count": 0,
        "trace_complete": True,
        "worker_ok": True,
        "cpu_stable": True,
        "pte_stable": True,
        "critical_probe_missed": {
            "consume": 0,
            "refill": 0,
            "drain": 0,
            "uncharge": 0,
            "q64": 0,
        },
        "hist_dropped": 0,
        "owner_refill_pages": 0,
        "owner_consume_pages": 0,
        "target_drain_pages": 0,
        "owner_uncharge_pages": 0,
        "boundary_observed": True,
        "final_boundary_T": 64,
    }
    values.update(overrides)
    return AmbientObservation(**values)


class AmbientStockClassifierTests(unittest.TestCase):
    def test_stable_residual(self):
        result = classify_ambient_stock(base())
        self.assertEqual(result["classification"], "STABLE_RESIDUAL")
        self.assertEqual(result["boundary_delta"], 0)
        self.assertFalse(result["exact_mechanistic_fingerprint"])

    def test_exact_drain31_t33_fingerprint(self):
        result = classify_ambient_stock(base(
            target_drain_pages=31,
            owner_uncharge_pages=31,
            final_boundary_T=33,
        ))
        self.assertEqual(
            result["classification"],
            "DIRECT_SLOT_EVICTION_FINGERPRINT",
        )
        self.assertEqual(result["predicted_boundary_T"], 33)
        self.assertEqual(result["boundary_delta"], -31)
        self.assertTrue(result["exact_mechanistic_fingerprint"])

    def test_drain_needs_matching_owner_uncharge(self):
        result = classify_ambient_stock(base(
            target_drain_pages=31,
            owner_uncharge_pages=0,
            final_boundary_T=33,
        ))
        self.assertEqual(result["classification"], "UNKNOWN_COMPLETE")
        self.assertFalse(result["exact_mechanistic_fingerprint"])

    def test_exact_consume31_t33_fingerprint(self):
        result = classify_ambient_stock(base(
            owner_consume_pages=31,
            final_boundary_T=33,
        ))
        self.assertEqual(
            result["classification"],
            "DIRECT_STOCK_CONSUMPTION_FINGERPRINT",
        )
        self.assertEqual(result["predicted_boundary_T"], 33)
        self.assertTrue(result["exact_mechanistic_fingerprint"])

    def test_consume_receipt_without_boundary_match_stays_unknown(self):
        result = classify_ambient_stock(base(
            owner_consume_pages=31,
            final_boundary_T=64,
        ))
        self.assertEqual(result["classification"], "UNKNOWN_COMPLETE")

    def test_unattributed_owner_uncharge_preserved(self):
        result = classify_ambient_stock(base(
            owner_uncharge_pages=31,
            final_boundary_T=33,
        ))
        self.assertEqual(
            result["classification"],
            "UNATTRIBUTED_OWNER_UNCHARGE",
        )

    def test_refill_is_not_promoted_to_simple_causal_fingerprint(self):
        result = classify_ambient_stock(base(
            owner_refill_pages=1,
            final_boundary_T=65,
        ))
        self.assertEqual(result["classification"], "REFILL_MUTATION_PRESENT")
        self.assertFalse(result["exact_mechanistic_fingerprint"])

    def test_multiple_mechanisms_stay_multi_path(self):
        result = classify_ambient_stock(base(
            owner_consume_pages=3,
            owner_refill_pages=2,
            final_boundary_T=63,
        ))
        self.assertEqual(result["classification"], "MULTI_PATH_TRANSITION")

    def test_probe_miss_forces_hold_before_scientific_classification(self):
        result = classify_ambient_stock(base(
            critical_probe_missed={
                "consume": 1,
                "refill": 0,
                "drain": 0,
                "uncharge": 0,
                "q64": 0,
            }
        ))
        self.assertEqual(result["classification"], "INSTRUMENTATION_HOLD")

    def test_ambient_target_touch_contaminates_canary(self):
        result = classify_ambient_stock(base(ambient_target_touch_count=1))
        self.assertEqual(result["classification"], "CANARY_CONTAMINATED")

    def test_ambient_owner_q64_blocks_simple_boundary_arithmetic(self):
        result = classify_ambient_stock(base(
            ambient_owner_q64_count=1,
            owner_consume_pages=31,
            final_boundary_T=64,
        ))
        self.assertEqual(result["classification"], "AMBIENT_Q64_RESET")
        self.assertFalse(result["exact_mechanistic_fingerprint"])

    def test_censored_boundary_is_not_failure(self):
        result = classify_ambient_stock(base(
            boundary_observed=False,
            final_boundary_T=None,
        ))
        self.assertEqual(result["classification"], "BOUNDARY_CENSORED")
        self.assertEqual(result["claim_ceiling"], "COMPLETE_BUT_NONPROMOTED")

    def test_invalid_verify_state_holds(self):
        result = classify_ambient_stock(base(initial_residual=30))
        self.assertEqual(result["classification"], "PREVERIFY_HOLD")


class AmbientStockClassifierFuzzTests(unittest.TestCase):
    def test_deterministic_50000_case_fuzz(self):
        rng = random.Random(0)
        probes = ("consume", "refill", "drain", "uncharge", "q64")

        for _ in range(50_000):
            boundary = bool(rng.randrange(2))
            observation = base(
                normalized=bool(rng.randrange(2)),
                initial_residual=rng.randint(0, 40),
                ambient_target_touch_count=rng.randint(0, 2),
                trace_complete=bool(rng.randrange(2)),
                worker_ok=bool(rng.randrange(2)),
                cpu_stable=bool(rng.randrange(2)),
                pte_stable=bool(rng.randrange(2)),
                critical_probe_missed={
                    name: rng.choice((0, 0, 0, 1, None))
                    for name in probes
                },
                hist_dropped=rng.randint(0, 1),
                owner_refill_pages=rng.randint(0, 35),
                owner_consume_pages=rng.randint(0, 35),
                target_drain_pages=rng.randint(0, 35),
                owner_uncharge_pages=rng.randint(0, 35),
                boundary_observed=boundary,
                final_boundary_T=(rng.randint(1, 100) if boundary else None),
            )
            result = classify_ambient_stock(observation)
            self.assertIn(result["classification"], CLASSIFICATIONS)
            if result["exact_mechanistic_fingerprint"]:
                self.assertIn(
                    result["classification"],
                    {
                        "DIRECT_SLOT_EVICTION_FINGERPRINT",
                        "DIRECT_STOCK_CONSUMPTION_FINGERPRINT",
                    },
                )


if __name__ == "__main__":
    unittest.main()
