#!/usr/bin/env python3
"""Deterministic toy model for a finite context working-set optimum.

Research-only. This script does not model a real CLM or claim empirical thresholds.
It exists to make the intake note's mathematical example reproducible.
"""

from __future__ import annotations

import json
import math


LAMBDAS = (0.005, 0.010, 0.020, 0.040)
K_MAX = 64


def utility(k: int) -> float:
    return 1.0 - math.exp(-k / 8.0)


def cost(k: int, lam: float) -> float:
    return lam * k + 0.6 * (k / K_MAX) ** 2


def objective(k: int, lam: float) -> float:
    return utility(k) - cost(k, lam)


def best_for(lam: float) -> dict[str, float | int]:
    rows = [(k, objective(k, lam)) for k in range(K_MAX + 1)]
    k, score = max(rows, key=lambda row: row[1])
    return {
        "lambda": lam,
        "best_k": k,
        "objective": round(score, 12),
        "utility": round(utility(k), 12),
        "cost": round(cost(k, lam), 12),
    }


def main() -> None:
    results = [best_for(lam) for lam in LAMBDAS]
    expected = [20, 17, 13, 9]
    observed = [int(row["best_k"]) for row in results]
    assert observed == expected, (observed, expected)
    assert all(
        observed[i] >= observed[i + 1] for i in range(len(observed) - 1)
    ), observed

    print(
        json.dumps(
            {
                "schema": "finite-ram-lab.clm-working-set-toy/v0.1",
                "empirical_claim": False,
                "model": {
                    "utility": "1-exp(-k/8)",
                    "cost": "lambda*k + 0.6*(k/64)^2",
                    "k_domain": [0, K_MAX],
                },
                "results": results,
                "status": "CLM_WORKING_SET_TOY=PASS",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
