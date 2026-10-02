# B498 — Host-Bound Local Policy Promoter Receipt

Status: **PASS / LOCAL POLICY PROMOTION AND BOUND SELECTION QUALIFIED**

## Frozen qualification

- workflow run: 36966361523
- job: 110710878352
- execution head: 16b89fae677dc0ec7e1316c14944721a1e8563d1
- tests: 5/5 PASS
- artifact ID: 11210111750
- artifact ZIP SHA256: ff72012f591a26c2f64f146568a86095010e36d5e4798c5012f2e24341d44cef

Synthetic qualification outputs:

- policy SHA256: 8340b85271f56ee15b5c84d113d42b89261f84b8a73b54927fcec1ef0375d79f
- decision SHA256: f1425f388b4302bfd0786e877f6b3596ff14af908c71f935625a2247997c1bc5

## Qualified behavior

A sufficient local calibration state can now be promoted into:

`finite-ram-lab.governor-policy/v0.1`

with:

`scope = LOCAL_HOST_BOUND`.

The policy carries the calibration environment fingerprint and evidence-state
digest.

## Fingerprint enforcement

Selection through:

`frl local-governor-select`

validates the current environment fingerprint before applying the common
budget/coverage selector.

A fingerprint mismatch fails closed.

## Generic-selector bypass closed

A local host-bound policy cannot be used through the ordinary unbound:

`frl governor-select`

surface.

The generic selector now rejects LOCAL_HOST_BOUND policies unless a trusted
adapter has already validated the binding.

This prevents copying a local policy to another machine and silently reusing it.

## Host-specific Pareto ordering

B498 removed the unnecessary requirement that empirical peak budgets be sorted by
q.

The common selector evaluates all eligible Pareto points and chooses the
lowest-latency qualified point.

Therefore local policy can represent a topology that differs from the
GitHub-hosted q ordering.

## Claim ceiling

**HOST_BOUND_LOCAL_GOVERNOR**

## Next

B499 should make local calibration efficient:

1. consume the B497 n8 exploration;
2. identify the locally observed Pareto q set;
3. execute +11 fresh-process observations only for those Pareto q values;
4. merge old and new evidence into one local calibration state;
5. pass that state into B498 for promotion.

Dominated local q values keep their exploratory evidence but do not consume the
95% expansion budget.
