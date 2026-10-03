from __future__ import annotations

import hashlib
import json
import math
from functools import lru_cache
from statistics import mean


SCHEMA = "finite-ram-lab.ksla-real-state-bounded-idiocy/v0.1"
EPISODES = 512
N = 256
ACTIVE = 48
CACHE = 8
STALL_LIMIT = 3
MAX_ROUNDS = 500
STEPS = (-4, -2, -1, 1, 2, 4)

POLICIES = (
    "EXPERT_HEAVY",
    "EXPERT_ONLY",
    "FIXED_LOW",
    "FIXED_HIGH",
    "STALL_ADAPTIVE",
    "IDIOT_ONLY",
)


def _h(text: str) -> int:
    return int.from_bytes(
        hashlib.sha256(text.encode()).digest()[:8],
        "big",
    )


@lru_cache(maxsize=None)
def _episode_template(
    ep: int,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    coords = list(range(N))
    coords.sort(
        key=lambda i: _h(
            f"ep{ep}|coord|{i}"
        )
    )

    target = [0] * N

    for coordinate in coords[:ACTIVE]:
        magnitude = (
            _h(
                f"ep{ep}|val|{coordinate}"
            )
            % 4
        ) + 1

        sign = (
            -1
            if _h(
                f"ep{ep}|sign|{coordinate}"
            ) & 1
            else 1
        )

        target[coordinate] = (
            sign * magnitude
        )

    permutation = list(range(N))
    permutation.sort(
        key=lambda i: _h(
            f"ep{ep}|cache|{i}"
        )
    )

    return tuple(target), tuple(permutation)


def _episode(ep: int):
    target, permutation = _episode_template(ep)

    # Preserve the original per-policy mutable-list contract while sharing only
    # the expensive deterministic hash/sort template.
    return list(target), list(permutation)

def _idiot_action(
    ep: int,
    round_index: int,
    slot: int,
) -> tuple[int, int]:
    value = _h(
        f"ep{ep}|round{round_index}|idiot{slot}"
    )

    coordinate = value % N
    step = STEPS[
        (value // N)
        % len(STEPS)
    ]

    return coordinate, step


def _expert_action(
    state: list[int],
    target: list[int],
    cache: list[int],
):
    best = None
    evaluations = 0

    for coordinate in cache:
        before = (
            state[coordinate]
            - target[coordinate]
        ) ** 2

        for step in STEPS:
            evaluations += 1

            after = (
                state[coordinate]
                + step
                - target[coordinate]
            ) ** 2

            delta = after - before

            if (
                delta < 0
                and (
                    best is None
                    or delta < best[0]
                )
            ):
                best = (
                    delta,
                    coordinate,
                    step,
                )

    return best, evaluations


def _idiot_count(
    policy: str,
    *,
    expert_has_action: bool,
) -> int:
    if policy in (
        "EXPERT_HEAVY",
        "EXPERT_ONLY",
    ):
        return 0

    if policy == "FIXED_LOW":
        return 3

    if policy == "FIXED_HIGH":
        return 8

    if policy == "STALL_ADAPTIVE":
        return (
            0
            if expert_has_action
            else 32
        )

    if policy == "IDIOT_ONLY":
        return 16

    raise ValueError(
        f"unknown_policy:{policy}"
    )


def _expert_count(
    policy: str,
) -> int:
    if policy == "EXPERT_HEAVY":
        return 2

    if policy == "IDIOT_ONLY":
        return 0

    return 1


def run_episode(
    ep: int,
    policy: str,
) -> dict:
    target, permutation = _episode(ep)
    state = [0] * N

    expert_count = _expert_count(
        policy
    )

    caches = [
        list(
            permutation[
                expert_index
                * CACHE :
                (expert_index + 1)
                * CACHE
            ]
        )
        for expert_index
        in range(expert_count)
    ]

    rounds = 0
    stalls = 0
    proposal_evaluations = 0
    refresh_evaluations = 0
    refreshes = 0
    accepted_expert = 0
    accepted_idiot = 0
    cold_discoveries = 0

    while (
        state != target
        and rounds < MAX_ROUNDS
    ):
        proposals = []
        expert_has_action = False

        for expert_index, cache in (
            enumerate(caches)
        ):
            proposal, evaluations = (
                _expert_action(
                    state,
                    target,
                    cache,
                )
            )

            proposal_evaluations += (
                evaluations
            )

            if proposal is not None:
                expert_has_action = True
                delta, coordinate, step = (
                    proposal
                )

                proposals.append(
                    (
                        "expert",
                        expert_index,
                        delta,
                        coordinate,
                        step,
                    )
                )

        idiots = _idiot_count(
            policy,
            expert_has_action=(
                expert_has_action
            ),
        )

        for slot in range(idiots):
            coordinate, step = (
                _idiot_action(
                    ep,
                    rounds,
                    slot,
                )
            )

            proposal_evaluations += 1

            before = (
                state[coordinate]
                - target[coordinate]
            ) ** 2

            after = (
                state[coordinate]
                + step
                - target[coordinate]
            ) ** 2

            delta = after - before

            if delta < 0:
                proposals.append(
                    (
                        "idiot",
                        slot,
                        delta,
                        coordinate,
                        step,
                    )
                )

        best_by_coordinate = {}

        for proposal in proposals:
            coordinate = proposal[3]

            previous = (
                best_by_coordinate.get(
                    coordinate
                )
            )

            if (
                previous is None
                or proposal[2]
                < previous[2]
            ):
                best_by_coordinate[
                    coordinate
                ] = proposal

        if best_by_coordinate:
            stalls = 0

            for proposal in (
                best_by_coordinate.values()
            ):
                (
                    kind,
                    _,
                    _,
                    coordinate,
                    step,
                ) = proposal

                cold = all(
                    coordinate not in cache
                    for cache in caches
                )

                state[coordinate] += step

                if kind == "expert":
                    accepted_expert += 1
                    continue

                accepted_idiot += 1

                if cold:
                    cold_discoveries += 1

                if (
                    expert_count
                    and state[coordinate]
                    != target[coordinate]
                ):
                    cache = caches[0]

                    replace_index = next(
                        (
                            index
                            for index, resident
                            in enumerate(cache)
                            if state[resident]
                            == target[resident]
                        ),
                        0,
                    )

                    cache[
                        replace_index
                    ] = coordinate
        else:
            stalls += 1

        if (
            stalls >= STALL_LIMIT
            and expert_count
        ):
            refreshes += 1

            refresh_evaluations += (
                N * len(STEPS)
            )

            unsolved = [
                coordinate
                for coordinate
                in range(N)
                if state[coordinate]
                != target[coordinate]
            ]

            unsolved.sort(
                key=lambda coordinate: (
                    -abs(
                        target[coordinate]
                        - state[coordinate]
                    ),
                    coordinate,
                )
            )

            required = (
                expert_count
                * CACHE
            )

            fill = unsolved[:required]

            if fill:
                while len(fill) < required:
                    fill.append(
                        fill[-1]
                    )

                for expert_index in range(
                    expert_count
                ):
                    caches[
                        expert_index
                    ] = list(
                        fill[
                            expert_index
                            * CACHE :
                            (expert_index + 1)
                            * CACHE
                        ]
                    )

            stalls = 0

        rounds += 1

    return {
        "success": state == target,
        "rounds": rounds,
        "proposal_evaluations": (
            proposal_evaluations
        ),
        "refresh_evaluations": (
            refresh_evaluations
        ),
        "work_cost": (
            proposal_evaluations
            + refresh_evaluations
        ),
        "refreshes": refreshes,
        "accepted_expert": (
            accepted_expert
        ),
        "accepted_idiot": (
            accepted_idiot
        ),
        "cold_discoveries": (
            cold_discoveries
        ),
        "peak_resident_coordinates": (
            expert_count * CACHE
        ),
    }


def _quantile(
    values: list[int],
    q: float,
) -> int:
    ordered = sorted(values)
    index = (
        math.ceil(
            q * len(ordered)
        )
        - 1
    )

    return ordered[
        max(index, 0)
    ]


def _summarize(
    rows: list[dict],
) -> dict:
    return {
        "success_count": sum(
            row["success"]
            for row in rows
        ),
        "success_rate": (
            sum(
                row["success"]
                for row in rows
            )
            / len(rows)
        ),
        "mean_rounds": mean(
            row["rounds"]
            for row in rows
        ),
        "p95_rounds": _quantile(
            [
                row["rounds"]
                for row in rows
            ],
            0.95,
        ),
        "p99_rounds": _quantile(
            [
                row["rounds"]
                for row in rows
            ],
            0.99,
        ),
        "mean_work_cost": mean(
            row["work_cost"]
            for row in rows
        ),
        "p95_work_cost": _quantile(
            [
                row["work_cost"]
                for row in rows
            ],
            0.95,
        ),
        "p99_work_cost": _quantile(
            [
                row["work_cost"]
                for row in rows
            ],
            0.99,
        ),
        "mean_refresh_evaluations": (
            mean(
                row[
                    "refresh_evaluations"
                ]
                for row in rows
            )
        ),
        "mean_refreshes": mean(
            row["refreshes"]
            for row in rows
        ),
        "mean_cold_discoveries": (
            mean(
                row[
                    "cold_discoveries"
                ]
                for row in rows
            )
        ),
        "peak_resident_coordinates": (
            rows[0][
                "peak_resident_coordinates"
            ]
        ),
    }


def run_panel() -> dict:
    raw = {
        policy: []
        for policy in POLICIES
    }

    for episode in range(
        EPISODES
    ):
        for policy in POLICIES:
            raw[policy].append(
                run_episode(
                    episode,
                    policy,
                )
            )

    summary = {
        policy: _summarize(
            rows
        )
        for policy, rows
        in raw.items()
    }

    frozen = {
        "EXPERT_HEAVY": (
            512,
            46.083984375,
            9032.0625,
            4608.0,
            16,
        ),
        "EXPERT_ONLY": (
            512,
            77.9921875,
            12959.625,
            9216.0,
            8,
        ),
        "FIXED_LOW": (
            512,
            75.513671875,
            12416.197265625,
            8565.0,
            8,
        ),
        "FIXED_HIGH": (
            512,
            70.86328125,
            10685.34375,
            6717.0,
            8,
        ),
        "STALL_ADAPTIVE": (
            512,
            73.255859375,
            8169.34375,
            3636.0,
            8,
        ),
        "IDIOT_ONLY": (
            384,
            414.21875,
            6627.5,
            0.0,
            0,
        ),
    }

    for policy, expected in (
        frozen.items()
    ):
        row = summary[policy]

        actual = (
            row["success_count"],
            row["mean_rounds"],
            row["mean_work_cost"],
            row[
                "mean_refresh_evaluations"
            ],
            row[
                "peak_resident_coordinates"
            ],
        )

        if actual != expected:
            raise RuntimeError(
                f"frozen_result_changed:{policy}:{actual}"
            )

    adaptive = summary[
        "STALL_ADAPTIVE"
    ]

    heavy = summary[
        "EXPERT_HEAVY"
    ]

    exact_policies = [
        policy
        for policy, row
        in summary.items()
        if row["success_rate"] == 1.0
    ]

    if adaptive[
        "mean_work_cost"
    ] >= heavy[
        "mean_work_cost"
    ]:
        raise RuntimeError(
            "adaptive_not_cheaper_than_heavy"
        )

    if adaptive[
        "peak_resident_coordinates"
    ] >= heavy[
        "peak_resident_coordinates"
    ]:
        raise RuntimeError(
            "adaptive_not_lower_residency"
        )

    lambda_break_even = (
        heavy["mean_work_cost"]
        - adaptive[
            "mean_work_cost"
        ]
    ) / (
        adaptive["mean_rounds"]
        - heavy["mean_rounds"]
    )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "REAL_STATE_FINITE_VIEW_BOUNDED_IDIOCY_VALIDATED"
        ),
        "episodes": EPISODES,
        "problem": {
            "dimension": N,
            "active_coordinates": (
                ACTIVE
            ),
            "expert_cache": CACHE,
            "steps": list(STEPS),
            "stall_limit": (
                STALL_LIMIT
            ),
            "max_rounds": (
                MAX_ROUNDS
            ),
        },
        "policy_summary": summary,
        "matched_random_tapes": True,
        "exact_policy_set": (
            exact_policies
        ),
        "derived": {
            "adaptive_work_reduction_vs_expert_heavy": (
                1.0
                - adaptive[
                    "mean_work_cost"
                ]
                / heavy[
                    "mean_work_cost"
                ]
            ),
            "adaptive_round_increase_vs_expert_heavy": (
                adaptive[
                    "mean_rounds"
                ]
                / heavy[
                    "mean_rounds"
                ]
                - 1.0
            ),
            "adaptive_refresh_reduction_vs_expert_heavy": (
                1.0
                - adaptive[
                    "mean_refresh_evaluations"
                ]
                / heavy[
                    "mean_refresh_evaluations"
                ]
            ),
            "adaptive_resident_fraction_vs_expert_heavy": (
                adaptive[
                    "peak_resident_coordinates"
                ]
                / heavy[
                    "peak_resident_coordinates"
                ]
            ),
            "round_price_break_even_adaptive_vs_expert_heavy": (
                lambda_break_even
            ),
            "interpretation": (
                "For J = work_cost + lambda_round * rounds and full-success policies, STALL_ADAPTIVE beats EXPERT_HEAVY for lambda_round below the frozen break-even; EXPERT_HEAVY wins when serial round latency is priced higher."
            ),
        },
        "primary_findings": [
            "ADAPTIVE_IDIOCY_CAN_REDUCE_EXPENSIVE_GLOBAL_REFRESH",
            "ADAPTIVE_IDIOCY_CAN_USE_HALF_THE_EXPERT_RESIDENT_VIEW_OF_EXPERT_HEAVY",
            "PURE_IDIOCY_IS_CHEAP_BUT_FAILS_THE_FROZEN_RELIABILITY_FLOOR",
            "FIXED_IDIOCY_IS_INFERIOR_TO_STALL_GATED_IDIOCY_IN_THIS_FIXTURE",
            "EXPERT_HEAVY_REMAINS_THE_LOWEST_ROUND_DEPTH_POLICY",
            "BOUNDED_IDIOCY_IS_A_RESOURCE_TRADE_NOT_A_UNIVERSAL_SPEED_WIN",
        ],
        "claim_ceiling": (
            "SYNTHETIC_REAL_STATE_FINITE_VIEW_EXPERIMENT_ONLY"
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
