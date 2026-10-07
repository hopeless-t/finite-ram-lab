from __future__ import annotations

import unittest

from finite_ram_lab.fr_p9_023_prefix_streaming_release import _service_at_deadline


class PrefixStreamingReleaseTests(unittest.TestCase):
    def test_service_trace_at_deadline(self) -> None:
        samples = [(10, 1), (20, 2), (30, 4)]
        self.assertEqual(_service_at_deadline(samples, 0), 0)
        self.assertEqual(_service_at_deadline(samples, 20), 2)
        self.assertEqual(_service_at_deadline(samples, 29), 2)
        self.assertEqual(_service_at_deadline(samples, 30), 4)


if __name__ == "__main__":
    unittest.main()
