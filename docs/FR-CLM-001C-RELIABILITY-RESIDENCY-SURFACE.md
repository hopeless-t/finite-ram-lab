# FR-CLM-001C — Reliability × Residency Surface

Status: **SYNTHETIC SURFACE QUALIFICATION**

## Goal

FR-CLM-001B proved that low-frequency semantic omissions can remain visible
inside an otherwise strong average success rate.

FR-CLM-001C asks a different question:

> When the selector itself becomes less reliable, how much extra resident
> context is needed to preserve qualified semantic survival?

This turns a one-dimensional pressure sweep into a two-dimensional surface.

## Synthetic selector

For each case, the ground-truth relevant events are the latest events for the
declared query keys.

Every event is given a predicted relevance label.

With probability `p`, the label is flipped:

- required-latest event -> false negative;
- distractor or superseded event -> false positive.

Selection then ranks:

1. predicted-relevant events first;
2. newer events first as the deterministic tie-break.

The first `B` events become resident.

Unlike FR-CLM-001B's hard omission fixture, a ranking error is not permanently
deleted from the universe. A larger resident budget can recover the missed fact.

## Surface

Resident budgets:

`1, 2, 4, 6, 8`

Selector error probabilities:

`0, 0.001, 0.0025, 0.005, 0.01, 0.02, 0.03, 0.05, 0.10, 0.20`

Each cell receives:

- 2,048 replicates;
- 4 cases per replicate;
- 8,192 observations.

Total frozen case observations:

`10 x 5 x 8,192 = 409,600`.

## Qualified survival rule

A surface cell qualifies only when both are true:

- exact rate >= 0.95;
- Wilson 95% lower bound >= 0.95.

For each selector error probability, the primary frontier statistic is:

`minimum resident budget that qualifies`.

## Frozen frontier target

| selector error p | selector reliability | minimum qualified budget |
|---:|---:|---:|
| 0 | 1.000 | 2 |
| 0.001 | 0.999 | 2 |
| 0.0025 | 0.9975 | 2 |
| 0.005 | 0.995 | 2 |
| 0.01 | 0.99 | 2 |
| 0.02 | 0.98 | 4 |
| 0.03 | 0.97 | 4 |
| 0.05 | 0.95 | 6 |
| 0.10 | 0.90 | 8 |
| 0.20 | 0.80 | 8 |

This is the first explicit synthetic trade curve between cognition quality and
resident semantic capacity in Finite RAM Lab.

## Rare-event sentinel

The low-noise cell:

- p = 0.001;
- budget = 2;

must remain statistically qualified while still exposing reproducible failures.

Frozen expected failures:

`30 / 8,192`.

This verifies that the 2-D surface does not lose the rare-event biopsy
capability introduced in FR-CLM-001B.

## Failure-state biopsy

The first failures in every cell retain:

- replicate id;
- case id;
- resident indices;
- required-latest indices;
- false-negative required indices;
- false-positive distractor indices;
- missing required keys;
- stale required keys;
- interference event count.

The failure is therefore tied back to a concrete selector mistake rather than
being represented only as an aggregate score decrement.

## Full-residency reference

At budget 8 every event in the frozen corpus is resident.

Therefore exact rate must remain 1.0 at every selector-error level.

This is an important falsifier: if full residency ever fails, the defect is in
the harness or semantic evaluator rather than in finite selection.

## Interpretation

The expected shape is not "better selector always wins".

It is:

`selector reliability ↓ -> required resident redundancy ↑`

This is directly useful for later CLM/Pi/KITten experiments because a context
manager can be evaluated as a pair:

`selection quality + resident budget`

rather than attributing all outcomes to token count alone.

## Important non-claim

The selector is synthetic.

The error probabilities are injected experimental controls, not measured error
rates for any real model or context manager.

The resulting frontier is specific to this frozen corpus and fixture.

## Claim ceiling

**SYNTHETIC_RELIABILITY_RESIDENCY_SURFACE_ONLY**

## Next if PASS

FR-CLM-001D should introduce trajectory length and repeated context rewrites.

That would test whether a small per-step selector error compounds across time:

`per-step survival -> trajectory survival`

and connect the semantic Finite RAM lane directly to the existing
Low-interference cognition / trajectory-survival hypothesis.

## Execution gate

Qualification is accepted only from the frozen GitHub Actions workflow on the exact branch head, with the result artifact digest recorded in a receipt.
