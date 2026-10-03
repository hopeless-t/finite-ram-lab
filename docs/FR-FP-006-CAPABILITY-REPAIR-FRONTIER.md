# FR-FP-006 — Capability repair frontier

Status: **SYNTHETIC REPAIR FRONTIER CANDIDATE**

Parent: **FR-FP-005**

## Baseline

FR-FP-005 classifies:

    transfer lead = 4
    hot budget = 4

as:

    TRANSFER_SURFACE_CAPABILITY_GAP

Policy tuning is therefore the wrong next action.

FR-FP-006 asks:

> What is the smallest change along each already-measured resource axis that
> escapes the capability gap?

## Measured repair 1 — transfer lead

Hold hot budget at 4.

The frozen phase map says:

    lead 4 -> capability gap
    lead 3 -> feasible simple-policy region

Therefore the minimum measured repair on this axis is:

    reduce transfer lead by 1 step
    4 -> 3
    25% reduction

This is a latency / bandwidth / transfer-surface target.

## Measured repair 2 — hot capacity

Hold transfer lead at 4.

The frozen phase map says:

    budget 4 -> capability gap
    budget 6 -> feasible simple-policy region

Therefore the minimum measured repair on this axis is:

    add 2 hot state slots
    4 -> 6
    50% capacity increase

## Geometric equivalent — state size

At fixed hot bytes:

    number of resident states
    =
    hot bytes / bytes per state

To make a four-state byte budget hold six states, state size must be at most:

    4 / 6 = 0.6667

of baseline.

Equivalent required state-size reduction:

    at least 33.33%

This is geometry only.

It does not prove that quantization, compression, deduplication, rematerializing,
or any other mechanism can achieve that reduction within the task contract.

## Unmodeled lever — reclaimability timing

The phase map does not vary when safe semantic reclaimability arrives.

Therefore FR-FP-006 deliberately does not invent a number such as:

    reclaim 2 steps earlier

The correct classification is:

    MODEL_GAP

The next experiment must vary safe-reclaimability arrival and measure how much
earlier it must occur to cross the deadline frontier.

## No fake common score

A one-step transfer improvement, a 50% capacity increase, and a 33.3% state-size
reduction have different engineering costs.

FR-FP-006 does not rank them.

A cross-lever recommendation requires a frozen common cost model such as:

- dollars;
- joules;
- latency;
- SSD writes;
- quality loss;
- implementation complexity;
- or a declared multi-objective task contract.

Until then they remain separate repair coordinates.

## North-Star consequence

A capability gap is now decomposed into:

- measured repair coordinates;
- geometric equivalents;
- remaining model gaps.

This prevents the lab from opening an arbitrary new mechanism lane when the
needed physical change can already be stated precisely.

## Claim ceiling

**SYNTHETIC_CAPABILITY_REPAIR_FRONTIER_AND_GEOMETRIC_EQUIVALENCE_ONLY**
