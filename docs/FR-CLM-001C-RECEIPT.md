# FR-CLM-001C — Reliability × Residency Surface Qualification Receipt

Status: **PASS / SYNTHETIC SURFACE VALIDATED**

## Frozen qualification

- workflow run: 37003934504
- job: 110827697507
- execution head: 405110a6261ebad1b445411dd8d0797fda70ba11
- targeted tests: 6/6 PASS
- surface observations: 409,600 case evaluations
- artifact ID: 11225225846
- artifact ZIP SHA256: 3c8f3f517032291d2e413599f163707b9a87b77fbb86e2c5b27c5b4ee6a5e6b4
- spec SHA256: 995cebdc4e42eb174dd35b6a8700d372cf7341543a61acefc4c634462fd026e2
- result SHA256: 229e67abf27b3a1e090f74605158264d62eec8467648dfcba0fc93d8859103f4

## Qualified reliability-residency frontier

The minimum resident budget whose exact rate and Wilson 95% lower bound both
remain at least 0.95 is:

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

The frozen synthetic surface therefore shows:

`selector reliability down -> required resident redundancy up`.

## Boundary examples

The transition is not a reporting artifact.

Representative cells:

- p=0.01, budget 2: exact ≈ 0.963257; Wilson95 lower ≈ 0.958961 -> QUALIFIED
- p=0.02, budget 2: exact ≈ 0.926514; Wilson95 lower ≈ 0.920661 -> NOT QUALIFIED
- p=0.02, budget 4: exact ≈ 0.976074; Wilson95 lower ≈ 0.972535 -> QUALIFIED
- p=0.05, budget 4: exact ≈ 0.939941; Wilson95 lower ≈ 0.934587 -> NOT QUALIFIED
- p=0.05, budget 6: exact ≈ 0.973877; Wilson95 lower ≈ 0.970195 -> QUALIFIED
- p=0.10, budget 6: exact ≈ 0.943604; Wilson95 lower ≈ 0.938397 -> NOT QUALIFIED
- p=0.10, budget 8: exact = 1.0 -> QUALIFIED

At full synthetic residency, all events are retained and every error level
returns exact rate 1.0, preserving the full-context reference.

## Rare-event sentinel

At:

- selector error p = 0.001;
- resident budget = 2;

the harness captured:

- failures: 30 / 8,192;
- successes: 8,162 / 8,192;
- exact rate: 0.996337890625;
- Wilson95 lower: 0.9947769851;
- failure biopsies: non-zero and bounded by the frozen capture limit.

Thus the low-noise operating point remains qualified without averaging rare
selector failures away.

## Pre-qualification harness repair

An earlier workflow run, 37003776652, failed before qualification with:

`rare_event_sentinel_count_unexpected`.

The frontier check executed before that assertion and did not fail.

Inspection found that the implementation used hash domain
`RELEVANCE_FLIP` while the frozen deterministic reference vector had been
generated under `SCORE_FLIP`.

The repair:

- changed only the deterministic pseudo-random hash-domain tag;
- bound `SCORE_FLIP` explicitly in the frozen spec;
- did not change selector error probabilities;
- did not change budgets;
- did not change the 95% exact/Wilson qualification thresholds;
- did not change the expected frontier.

The repaired frozen run then passed.

This failure is retained because deterministic fixture identity is part of the
evidence contract.

## What was learned

FR-CLM-001A showed that semantic obligation need not equal resident context.

FR-CLM-001B showed that rare semantic loss must remain visible.

FR-CLM-001C adds a new result shape:

`semantic capacity can compensate for imperfect selection`.

In this synthetic corpus, the tradeoff is discrete and measurable as a
reliability-residency frontier rather than a single context-size optimum.

This suggests that future real context managers should be compared on at least
two axes:

1. selector / rewrite reliability;
2. simultaneously resident semantic budget.

Token count alone cannot distinguish them.

## Important non-claim

The selector and its error probabilities are synthetic controls.

No empirical CLM, Pi, KITten, provider, or language-model reliability is
measured here.

The frontier is specific to the frozen corpus and synthetic selector.

## Claim ceiling

**SYNTHETIC_RELIABILITY_RESIDENCY_SURFACE_ONLY**

## Next

FR-CLM-001D should add repeated context rewrites and trajectory length.

The next question is whether local semantic survival compounds approximately as:

`S_trajectory ~= product(S_step)`

or whether state structure, recovery, and correlated failures create a
different law.

That experiment should preserve per-step biopsies and identify the first
irrecoverable semantic loss event.
