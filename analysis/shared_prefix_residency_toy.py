#!/usr/bin/env python3
"""Logical shared-prefix residency model.

No inference engine is loaded. This is an idealized accounting bound.
"""

from __future__ import annotations

import json


def savings(n: int, prefix: int, suffix: int) -> float:
    if n <= 0 or prefix < 0 or suffix < 0:
        raise ValueError
    naive = n * (prefix + suffix)
    shared = prefix + n * suffix
    return 1.0 - shared / naive


def main() -> None:
    rows = []
    for n in (1, 2, 4, 8, 16):
        s = savings(n, 8000, 2000)
        rows.append({"sessions": n, "logical_savings": round(s, 12)})
    assert rows[0]["logical_savings"] == 0.0
    assert abs(rows[1]["logical_savings"] - 0.4) < 1e-12
    assert abs(rows[2]["logical_savings"] - 0.6) < 1e-12
    assert abs(rows[3]["logical_savings"] - 0.7) < 1e-12
    assert abs(rows[4]["logical_savings"] - 0.75) < 1e-12
    print(json.dumps({
        "schema": "finite-ram-lab.shared-prefix-residency-toy/v0.1",
        "empirical_engine_claim": False,
        "prefix": 8000,
        "suffix": 2000,
        "rows": rows,
        "status": "SHARED_PREFIX_RESIDENCY_TOY=PASS",
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
