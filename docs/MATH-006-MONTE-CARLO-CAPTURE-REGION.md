# MATH-006 — Monte Carlo Capture-Region Localization

Inputs:
- MEMCG-005G-B
- MEMCG-005G-D
- MEMCG-005G-E

Purpose:
choose the next sampling region and sample size without guessing.

## 1. Cross-experiment same-capacity meta-counts

CAP8:
- failures 6 / valid LOW 415 = **1.4458%**

CAP32:
- failures 21 / 184 = **11.4130%**

CAP70:
- failures 41 / 434 = **9.4470%**

Other observed capacities:
- CAP12 11/68
- CAP16 2/74
- CAP19 9/75
- CAP22 7/72
- CAP26 6/81
- CAP63 8/104
- CAP64 14/105
- CAP65 9/103

All are first-touch-zero counts under the REMOTE_LOW measurement family; cross-experiment batch effects remain possible.

## 2. Hard-step family localization

Assume only for localization:
- integer threshold T;
- one rate below T;
- one rate at/above T;
- Beta(1,1) priors for both rates;
- uniform T prior over 9..70.

The combined posterior gives:

`P(T in {9,10,11,12}) = 0.999598`

with approximately equal mass:

- T=9: 0.24990
- T=10: 0.24990
- T=11: 0.24990
- T=12: 0.24990

This equality occurs because CAP9/CAP10/CAP11 have not yet been measured.

This is model-conditional localization, not proof that a hard threshold exists.

## 3. Plateau-noise Monte Carlo

For MEMCG-005G-E CAP12+:
- pooled capture rate = **8.7619%**
- observed max-minus-min arm rate range = **13.4738 points**

500,000 binomial Monte Carlo replicates under a shared plateau give:

`P(simulated range >= observed range) ~= 0.0569`

Therefore CAP12-vs-CAP16 non-monotonicity is not yet strong enough to require distinct capacity-specific mechanisms.

## 4. Confirmatory sampling design

Next frozen arm panel:

`{8,9,10,11,12,32}`

Under a hard-step candidate:
- T=9 means CAP9+ high;
- T=10 means CAP9 low, CAP10+ high;
- T=11 means CAP9/10 low, CAP11+ high;
- T=12 means CAP9/10/11 low, CAP12+ high.

Thus CAP9/10/11 directly identify the four remaining threshold locations.

## 5. Monte Carlo sample-size study

Posterior-predictive simulation used:
- low-rate posterior from combined CAP8: Beta(7,410);
- high-rate posterior from combined non-CAP8 observations: Beta(129,1173);
- LOW-admission posterior from MEMCG-005G-E: Beta(600,682);
- true T sampled uniformly from {9,10,11,12};
- future results added to existing evidence;
- posterior recomputed for T in {9,10,11,12}.

For **480 candidates per arm**:
- expected valid LOW per arm ~= **225**
- 5th..95th percentile valid LOW ~= **204..246**
- P(MAP threshold = true T) ~= **0.991**
- P(posterior mass on true T >=0.90) ~= **0.973**
- P(posterior mass on true T >=0.95) ~= **0.960**
- mean posterior threshold entropy ~= **0.036 bits**

Per-threshold MAP recovery was approximately:
- T9: 99.36%
- T10: 98.86%
- T11: 98.73%
- T12: 99.47%

## 6. Chosen scale

Use:
- 48 independent hosted blocks;
- 60 candidates/block;
- 10 candidates/arm/block;
- 6 arms;
- **2880 total candidates**
- **480 candidates/arm**

This is intentionally larger than prior refinements because the goal is now localization, not merely discovery.

## 7. Falsification logic

If CAP9/10/11 do not form a coherent low/high split consistent with one T in 9..12, the hard-step hypothesis is rejected as an adequate description.

In that case the next model should emphasize:
- capacity-specific or periodic structure;
- block/batch latent effects;
- worker virtual-layout mechanism;
rather than further threshold refinement.

Hosted research only.
