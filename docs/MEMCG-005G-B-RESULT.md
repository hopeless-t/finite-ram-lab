# MEMCG-005G-B Biopsy-Footprint Control Result v1

> Status: PASS / SUPPORT_FOOTPRINT_EFFECT
> Run: `36568284433`
> Launch: `01dea9af49e28df4843019f924e717efde0c0426`
> Aggregate artifact: `11032159838`
> Digest: `sha256:ad9f759cf3d8760fd5b46fb0e01fe237934ec90a159250fca3db78dffbfa5119`

## Primary

Decision: `SUPPORT_FOOTPRINT_EFFECT`

Valid REMOTE_LOW:

- CAP8: 3 failures / 240 = **1.25%**
- CAP70: 26 failures / 249 = **10.4418%**
- difference CAP70-CAP8 = **+9.1918 percentage points**
- Fisher two-sided OR = **9.2108**
- Fisher p = **9.6121e-06**
- CPU mismatches = **0**
- non-{0,Q64} failures = **0**

All preregistered SUPPORT conditions passed.

## Stratified replication

Mantel-Haenszel OR CAP70 vs CAP8:

`9.1611`

Woolf heterogeneity:

- Q = 4.2918
- df = 15
- p = **0.9966**

Failure appeared in:
- CAP70: **15/16 blocks**
- CAP8: **2/16 blocks**

Exploratory block-presence Fisher one-sided:
`p ~= 3.42e-06`

## Measured confound checks

Pre-current:
- CAP8 median 99 pages, mean 98.396
- CAP70 median 99 pages, mean 98.361

Affinity-to-GO:
- CAP8 median 157.805 us, mean 152.432 us
- CAP70 median 156.322 us, mean 153.007 us

The arm effect is not explained by a gross pre_current or migration-latency shift in these data.

## Accepted interpretation

Changing only the worker's pre-first-touch anonymous mapping capacity from 8 pages to 70 pages materially increased valid REMOTE_LOW first-touch zero events in this hosted setup.

CAP70 is therefore a reproducible rare-state enrichment intervention.

Mechanism is unknown.

MEMCG-005G-B did not biopsy failures, so it does not establish whether CAP70 enriches depth1, deep, or another phenotype.

## Context

CAP8 is close to the prior natural-tail observation:
- MEMCG-005F: 2/123 = 1.626%
- MEMCG-005G-B CAP8: 3/240 = 1.25%

No 64-page threshold claim.
No K7 inference.
Hosted research only.
