from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict


SCHEMA = "finite-ram-lab.fr-alloc-001-fragmentation-surface/v0.1"
SEED = "FR-ALLOC-001"

POOL_BLOCKS = 512
TICKS = 5000
TOKEN_GRANULARITY_PROBE = 8192

SIZE_BLOCKS = (
    2, 4, 6, 8, 12, 16, 24, 32
)

SIZE_PROB = (
    0.08, 0.12, 0.13, 0.18,
    0.17, 0.15, 0.10, 0.07,
)


def _u(*parts: object) -> float:
    digest = hashlib.sha256(
        "|".join(
            str(x)
            for x in (
                SEED,
                *parts,
            )
        ).encode("utf-8")
    ).digest()

    return int.from_bytes(
        digest[:8],
        "big",
    ) / float(
        (1 << 64) - 1
    )


def _draw_size(
    request_id: int,
) -> int:
    draw = _u(
        "size",
        request_id,
    )

    total = 0.0

    for size, probability in zip(
        SIZE_BLOCKS,
        SIZE_PROB,
    ):
        total += probability

        if draw < total:
            return size

    return SIZE_BLOCKS[-1]


def generate_events() -> list[
    tuple[int, int, int, int, int, int]
]:
    events = []
    request_id = 0

    for tick in range(
        TICKS
    ):
        arrival_draw = _u(
            "arrival",
            tick,
        )

        if arrival_draw < 0.15:
            arrivals = 0
        elif arrival_draw < 0.80:
            arrivals = 1
        else:
            arrivals = 2

        for _ in range(
            arrivals
        ):
            blocks = _draw_size(
                request_id
            )

            lifetime = (
                8
                + int(
                    _u(
                        "life",
                        request_id,
                    )
                    * 70
                )
            )

            prefix_group = int(
                _u(
                    "prefix-group",
                    request_id,
                )
                * 12
            )

            prefix_blocks = (
                4
                if (
                    blocks >= 4
                    and _u(
                        "has-prefix",
                        request_id,
                    )
                    < 0.70
                )
                else 0
            )

            events.append(
                (
                    tick,
                    request_id,
                    blocks,
                    lifetime,
                    prefix_group,
                    prefix_blocks,
                )
            )

            request_id += 1

    return events


def _first_fit(
    free: list[bool],
    need: int,
) -> list[int] | None:
    run = 0

    for index, available in enumerate(
        free
    ):
        run = (
            run + 1
            if available
            else 0
        )

        if run >= need:
            start = (
                index
                - need
                + 1
            )

            return list(
                range(
                    start,
                    start + need,
                )
            )

    return None


def _any_free(
    free: list[bool],
    need: int,
) -> list[int] | None:
    if sum(free) < need:
        return None

    return [
        index
        for index, available
        in enumerate(free)
        if available
    ][:need]


def _mark(
    free: list[bool],
    pages: list[int],
    *,
    available: bool,
) -> None:
    for page in pages:
        free[page] = available


def simulate(
    policy: str,
) -> dict:
    events = (
        generate_events()
    )

    arrivals: dict[
        int,
        list[
            tuple[
                int,
                int,
                int,
                int,
                int,
                int,
            ]
        ],
    ] = defaultdict(list)

    for event in events:
        arrivals[
            event[0]
        ].append(
            event
        )

    free = [
        True
    ] * POOL_BLOCKS

    active: dict[
        int,
        dict,
    ] = {}

    shared_prefix: dict[
        int,
        list[int],
    ] = {}

    shared_prefix_refcount: dict[
        int,
        int,
    ] = defaultdict(int)

    admitted = 0
    rejected = 0
    external_fragmentation_rejects = 0
    max_reserve_waste_blocks = 0
    prefix_blocks_avoided = 0
    occupancy_sum = 0
    peak_used = 0

    for tick in range(
        TICKS
    ):
        for request_id, row in list(
            active.items()
        ):
            if row[
                "end"
            ] > tick:
                continue

            if row[
                "mode"
            ] == "SHARED":
                _mark(
                    free,
                    row["body"],
                    available=True,
                )

                group = row[
                    "prefix_group"
                ]

                shared_prefix_refcount[
                    group
                ] -= 1

                if (
                    shared_prefix_refcount[
                        group
                    ]
                    == 0
                ):
                    _mark(
                        free,
                        shared_prefix[
                            group
                        ],
                        available=True,
                    )

                    del shared_prefix[
                        group
                    ]

            else:
                _mark(
                    free,
                    row["pages"],
                    available=True,
                )

            del active[
                request_id
            ]

        for (
            _,
            request_id,
            blocks,
            lifetime,
            prefix_group,
            prefix_blocks,
        ) in arrivals.get(
            tick,
            (),
        ):
            if policy == (
                "MAX_RESERVE"
            ):
                need = max(
                    SIZE_BLOCKS
                )

                pages = _any_free(
                    free,
                    need,
                )

                if pages is None:
                    rejected += 1
                    continue

                _mark(
                    free,
                    pages,
                    available=False,
                )

                max_reserve_waste_blocks += (
                    need - blocks
                )

                active[
                    request_id
                ] = {
                    "end": (
                        tick
                        + lifetime
                    ),
                    "mode": "PLAIN",
                    "pages": pages,
                }

            elif policy == (
                "CONTIG_FIRST_FIT"
            ):
                pages = _first_fit(
                    free,
                    blocks,
                )

                if pages is None:
                    rejected += 1

                    if (
                        sum(free)
                        >= blocks
                    ):
                        (
                            external_fragmentation_rejects
                        ) += 1

                    continue

                _mark(
                    free,
                    pages,
                    available=False,
                )

                active[
                    request_id
                ] = {
                    "end": (
                        tick
                        + lifetime
                    ),
                    "mode": "PLAIN",
                    "pages": pages,
                }

            elif policy == (
                "PAGED"
            ):
                pages = _any_free(
                    free,
                    blocks,
                )

                if pages is None:
                    rejected += 1
                    continue

                _mark(
                    free,
                    pages,
                    available=False,
                )

                active[
                    request_id
                ] = {
                    "end": (
                        tick
                        + lifetime
                    ),
                    "mode": "PLAIN",
                    "pages": pages,
                }

            elif policy == (
                "PAGED_PREFIX_SHARE"
            ):
                body_need = (
                    blocks
                    - prefix_blocks
                )

                new_prefix_need = 0

                if (
                    prefix_blocks
                    and prefix_group
                    not in shared_prefix
                ):
                    new_prefix_need = (
                        prefix_blocks
                    )

                need = (
                    body_need
                    + new_prefix_need
                )

                pages = _any_free(
                    free,
                    need,
                )

                if pages is None:
                    rejected += 1
                    continue

                cursor = 0

                if new_prefix_need:
                    prefix_pages = pages[
                        cursor:
                        cursor
                        + new_prefix_need
                    ]

                    cursor += (
                        new_prefix_need
                    )

                    _mark(
                        free,
                        prefix_pages,
                        available=False,
                    )

                    shared_prefix[
                        prefix_group
                    ] = prefix_pages

                elif prefix_blocks:
                    prefix_blocks_avoided += (
                        prefix_blocks
                    )

                if prefix_blocks:
                    (
                        shared_prefix_refcount[
                            prefix_group
                        ]
                    ) += 1

                body_pages = pages[
                    cursor:
                    cursor
                    + body_need
                ]

                _mark(
                    free,
                    body_pages,
                    available=False,
                )

                active[
                    request_id
                ] = {
                    "end": (
                        tick
                        + lifetime
                    ),
                    "mode": "SHARED",
                    "body": body_pages,
                    "prefix_group": (
                        prefix_group
                    ),
                }

            else:
                raise ValueError(
                    f"unknown_policy:{policy}"
                )

            admitted += 1

            peak_used = max(
                peak_used,
                POOL_BLOCKS
                - sum(free),
            )

        used = (
            POOL_BLOCKS
            - sum(free)
        )

        occupancy_sum += used
        peak_used = max(
            peak_used,
            used,
        )

    return {
        "policy": policy,
        "requests": len(events),
        "admitted": admitted,
        "rejected": rejected,
        "admission_rate": (
            admitted
            / len(events)
        ),
        "external_fragmentation_rejects": (
            external_fragmentation_rejects
        ),
        "max_reserve_waste_blocks": (
            max_reserve_waste_blocks
        ),
        "prefix_blocks_avoided": (
            prefix_blocks_avoided
        ),
        "mean_used_blocks": (
            occupancy_sum
            / TICKS
        ),
        "peak_used_blocks": (
            peak_used
        ),
    }


def block_granularity_panel() -> dict:
    token_lengths = [
        1
        + int(
            _u(
                "granularity-length",
                index,
            )
            * 2048
        )
        for index in range(
            TOKEN_GRANULARITY_PROBE
        )
    ]

    total_tokens = sum(
        token_lengths
    )

    result = {}

    for block_tokens in (
        8,
        16,
        32,
        64,
        128,
    ):
        allocated = sum(
            math.ceil(
                tokens
                / block_tokens
            )
            * block_tokens
            for tokens
            in token_lengths
        )

        waste = (
            allocated
            - total_tokens
        )

        result[
            str(block_tokens)
        ] = {
            "block_tokens": (
                block_tokens
            ),
            "allocated_tokens": (
                allocated
            ),
            "waste_tokens": waste,
            "waste_fraction": (
                waste
                / allocated
            ),
            "mean_waste_tokens_per_request": (
                waste
                / len(
                    token_lengths
                )
            ),
        }

    return result


def run_panel() -> dict:
    policies = {
        name: simulate(
            name
        )
        for name in (
            "MAX_RESERVE",
            "CONTIG_FIRST_FIT",
            "PAGED",
            "PAGED_PREFIX_SHARE",
        )
    }

    granularity = (
        block_granularity_panel()
    )

    frozen = {
        "requests": 5308,
        "max_reserve_admitted": 1862,
        "contig_admitted": 4691,
        "contig_rejected": 617,
        "contig_external_fragmentation_rejects": 615,
        "paged_admitted": 4804,
        "paged_rejected": 504,
        "paged_prefix_admitted": 5067,
        "paged_prefix_rejected": 241,
        "paged_prefix_blocks_avoided": 12996,
        "granularity_16_waste_fraction": (
            0.007315450336589354
        ),
        "granularity_128_waste_fraction": (
            0.05783839902464139
        ),
    }

    actual = {
        "requests": (
            policies[
                "MAX_RESERVE"
            ]["requests"]
        ),
        "max_reserve_admitted": (
            policies[
                "MAX_RESERVE"
            ]["admitted"]
        ),
        "contig_admitted": (
            policies[
                "CONTIG_FIRST_FIT"
            ]["admitted"]
        ),
        "contig_rejected": (
            policies[
                "CONTIG_FIRST_FIT"
            ]["rejected"]
        ),
        "contig_external_fragmentation_rejects": (
            policies[
                "CONTIG_FIRST_FIT"
            ][
                "external_fragmentation_rejects"
            ]
        ),
        "paged_admitted": (
            policies[
                "PAGED"
            ]["admitted"]
        ),
        "paged_rejected": (
            policies[
                "PAGED"
            ]["rejected"]
        ),
        "paged_prefix_admitted": (
            policies[
                "PAGED_PREFIX_SHARE"
            ]["admitted"]
        ),
        "paged_prefix_rejected": (
            policies[
                "PAGED_PREFIX_SHARE"
            ]["rejected"]
        ),
        "paged_prefix_blocks_avoided": (
            policies[
                "PAGED_PREFIX_SHARE"
            ]["prefix_blocks_avoided"]
        ),
        "granularity_16_waste_fraction": (
            granularity[
                "16"
            ]["waste_fraction"]
        ),
        "granularity_128_waste_fraction": (
            granularity[
                "128"
            ]["waste_fraction"]
        ),
    }

    if actual != frozen:
        raise RuntimeError(
            "frozen_allocator_surface_changed:"
            f"{actual}"
        )

    contig = policies[
        "CONTIG_FIRST_FIT"
    ]

    if (
        contig[
            "external_fragmentation_rejects"
        ]
        / contig["rejected"]
        < 0.95
    ):
        raise RuntimeError(
            "external_fragmentation_not_dominant"
        )

    if not (
        policies[
            "PAGED_PREFIX_SHARE"
        ]["admitted"]
        > policies[
            "PAGED"
        ]["admitted"]
        > policies[
            "CONTIG_FIRST_FIT"
        ]["admitted"]
        > policies[
            "MAX_RESERVE"
        ]["admitted"]
    ):
        raise RuntimeError(
            "expected_admission_order_changed"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_FRAGMENTATION_AND_PREFIX_SHARING_SURFACE_VALIDATED"
        ),
        "fixture": {
            "pool_blocks": (
                POOL_BLOCKS
            ),
            "ticks": TICKS,
            "requests": len(
                generate_events()
            ),
            "prefix_groups": 12,
            "prefix_share_probability": (
                0.70
            ),
            "prefix_blocks_when_present": (
                4
            ),
        },
        "policies": policies,
        "block_granularity": (
            granularity
        ),
        "derived": {
            "contiguous_rejects_due_to_external_fragmentation_fraction": (
                contig[
                    "external_fragmentation_rejects"
                ]
                / contig["rejected"]
            ),
            "paged_reject_reduction_vs_contiguous": (
                1.0
                - policies[
                    "PAGED"
                ]["rejected"]
                / contig["rejected"]
            ),
            "prefix_share_reject_reduction_vs_paged": (
                1.0
                - policies[
                    "PAGED_PREFIX_SHARE"
                ]["rejected"]
                / policies[
                    "PAGED"
                ]["rejected"]
            ),
            "prefix_share_admission_gain_vs_paged": (
                policies[
                    "PAGED_PREFIX_SHARE"
                ]["admitted"]
                - policies[
                    "PAGED"
                ]["admitted"]
            ),
        },
        "source_boundaries": {
            "vllm": (
                "PagedAttention motivates block-based on-demand KV allocation and prefix sharing; this simulator is not vLLM."
            ),
            "vattention": (
                "vAttention motivates separating virtual contiguity from physical on-demand allocation; this simulator does not model CUDA VMM overhead."
            ),
            "performance": (
                "No throughput or kernel-performance claim is made."
            ),
        },
        "primary_findings": [
            "ALLOCATOR_GEOMETRY_IS_AN_INDEPENDENT_MEMORY_CONTROL_ATOM",
            "TOTAL_FREE_CAPACITY_DOES_NOT_IMPLY_CONTIGUOUS_ADMISSIBILITY",
            "PAGING_CAN_REMOVE_EXTERNAL_FRAGMENTATION_WITHOUT_REDUCING_INFORMATION_BYTES",
            "PREFIX_SHARING_ATTACKS_DUPLICATION_AFTER_FRAGMENTATION_IS_FIXED",
            "SMALLER_BLOCKS_REDUCE_INTERNAL_FRAGMENTATION_BUT_MAY_INCREASE_METADATA_OR_KERNEL_OVERHEAD",
            "ALLOCATOR_POLICY_MUST_BE_OPTIMIZED_JOINTLY_WITH_QUANTIZATION_AND_SHARING",
        ],
        "claim_ceiling": (
            "SOURCE_GROUNDED_SYNTHETIC_ALLOCATOR_GEOMETRY_ONLY"
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
    raise SystemExit(
        main()
    )
