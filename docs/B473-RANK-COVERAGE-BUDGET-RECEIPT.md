# B473 — Rank-Coverage Sample Budget Receipt

Status: **PASS / 95% SAMPLE BUDGET FROZEN**

## Frozen execution

- workflow run: 36934549234
- job: 110611626331
- execution head: 7f51a6154875b376d997470de2aeceabfe966646
- tests: 4/4 PASS
- artifact ID: 11196999524
- artifact ZIP SHA256: dde23945b65b61b39afc39f59d2737d51c82e89105a2fff26603f0b5c7312789
- budget SHA256: f7bedb95311520e6f6a85133e436863a38c406851597ccb4e9c250715e15bd44

## Rank-max budget rule

Under the explicit exchangeability assumption:

`coverage_floor = n/(n+1)`.

Therefore:

- 95% requires n >= 19
- 99% requires n >= 99

## Current counts

- q1 = 20 -> target met
- q2 = 8 -> 11 additional required
- q4 = 8 -> 11 additional required
- q7 = 8 -> 11 additional required

Total additional physical observations:

`33`

## Research significance

This converts confidence into an explicit experiment resource budget.

The scheduler can now answer:

> How many runner executions must be purchased before a q policy can claim a
> given exchangeability-conditional sample-max coverage class?

rather than collecting runs indefinitely.

## Claim ceiling

**EXCHANGEABILITY_CONDITIONAL_SAMPLE_BUDGET**

No worst-case guarantee is implied.

## Next

B474 should spend exactly the frozen 33-run budget with balanced q2/q4/q7
execution order, preserve exact semantics, update the pooled empirical maxima,
and report the resulting coverage floors.
