#!/usr/bin/env python3
"""Deterministic hysteresis-controller toy.

This is a control-shape probe, not a Linux performance reproduction.
"""

from __future__ import annotations

import json


def run(trace: list[float], low: float, high: float, start: int, nmin: int, nmax: int):
    n = start
    transitions = 0
    history = [n]
    for p in trace:
        old = n
        if p > high:
            n = max(nmin, n - 1)
        elif p <= low:
            n = min(nmax, n + 1)
        if n != old:
            transitions += 1
        history.append(n)
    return transitions, history


def main() -> None:
    # Noisy trace around 3.5%; Linux-shaped deadband should hold,
    # while a single 3.5% threshold chatters.
    trace = [0.034, 0.036, 0.033, 0.037, 0.034, 0.036, 0.033, 0.037]
    hysteresis = run(trace, 0.02, 0.05, 4, 1, 8)
    single = run(trace, 0.035, 0.035, 4, 1, 8)

    assert hysteresis[0] == 0
    assert single[0] > hysteresis[0]

    print(json.dumps({
        "schema": "finite-ram-lab.hysteresis-toy/v0.1",
        "empirical_linux_claim": False,
        "trace": trace,
        "hysteresis_transitions": hysteresis[0],
        "single_threshold_transitions": single[0],
        "status": "STEAL_GOVERNOR_HYSTERESIS_TOY=PASS",
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
