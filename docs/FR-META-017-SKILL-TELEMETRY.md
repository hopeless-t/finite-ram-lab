# FR-META-017 — Compiled Skill Telemetry Plane

Status: **DOGFOOD OBSERVATION CANDIDATE**

Parent: **FR-META-016**

## Question

Decision skills are now compiled and lifecycle-governed.

The next question is empirical:

> Do they actually reduce resident decision context while preserving qualified
> outcomes over time?

FR-META-017 adds prospective telemetry for that question.

## First real event

FR-META-015 is the first prospective compiled-skill decision.

Its decision facts selected EXACT_REUSE_BEFORE_SAMPLE_REDUCTION and did not fall
back to the full FR-META history.

The experiment then passed the original frozen ABA semantic gate.

The telemetry event records:

- selected skill IDs;
- primary action;
- frozen source-history character surface;
- selected resident-context character surface;
- full-history fallback flag;
- durable outcome;
- authority expansion;
- later reversal / invalidation when it becomes observable.

## Missing future evidence

A newly successful decision has not yet had time to be contradicted.

Therefore:

    reversal = null

is not converted to:

    reversal = false

Aggregate reversal metrics always carry observed count and coverage.

This prevents recent skills from appearing artificially perfect merely because
there has not yet been time for them to fail.

## Context metric

The first event compares the explicit compiled decision context against the
frozen FR-META-004..013 source-history surface.

The current exact-reuse capsule reduces that surface by more than 97 percent.

This remains a character-surface measurement, not a model-internal token or
latency claim.

## Effect claim gate

One successful event is useful dogfood, but it is not enough to claim the skill
layer is generally superior.

The first frozen minimum is 20 prospective events with observed reversal
coverage before a general effect claim may be considered.

That threshold itself may later become a meta-research question.

## Data boundary

Allowed:

- explicit decision facts;
- selected skill IDs;
- context character count;
- fallback flag;
- durable experiment outcome;
- later explicit reversals / invalidations.

Forbidden:

- private chain-of-thought;
- hidden reasoning tokens;
- backfilled success or reversal values from guesses.

## North-Star metric direction

A future mature metric is:

    qualified surviving decisions
    -----------------------------
       resident context chars

with separate penalties for fallback, reversal, rare-failure miss, and authority
violation.

## Claim ceiling

**ONE_PROSPECTIVE_SKILL_DOGFOOD_EVENT_AND_TELEMETRY_SCHEMA_ONLY**
