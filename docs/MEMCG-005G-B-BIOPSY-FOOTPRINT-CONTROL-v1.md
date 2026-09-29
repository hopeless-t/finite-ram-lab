# MEMCG-005G-B Biopsy-Footprint Control v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED

## Question

Did changing worker virtual mapping capacity from the historical `--max-pages 8` to biopsy-capable `--max-pages 70` materially increase REMOTE_LOW first-touch failure probability?

This must be resolved before treating the 005G-A 6.9% failure rate as the same population as the 005F 1.6% tail.

## Arms

Within each independent hosted runner:

- **CAP8**: unchanged worker, `--max-pages 8`
- **CAP70**: unchanged worker, `--max-pages 70`

All other controller steps are identical.

Candidates alternate arm by identity parity, with arm order reversed by block parity to reduce temporal-order confounding.

No biopsy is performed during the primary A/B measurement. This keeps the two arms identical after first touch.

## Gate

Use the confirmed REMOTE_LOW rule:

- startup P
- measured S != P
- pre_current_pages <=110
- Q64 = 60..68 pages

## Scale

Freeze at:

- 16 independent hosted blocks
- 64 candidate identities per block
- 32 CAP8 + 32 CAP70
- total 1024 candidates

Expected LOW count is descriptive only; decision uses observed valid LOW.

## Primary outcome

First-touch failure rate among valid REMOTE_LOW probes.

Primary contrast:

`CAP70 failure rate - CAP8 failure rate`

Use two-sided Fisher exact.

### SUPPORT_FOOTPRINT_EFFECT

Require:
- >=180 valid LOW per arm;
- absolute failure-rate difference >=3 percentage points;
- two-sided Fisher p <0.01;
- zero CPU mismatches;
- all first-touch failures zero-delta.

### REJECT_FOOTPRINT_EFFECT

If:
- >=180 valid LOW per arm;
- absolute difference <2 percentage points;
- Fisher p >=0.10.

Otherwise INCONCLUSIVE.

## Secondary

Report:
- failure rate per block and arm;
- Mantel-Haenszel common odds ratio across blocks;
- arm × block heterogeneity;
- pre_current distribution per arm;
- latency distribution per arm.

Do not change threshold or arm definition after launch.

## Follow-up logic

If SUPPORT_FOOTPRINT_EFFECT:
redesign biopsy so first-touch measurement uses the historical CAP8 footprint and only then expands/takes a separate biopsy path.

If REJECT_FOOTPRINT_EFFECT:
the elevated 005G-A failure rate is more likely runner/batch/state variability than max-pages footprint; preserve CAP70 biopsy and study block-level hidden state.

If INCONCLUSIVE:
replicate without changing the design before causal interpretation.

## Boundary

Hosted research only.
No K7 inference.
No local-PC execution.
