# MATH-002 Sidecar Implementation Note

> **Status:** IMPLEMENTED / NOT LAUNCHED

Pinned dependency:
`pmndrs/math@98762395c1f34d7d594d31165e8005fd6915c431`

Implementation:
- `analysis/math002/math002.mjs`
- `analysis/math002/test.mjs`
- `analysis/math002/package.json`
- `.github/workflows/math-002-geometric.yml`

The sidecar consumes only a prepared canonical MEMCG-003B summary.

It computes:
- pooled DISTINCT_CHURN QuickHull2 envelope;
- pooled control QuickHull2 envelope;
- per-block hulls;
- maximum passive-drop challenger index;
- 100,000-label-permutation null using `mulberry32` seed 20260929.

Primary geometric statistic:
`G = number of blocks whose maximum passive-drop point occurs at m in {6,7,8}`

The workflow intentionally fails if canonical MEMCG-003B input has not first been prepared.

Ordering is fixed:
1. primary MEMCG-003B decision;
2. canonical evidence;
3. secondary geometric lens.

The secondary lens cannot rescue or overwrite the primary decision.
