# MEMCG-005G-D Footprint Dose-Response v1

> **Status:** FROZEN DESIGN / IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Question

How does valid REMOTE_LOW first-touch-zero capture probability vary with the worker's untouched anonymous mapping capacity before first touch?

MEMCG-005G-B established:
- CAP8: 3/240 = 1.25%
- CAP70: 26/249 = 10.44%

The mechanism and shape of the dose-response are unknown.

## Frozen capacity panel

`cap_pages = {8, 32, 63, 64, 65, 70}`

Rationale:
- 8 = natural-tail anchor;
- 70 = confirmed enrichment anchor;
- 32 = intermediate;
- 63/64/65 bracket the known 64-page memcg accounting quantum.

The inclusion of 64 is a candidate-mechanism probe, **not** a preregistered threshold claim.

## Gate

Use unchanged REMOTE_LOW:

- worker starts on P;
- measured CPU S != P;
- pre_current_pages <=110;
- Q64 = 60..68 pages.

Failure = first-touch delta not Q64.
Preserve zero vs other magnitude.

## Scale

- 16 independent hosted block jobs;
- 72 fresh identities/block;
- 12 candidates/capacity/block;
- 1152 candidates total.

Capacity assignment is cyclic:

`arm_index = (identity + block) mod 6`

so each block has exactly 12 candidates per arm and temporal positions rotate across blocks.

## Primary purpose

This is a **dose-response discovery experiment**, not a final threshold-confirmation experiment.

Report for each capacity:
- valid LOW n;
- failures/successes;
- capture rate;
- Beta(1,1) posterior median and 95% interval;
- blockwise capture counts.

## Model comparison

Fit four prespecified descriptive models to the six arm aggregates:

1. CONSTANT: one shared capture rate.
2. LOGISTIC_LINEAR: `logit(p)=a+b*cap_pages`.
3. STEP64: one rate for cap<64 and one rate for cap>=64.
4. CATEGORICAL: independent rate per capacity.

Compare by AIC.

No model is allowed to become a confirmatory mechanism claim from this experiment alone.

## Shape diagnostics

Also report:
- monotonic ordering violations;
- adjacent-arm Fisher exact contrasts;
- posterior probability `P(p_70 > p_8)`;
- posterior probability for each adjacent increase via Monte Carlo;
- pre_current and affinity-to-GO distributions by arm;
- CPU mismatches;
- non-{0,Q64} failures.

## Interpretation gates

### DISCOVERY_STEP64_CANDIDATE

Descriptive label only, requiring:
- STEP64 AIC at least 6 lower than CONSTANT;
- STEP64 AIC <= LOGISTIC_LINEAR AIC - 2;
- empirical mean capture rate for {64,65,70} exceeds {8,32,63} by >=4 percentage points.

If this occurs, freeze a separate confirmatory threshold experiment.

### DISCOVERY_SMOOTH_CANDIDATE

If LOGISTIC_LINEAR beats CONSTANT by >=6 AIC and is within 2 AIC of or better than STEP64.

### DISCOVERY_OTHER_SHAPE

If CATEGORICAL wins by >=6 AIC over both STEP64 and LOGISTIC_LINEAR.

### FLAT_OR_UNRESOLVED

Otherwise.

These labels guide successor design only.

## Biopsy

No biopsy during this primary dose-response experiment.

The first-touch path must remain identical across arms except for `--max-pages`.

After the dose-response shape is known, a successor biopsy design may expand or attach a post-first-touch measurement region only after the first-touch outcome is irrevocably recorded.

## Non-claims

No K7 inference.
No DRAM/hardware claim.
No causal 64-page threshold claim.
No local-PC execution.
