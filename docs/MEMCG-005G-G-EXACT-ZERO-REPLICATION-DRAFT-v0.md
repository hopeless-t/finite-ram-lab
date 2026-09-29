# MEMCG-005G-G Exact-Zero Phenotype Replication — Draft v0

> **Status:** DRAFT / NOT FROZEN / NOT IMPLEMENTED / NOT LAUNCHED

## Goal

Independently test whether the exact-zero first-touch phenotype localizes at T=10 across:

`cap_pages = {8,9,10,11,12,32}`

without treating nonzero anomalous deltas as the same species.

## Primary endpoint

For valid REMOTE_LOW rows:

`ZERO_CAPTURE := first_touch_delta_pages == 0`

Q64 and other nonzero deltas are not ZERO_CAPTURE.

Nonzero non-Q64 deltas are recorded as a separate morphology endpoint.

## Primary hypothesis family

Candidate thresholds:
`T={9,10,11,12}`

Primary support for T10 should require prospectively:
- posterior mass T10 >= .90;
- posterior odds T10 / second-best >=10;
- pooled exact-zero rate below T10 < rate at/above T10;
- categorical adequacy audit does not beat T10 step by >=6 AIC;
- zero CPU mismatches.

Nonzero morphology count is reported separately and does not automatically invalidate the exact-zero endpoint.

## Candidate scale

Preferred Monte-Carlo-calibrated scale:

- 96 independent hosted blocks;
- 60 candidates/block;
- 10 candidates/arm/block;
- **5760 total candidates**;
- **960 candidates/arm**.

Expected under current planning assumptions:
- ~458 valid LOW/arm;
- P(MAP=T10) ~97.7%;
- P(T10 posterior >=.90) ~90.3%.

## Compute authority

This is a materially larger hosted experiment.

Do not implement or launch until Human approves the compute scale.

No local-PC execution.
