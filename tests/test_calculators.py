import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from finite_ram_lab.calculators import (
    changepoint,
    exact_oracle,
    info_gain,
    prcc,
    qmc_design,
    system_id,
    tail_fit,
)
from finite_ram_lab.sim import opt_faults


class CalculatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_changepoint_finds_known_boundary(self):
        x = np.arange(20, dtype=float)
        y = np.concatenate([
            0.2 * x[:10],
            2 + 2.0 * x[10:],
        ])
        path = self.root / "cp.csv"
        pd.DataFrame({"x": x, "y": y}).to_csv(
            path,
            index=False,
        )
        result = changepoint(
            path,
            {"x": "x", "y": "y", "min_segment": 3},
        )
        self.assertAlmostEqual(
            result["breakpoint"],
            9.5,
        )

    def test_exact_oracle_matches_belady(self):
        trace = [
            1, 2, 3, 1, 4, 1, 2,
            5, 1, 2, 3, 4, 5,
        ]
        path = self.root / "trace.json"
        path.write_text(
            json.dumps({"trace": trace})
        )
        result = exact_oracle(
            path,
            {"capacity": 3},
        )
        self.assertEqual(
            result["misses"],
            opt_faults(trace, 3),
        )

    def test_information_gain_known_one_bit(self):
        path = self.root / "ig.csv"
        pd.DataFrame(
            {
                "os": ["same"] * 4,
                "app": [0, 0, 1, 1],
                "target": [0, 0, 1, 1],
            }
        ).to_csv(path, index=False)
        result = info_gain(
            path,
            {
                "target": "target",
                "observed": ["os"],
                "added": ["app"],
            },
        )
        self.assertAlmostEqual(
            result["information_gain_bits"],
            1.0,
        )

    def test_system_id_recovers_delay(self):
        rng = np.random.default_rng(1)
        n = 120
        u = rng.normal(size=n)
        y = np.zeros(n)
        for t in range(1, n):
            delayed = (
                u[t - 3]
                if t >= 3
                else 0.0
            )
            y[t] = (
                0.4 * y[t - 1]
                + 2.0 * delayed
                + rng.normal(scale=0.01)
            )
        path = self.root / "sys.csv"
        pd.DataFrame(
            {"u": u, "y": y}
        ).to_csv(path, index=False)
        result = system_id(
            path,
            {
                "input": "u",
                "output": "y",
                "max_delay": 6,
            },
        )
        self.assertEqual(
            result["best"]["delay"],
            3,
        )

    def test_qmc_design_is_deterministic(self):
        params = {
            "method": "sobol",
            "n": 8,
            "seed": 42,
            "parameters": [
                {
                    "name": "ram",
                    "min": 128,
                    "max": 512,
                }
            ],
        }
        self.assertEqual(
            qmc_design(params),
            qmc_design(params),
        )

    def test_prcc_ranks_dominant_parameter_first(self):
        rng = np.random.default_rng(2)
        a = rng.normal(size=200)
        b = rng.normal(size=200)
        y = (
            5 * a
            + 0.2 * b
            + rng.normal(scale=0.1, size=200)
        )
        path = self.root / "prcc.csv"
        pd.DataFrame(
            {"a": a, "b": b, "y": y}
        ).to_csv(path, index=False)
        result = prcc(
            path,
            {
                "inputs": ["a", "b"],
                "output": "y",
            },
        )
        self.assertEqual(
            result["ranking"][0]["parameter"],
            "a",
        )

    def test_tail_fit_returns_finite_parameters(self):
        rng = np.random.default_rng(3)
        values = rng.lognormal(
            mean=1.0,
            sigma=0.8,
            size=1000,
        )
        path = self.root / "tail.csv"
        pd.DataFrame(
            {"latency": values}
        ).to_csv(path, index=False)
        result = tail_fit(
            path,
            {
                "value": "latency",
                "threshold_quantile": 0.95,
            },
        )
        self.assertTrue(
            np.isfinite(result["gpd_shape"])
        )
        self.assertTrue(
            np.isfinite(result["gpd_scale"])
        )


if __name__ == "__main__":
    unittest.main()
