from __future__ import annotations

import unittest

from finite_ram_lab.strata001_probe import classify


SPEC = {
    "prepare": {"require_precache_fraction_le": 0.10},
    "capability_checks": {
        "buffered_postcache_fraction_ge": 0.50,
        "mmap_postcache_fraction_ge": 0.50,
        "direct_postcache_fraction_le": 0.10,
    },
}


def arm(pre: float, post: float, *, direct: bool = False, error=None, err_no=None):
    return {
        "expected_bytes": 16,
        "pre": {"resident_fraction": pre},
        "post": {"resident_fraction": post},
        "scan": {
            "logical_span_bytes": 16 if error is None else 0,
            "direct_io": direct,
            "error": error,
            "errno": err_no,
        },
    }


class Strata001ProbeTests(unittest.TestCase):
    def test_pass_shape(self) -> None:
        arms = {
            "mmap": arm(0.0, 1.0),
            "buffered_pread": arm(0.0, 1.0),
            "direct_pread": arm(0.0, 0.0, direct=True),
        }
        status, checks = classify(SPEC, arms)
        self.assertEqual(status, "PASS")
        self.assertTrue(all(checks.values()))

    def test_warm_input_is_invalid(self) -> None:
        arms = {
            "mmap": arm(0.2, 1.0),
            "buffered_pread": arm(0.0, 1.0),
            "direct_pread": arm(0.0, 0.0, direct=True),
        }
        status, _ = classify(SPEC, arms)
        self.assertEqual(status, "INVALID")

    def test_unsupported_direct_io_is_hold(self) -> None:
        import errno

        arms = {
            "mmap": arm(0.0, 1.0),
            "buffered_pread": arm(0.0, 1.0),
            "direct_pread": arm(
                0.0,
                0.0,
                direct=True,
                error="OSError: unsupported",
                err_no=errno.EINVAL,
            ),
        }
        status, _ = classify(SPEC, arms)
        self.assertEqual(status, "CAPABILITY_HOLD")

    def test_direct_cache_pollution_fails_capability(self) -> None:
        arms = {
            "mmap": arm(0.0, 1.0),
            "buffered_pread": arm(0.0, 1.0),
            "direct_pread": arm(0.0, 0.8, direct=True),
        }
        status, checks = classify(SPEC, arms)
        self.assertEqual(status, "FAIL")
        self.assertFalse(checks["direct_does_not_materially_populate_page_cache"])


if __name__ == "__main__":
    unittest.main()
