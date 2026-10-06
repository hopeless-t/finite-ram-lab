from __future__ import annotations

import unittest

from finite_ram_lab.fr_p9_009_cgroup_quota_replan import MIB
from finite_ram_lab.fr_p9_010_phase_overlap_residency import derive_overlap_quota_bytes


class PhaseOverlapQuotaTests(unittest.TestCase):
    def test_derived_quota_sits_between_fault_and_warm_peaks(self) -> None:
        fault = [64 * MIB, 65 * MIB]
        warm = [96 * MIB, 97 * MIB]
        quota = derive_overlap_quota_bytes(fault, warm)
        self.assertGreater(quota, max(fault))
        self.assertLess(quota, min(warm))

    def test_missing_calibration_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            derive_overlap_quota_bytes([], [96 * MIB])

    def test_insufficient_overlap_separation_fails_closed(self) -> None:
        with self.assertRaises(RuntimeError):
            derive_overlap_quota_bytes([64 * MIB], [70 * MIB])

    def test_quota_is_deterministic_for_frozen_peaks(self) -> None:
        fault = [64 * MIB, 65 * MIB]
        warm = [96 * MIB, 97 * MIB]
        self.assertEqual(
            derive_overlap_quota_bytes(fault, warm),
            derive_overlap_quota_bytes(list(reversed(fault)), list(reversed(warm))),
        )


if __name__ == "__main__":
    unittest.main()
