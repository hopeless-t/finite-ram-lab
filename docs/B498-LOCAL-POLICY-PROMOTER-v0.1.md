# B498 — Host-Bound Local Policy Promoter v0.1

Status: **LOCAL EVIDENCE -> GENERIC GOVERNOR POLICY COMPILER**.

## 1. Goal

B497 can collect the local q surface.

B498 defines the gate that turns sufficient local evidence into a usable
Governor policy.

The output reuses the same generic policy schema consumed by B494:

`finite-ram-lab.governor-policy/v0.1`

but adds:

`scope = LOCAL_HOST_BOUND`.

## 2. Promotion requirements

For every q on the locally observed Pareto frontier:

- the row must exist;
- sample count must satisfy the requested coverage target;
- stored coverage must equal n/(n+1);
- implementation must be TILED_WHERE;
- the current host fingerprint must match the calibration binding.

At 95%:

`n>=19`.

Any insufficient Pareto q blocks the entire promotion.

## 3. No hosted topology assumptions

The promoter accepts the locally measured Pareto set.

It does not hard-code:

- hosted q1 exclusion;
- hosted q2/q4/q7 ordering;
- hosted peak thresholds.

The local Pareto points may have a different q ordering by memory.

The generic selector was therefore generalized to evaluate all points rather
than require peak budgets to be monotonically ordered by q.

## 4. Fingerprint binding

A promoted policy carries:

- full non-identifying environment fingerprint;
- canonical fingerprint SHA256;
- calibration-state digest.

Selection requires a fresh fingerprint match.

## 5. Bypass prevention

A LOCAL_HOST_BOUND policy is rejected by the generic unbound selector.

It may only be used through:

`local-governor-select`

which validates the current environment before delegating to the common
budget/coverage selection logic.

Thus copying a local policy JSON onto another host does not silently authorize
the same q decisions.

## 6. CLI surfaces

Promotion:

```bash
frl local-policy-promote \
  --calibration local-calibration-state.json \
  --target-rank-coverage 0.95 \
  --out local-governor-policy.json
```

Selection:

```bash
frl local-governor-select \
  --policy local-governor-policy.json \
  --peak-budget-bytes <bytes> \
  --minimum-rank-coverage 0.95 \
  --out local-decision-receipt.json
```

## 7. Shared application semantics

The local selector still emits:

`finite-ram-lab.governor-decision-receipt/v0.1`

so downstream application code can use the same decision/execution receipt
pipeline as GitHub Actions.

The environment-binding validation is included as an additional receipt field.

## 8. Claim ceiling

**HOST_BOUND_LOCAL_GOVERNOR**

## 9. Next

B499 should add an efficient Pareto-only local evidence extension/merge path.

After the B497 n8 exploration:

- keep all q exploration evidence;
- run +11 only for locally observed Pareto q;
- merge into one local calibration state;
- pass that state into B498 for promotion.

This avoids paying 19 samples for locally dominated q values.
