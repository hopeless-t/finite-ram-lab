# FR-META-018 — Compile the reclaimability survival law

Status: **DOGFOOD COMPILATION CANDIDATE**

Parent: **FR-META-017**

Evidence: **FR-FP-009 / PR #127**

## Why

FR-FP-009 started with a Monte Carlo / simulator research path and ended with an
analytic law that matched the simulator exactly across 252 frozen cells.

That is precisely the kind of repeated decision that should stop consuming a
full research loop.

## Compiled skill

ID:

    SEMANTIC_OOM_SURVIVAL_LAW

Action:

    USE_ANALYTIC_SURVIVAL_LAW

Monte Carlo:

    SKIP

Maturity:

    QUALIFIED

The maturity remains QUALIFIED because the law has one bounded qualification
campaign. It is not promoted to STABLE merely because that campaign contains
252 cells.

## Trigger facts

Every fact is required explicitly:

- semantic-OOM question;
- one hot-state arrival per step;
- always-preemptive transfer;
- at most one new transfer initiation per step;
- fixed integer transfer lead;
- no transfer failures;
- safe reclaimability collapses retained hot history to one state.

If any fact is missing, the compiler returns unresolved facts.

If a trigger is contradicted, the skill is not selected.

## Why this is not overfitting the skill system

The compiled action does not claim the survival law applies to arbitrary memory
systems.

It carries the exact assumptions that made the proof work.

The invalidation list includes changes to state-arrival rate, transfer
throughput, lead-time semantics, transfer failures, and safe-history collapse.

## Research-speed consequence

The expensive path was:

    Monte Carlo phase discovery
      -> timing/coverage biopsy
      -> interaction frontier
      -> survival-law derivation
      -> 252-cell exact validation

The future resident decision is now:

    seven explicit facts
      -> one small capsule
      -> analytic law
      -> MC skipped

That is the desired self-hosting behavior of Finite RAM Lab.

## Claim ceiling

**QUALIFIED_DECISION_SKILL_FOR_FROZEN_SYNTHETIC_SURVIVAL_LAW_ONLY**
