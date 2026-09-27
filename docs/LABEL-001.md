# LABEL-001 — Natural Residency Outcome Audit

> **Status:** FROZEN ANALYSIS CONTRACT

## Scientific question

How faithfully does the experimental EXP-003 assignment label correspond to the natural pre-retouch residency outcome that occurs under NO_HINT?

This matters because future semantic-provider calibration should be grounded in the state that actually emerges without intervention, not only in the factorial assignment proxy.

## Source

Canonical EXP-003 aggregate:

- run: `36253713012`
- artifact id: `10910048127`
- artifact name: `EXP-003-aggregate-36253713012`
- artifact SHA-256: `08bfd999833274db962f9a017933aa53216d8fdff8ea003a54b81ce33ebed4d3`
- member: `trials.csv`
- member SHA-256: `29aa46c700b817785bdc67ae4a6eb3c3330887ff5a06efd1f7516aa6ed53ba66`

The analysis must fail closed if the supplied `trials.csv` does not match the frozen member digest.

## Natural-outcome arm

Use only:

`arm == no_hint`

Reason:

CORRECT_PAGEOUT and WRONG_PAGEOUT modify residency before the stored `residency_pre_retouch` measurement and therefore cannot define the no-intervention natural outcome.

Expected data:

- 16 runner blocks;
- 160 / 162 MiB;
- 128 NO_HINT trials.

## Primary observable class

Define:

`observable_misaligned = hot_fraction < cold_fraction`

Interpretation:

the region required by the upcoming semantic HOT reuse is less resident than the COLD region after the pressure burst under NO_HINT.

Exact ties are:

`AMBIGUOUS`

They must be reported and excluded from binary sensitivity/specificity calculations rather than silently assigned.

## Assignment proxy

The pre-existing factorial proxy is:

`assignment_misaligned = not aligned`

where `aligned` is the frozen EXP-003 relationship between initial fault order and future HOT position.

LABEL-001 does not replace or rewrite that historical definition.

It audits how well it maps to the observable natural outcome.

## Primary outputs

Report pooled:

- confusion matrix;
- observable-misalignment prevalence;
- assignment-proxy sensitivity;
- assignment-proxy specificity;
- agreement;
- ambiguous count.

Uncertainty:

- 100,000 runner-block bootstrap resamples;
- 95% percentile intervals;
- runner block is the resampling unit.

## Pressure-stratified outputs

For 160 MiB and 162 MiB separately, report descriptive:

- confusion matrix;
- prevalence;
- sensitivity;
- specificity;
- agreement.

These are secondary descriptive strata and do not replace the pooled primary audit.

## Continuous mechanism check

Primary continuous residency score:

`residency_gap = hot_fraction - cold_fraction`

Report:

- Spearman association with `log(hot_retouch_ms)`;
- runner-block bootstrap 95% interval;
- descriptive geometric HOT-retouch by observable class.

This checks whether the observable class is anchored to the mechanism-sensitive reuse cost rather than being a bookkeeping label only.

## Secondary sensitivity analysis

Use:

`hot_first16_fraction - cold_first16_fraction`

only as a secondary audit.

It cannot redefine the primary whole-region label after seeing the result.

## Prohibited work

LABEL-001 must not:

- train a provider;
- tune a residency threshold;
- introduce PAGEOUT;
- alter the frozen 16 MiB intervention range;
- pool intervention arms into the natural-label analysis;
- claim production prevalence.

## Authority boundary

Retrospective label validation only.
