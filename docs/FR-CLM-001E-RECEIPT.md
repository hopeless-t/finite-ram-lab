# FR-CLM-001E — Matched-Marginal Temporal Error Shape Receipt

Status: **PASS / SYNTHETIC TEMPORAL-DEPENDENCE HARNESS VALIDATED**

## Frozen qualification

- workflow run: 37005074443
- job: 110831326200
- execution head: 9818777233df6255bb9374a1ae2a3beb75870c79
- targeted tests: 6/6 PASS
- expected marginal label-flip rate: 0.01
- resident budget: 4
- trajectory length: 64
- replicates per arm: 8,192
- artifact ID: 11225567285
- artifact ZIP SHA256: e4a47e3247c59d4d9daaa2ad258e599b2a1d7cba9c7ef65e9e23ec79ef51a71c
- spec SHA256: 01e4be3fec53852dd7182624332e65489f59d8c66a81cf1a75687e753df1954c
- result SHA256: 4f61a271753cf67cdee4a53943d75562587d23a9d10d4a776ae3c1ff84d188e2

## Matched marginal check

Observed relevance-label flip rates:

| arm | observed label-flip rate |
|---|---:|
| IID_EVENT | 0.010036 |
| STEP_SHARED | 0.010017 |
| MARKOV_BURST | 0.009513 |

All three remain inside the frozen [0.009, 0.011] acceptance band.

Thus the experiment compares similar marginal label-error frequency while
changing dependence structure.

## Primary trajectory result

| arm | trajectory survival | affected trajectories | endpoint success | mean step exact |
|---|---:|---:|---:|---:|
| IID_EVENT | 0.334351 | 0.665649 | 0.999023 | 0.934534 |
| STEP_SHARED | 0.531738 | 0.468262 | 0.992188 | 0.958393 |
| MARKOV_BURST | 0.846191 | 0.153809 | 0.990356 | 0.982376 |

The survival ordering is:

`IID_EVENT < STEP_SHARED < MARKOV_BURST`.

This does **not** mean bursty errors are universally safer.

It means that, under matched marginal label-flip frequency in this fixture,
clustering concentrates damage into fewer trajectories.

## Conditional damage severity

Among trajectories that were actually affected:

| arm | mean max consecutive failure run | p95 max failure run | mean failed steps |
|---|---:|---:|---:|
| IID_EVENT | 4.611 | 7 | 6.294 |
| STEP_SHARED | 4.784 | 8 | 5.687 |
| MARKOV_BURST | 7.061 | 14 | 7.333 |

The MARKOV_BURST arm therefore combines:

- far fewer affected trajectories;
- substantially longer conditional failure episodes.

This is the central result.

The same marginal error rate can redistribute risk from:

`broad + shallow`

to:

`narrow + deep`.

## Why the mean is insufficient

A single scalar such as "1% error" loses at least three dimensions:

1. cross-event correlation within a step;
2. temporal correlation across steps;
3. conditional severity once failure begins.

Two systems can therefore have nearly identical marginal error rates while
having very different operational failure profiles.

## Endpoint masking remains visible

All three arms finish with endpoint success above 0.99 approximately, while
trajectory survival spans roughly 0.33 to 0.85.

Final-state correctness therefore remains a poor substitute for uninterrupted
trajectory validity in this synthetic process.

## Relation to Finite RAM rare-event methodology

This result is structurally similar to the physical Rare-state program:

`prevalence != severity != mechanism`.

A rarer state can dominate operational concern if its conditional damage is
larger.

For semantic working sets, evaluation should therefore report:

- marginal error rate;
- affected-trajectory prevalence;
- failure-run tail;
- recovery behavior;
- first-failure state.

## Important non-claim

The controlled variable is a synthetic relevance-label flip rate.

The experiment does not measure real CLM, provider, Pi, KITten, or
language-model temporal dependence.

The MARKOV persistence value 0.75 is an experimental control.

## Claim ceiling

**SYNTHETIC_TEMPORAL_ERROR_SHAPE_ONLY**

## Next

FR-CLM-001F should estimate temporal dependence from traces rather than receiving
the generating arm as ground truth.

The next tool should compare an IID failure model against a latent two-state
persistent model and report whether observed sequences contain evidence for
bursty failure.
