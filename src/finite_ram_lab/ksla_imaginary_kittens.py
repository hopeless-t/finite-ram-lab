from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


SCHEMA = "finite-ram-lab.ksla-imaginary-kitten-random-actions/v0.1"
SEED = "KSLA-002-v0.1"

N = 64
DIAG = 6
OFF = -1
STEPS = (-4, -2, -1, 1, 2, 4)

BATCHES = (1, 4, 8, 16, 32, 64, 128)
MAX_ROUNDS = 50_000


@dataclass(frozen=True)
class Action:
    coordinate: int
    step: int


def _hash_int(domain: str) -> int:
    return int.from_bytes(
        hashlib.sha256(
            f"{SEED}|{domain}".encode("utf-8")
        ).digest()[:8],
        "big",
    )


def _target() -> list[int]:
    return [
        (_hash_int(f"TARGET|{index}") % 15) - 7
        for index in range(N)
    ]


def _apply_q(vector: list[int]) -> list[int]:
    output: list[int] = []

    for index, value in enumerate(vector):
        total = DIAG * value

        if index > 0:
            total += OFF * vector[index - 1]

        if index < len(vector) - 1:
            total += OFF * vector[index + 1]

        output.append(total)

    return output


def _column_entries(
    coordinate: int,
) -> tuple[tuple[int, int], ...]:
    entries: list[tuple[int, int]] = [
        (coordinate, DIAG),
    ]

    if coordinate > 0:
        entries.append(
            (coordinate - 1, OFF)
        )

    if coordinate < N - 1:
        entries.append(
            (coordinate + 1, OFF)
        )

    return tuple(entries)


def _proposal(
    *,
    batch: int,
    round_index: int,
    kitten_index: int,
) -> Action:
    value = _hash_int(
        f"ACTION|B{batch}|R{round_index}|K{kitten_index}"
    )

    coordinate = value % N

    step = STEPS[
        (value // N) % len(STEPS)
    ]

    return Action(
        coordinate=coordinate,
        step=step,
    )


def _chaos_action(
    round_index: int,
) -> Action:
    value = _hash_int(
        f"CHAOS|R{round_index}"
    )

    coordinate = value % N

    step = STEPS[
        (value // N) % len(STEPS)
    ]

    return Action(
        coordinate=coordinate,
        step=step,
    )


def _residual_norm(
    residual: list[int],
) -> int:
    return sum(
        value * value
        for value in residual
    )


def _action_delta(
    residual: list[int],
    action: Action,
) -> int:
    delta = 0

    for row, coefficient in (
        _column_entries(
            action.coordinate,
        )
    ):
        old = residual[row]

        new = (
            old
            + action.step
            * coefficient
        )

        delta += (
            new * new
            - old * old
        )

    return delta


def _apply_action(
    state: list[int],
    residual: list[int],
    action: Action,
) -> None:
    state[
        action.coordinate
    ] += action.step

    for row, coefficient in (
        _column_entries(
            action.coordinate,
        )
    ):
        residual[row] += (
            action.step
            * coefficient
        )


def _initial_state() -> tuple[
    list[int],
    list[int],
    list[int],
]:
    target = _target()
    rhs = _apply_q(target)

    state = [
        0
        for _ in range(N)
    ]

    residual = [
        -value
        for value in rhs
    ]

    return target, state, residual


def run_filtered_swarm(
    batch: int,
) -> dict:
    target, state, residual = (
        _initial_state()
    )

    start_norm = _residual_norm(
        residual
    )

    current_norm = start_norm
    accepted = 0
    proposals = 0
    empty_rounds = 0

    for round_index in range(
        MAX_ROUNDS
    ):
        best: tuple[
            int,
            int,
            int,
            Action,
        ] | None = None

        for kitten_index in range(
            batch
        ):
            action = _proposal(
                batch=batch,
                round_index=round_index,
                kitten_index=kitten_index,
            )

            delta = _action_delta(
                residual,
                action,
            )

            proposals += 1

            if delta >= 0:
                continue

            candidate = (
                delta,
                action.coordinate,
                action.step,
                action,
            )

            if (
                best is None
                or candidate[:3]
                < best[:3]
            ):
                best = candidate

        if best is None:
            empty_rounds += 1
        else:
            delta, _, _, action = best

            _apply_action(
                state,
                residual,
                action,
            )

            current_norm += delta
            accepted += 1

        if current_norm == 0:
            return {
                "batch": batch,
                "rounds": (
                    round_index + 1
                ),
                "proposals": proposals,
                "accepted_actions": accepted,
                "rejected_or_unused_actions": (
                    proposals - accepted
                ),
                "empty_rounds": empty_rounds,
                "start_residual_norm": start_norm,
                "final_residual_norm": current_norm,
                "exact_solution": (
                    state == target
                ),
            }

    raise RuntimeError(
        f"swarm_did_not_converge:B{batch}"
    )


def run_exhaustive_validator() -> dict:
    target, state, residual = (
        _initial_state()
    )

    start_norm = _residual_norm(
        residual
    )

    current_norm = start_norm
    proposals = 0
    accepted = 0

    for round_index in range(
        MAX_ROUNDS
    ):
        best: tuple[
            int,
            int,
            int,
            Action,
        ] | None = None

        for coordinate in range(N):
            for step in STEPS:
                action = Action(
                    coordinate=coordinate,
                    step=step,
                )

                delta = _action_delta(
                    residual,
                    action,
                )

                proposals += 1

                if delta >= 0:
                    continue

                candidate = (
                    delta,
                    coordinate,
                    step,
                    action,
                )

                if (
                    best is None
                    or candidate[:3]
                    < best[:3]
                ):
                    best = candidate

        if best is None:
            raise RuntimeError(
                "exhaustive_scan_stalled"
            )

        delta, _, _, action = best

        _apply_action(
            state,
            residual,
            action,
        )

        current_norm += delta
        accepted += 1

        if current_norm == 0:
            return {
                "rounds": (
                    round_index + 1
                ),
                "proposals": proposals,
                "accepted_actions": accepted,
                "start_residual_norm": start_norm,
                "final_residual_norm": 0,
                "exact_solution": (
                    state == target
                ),
            }

    raise RuntimeError(
        "exhaustive_scan_did_not_converge"
    )


def run_unfiltered_chaos(
    rounds: int,
) -> dict:
    target, state, residual = (
        _initial_state()
    )

    start_norm = _residual_norm(
        residual
    )

    for round_index in range(
        rounds
    ):
        action = _chaos_action(
            round_index
        )

        _apply_action(
            state,
            residual,
            action,
        )

    final_norm = _residual_norm(
        residual
    )

    return {
        "rounds": rounds,
        "actions": rounds,
        "start_residual_norm": start_norm,
        "final_residual_norm": final_norm,
        "residual_growth_ratio": (
            final_norm / start_norm
        ),
        "exact_solution": (
            state == target
        ),
        "max_abs_state_coordinate": (
            max(
                abs(value)
                for value in state
            )
        ),
    }


def _scale_model() -> dict:
    large_n = 1_000_000
    max_touched = 3

    return {
        "modeled_dimension": large_n,
        "logical_kitten_state": (
            "coordinate_plus_step_only"
        ),
        "matrix_structure": (
            "tridiagonal_spd"
        ),
        "matrix_storage_scaling": "O(n)",
        "validator_state_scaling": "O(n)",
        "max_residual_entries_touched_per_proposal": (
            max_touched
        ),
        "proposal_touch_fraction": (
            max_touched / large_n
        ),
        "proposal_knows_gradient": False,
        "proposal_knows_rhs": False,
        "proposal_knows_matrix": False,
        "proposal_knows_objective": False,
        "physical_worker_required": False,
        "llm_required": False,
    }


def run_panel() -> dict:
    filtered = {
        f"BATCH_{batch}": (
            run_filtered_swarm(batch)
        )
        for batch in BATCHES
    }

    exhaustive = (
        run_exhaustive_validator()
    )

    single_rounds = filtered[
        "BATCH_1"
    ]["rounds"]

    chaos = run_unfiltered_chaos(
        single_rounds
    )

    reference = {
        "BATCH_1": (
            2753,
            2753,
            183,
        ),
        "BATCH_4": (
            635,
            2540,
            189,
        ),
        "BATCH_8": (
            305,
            2440,
            150,
        ),
        "BATCH_16": (
            232,
            3712,
            148,
        ),
        "BATCH_32": (
            185,
            5920,
            137,
        ),
        "BATCH_64": (
            155,
            9920,
            132,
        ),
        "BATCH_128": (
            122,
            15616,
            122,
        ),
    }

    for name, expected in (
        reference.items()
    ):
        row = filtered[name]

        actual = (
            row["rounds"],
            row["proposals"],
            row[
                "accepted_actions"
            ],
        )

        if actual != expected:
            raise RuntimeError(
                f"filtered_reference_changed:{name}:{actual}"
            )

        if (
            not row[
                "exact_solution"
            ]
            or row[
                "final_residual_norm"
            ]
            != 0
        ):
            raise RuntimeError(
                f"filtered_arm_not_exact:{name}"
            )

    if (
        exhaustive["rounds"]
        != 124
        or exhaustive[
            "proposals"
        ]
        != 47_616
        or not exhaustive[
            "exact_solution"
        ]
    ):
        raise RuntimeError(
            "exhaustive_reference_changed"
        )

    if (
        chaos[
            "final_residual_norm"
        ]
        != 585_361
        or chaos[
            "exact_solution"
        ]
    ):
        raise RuntimeError(
            "chaos_reference_changed"
        )

    best_proposal_arm = min(
        filtered,
        key=lambda name: (
            filtered[name][
                "proposals"
            ],
            filtered[name][
                "rounds"
            ],
        ),
    )

    best_round_arm = min(
        filtered,
        key=lambda name: (
            filtered[name][
                "rounds"
            ],
            filtered[name][
                "proposals"
            ],
        ),
    )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_IMAGINARY_KITTEN_RANDOM_ACTION_SOLVER_VALIDATED"
        ),
        "synthetic_only": True,
        "live_parallel_runtime_claim": False,
        "kitten_definition": (
            "STATELESS_RANDOM_ACTION_PROPOSAL_NOT_A_PROCESS_AGENT_OR_LLM"
        ),
        "problem": {
            "equation": "Qx=c",
            "dimension": N,
            "q_structure": (
                "tridiagonal_spd_diag6_offdiag_minus1"
            ),
            "candidate_steps": list(STEPS),
            "start_residual_norm": (
                filtered[
                    "BATCH_1"
                ][
                    "start_residual_norm"
                ]
            ),
        },
        "filtered_swarms": filtered,
        "exhaustive_validator": exhaustive,
        "unfiltered_chaos": chaos,
        "best_proposal_efficiency_arm": (
            best_proposal_arm
        ),
        "best_round_depth_arm": (
            best_round_arm
        ),
        "derived": {
            "batch8_round_reduction_vs_single": (
                filtered[
                    "BATCH_1"
                ]["rounds"]
                / filtered[
                    "BATCH_8"
                ]["rounds"]
            ),
            "batch8_proposal_ratio_vs_single": (
                filtered[
                    "BATCH_8"
                ]["proposals"]
                / filtered[
                    "BATCH_1"
                ]["proposals"]
            ),
            "batch8_proposal_ratio_vs_exhaustive": (
                filtered[
                    "BATCH_8"
                ]["proposals"]
                / exhaustive["proposals"]
            ),
            "batch128_round_ratio_vs_exhaustive": (
                filtered[
                    "BATCH_128"
                ]["rounds"]
                / exhaustive["rounds"]
            ),
        },
        "scale_model": _scale_model(),
        "primary_findings": [
            "IMAGINARY_KITTENS_NEED_NOT_BE_LLMS_OR_PHYSICAL_WORKERS",
            "RANDOM_ACTION_GENERATION_PLUS_EXTERNAL_VALIDATION_CAN_REACH_AN_EXACT_SOLUTION",
            "UNFILTERED_RANDOM_ACTIONS_DIVERGE_IN_THE_FROZEN_FIXTURE",
            "A_SMALL_RANDOM_SWARM_CAN_REDUCE_BOTH_SEARCH_DEPTH_AND_CANDIDATE_EVALUATIONS_VS_SINGLE_RANDOM_ACTIONS",
            "EXHAUSTIVE_BEST_MOVE_SEARCH_CAN_COST_MORE_VALIDATOR_EVALUATIONS_THAN_RANDOM_PROPOSAL_SAMPLING",
            "SWARM_WIDTH_TRADES_PARALLEL_DEPTH_AGAINST_TOTAL_PROPOSAL_WORK",
        ],
        "novelty_boundary": (
            "SYSTEMS_COMPOSITION_RELATIVE_TO_RANDOMIZED_COORDINATE_AND_ZEROTH_ORDER_SEARCH_NOT_A_NEW_OPTIMIZATION_PRIMITIVE"
        ),
        "claim_ceiling": (
            "SYNTHETIC_IMAGINARY_KITTEN_RANDOM_ACTION_SOLVER_ONLY"
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
