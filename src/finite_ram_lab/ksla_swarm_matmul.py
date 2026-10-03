from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass


SCHEMA = "finite-ram-lab.ksla-swarm-verified-matmul/v0.1"
SEED = "KSLA-001-v0.1"
PRIME = 65537

MICRO_N = 24
MICRO_GRID = 4
MICRO_BLOCK = MICRO_N // MICRO_GRID
VERIFIER_ROUNDS = 2

FAULT_TASKS = (
    (0, 0, 3),
    (1, 2, 3),
    (2, 3, 1),
    (3, 1, 2),
)

MODEL_N = 4096
MODEL_GRID = 16
MODEL_WORKERS = MODEL_GRID**3
MODEL_FAULT_RATE = 0.01


@dataclass(frozen=True)
class Task:
    row_block: int
    inner_block: int
    col_block: int


def _hash_int(domain: str) -> int:
    return int.from_bytes(
        hashlib.sha256(
            f"{SEED}|{domain}".encode("utf-8")
        ).digest()[:8],
        "big",
    )


def _matrix(label: str, n: int) -> list[list[int]]:
    return [
        [
            _hash_int(
                f"{label}|{row}|{col}"
            )
            % PRIME
            for col in range(n)
        ]
        for row in range(n)
    ]


def _tile(
    matrix: list[list[int]],
    row_block: int,
    col_block: int,
    block: int,
) -> list[list[int]]:
    row_start = row_block * block
    col_start = col_block * block

    return [
        row[
            col_start : col_start + block
        ]
        for row in matrix[
            row_start : row_start + block
        ]
    ]


def _zeros(
    rows: int,
    cols: int,
) -> list[list[int]]:
    return [
        [0 for _ in range(cols)]
        for _ in range(rows)
    ]


def _matmul_mod(
    left: list[list[int]],
    right: list[list[int]],
) -> list[list[int]]:
    rows = len(left)
    inner = len(right)
    cols = len(right[0])

    output = _zeros(rows, cols)

    for i in range(rows):
        for k in range(inner):
            left_value = left[i][k]

            for j in range(cols):
                output[i][j] = (
                    output[i][j]
                    + left_value
                    * right[k][j]
                ) % PRIME

    return output


def _matvec_mod(
    matrix: list[list[int]],
    vector: list[int],
) -> list[int]:
    return [
        sum(
            value * vector[col]
            for col, value
            in enumerate(row)
        )
        % PRIME
        for row in matrix
    ]


def _random_field_vector(
    length: int,
    *,
    domain: str,
    round_index: int,
) -> list[int]:
    vector = [
        _hash_int(
            f"VECTOR|{domain}|{round_index}|{index}"
        )
        % PRIME
        for index in range(length)
    ]

    if not any(vector):
        vector[0] = 1

    return vector


def _freivalds(
    left: list[list[int]],
    right: list[list[int]],
    candidate: list[list[int]],
    *,
    domain: str,
    rounds: int = VERIFIER_ROUNDS,
) -> bool:
    vector_length = len(right[0])

    for round_index in range(rounds):
        vector = _random_field_vector(
            vector_length,
            domain=domain,
            round_index=round_index,
        )

        right_vector = _matvec_mod(
            right,
            vector,
        )

        lhs = _matvec_mod(
            left,
            right_vector,
        )

        rhs = _matvec_mod(
            candidate,
            vector,
        )

        if lhs != rhs:
            return False

    return True


def _task_contribution(
    left: list[list[int]],
    right: list[list[int]],
    task: Task,
    *,
    inject_fault: bool,
) -> list[list[int]]:
    left_tile = _tile(
        left,
        task.row_block,
        task.inner_block,
        MICRO_BLOCK,
    )

    right_tile = _tile(
        right,
        task.inner_block,
        task.col_block,
        MICRO_BLOCK,
    )

    contribution = _matmul_mod(
        left_tile,
        right_tile,
    )

    if (
        inject_fault
        and (
            task.row_block,
            task.inner_block,
            task.col_block,
        )
        in FAULT_TASKS
    ):
        contribution[0][0] = (
            contribution[0][0] + 1
        ) % PRIME

    return contribution


def _all_tasks() -> list[Task]:
    return [
        Task(i, k, j)
        for i in range(MICRO_GRID)
        for k in range(MICRO_GRID)
        for j in range(MICRO_GRID)
    ]


def _aggregate(
    task_outputs: dict[Task, list[list[int]]],
) -> list[list[int]]:
    output = _zeros(
        MICRO_N,
        MICRO_N,
    )

    for task, contribution in (
        task_outputs.items()
    ):
        row_start = (
            task.row_block
            * MICRO_BLOCK
        )

        col_start = (
            task.col_block
            * MICRO_BLOCK
        )

        for i in range(MICRO_BLOCK):
            for j in range(MICRO_BLOCK):
                output[
                    row_start + i
                ][
                    col_start + j
                ] = (
                    output[
                        row_start + i
                    ][
                        col_start + j
                    ]
                    + contribution[i][j]
                ) % PRIME

    return output


def _verify_task(
    left: list[list[int]],
    right: list[list[int]],
    task: Task,
    contribution: list[list[int]],
) -> bool:
    left_tile = _tile(
        left,
        task.row_block,
        task.inner_block,
        MICRO_BLOCK,
    )

    right_tile = _tile(
        right,
        task.inner_block,
        task.col_block,
        MICRO_BLOCK,
    )

    return _freivalds(
        left_tile,
        right_tile,
        contribution,
        domain=(
            f"TASK|{task.row_block}|"
            f"{task.inner_block}|"
            f"{task.col_block}"
        ),
    )


def _full_exact(
    left: list[list[int]],
    right: list[list[int]],
) -> list[list[int]]:
    return _matmul_mod(
        left,
        right,
    )


def _micro_panel() -> dict:
    left = _matrix(
        "A",
        MICRO_N,
    )

    right = _matrix(
        "B",
        MICRO_N,
    )

    exact = _full_exact(
        left,
        right,
    )

    weak_outputs = {
        task: _task_contribution(
            left,
            right,
            task,
            inject_fault=True,
        )
        for task in _all_tasks()
    }

    unverified = _aggregate(
        weak_outputs
    )

    initial_global_check = (
        _freivalds(
            left,
            right,
            unverified,
            domain="GLOBAL|INITIAL",
        )
    )

    flagged = [
        task
        for task, contribution
        in weak_outputs.items()
        if not _verify_task(
            left,
            right,
            task,
            contribution,
        )
    ]

    repaired_outputs = dict(
        weak_outputs
    )

    for task in flagged:
        repaired_outputs[task] = (
            _task_contribution(
                left,
                right,
                task,
                inject_fault=False,
            )
        )

    repaired = _aggregate(
        repaired_outputs
    )

    final_global_check = _freivalds(
        left,
        right,
        repaired,
        domain="GLOBAL|FINAL",
    )

    expected_faults = [
        Task(*triple)
        for triple in FAULT_TASKS
    ]

    if unverified == exact:
        raise RuntimeError(
            "fault_injection_failed"
        )

    if initial_global_check:
        raise RuntimeError(
            "initial_bad_product_not_detected"
        )

    if sorted(flagged, key=str) != sorted(
        expected_faults,
        key=str,
    ):
        raise RuntimeError(
            "fault_localization_reference_changed"
        )

    if repaired != exact:
        raise RuntimeError(
            "selective_repair_not_exact"
        )

    if not final_global_check:
        raise RuntimeError(
            "final_product_not_verified"
        )

    per_round_false_accept_bound = (
        1.0 / PRIME
    )

    per_bad_task_bound = (
        per_round_false_accept_bound
        ** VERIFIER_ROUNDS
    )

    union_bound = (
        len(expected_faults)
        * per_bad_task_bound
    )

    return {
        "matrix_n": MICRO_N,
        "grid": MICRO_GRID,
        "block_n": MICRO_BLOCK,
        "worker_task_count": len(
            weak_outputs
        ),
        "fault_task_count": len(
            expected_faults
        ),
        "fault_tasks": [
            [
                task.row_block,
                task.inner_block,
                task.col_block,
            ]
            for task in expected_faults
        ],
        "unverified_matches_exact": (
            unverified == exact
        ),
        "initial_global_verifier_pass": (
            initial_global_check
        ),
        "localized_fault_count": len(
            flagged
        ),
        "recomputed_task_count": len(
            flagged
        ),
        "repaired_matches_exact": (
            repaired == exact
        ),
        "final_global_verifier_pass": (
            final_global_check
        ),
        "verifier_rounds": (
            VERIFIER_ROUNDS
        ),
        "field_prime": PRIME,
        "per_bad_task_false_accept_bound": (
            per_bad_task_bound
        ),
        "fixture_fault_union_bound": (
            union_bound
        ),
    }


def _scale_model() -> dict:
    n = MODEL_N
    grid = MODEL_GRID
    block = n // grid
    task_count = grid**3

    strong_multiply_work = n**3

    one_task_multiply_work = (
        block**3
    )

    local_verifier_work = (
        3
        * VERIFIER_ROUNDS
        * n**2
        * grid
    )

    global_verifier_work = (
        3
        * VERIFIER_ROUNDS
        * n**2
    )

    expected_fault_tasks = math.ceil(
        task_count
        * MODEL_FAULT_RATE
    )

    selective_recompute_work = (
        expected_fault_tasks
        * one_task_multiply_work
    )

    total_verified_swarm_work = (
        strong_multiply_work
        + local_verifier_work
        + global_verifier_work
        + selective_recompute_work
    )

    strong_working_set_scalars = (
        3
        * n**2
    )

    task_working_set_scalars = (
        3
        * block**2
    )

    return_tile_scalars = (
        task_count
        * block**2
    )

    output_scalars = n**2

    return {
        "matrix_n": n,
        "grid": grid,
        "block_n": block,
        "worker_task_count": task_count,
        "modeled_fault_rate": (
            MODEL_FAULT_RATE
        ),
        "modeled_fault_task_count": (
            expected_fault_tasks
        ),
        "strong_multiply_work": (
            strong_multiply_work
        ),
        "verified_swarm_total_work": (
            total_verified_swarm_work
        ),
        "verified_swarm_work_ratio": (
            total_verified_swarm_work
            / strong_multiply_work
        ),
        "verification_plus_repair_overhead_ratio": (
            (
                total_verified_swarm_work
                - strong_multiply_work
            )
            / strong_multiply_work
        ),
        "single_task_multiply_fraction": (
            one_task_multiply_work
            / strong_multiply_work
        ),
        "single_task_working_set_fraction": (
            task_working_set_scalars
            / strong_working_set_scalars
        ),
        "local_verifier_work_ratio": (
            local_verifier_work
            / strong_multiply_work
        ),
        "global_verifier_work_ratio": (
            global_verifier_work
            / strong_multiply_work
        ),
        "selective_recompute_work_ratio": (
            selective_recompute_work
            / strong_multiply_work
        ),
        "raw_task_return_amplification_vs_output": (
            return_tile_scalars
            / output_scalars
        ),
        "reducer_required": True,
        "interpretation": {
            "worker_compute": (
                "small"
            ),
            "worker_residency": (
                "small"
            ),
            "aggregate_arithmetic": (
                "slightly_higher_than_one_exact_matmul"
            ),
            "communication": (
                "potentially_dominant_without_hierarchical_reduction"
            ),
        },
    }


def run_panel() -> dict:
    micro = _micro_panel()
    scale = _scale_model()

    if (
        scale[
            "single_task_multiply_fraction"
        ]
        != 1.0 / MODEL_GRID**3
    ):
        raise RuntimeError(
            "task_compute_fraction_changed"
        )

    if (
        scale[
            "single_task_working_set_fraction"
        ]
        != 1.0 / MODEL_GRID**2
    ):
        raise RuntimeError(
            "task_working_set_fraction_changed"
        )

    if not (
        1.03
        < scale[
            "verified_swarm_work_ratio"
        ]
        < 1.04
    ):
        raise RuntimeError(
            "swarm_overhead_reference_changed"
        )

    if (
        scale[
            "raw_task_return_amplification_vs_output"
        ]
        != MODEL_GRID
    ):
        raise RuntimeError(
            "communication_amplification_changed"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_VERIFIED_SWARM_MATMUL_VALIDATED"
        ),
        "synthetic_only": True,
        "live_distributed_execution_claim": False,
        "novelty_boundary": (
            "SYSTEMS_COMPOSITION_NOT_INVENTION_OF_FREIVALDS_OR_BLOCK_MATMUL"
        ),
        "micro_exact_fixture": micro,
        "scale_model": scale,
        "primary_findings": [
            "WEAK_WORKERS_CAN_HAVE_SMALL_LOCAL_COMPUTE_AND_MEMORY_CONTRACTS",
            "CHEAP_PROBABILISTIC_VERIFICATION_CAN_LOCALIZE_INJECTED_FAULTS",
            "SELECTIVE_RECOMPUTE_CAN_RESTORE_EXACT_OUTPUT_WITHOUT_FULL_REDO",
            "SWARMING_SHIFTS_COST_FROM_WORKER_CAPABILITY_TO_COMMUNICATION_AND_COORDINATION",
            "VERIFIER_COST_CAN_BE_ASYMPTOTICALLY_SMALL_RELATIVE_TO_LARGE_MATMUL",
        ],
        "claim_ceiling": (
            "SYNTHETIC_VERIFIED_SWARM_MATMUL_ONLY"
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
