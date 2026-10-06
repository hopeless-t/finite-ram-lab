from __future__ import annotations

import unittest

from finite_ram_lab.fr_p9_009_cgroup_quota_replan import (
    MIB,
    derive_quota_bytes,
    resource_certificate,
)


class FrP9009CgroupQuotaReplanTests(unittest.TestCase):
    def test_quota_is_between_n2_and_n4_envelopes(self) -> None:
        n2 = [60 * MIB, 61 * MIB]
        n4 = [95 * MIB, 96 * MIB]
        quota = derive_quota_bytes(n2, n4)
        self.assertGreater(quota, max(n2))
        self.assertLess(quota, min(n4))

    def test_small_separation_fails_closed(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "insufficient_physical_separation"):
            derive_quota_bytes([60 * MIB], [68 * MIB])

    def test_resource_certificate_ignores_no_fields_it_depends_on(self) -> None:
        high = resource_certificate(256 * MIB, 8, 16)
        tight = resource_certificate(80 * MIB, 8, 16)
        changed_workspace = resource_certificate(256 * MIB, 8, 8)
        self.assertNotEqual(high, tight)
        self.assertNotEqual(high, changed_workspace)
        self.assertEqual(high, resource_certificate(256 * MIB, 8, 16))


if __name__ == "__main__":
    unittest.main()
