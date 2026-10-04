# FR-FP-044 — Break-even horizon interval gate

Status: **ANALYTIC HORIZON-REDUCTION CANDIDATE**

Parent: **FR-FP-043**

## Why

FR-FP-043 physically qualified migration hysteresis at an oracle validity
horizon of 100 rounds.

The Governor should not need an exact horizon estimate when a coarse interval
already implies the same decision.

## Break-even law

For a candidate placement:

    benefit per round = current service penalty - candidate service penalty

and:

    H_star
      =
    predicted physical migration cost
      /
    benefit per round

Safety remains a separate override.

## Decision from a horizon interval

Given a conservative validity interval:

    [H_lower, H_upper]

the migration decision is already resolved when:

### MIGRATE

    H_lower >= H_star

Every admissible horizon amortizes migration.

### HOLD

    H_upper < H_star

No admissible horizon amortizes migration.

### MEASURE MORE

    H_lower < H_star <= H_upper

The interval crosses the decision boundary.

Only this case keeps horizon measurement resident.

## Exact grid check

Use the physical/modeled contexts already qualified by FR-FP-042/043.

Sweep every 5-round interval endpoint from 0 to 300.

For every interval compare the interval classifier against the direct migration
decision at both endpoints.

The candidate requires zero mismatches.

## Frozen break-even examples

Expected thresholds are approximately:

    phase 1 -> 2: 60.5 rounds
    phase 2 -> 3: 80.0 rounds
    phase 4 -> 5: 222.2 rounds

This explains why H=100 physically produced:

    MIGRATE / MIGRATE / HOLD

for the value-changing transitions.

## Meta consequence

The same decision-relevance principle appears again:

> do not estimate a variable more precisely once every admissible remaining
> value yields the same action.

The next lane should build a sequential horizon evidence process that narrows an
interval only until this gate resolves.

## Claim ceiling

**ANALYTIC_HORIZON_INTERVAL_REDUCTION_ON_FP042_043_EQUAL_SIZE_MIGRATION_CONTEXTS_ONLY**
