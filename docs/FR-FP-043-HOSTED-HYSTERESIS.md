# FR-FP-043 — Hosted physical migration hysteresis

Status: **HOSTED PHYSICAL HYSTERESIS CANDIDATE**

Parent: **FR-FP-042**

## Why

FR-FP-042 qualified a cross-validated migration-cost model and showed that a
20-round horizon should HOLD every value-only swap.

A stronger physical test needs both regimes in one trace.

Use:

    validity horizon = 100 rounds

On the frozen FR-FP-038 value phases this predicts:

    phase 1 -> 2: MIGRATE
    phase 2 -> 3: MIGRATE
    phase 3 -> 4: HOLD (same optimum)
    phase 4 -> 5: HOLD (benefit too small)

## Physical arms

IMMEDIATE_OPTIMUM
: enact every semantic optimum.

HYSTERETIC
: enact only when the cross-validated migration cost can amortize within the
  100-round horizon, unless deadline safety requires migration.

Both arms:
- ten durable 8 MiB states;
- five WARM slots = 40 MiB;
- same semantic phase states;
- hosted Linux page-cache actuation.

## Qualification

Require:

- the hysteretic plan contains both MIGRATE and HOLD;
- immediate arm executes 24 physical delta actions;
- hysteretic arm executes 16;
- both arms remain exactly at 40 MiB resident;
- WARM/COLD physical residency matches target sets;
- observed hysteretic actuation time is lower;
- transparent hybrid total
  (model service penalty + observed actuation time)
  is lower for hysteresis.

The hybrid total is not hidden.

Both components are reported separately.

## Evidence boundary

Physical:
- DONTNEED / prefetch actuation;
- page-cache residency;
- actuation timing.

Modeled:
- service penalty;
- 100-round validity horizon.

The next lane should remove the oracle horizon.

## Claim ceiling

**HOSTED_PHYSICAL_HYSTERESIS_ON_ONE_FIVE_PHASE_EQUAL_SIZE_FIXED_CAPACITY_H100_FIXTURE_ONLY**
