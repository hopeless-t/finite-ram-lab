# MATH-007 — T10 Robustness and Morphology Separation

Input:
MEMCG-005G-F run `36577573774`.

Purpose:
audit whether the T10 capacity signal is an artifact of block/batch variation or of the two nonzero failure morphologies.

## 1. Frozen primary

The preregistered primary decision is:
`REJECT_OR_UNRESOLVED_HARD_STEP`

because two non-{0,Q64} failures violated the morphology invariant.

This document does not override that decision.

## 2. Exact-zero sensitivity analysis

Remove the two nonzero anomalous rows from the threshold localization calculation.

Exact-zero counts become:

- CAP8: 7/226
- CAP9: 7/225
- CAP10: 21/243
- CAP11: 23/231
- CAP12: 17/225
- CAP32: 16/222

Restricted hard-step posterior:

- T=9: 1.4353%
- T=10: **97.4957%**
- T=11: 0.9860%
- T=12: 0.0830%

Thus the T10 signal is not created by the two nonzero anomalies.

This is a sensitivity analysis only.

## 3. Block-conditioned Monte Carlo permutation

Null:
within each hosted block, preserve:
- the exact number of valid REMOTE_LOW rows;
- the exact capacity allocation among those rows;
- the exact total number of first-touch failures;

but randomly reassign failure labels to valid LOW rows inside the block.

This removes a capacity effect while preserving block-level latent failure propensity.

Observed T10 pooled risk difference:
`+5.1413 percentage points`

Monte Carlo:
- **300,000** conditional replicates
- probability of simulated risk difference >= observed:
  `p ~= 3.50e-4`

Therefore ordinary block-level heterogeneity alone does not readily explain the T10 split.

This is an exploratory randomization audit, not the frozen primary test.

## 4. Leave-one-block-out stability

Recompute the restricted threshold posterior 48 times, dropping one hosted block each time.

Result:
- MAP threshold = **T10 in 48/48 leave-one-block-out fits**
- T10 posterior range ≈ **89.57%..98.17%**

No single hosted block creates the T10 localization.

## 5. Morphology conclusion

The data support at least two measurement phenotypes:

A. exact-zero first-touch capture;
B. rare nonzero anomalous first-touch deltas.

The frozen 005G-F model conflated them under one failure category and was therefore too strict.

The scientifically clean successor is not to relax 005G-F after seeing the data.

It is to prospectively define **exact-zero** as the target phenotype and track nonzero anomalies as a separate endpoint.

## 6. Independent zero-phenotype sample-size Monte Carlo

Planning assumptions from 005G-F:
- valid-LOW admission rate ≈ 1374/2880 = 47.71%
- low-side exact-zero rate ≈ 14/451 = 3.10%
- high-side exact-zero rate ≈ 77/921 = 8.36%
- true candidate threshold T10 for calibration only.

Standalone future-run simulations:

| candidates / arm | expected valid LOW / arm | P(MAP=T10) | P(T10 posterior >= .90) | P(T10 posterior >= .95) |
| ---: | ---: | ---: | ---: | ---: |
| 480 | ~229 | 88.6% | 55.0% | 43.3% |
| 600 | ~286 | 92.7% | 68.6% | 58.4% |
| 720 | ~343 | 95.0% | 78.6% | 70.1% |
| 960 | ~458 | 97.7% | 90.3% | 85.8% |
| 1200 | ~572 | 99.0% | 95.5% | 93.2% |

This table is design calibration, not evidence for T10.

## 7. Recommended successor scale

For an independent confirmatory zero-phenotype replication:
- preferred: **960 candidates/arm**
- six arms -> **5760 total candidates**
- with 10 candidates/arm/block -> **96 independent hosted blocks**

This is intentionally larger than 005G-F.

Because this is a material increase in hosted compute, implementation/launch should remain separated from human approval of the compute expenditure.

Hosted research only.
