# STRATA-002-CONFIRMATORY-MC-v1

> **Status:** FROZEN DESIGN
> **Purpose:** conservative confirmatory sample-size selection
> **Physical launch authority:** NONE

## Source

STRATA-002-PILOT-v1:

- run `36338522437`
- aggregate artifact `10938470859`
- digest `sha256:bec214018ea7a71e948cdb13c76c5292613f2fc0dd16a1bb03929988c747149d`

## Efficacy model

Pilot efficacy criterion:

`buffered memory.current - DONTNEED memory.current >= 64 MiB`

Observed:

`8 / 8` blocks.

Do not use p=1.0 for design.

Use the one-sided exact 95% Clopper-Pearson lower bound:

`p = 0.6876560219336321`

For each candidate N:

1. simulate N Bernoulli efficacy outcomes with this probability;
2. count successes K;
3. apply the exact one-sided binomial sign test against p=0.5;
4. efficacy passes if p-value <= 0.025.

## Latency model

Pilot paired scan ratios:

`DONTNEED / buffered`

are frozen in the machine-readable spec.

Transform to natural log.

Estimate:

- pilot mean log ratio;
- pilot sample standard deviation.

For each candidate N:

1. draw N log ratios from Normal(pilot mean, pilot sample SD);
2. calculate sample mean and sample SD;
3. calculate the one-sided 95% Student-t upper bound for mean log ratio;
4. latency passes if the upper bound <= `log(1.25)`.

This is a design model, not a claim that hosted timing is exactly normal.

It deliberately preserves the large timing variance observed in the pilot.

## Joint pass

A Monte Carlo replicate passes only if:

- efficacy gate passes;
- latency gate passes.

For each N report:

- efficacy design assurance;
- latency design assurance;
- joint design assurance;
- Monte Carlo standard error for each estimated rate.

## Candidate block counts

`16, 24, 32, 40, 48, 56, 64, 72`

Each candidate receives 200,000 seeded replicates.

Seed:

`2026092803`

## Selection rule

Choose the first candidate with:

`joint design assurance >= 0.80`

If none qualifies:

`SELECTION = NONE_WITHIN_FROZEN_RANGE`

Do not silently extend the grid.

A separate Council must decide whether to:

- extend hosted sizing;
- run a smaller replication;
- prioritize MVCA-gated local external-validity dogfood.

## Authority boundary

This analysis cannot launch physical trials.
