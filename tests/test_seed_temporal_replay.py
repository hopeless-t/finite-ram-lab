from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.seed_temporal_replay import (
    PER_TEST_ALPHA,
    run_seed_temporal_replay,
)


def reference_input() -> dict:
    return {
        "schema": "finite-ram-lab.location-shift-input/v0.1",
        "reference_batches": {
            "2": [100,101,102,103,104,105,106,107,108,109,110],
            "4": [200,201,202,203,204,205,206,207,208,209,210],
        },
    }


class SeedTemporalReplayTests(unittest.TestCase):
    def test_temporal_shift_without_seed_effect_is_classified(self):
        counters = {(2,474):0,(2,476):0,(4,474):0,(4,476):0}

        def fake_child(**kwargs):
            q=kwargs["q"]; seed=kwargs["seed"]
            counters[(q,seed)] += 1
            if q == 2:
                peak = 50 + counters[(q,seed)]
            else:
                peak = 200 + counters[(q,seed)]
            return {
                "semantic_exact": True,
                "normalized_peak_growth_bytes": peak,
                "work_seconds": 1.0,
                "output_sha256": f"seed-{seed}",
            }

        with patch(
            "finite_ram_lab.seed_temporal_replay._run_fresh_child",
            side_effect=fake_child,
        ):
            result=run_seed_temporal_replay(reference_input(),size=64)

        q2=next(row for row in result["rows"] if row["q"]==2)
        self.assertEqual(q2["classification"],"TEMPORAL_RUNNER_SHIFT_SUSPECT")
        self.assertLess(q2["temporal_exact_two_sided_p"],PER_TEST_ALPHA)
        self.assertGreater(q2["seed_exact_two_sided_p"],PER_TEST_ALPHA)

    def test_seed_effect_without_temporal_shift_is_classified(self):
        counters={(2,474):0,(2,476):0,(4,474):0,(4,476):0}

        def fake_child(**kwargs):
            q=kwargs["q"]; seed=kwargs["seed"]
            i=counters[(q,seed)]
            counters[(q,seed)] += 1
            base=100 if q==2 else 200
            peak=base+i if seed==474 else base+100+i
            return {
                "semantic_exact": True,
                "normalized_peak_growth_bytes": peak,
                "work_seconds":1.0,
                "output_sha256":f"seed-{seed}",
            }

        with patch(
            "finite_ram_lab.seed_temporal_replay._run_fresh_child",
            side_effect=fake_child,
        ):
            result=run_seed_temporal_replay(reference_input(),size=64)

        q2=next(row for row in result["rows"] if row["q"]==2)
        self.assertEqual(q2["classification"],"WORKLOAD_SEED_EFFECT_SUSPECT")
        self.assertGreater(q2["temporal_exact_two_sided_p"],PER_TEST_ALPHA)
        self.assertLess(q2["seed_exact_two_sided_p"],PER_TEST_ALPHA)

    def test_semantic_failure_blocks_replay(self):
        def fake_child(**kwargs):
            return {
                "semantic_exact": False,
                "normalized_peak_growth_bytes":1,
                "work_seconds":1.0,
                "output_sha256":"bad",
            }

        with patch(
            "finite_ram_lab.seed_temporal_replay._run_fresh_child",
            side_effect=fake_child,
        ):
            with self.assertRaisesRegex(RuntimeError,"semantic_gate_failed"):
                run_seed_temporal_replay(reference_input(),size=64)


if __name__=="__main__":
    unittest.main()
