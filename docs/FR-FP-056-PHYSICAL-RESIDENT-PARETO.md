# FR-FP-056 — Physical resident/service/actuation Pareto frontier

Status: **REUSED PHYSICAL EVIDENCE PARETO CANDIDATE**

Parent: **FR-FP-055**

## Why

FR-FP-055 physically proves that memory rent can move the Governor along a
resident byte-time frontier.

It does not prove that one memory rent is universally best.

Three quantities remain distinct:

1. resident byte-time;
2. semantic service cost;
3. physical tier-actuation cost.

FR-FP-056 preserves those dimensions instead of inventing one hidden score.

## Four physical anchors

The frozen hosted anchors are:

    lambda=0
    lambda=0.10
    lambda=0.25
    lambda=0.40

For each anchor retain:

- physical resident MiB-round;
- modeled semantic service ms;
- hosted physical actuation ms.

## Pareto rule

A policy is dominated only if another tested policy is no worse in all three
dimensions and strictly better in at least one.

No unit conversion is performed for this Pareto test.

## Explicit scalar policy

Only when an external memory rent lambda is explicitly supplied may the two
time dimensions and resident byte-time be combined:

    score
      =
    semantic_service_ms
      + physical_actuation_ms
      + lambda * resident_mib_round

The resulting crossovers are unit-consistent because lambda has units:

    ms / MiB-round

They select only among the four physically tested anchors.

They are not a claim that an untested intermediate policy cannot be better.

## Why this matters

The Governor can now export a typed control surface rather than a fake
all-purpose performance number.

External policy decides how much resident byte-time is worth.

The research system supplies the physical tradeoff.

## Claim ceiling

**FOUR_ANCHOR_HOSTED_PHYSICAL_PARETO_AND_CANDIDATE_CROSSOVERS_ONLY**
