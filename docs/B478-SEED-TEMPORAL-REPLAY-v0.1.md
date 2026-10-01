# B478 — Seed vs Temporal Replay v0.1

Status: **TARGETED TWO-FACTOR REPLAY**.

## 1. Why this bounce exists

B477 found strong downward location shifts for q2 and q4.

However:

- the recent calibration batch used seed 474;
- B476 used seed 476.

Therefore the shift was confounded.

B478 replays both seeds in the same current GitHub-hosted environment.

## 2. Conditions

Only the two suspect q values are tested:

- q2
- q4

For each q:

- seed474
- seed476

Eight fresh-process observations are collected per condition.

Total new observations:

`2 q x 2 seeds x 8 = 32`.

The four conditions are order-balanced so each condition occupies each execution
position twice.

## 3. Two comparisons per q

### A. Current seed effect

Compare:

`current(seed474) vs current(seed476)`

If this is significant while the seed474 replay remains compatible with its
historical seed474 batch, the workload seed is a plausible contributor.

### B. Temporal / runner effect

Compare:

`historical(seed474) vs current(seed474)`

The seed is held fixed.

A significant difference therefore points toward a time/runner/environment
component rather than the seed change itself.

Both comparisons use the exact two-sided permutation rank-sum test.

## 4. Familywise threshold

There are four factor tests:

- q2 temporal
- q2 seed
- q4 temporal
- q4 seed

So:

- family alpha = 0.05
- Bonferroni per-test alpha = 0.0125

## 5. Classifications

Per q:

- TEMPORAL_RUNNER_SHIFT_SUSPECT
- WORKLOAD_SEED_EFFECT_SUSPECT
- MIXED_TEMPORAL_AND_SEED_SHIFT_SUSPECT
- NO_FACTOR_SHIFT_RESOLVED

These are bounded diagnostic labels, not causal proof.

## 6. Determinism gate

Different seeds intentionally produce different exact numerical outputs.

Therefore B478 does not require one digest across seeds.

It requires deterministic output digest within each (q,seed) condition across
the eight repetitions.

## 7. Claim ceiling

**TWO_FACTOR_BOUNDED_REPLAY_DIAGNOSTIC**

Even with seed fixed, GitHub-hosted runner instances may vary in ways not recorded
by this experiment. "Temporal/runner" is therefore a bundled factor.

## 8. Next

If temporal/runner shift is supported, B479 should capture additional environment
features and compare current q behavior under repeated runner instances.

If seed effect is supported, the governor calibration must condition on workload
class/seed-sensitive features rather than assuming one universal q peak
distribution.
