from __future__ import annotations

import unittest

from finite_ram_lab.fr_meta_010_episode_template_cache import run_panel


class EpisodeTemplateCacheTests(unittest.TestCase):
    def test_panel(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["decision"],
            "CACHE_IMMUTABLE_EPISODE_TEMPLATE_COPY_PER_POLICY",
        )
        self.assertEqual(result["baseline_template_builds"], 3072)
        self.assertEqual(result["candidate_template_builds"], 512)
        self.assertGreaterEqual(result["structural_reduction_fraction"], 5 / 6)


if __name__ == "__main__":
    unittest.main()
