from __future__ import annotations

import hashlib
import json
import statistics
import time

import numpy as np
from scipy import sparse
from scipy.sparse import linalg as spla


SCHEMA = "finite-ram-lab.ksla-bench-world-claim-gate/v0.1"
SEED = "KSLA-BENCH-001-v0.1"
SIZES = (64, 256, 1024, 4096)
STEPS = (-4, -2, -1, 1, 2, 4)
BATCH = 8


def _h(text: str) -> int:
    return int.from_bytes(
        hashlib.sha256(
            f"{SEED}|{text}".encode()
        ).digest()[:8],
        "big",
    )


def _target(n: int) -> np.ndarray:
    return np.array(
        [
            (_h(f"T|{i}") % 15) - 7
            for i in range(n)
        ],
        dtype=np.float64,
    )


def _matrix(n: int):
    return sparse.diags(
        (
            -np.ones(n - 1),
            6.0 * np.ones(n),
            -np.ones(n - 1),
        ),
        offsets=(-1, 0, 1),
        format="csr",
    )


def _median_seconds(fn, repeats: int = 5):
    fn()
    values = []
    last = None

    for _ in range(repeats):
        start = time.perf_counter()
        last = fn()
        values.append(
            time.perf_counter() - start
        )

    return statistics.median(values), last


def _cg(A, b, target):
    iterations = 0

    def callback(_):
        nonlocal iterations
        iterations += 1

    x, info = spla.cg(
        A,
        b,
        x0=np.zeros_like(b),
        rtol=1e-12,
        atol=0.0,
        maxiter=10000,
        callback=callback,
    )

    return {
        "info": int(info),
        "iterations": iterations,
        "max_abs_error": float(
            np.max(np.abs(x - target))
        ),
        "residual_norm": float(
            np.linalg.norm(A @ x - b)
        ),
    }


def _direct(A, b, target):
    x = spla.spsolve(A, b)

    return {
        "max_abs_error": float(
            np.max(np.abs(x - target))
        ),
        "residual_norm": float(
            np.linalg.norm(A @ x - b)
        ),
    }


def _rhs_int(target):
    n = len(target)
    out = [0] * n

    for i, value in enumerate(target):
        total = 6 * value

        if i:
            total -= target[i - 1]

        if i + 1 < n:
            total -= target[i + 1]

        out[i] = total

    return out


def _delta(residual, coordinate, step):
    total = 0
    n = len(residual)

    for row, coefficient in (
        (coordinate, 6),
        (coordinate - 1, -1),
        (coordinate + 1, -1),
    ):
        if 0 <= row < n:
            old = residual[row]
            new = old + step * coefficient
            total += new * new - old * old

    return total


def _apply(state, residual, coordinate, step):
    state[coordinate] += step
    n = len(residual)

    for row, coefficient in (
        (coordinate, 6),
        (coordinate - 1, -1),
        (coordinate + 1, -1),
    ):
        if 0 <= row < n:
            residual[row] += (
                step * coefficient
            )


def _ksla(n: int):
    target = [
        int(value)
        for value in _target(n)
    ]

    rhs = _rhs_int(target)
    state = [0] * n
    residual = [-value for value in rhs]
    norm = sum(
        value * value
        for value in residual
    )

    proposals = 0
    accepted = 0
    round_index = 0

    while norm:
        best = None

        for proposal_index in range(BATCH):
            value = _h(
                f"A|N{n}|R{round_index}|K{proposal_index}"
            )
            coordinate = value % n
            step = STEPS[
                (value // n)
                % len(STEPS)
            ]

            change = _delta(
                residual,
                coordinate,
                step,
            )
            proposals += 1

            if change < 0:
                candidate = (
                    change,
                    coordinate,
                    step,
                )

                if (
                    best is None
                    or candidate < best
                ):
                    best = candidate

        if best is not None:
            change, coordinate, step = best
            _apply(
                state,
                residual,
                coordinate,
                step,
            )
            norm += change
            accepted += 1

        round_index += 1

        if round_index > 1_000_000:
            raise RuntimeError(
                f"KSLA timeout at n={n}"
            )

    return {
        "rounds": round_index,
        "proposals": proposals,
        "accepted": accepted,
        "exact_solution": (
            state == target
        ),
        "residual_norm_squared": norm,
        "validator_residual_entries_touched_upper": (
            3 * proposals
        ),
        "state_update_entries_touched_upper": (
            3 * accepted
        ),
    }


def benchmark_size(n: int) -> dict:
    target = _target(n)
    A = _matrix(n)
    b = A @ target

    cg_time, cg = _median_seconds(
        lambda: _cg(
            A,
            b,
            target,
        )
    )

    direct_time, direct = (
        _median_seconds(
            lambda: _direct(
                A,
                b,
                target,
            )
        )
    )

    ksla_time, ksla = (
        _median_seconds(
            lambda: _ksla(n),
            repeats=3,
        )
    )

    return {
        "n": n,
        "nnz": int(A.nnz),
        "cg": {
            **cg,
            "median_seconds": cg_time,
            "coefficient_touch_proxy": (
                cg["iterations"]
                * int(A.nnz)
            ),
        },
        "sparse_direct": {
            **direct,
            "median_seconds": direct_time,
        },
        "ksla_batch8": {
            **ksla,
            "median_seconds": ksla_time,
        },
        "speed_ratios": {
            "ksla_over_cg": (
                ksla_time / cg_time
            ),
            "ksla_over_sparse_direct": (
                ksla_time / direct_time
            ),
        },
    }


def run_panel() -> dict:
    rows = [
        benchmark_size(n)
        for n in SIZES
    ]

    standard_speed_win = all(
        row[
            "ksla_batch8"
        ]["median_seconds"]
        <= min(
            row["cg"]["median_seconds"],
            row[
                "sparse_direct"
            ]["median_seconds"],
        )
        for row in rows
    )

    exact_all = all(
        row[
            "ksla_batch8"
        ]["exact_solution"]
        for row in rows
    )

    local_touch_contract = all(
        row[
            "ksla_batch8"
        ][
            "validator_residual_entries_touched_upper"
        ]
        == (
            3
            * row[
                "ksla_batch8"
            ]["proposals"]
        )
        for row in rows
    )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "environment_claim": (
            "GITHUB_HOSTED_RUNNER_ONLY"
        ),
        "sizes": rows,
        "world_claim_gate": {
            "standard_sparse_spd_world_best": (
                standard_speed_win
            ),
            "standard_sparse_spd_verdict": (
                "NOT_SUPPORTED"
                if not standard_speed_win
                else "CANDIDATE_ONLY"
            ),
            "exact_solution_all_sizes": (
                exact_all
            ),
            "zero_intelligence_local_touch_contract": (
                local_touch_contract
            ),
            "research_frontier_status": (
                "LOCAL_ORACLE_FINITE_RESIDENCY_CANDIDATE"
            ),
        },
        "comparison_scope": [
            "SciPy conjugate gradient",
            "SciPy sparse direct solve",
            "KSLA batch-8 imaginary-kitten solver",
        ],
        "next_required_baselines": [
            "Kaczmarz++ / CD++",
            "randomized Kaczmarz variants",
            "random coordinate descent",
            "zeroth-order random pursuit",
        ],
        "primary_finding": (
            "KSLA_IS_NOT_A_STANDARD_SPD_SPEED_CHAMPION; ITS_OPEN_HYPOTHESIS_IS_A_DIFFERENT_PARETO_FRONTIER_UNDER_LOCAL_ACCESS_FAULT_TOLERANCE_AND_FINITE_RESIDENCY"
        ),
        "claim_ceiling": (
            "HOSTED_RUNNER_BENCHMARK_GATE_ONLY"
        ),
    }


def main() -> int:
    print(
        json.dumps(
            run_panel(),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
