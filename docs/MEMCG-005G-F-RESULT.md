# MEMCG-005G-F Confirmatory Threshold Localization Result v1

> **Status:** SCIENTIFIC RUN PASS / PRIMARY DECISION REJECT_OR_UNRESOLVED_HARD_STEP
> **Run:** `36577573774`
> **Launch:** `77f0c6e160190a37f1fb07796e3f8fd6de178a66`
> **Aggregate artifact:** `11037439387`
> **Digest:** `sha256:da5eb0c5b3ab3bd17d078dda7ff052c2ed6d70af1949fb4145b0f150daf4f346`

## Frozen-arm valid REMOTE_LOW results

- CAP8: 7/226 = **3.0973%**
- CAP9: 8/226 = **3.5398%**
- CAP10: 21/243 = **8.6420%**
- CAP11: 23/231 = **9.9567%**
- CAP12: 17/225 = **7.5556%**
- CAP32: 17/223 = **7.6233%**

CPU mismatches: **0**.

## Primary Bayesian threshold result

Candidate family: `T in {9,10,11,12}`.

Posterior:
- T=9: **2.7866%**
- T=10: **95.5757%**
- T=11: **1.4976%**
- T=12: **0.1401%**

MAP:
`T=10`

MAP / second-best posterior odds:
`34.30:1`

T10 pooled split:
- low side CAP8+CAP9: 15/452 = **3.3186%**
- high side CAP10+CAP11+CAP12+CAP32: 78/922 = **8.4599%**

Frequentist audit:
- risk difference = **+5.1413 percentage points**
- odds ratio = **2.6924**
- Fisher two-sided p = **2.268e-4**

## Model adequacy

AIC:
- CONSTANT: **682.4343**
- HARD_STEP(T=10): **672.1670**
- CATEGORICAL: **676.9986**

CATEGORICAL does not beat HARD_STEP by the frozen rejection margin.

## Why the frozen primary still rejects

The frozen design required **zero non-{0,Q64} failures**.

Two valid REMOTE_LOW nonzero failure morphologies occurred:

1. CAP32, block35, identity0:
   - first-touch delta = **+1 page**
   - pre_current = 98 pages
   - migration delta = 0
   - affinity-to-GO = 216.112 us

2. CAP9, block36, identity19:
   - first-touch delta = **+57 pages**
   - pre_current = 106 pages
   - migration delta = 0
   - affinity-to-GO = 223.467 us

Therefore the preregistered decision is:

`REJECT_OR_UNRESOLVED_HARD_STEP`

This decision is not changed post hoc.

## Accepted interpretation

The capacity signal strongly favors a transition near CAP10 inside the restricted hard-step family, but the literal model that all rare first-touch failures belong to the exact-zero phenotype is falsified by two distinct nonzero morphologies.

The next experiment must separate:
- exact-zero capture phenotype;
- nonzero anomalous first-touch phenotype.

No causal kernel-path claim.
No K7 inference.
Hosted research only.
