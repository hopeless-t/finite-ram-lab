# FR-CLM-001B — Stochastic Omission and Rare-Event Harness

Status: **SYNTHETIC STOCHASTIC HARNESS VALIDATION**

## Goal

FR-CLM-001A proved that the lab can separate resident size, semantic omission,
and resident interference on a deterministic corpus.

FR-CLM-001B asks the next question:

> Can the same apparatus expose low-frequency selector failures without hiding
> them inside a high average success rate?

This experiment still does **not** run a language model.

## Design

The frozen corpus and budgets from FR-CLM-001A are reused:

`1, 2, 4, 6, 8` resident events.

Each budget/arm receives:

- 512 replicated passes;
- 4 cases per replicate;
- 2,048 observations per budget/arm.

Two arms are evaluated.

### APPEND_TRUNCATE

The recency-only reference from FR-CLM-001A.

### NOISY_KEY_AWARE

Start from deterministic KEY_AWARE, then independently inject a 0.5% synthetic
omission probability for each selected required-latest event.

The random-looking draw is generated from SHA256 over the frozen experiment
identity, so every omission is reproducible across runs.

When a required event is omitted:

1. that exact event is blocked from immediate reselection;
2. the resident set is back-filled from the newest available events;
3. resident count remains fixed whenever enough events exist.

This isolates semantic sufficiency from resident-size shrinkage.

## Primary endpoint

`exact_rate`

## Uncertainty

Every success rate carries a Wilson 95% interval.

The synthetic pressure knee is the first budget where both are true:

- exact rate >= 0.95;
- Wilson 95% lower bound >= 0.95.

This prevents a tiny sample with a lucky average from qualifying as a knee.

## Rare-event capture

Every failure contributes a normalized signature:

`missing=<keys>|stale=<keys>`

The first 16 failures per budget/arm are retained as biopsies containing:

- replicate id;
- case id;
- resident indices;
- omitted required indices;
- missing required keys;
- stale required keys;
- interference event count.

The goal is not to erase rare failures. The goal is to make them searchable and
replayable.

## Acceptance

The frozen fixture is accepted only if:

- APPEND_TRUNCATE qualified knee remains budget 8;
- NOISY_KEY_AWARE qualified knee is budget 2;
- NOISY_KEY_AWARE at budget 2 captures at least one failure;
- its failure rate remains below 5%.

## Interpretation boundary

The 0.5% omission rate is an injected fixture, not an observed CLM error rate.

A qualified synthetic knee is not a universal context budget.

No real CLM, Pi, KITten worker, provider, or language model is evaluated.

## Claim ceiling

**SYNTHETIC_STOCHASTIC_SEMANTIC_WORKING_SET_ONLY**

## Next if PASS

FR-CLM-001C should stop fixing the omission probability and sweep selector
reliability as another pressure dimension.

That creates a two-dimensional surface:

`resident budget x selector reliability -> semantic survival`

The first real-model experiment should only begin after that surface and its
failure-biopsy contract are stable.
