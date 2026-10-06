import unittest

from finite_ram_lab.fr_p9_003_phase_residency import (
    dominates,
    phase_vectors,
    run_synthetic_panel,
    scalar_break_even_gap_seconds,
)


class FrP9003PhaseResidencyTests(unittest.TestCase):
    def test_synthetic_panel_passes(self) -> None:
        panel = run_synthetic_panel()
        self.assertEqual(panel["status"], "PASS")
        self.assertTrue(all(panel["checks"].values()))
        self.assertIsNone(panel["scalar_gain"])

    def test_warm_and_fault_are_typed_pareto_alternatives(self) -> None:
        warm, fault = phase_vectors(
            payload_bytes=8 * 1024 * 1024,
            phase_gap_seconds=1.0,
            warm_resume_latency_ns=1_000_000,
            fault_resume_latency_ns=5_000_000,
        )
        self.assertFalse(dominates(warm, fault))
        self.assertFalse(dominates(fault, warm))
        self.assertGreater(warm.resident_byte_seconds, fault.resident_byte_seconds)
        self.assertLess(warm.requested_transfer_bytes, fault.requested_transfer_bytes)

    def test_break_even_requires_external_resident_price(self) -> None:
        gap = scalar_break_even_gap_seconds(
            payload_bytes=1024,
            warm_resume_latency_ns=100,
            fault_resume_latency_ns=300,
            resident_byte_second_price=0.0,
            transfer_byte_price=1.0,
            latency_ns_price=1.0,
        )
        self.assertIsNone(gap)

    def test_break_even_matches_closed_form(self) -> None:
        gap = scalar_break_even_gap_seconds(
            payload_bytes=100,
            warm_resume_latency_ns=10,
            fault_resume_latency_ns=30,
            resident_byte_second_price=2.0,
            transfer_byte_price=3.0,
            latency_ns_price=4.0,
        )
        self.assertEqual(gap, (3.0 * 100 + 4.0 * 20) / (2.0 * 100))

    def test_invalid_gap_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            phase_vectors(
                payload_bytes=1024,
                phase_gap_seconds=0.0,
                warm_resume_latency_ns=1,
                fault_resume_latency_ns=2,
            )


if __name__ == "__main__":
    unittest.main()
