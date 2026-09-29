# MEMCG-005G-E Adaptive Capacity Refinement v1

> **Status:** FROZEN DESIGN / IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Question

Where, between CAP8 and CAP32, does the rare first-touch-zero capture probability transition, and is that transition step-like or smooth?

This experiment is motivated by MEMCG-005G-D and MATH-005.

## Frozen capacity panel

`{8,12,16,19,22,26,32,70}`

Roles:
- 8: confirmed low-rate anchor;
- 32: first observed enriched point;
- 70: independent enriched plateau anchor;
- 12/16/19/22/26: adaptive refinement points;
- 19: current maximum expected-information-gain point under the step-family posterior.

No capacity value may be moved after launch.

## Gate

Use unchanged REMOTE_LOW:
- startup P;
- measured S != P;
- pre_current_pages <=110;
- Q64 = 60..68 pages.

Failure = first-touch delta not Q64.
Preserve zero vs other magnitude.

## Scale

- 16 independent hosted blocks;
- 80 candidates/block;
- 10 candidates/capacity/block;
- 1280 total candidates.

Assignment:
`capacity_index=(identity+block) mod 8`

This rotates temporal positions across blocks.

## Primary outputs

For each capacity:
- valid LOW n;
- first-touch-zero failures;
- capture rate;
- Beta(1,1) posterior median and 95% interval;
- blockwise counts.

CPU mismatches and non-{0,Q64} failures must be reported.

## Prespecified shape models

Fit aggregate binomial likelihoods:

1. CONSTANT: one shared rate.
2. HARD_STEP: unknown integer threshold T in 9..32 plus low/high rates.
3. SMOOTH_SIGMOID: low plateau pL, high plateau pH, center c0, width w.
4. CATEGORICAL: one rate per capacity.

Use AIC as a descriptive model comparison.

HARD_STEP threshold is chosen only from the frozen integer grid 9..32.

SMOOTH_SIGMOID:
`p(c)=pL+(pH-pL)*sigmoid((c-c0)/w)`
with 0<=pL,pH<=1 and w>0.

## Discovery labels

### DISCOVERY_HARD_STEP
Require:
- HARD_STEP AIC <= CONSTANT-6;
- HARD_STEP AIC <= SMOOTH_SIGMOID-2;
- posterior/model threshold support is concentrated enough that the 90% threshold interval spans <=8 pages.

### DISCOVERY_SMOOTH
Require:
- SMOOTH_SIGMOID AIC <= CONSTANT-6;
- SMOOTH_SIGMOID AIC <= HARD_STEP+2;
- fitted width w >=3 pages.

### DISCOVERY_COMPLEX
Require:
- CATEGORICAL AIC <= min(HARD_STEP,SMOOTH_SIGMOID)-6.

Otherwise:
`UNRESOLVED_TRANSITION`.

These are discovery labels only.

## Bayesian threshold refinement

Under the HARD_STEP family with:
- uniform T prior over integers 9..32;
- independent Beta(1,1) low/high rate priors;

report:
- posterior probability for every T;
- posterior median and 90%/95% intervals;
- posterior entropy H(T).

Also compute expected information gain for every untested integer capacity 9..31, conditional on this experiment's posterior, to nominate the next point if further refinement is needed.

## Biopsy

No biopsy in this experiment.

## Non-claims

No causal threshold claim.
No 64-page claim.
No K7 inference.
No hardware-memory claim.
No local-PC execution.
