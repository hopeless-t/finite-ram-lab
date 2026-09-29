# MEMCG-005G-A Early-Transient + Residual-Stock Biopsy v1

> **Status:** FROZEN DESIGN / IMPLEMENTED WITH THIS BOUNCE / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Motivation

MEMCG-005E + MEMCG-005F REMOTE_LOW observations contained 213 valid LOW probes and 3 first-touch zero-delta failures.

All three failures occurred at block-local identity 0..7; identity 8+ was 180/180 Q64.

This boundary is post-hoc in the historical data. MEMCG-005G-A freezes it prospectively:

- EARLY = identity 0..7
- STEADY = identity 8..31

No cutpoint search is permitted after launch.

## Question

Is REMOTE_LOW first-touch failure concentrated in a reproducible block-start transient, and what residual stock depth is visible when such a failure occurs?

## Fixed gate

REMOTE_LOW:
- worker starts on P;
- measured CPU is remote S != P;
- pre_current_pages <= 110;
- Q64 = touch delta 60..68 pages.

## Independent blocks

Use 24 independent GitHub-hosted block jobs.

Each block creates 32 fresh identities.

Total candidates: 768.

Each block independently starts from a fresh hosted job so the "block-start" condition is genuinely recreated.

## Primary endpoint

Among valid REMOTE_LOW identities only, compare first-touch failure probability:

- EARLY identities 0..7
- STEADY identities 8..31

Failure = first-touch delta is not Q64.

Preserve exact zero vs other magnitude.

### SUPPORT_EARLY_TRANSIENT

Require:
- EARLY LOW n >= 70;
- STEADY LOW n >= 200;
- EARLY failure rate >= 5%;
- STEADY failure rate <= 2%;
- one-sided Fisher exact EARLY failure > STEADY failure: p < 0.01;
- zero CPU mismatches;
- zero non-{0,Q64} first-touch failures.

### REJECT_EARLY_TRANSIENT

If sample-size requirements are met and either:
- EARLY failure rate <= 2%; or
- EARLY minus STEADY failure rate < 2 percentage points and Fisher p >= 0.10.

Otherwise INCONCLUSIVE.

## Secondary mathematics

Report:
- risk difference EARLY - STEADY;
- risk ratio with 0.5 Haldane correction;
- Beta(1,1) posterior intervals for each failure rate;
- Bayes factor BF10 for two independent failure rates vs one shared failure rate;
- failure count by exact identity 0..31.

These do not override the preregistered primary decision.

## Failure biopsy

Only after the primary first-touch result has been recorded:

If a valid REMOTE_LOW first touch is exactly 0 pages, continue touching fresh anonymous pages on S.

Measure each touch with memory.current.

Stop at first Q64 or after total touch index 65.

If first Q64 occurs at touch t:

`residual_depth_candidate = t - 1`

Under the simple consume-stock model, this is the number of pre-existing stock pages consumed before a fresh Q64 batch was required.

Possible values: 1..64.

If no Q64 by touch65, mark:

`residual_depth_candidate = CENSORED_GT_64`

This estimator is source-consistent but not a causal proof because other refill/drain paths may intervene.

Preserve full biopsy delta sequence.

## Worker

Reuse `experiments/memcg005d_worker.c`.

Start with `--max-pages 70` so biopsy pages are pre-mapped before the measured first touch.

The pages remain untouched until commanded.

## Interpretation

If SUPPORT_EARLY_TRANSIENT:
the current ~1.6% aggregate tail is not well-described as homogeneous random failure; a block-start hidden phase is independently supported.

If biopsy depths cluster:
use the cluster to design MEMCG-005G-B causal warm-up interventions.

If REJECT:
the historical early concentration was likely a post-hoc fluctuation; retain REMOTE_LOW at its confirmatory 98.37% reliability.

## Non-claims

No K7 inference.
No hardware-memory claim.
No local-PC execution.
