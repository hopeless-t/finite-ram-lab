from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.fr_p9_013_compressed_reconstruction_external_validity import (
    MIB,
    _reconstruct_capability,
    _stride_work,
    _write_compressed_source,
    break_even_ms_per_mib,
)


class CompressedReconstructionExternalValidityTests(unittest.TestCase):
    def test_compressed_source_roundtrips_to_runtime_capability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capability.gz"
            digest, compressed_bytes = _write_compressed_source(path, 1 * MIB)
            capability, restored = _reconstruct_capability(
                path,
                payload_bytes=1 * MIB,
                expected_digest=digest,
            )
            try:
                self.assertEqual(restored, 1 * MIB)
                self.assertLess(compressed_bytes, (1 * MIB) // 16)
            finally:
                capability.close()

    def test_strided_arithmetic_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capability.gz"
            digest, _ = _write_compressed_source(path, 1 * MIB)
            capability, _ = _reconstruct_capability(
                path,
                payload_bytes=1 * MIB,
                expected_digest=digest,
            )
            try:
                a = _stride_work(capability, transition=3, rounds=2)
                b = _stride_work(capability, transition=3, rounds=2)
                c = _stride_work(capability, transition=4, rounds=2)
                self.assertEqual(a, b)
                self.assertNotEqual(a, c)
            finally:
                capability.close()

    def test_break_even_price_requires_real_tradeoff(self) -> None:
        warm = {"memory_peak_bytes": 40 * MIB, "reconstruct_ns_total": 10_000_000}
        fault = {"memory_peak_bytes": 24 * MIB, "reconstruct_ns_total": 42_000_000}
        self.assertAlmostEqual(break_even_ms_per_mib(warm, fault), 2.0)

        with self.assertRaises(ValueError):
            break_even_ms_per_mib(
                warm,
                {"memory_peak_bytes": 41 * MIB, "reconstruct_ns_total": 42_000_000},
            )

        with self.assertRaises(ValueError):
            break_even_ms_per_mib(
                warm,
                {"memory_peak_bytes": 24 * MIB, "reconstruct_ns_total": 9_000_000},
            )


if __name__ == "__main__":
    unittest.main()
