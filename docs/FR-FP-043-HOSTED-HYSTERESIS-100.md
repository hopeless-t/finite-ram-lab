# FR-FP-043 — Hosted 100-round mixed HOLD/MIGRATE hysteresis

Status: **HOSTED PHYSICAL HYSTERESIS CANDIDATE**

Parent: **FR-FP-042**

## Why

FR-FP-042 qualified a cross-validated migration-cost model, but the frozen
20-round horizon produced only HOLD decisions.

The next predeclared horizon is:

    100 rounds per phase

On the same five value phases, the calibrated model predicts a mixed control
regime:

    phase 1 -> 2: MIGRATE
    phase 2 -> 3: MIGRATE
    phase 3 -> 4: HOLD
    phase 4 -> 5: HOLD

That is the smallest fixture that exercises both branches of the hysteresis
policy.

## Arms

IMMEDIATE_OPTIMUM
: physically follow every semantic optimum.

HYSTERETIC_100
: migrate only when the 100-round expected service benefit amortizes the
cross-validated migration-cost model, unless safety requires migration.

Both arms:

- use ten 8 MiB files;
- hold exactly five WARM states = 40 MiB;
- start from the same phase-1 placement;
- use POSIX_FADV_DONTNEED / prefetch actuation;
- verify physical residency after every phase.

## Accounting

Keep separate:

    semantic service cost
    observed physical migration latency

Only after both are reported may they be added for total comparison.

No hidden scalar utility is introduced.

## Qualification

Require:

- both HOLD and MIGRATE decisions;
- exact physical WARM-set realization;
- exact 40 MiB resident capacity;
- fewer migrations and actions than immediate optimum;
- higher-or-equal semantic service cost than immediate optimum;
- lower observed total cost after migration is priced.

## North-Star consequence

The Governor now controls not only:

    which state should be WARM?

but:

    is changing the placement worth paying for before the placement is likely
    to become stale again?

The validity horizon becomes a first-class resource-control input.

## Claim ceiling

**HOSTED_PHYSICAL_100_ROUND_HYSTERESIS_ON_FP038_EQUAL_SIZE_FIVE_PHASE_FIXTURE_ONLY**
