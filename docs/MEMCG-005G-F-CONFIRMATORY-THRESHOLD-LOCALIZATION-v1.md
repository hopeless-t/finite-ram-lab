# MEMCG-005G-F Confirmatory Threshold Localization v1

> **Status:** FROZEN DESIGN / IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Question

Within the hard-step candidate family, is the REMOTE_LOW first-touch-zero transition located at T in {9,10,11,12}, and if so which T?

This is a confirmatory localization experiment.

If the new arms do not form a coherent split, the hard-step description is rejected.

## Frozen arms

`cap_pages = {8,9,10,11,12,32}`

Interpretation under candidate threshold T:
- T=9: 8 low; 9/10/11/12/32 high
- T=10: 8/9 low; 10/11/12/32 high
- T=11: 8/9/10 low; 11/12/32 high
- T=12: 8/9/10/11 low; 12/32 high

## Scale

- 48 independent hosted block jobs
- 60 candidates/block
- 10 candidates/arm/block
- **2880 total candidates**
- **480 candidates/arm**

Arm assignment rotates:
`capacity_index=(identity+block) mod 6`

## Gate

Unchanged REMOTE_LOW:
- startup P
- measured S != P
- pre_current_pages <=110
- Q64 = 60..68 pages

Failure = first-touch delta not Q64.
Preserve zero vs other magnitude.

## Primary Bayesian threshold posterior

Candidate thresholds:
`T={9,10,11,12}`

Use:
- uniform prior over four T;
- independent Beta(1,1) priors for low/high capture rates;
- aggregate binomial marginal likelihood.

Primary SUPPORT_LOCALIZED_T requires:
- zero CPU mismatches;
- zero non-{0,Q64} failures;
- posterior mass of MAP T >=0.90;
- posterior odds MAP T / second-best T >=10;
- fitted low-rate < fitted high-rate;
- posterior predictive arm ordering consistent with the MAP split.

Otherwise:
`REJECT_OR_UNRESOLVED_HARD_STEP`.

A rejection is a valid scientific outcome.

## Frequentist audit

For the MAP split only:
- report pooled low/high counts;
- Fisher exact two-sided;
- risk difference;
- odds ratio.

This audit does not replace the Bayesian primary.

## Monte Carlo calibration

MATH-006 estimated for 480 candidates/arm under current posterior predictive assumptions:
- expected valid LOW ~=225/arm
- P(MAP=true T) ~=0.991
- P(true T posterior >=0.90) ~=0.973

These values are design calibration, not decision thresholds.

## Model adequacy audit

Also fit:
- CONSTANT
- HARD_STEP over T={9,10,11,12}
- CATEGORICAL six-rate model

If CATEGORICAL AIC beats HARD_STEP by >=6, force:
`REJECT_OR_UNRESOLVED_HARD_STEP`
even if one T has high posterior within the restricted step family.

## Biopsy

No biopsy.

## Non-claims

No causal kernel-path claim.
No K7 inference.
No DRAM/hardware claim.
No local-PC execution.
