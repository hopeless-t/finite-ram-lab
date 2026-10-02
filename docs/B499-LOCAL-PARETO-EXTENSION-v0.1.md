# B499 — Pareto-Only Local Calibration Extension v0.1

Status: **EFFICIENT HOST-BOUND EVIDENCE EXPANSION**.

## 1. Goal

B497 produces the initial n8 local exploration over all q={1,2,4,7}.

B499 avoids blindly expanding every q to n19.

It spends new samples only on the locally observed initial Pareto set.

## 2. Default full-local flow

Input:

- B497 n8 exploration
- local Pareto q set
- target rank coverage = 0.95

Default extension:

- +11 fresh local processes per initial Pareto q
- same size2048 workload
- same TILED_WHERE implementation
- same host fingerprint

## 3. Why the final Pareto is recomputed

The initial n8 Pareto is not treated as immutable.

After adding evidence to the initial Pareto q values, B499 recomputes median peak
and median latency over the merged state.

A previously dominated q can re-enter the Pareto set.

If that happens, its sample count may still be only n8.

The final state then refuses promotion until that q receives enough additional
samples.

## 4. Merge semantics

For every q the merged local state keeps:

- all peak samples;
- all latency samples;
- exploration sample count;
- extension sample count;
- total n;
- empirical maximum;
- median peak;
- median latency;
- n/(n+1) rank floor.

Schema:

`finite-ram-lab.local-calibration-state/v0.1`

This is the direct input expected by B498.

## 5. Host and semantic gates

Before extension:

- current host fingerprint must match B497 exploration binding.

After extension:

- fingerprint must still match;
- all observations must share one exact output digest.

Any mismatch fails closed.

## 6. Efficiency

If the initial local Pareto has k points, default B499 cost is:

`11 * k`

new physical observations.

Examples:

- k=4 -> 44
- k=3 -> 33
- k=2 -> 22

instead of always paying 44 observations for all q.

The initial 32-observation exploration remains retained for all q.

## 7. Policy gate

B499 emits:

`policy_promotion_allowed`

only when every q on the **final recomputed Pareto** has enough samples for the
target coverage.

At 95% this means n>=19 per final Pareto q.

## 8. Claim ceiling

**HOST_SCOPED_LOCAL_PARETO_EXTENSION**

## 9. Next

Once a real B497 development-machine exploration exists, B499 can spend exactly
the required local Pareto budget and hand the merged state to B498.

At that point the development machine can receive its first genuinely local,
fingerprint-bound Governor policy without borrowing GitHub-hosted thresholds.
