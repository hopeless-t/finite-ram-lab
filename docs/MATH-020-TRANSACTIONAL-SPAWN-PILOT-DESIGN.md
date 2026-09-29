# MATH-020 — Minimal Information-Maximizing Transactional Spawn Pilot

> **Status:** FROZEN DESIGN / NOT AUTHORIZED / NO PHYSICAL RUN  
> **Inputs:** B400-B403, OBS-006, controlled-spawn v2, MATH-018  
> **Goal:** exercise the complete transaction protocol with the smallest useful physical panel before any reliability certification.

## 1. Why the next experiment must be small

The next unknown is no longer whether Q64 or the b62/b63/b64 arithmetic exists.

Those mechanisms already have strong evidence.

The immediate unknown is whether the full chain can operate end-to-end:

[
NORMALIZE
	o VERIFIED
	o EXECUTE
	o TARGET
	o COMMIT
]

while correctly diverting contaminated attempts into:

[
INVALIDATE
	o REPRIME
]

A large fixed-N reliability run before this wiring is proven would spend samples on instrumentation risk.

Therefore the next experiment is a protocol-integrity pilot, not a reliability certification.

## 2. Pilot structure

### Normal lane

12 scientific identities:

- b62: 4
- b63: 4
- b64: 4

No replacement identities.

Every identity may use at most two re-primes, for at most three epochs.

### Sentinel lane

One additional non-scientific identity:

FORCED_UNEXPECTED_REFILL_THEN_HARD_REPRIME

The sentinel does not enter b62/b63/b64 scientific denominators.

Its only job is to prove the fail-closed and epoch-isolation path.

## 3. Why 12 normal identities

Four per arm is deliberately too small for a reliability claim.

If all 12 accepted results were correct, the one-sided 95% all-success correctness floor would only be:

[
0.05^{1/12}approx 0.779
]

For one arm with 4/4:

[
0.05^{1/4}approx 0.473
]

Therefore any apparent 100% in this pilot cannot be mistaken for certification.

The sample is large enough to:

- exercise all three terminal bundle lengths repeatedly;
- test more than one normalization history per arm;
- expose gross packet-ordering or target-bundle defects;
- remain much smaller than the historical 72-identity pilot.

## 4. Natural invalidation is not relied upon

OBS-006 observed 14/16 state-preserved trials under an intentionally hostile masked-Q64 workload.

With Jeffreys posterior:

[
p_{preserve}sim Beta(14.5,2.5)
]

the posterior-predictive probability of seeing at least one invalidation in 12 future attempts under exchangeability would be approximately:

[
76.6%
]

This is only a sensitivity calculation.

The transactional pilot must not depend on that event occurring naturally because:

- OBS-006 workload differs from controlled-spawn;
- invalidations may be correlated;
- state preservation may improve materially under the new setup.

Hence the dedicated sentinel lane.

## 5. Hard re-prime baseline

For the first physical transactional pilot, use:

HARD_REPRIME

meaning:

1. terminate the invalidated worker/cgroup;
2. close its trace epoch;
3. create a fresh worker/cgroup;
4. repeat P-side PTE preconditioning;
5. migrate to S;
6. acquire a fresh direct Q64;
7. continue only in the new epoch.

Why start with hard re-prime?

### Interpretability

It creates a strong physical boundary between epochs.

### Receipt hygiene

Old trace windows cannot accidentally authorize the new epoch.

### Safe-span budget

A same-worker soft re-prime may consume too much of the one-PTE-table safe span after a long failed epoch.

A new worker resets the available measured span.

### Correlation control

Hard re-prime does not prove independence, but it reduces direct carry-over from the invalidated worker state.

Soft re-prime can be studied later as an optimization.

## 6. Re-prime budget

Freeze:

[
max_reprimes=2
]

Therefore each admitted identity has at most:

[
3 epochs.
]

Budget exhaustion yields:

ABORTED / NO_RESULT

never TARGET_FAIL.

This keeps worst-case work bounded and prevents a difficult identity from becoming an unbounded retry loop.

## 7. Sentinel construction

The sentinel's epoch 0 intentionally drives the verified stock through one extra ordinary CONSUME transition until a direct Q64/refill appears where the protocol expects no refill.

Required result:

[
UNEXPECTED_REFILL
	o INVALIDATED
]

The epoch must not emit:

- TARGET_MATCH;
- TARGET_FAIL;
- COMMIT;
- SUCCESS.

Then perform HARD_REPRIME.

Epoch 1 must not use the old epoch-0 Q64 receipt.

It must acquire a new direct:

- page_counter_try_charge(64);
- refill_stock(63).

Only after the fresh token may it proceed to a small b63 terminal path.

This sentinel validates the most important anti-retry bug:

> a refill that invalidates the old epoch cannot simultaneously serve as the reset token for the new epoch.

## 8. Normalization bound

Preserve the existing controlled-spawn bound:

[
64 calibration touches/epoch.
]

Historical G-A first-touch-zero biopsies all reached a later Q64 by touch65, but that evidence used net-delta observation and a different design.

The pilot should not silently expand its normalization horizon after launch.

If no direct Q64 appears inside the frozen bound:

NORMALIZE_EXHAUSTED -> INVALIDATED.

A re-prime may then open a new epoch, subject to the fixed budget.

## 9. Terminal bundle rules

Use B403 direct tokens.

### ZERO

No direct charge64/refill63 pair.

Release-only may coexist.

### Q64

Exactly one paired direct charge64/refill63 receipt.

Release-only may coexist.

### Partial pair

TRACE_GAP.

### Pattern mismatch with complete valid receipts

TARGET_FAIL.

Do not re-prime it away.

## 10. Pilot stop rules

### Immediate scientific stop

Any:

TARGET_FAIL

from an uninterrupted verified normal-lane epoch.

Reason:

the experiment would have produced the first genuine contradiction to the constructed stock-transition model under the new certification semantics.

Do not continue collecting retries to dilute it.

### Instrumentation hold

Any:

- trace gap;
- CPU mismatch;
- worker error

in the normal lane.

The pilot's purpose is instrumentation integrity.

### State invalidation

Unexpected refill, drain, or isolated PTE growth:

- record cause;
- invalidate;
- hard re-prime if budget remains.

If one invalidator dominates repeatedly, stop expansion and investigate rather than treating re-prime as a broom.

## 11. Reported outputs

Do not report one success percentage.

Report:

### C1 accepted correctness

- accepted SUCCESS count
- false accepts if any

### C2 target mismatch

- TARGET_FAIL / valid uninterrupted target evaluations

### C3 re-prime burden

- reprimes per identity
- attempts-to-valid-terminal
- maximum attempts

### C4 abstention

- ABORTED count

### Additional pilot telemetry

- normalization depth per epoch
- invalidation counts by reason
- release-only count
- direct-Q64 position
- packet/trace completeness

## 12. Information gain

The pilot is designed to answer five binary architecture questions cheaply:

1. Can direct Q64 acquisition drive VERIFIED in the real controlled-spawn runner?
2. Can release-only coexist without changing residual arithmetic?
3. Can all three multi-touch target patterns reach TARGET_MATCH?
4. Does a real unexpected refill invalidate rather than become target failure or success?
5. Does hard re-prime require and acquire a fresh epoch-local Q64 before commit?

A YES to all five justifies a larger reliability design.

A NO to any one identifies a specific layer to repair.

## 13. Pseudo-Council

### Statistician

Keep the panel too small to tempt reliability claims.

### Kernel observer

Require direct events; never reconstruct missing receipt pairs from net delta.

### Protocol engineer

Use hard re-prime first. Optimize to soft re-prime only after correctness.

### Falsification reviewer

TARGET_FAIL is terminal and immediately reportable.

### Resource reviewer

Bound retries and prohibit automatic scale expansion.

### Convergence

5/5 agree on:

- 12 normal identities;
- 4 per arm;
- one dedicated invalidation/re-prime sentinel;
- max_reprimes=2;
- hard re-prime;
- no reliability claim.

## 14. Launch boundary

The design is frozen but not authorized.

Before physical execution:

1. wire native trace markers into controlled-spawn;
2. wire direct charge/refill/drain observer;
3. freeze positive release-only classification;
4. archive packets by epoch;
5. pass CI and synthetic sentinel replay;
6. obtain Human authorization if the run uses any paid or explicitly gated compute.

No large reliability run follows automatically.
