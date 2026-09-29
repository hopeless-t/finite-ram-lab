# CURRENT

> Latest bounce: B367
> Stage: MEMCG-005G-D DOSE-RESPONSE IMPLEMENTED / CI PENDING
> Stop: CI_DISCOVERY_PENDING

Question:
`p_capture = f(mapping_capacity)`

Frozen capacities:
`{8,32,63,64,65,70}`

Scale:
16 independent blocks x72 candidates =1152.
12 candidates/arm/block.

Primary path:
unchanged REMOTE_LOW first-touch.
No biopsy.

Analysis:
- per-cap Beta posterior
- adjacent Fisher contrasts
- CONSTANT / LOGISTIC_LINEAR / STEP64 / CATEGORICAL AIC comparison
- discovery label only; no threshold causal claim

Implementation:
- `docs/MEMCG-005G-D-FOOTPRINT-DOSE-RESPONSE-v1.md`
- `specs/MEMCG-005G-D-FOOTPRINT-DOSE-RESPONSE-v1.json`
- `src/finite_ram_lab/memcg005gd_dose_response.py`
- `.github/workflows/memcg-005g-d-dose-response.yml`
- `tests/test_memcg005gd_dose_response.py`

No launch marker exists.

Next fresh bounce:
discover/read ordinary CI exactly once.

Hosted research only.
No local-PC execution.
