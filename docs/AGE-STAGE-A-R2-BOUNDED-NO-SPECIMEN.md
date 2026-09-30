# AGE Stage A R2 — verified-state wall-clock decoupling

## Frozen physical run

Experiment: `TX-AGE-DECOUPLING-STAGE-A-v2`

Run: `36703139110`

Launch commit: `52149a35e11a2c2151081b98cd0b00f82df92d2f`

R1 run `36702673576` remains a wiring-only failure and is not scientific evidence.

R2 completed all four block jobs and the aggregate successfully.

## Design

Stage A preserved the B410 structure:

- b63 only
- FAST x4
- HOLD32 x12
- four blocks
- hold after post-primer touch 32
- fixed target touch count
- requested HOLD dwell: 22.077060 s
- no automatic Stage B
- no automatic sample expansion

The v2 observer additionally binds refill_stock to the verified owner memcg and retains all refill sizes, so a refill1 cannot masquerade as an unexplained age effect.

## Result

All 16 identities physically reached:

```text
T = 64
final state = SUCCESS
target result = MATCH
```

Strict zero-miss classification:

```text
CANONICAL_SUCCESS      12
INSTRUMENTATION_HOLD    4
KNOWN_STATE_CHANGE      0
UNEXPLAINED_DEVIATION   0
UNKNOWN_COMPLETE        0
TRUE_TARGET_FAIL        0
```

By arm:

```text
FAST:
  n=4
  canonical zero-miss=3
  instrumentation hold=1
  T64=4/4

HOLD32:
  n=12
  canonical zero-miss=9
  instrumentation hold=3
  T64=12/12
```

No Stage-B trigger occurred.

## Exposure

The historical B404 R2 exact-b63 timing calibration gave:

```text
tau_fast median = 1.471804 s
requested dwell = 15 * tau_fast = 22.077060 s
```

R2 zero-miss canonical medians were:

```text
FAST verified -> first owner Q64:
  1.868684 s

HOLD32 verified -> first owner Q64:
  25.001723 s

realized median exposure factor:
  13.3793
```

The HOLD checkpoint itself was accurately realized:

```text
median observed HOLD checkpoint = 22.077272 s
```

The design therefore achieved a large wall-clock separation while keeping measured target touches fixed.

## Instrumentation holds

Four identities were excluded from zero-miss scientific classification:

- 0:3 HOLD32 — refill_stock missed 1
- 2:3 HOLD32 — refill_stock missed 2
- 3:0 HOLD32 — refill_stock missed 1
- 3:2 FAST   — refill_stock missed 6

For all four:

- page_counter_try_charge(64) missed = 0
- owner page_counter_uncharge missed = 0
- T = 64
- final state = SUCCESS
- continuity = clean
- no target drain observed
- no owner refill observed in the relevant measured/checkpoint windows

They remain instrumentation holds because a missed owner-memcg refill event could in principle be state-changing.

Do not retroactively promote them.

## What Stage A says

At the realized exposure factor of about 13.38, the complete zero-miss panel captured:

- no known verified-state hazard;
- no unexplained boundary deviation;
- no complete unknown owner emission;
- no true target failure.

This is a bounded no-specimen result.

It does **not** prove that time-driven hazards do not exist.

Descriptively, all 16 physical identities still reached the canonical T=64 boundary.

## Frozen no-event sensitivity replay

Using only the complete panel:

- FAST n=3
- HOLD32 n=9
- hazard/deviation events=0

and replaying the original B410 log-uniform design-sensitivity priors at realized F=13.3793 gives:

```text
LOW prior range:
  BF TOUCH/TIME ~= 1.48

CENTRAL:
  BF TOUCH/TIME ~= 2.59

HIGH:
  BF TOUCH/TIME ~= 10.08
```

Interpretation:

- a high-frequency pure TIME hazard is increasingly disfavored;
- a rare TIME hazard can easily escape nine HOLD identities;
- these are design-sensitivity calculations, not empirical prevalence estimates or objective posterior mechanism probabilities.

## Next mechanistic hypothesis

The quiet HOLD result, combined with the already established TARGET_STOCK_EVICTION mechanism, motivates a new contrast:

```text
wall-clock age alone
vs
CPU-local memcg-stock slot pressure
```

Linux currently has:

```text
NR_MEMCG_STOCK = 7
```

per CPU.

When all slots are occupied, refill_stock uses a round-robin drain_idx and calls drain_stock on the selected existing slot before installing a new memcg.

This supports a causal next experiment:

```text
QUIET
OFFCPU_SLOT_PRESSURE
SAMECPU_SLOT_PRESSURE
```

with equalized wall-clock exposure and fixed target touch count.

The experiment should test whether same-CPU activity, rather than passive wall-clock age, drives target stock eviction.

## Evidence

Machine result:

- `analysis/inputs/AGE-DECOUPLING-STAGE-A-R2-PHYSICAL-RESULT-v1.json`

Sensitivity:

- `analysis/inputs/AGE-STAGE-A-R2-NO-EVENT-SENSITIVITY-v1.json`

Raw manifest:

- files: 68
- bytes: 7,056,729
- content-set SHA-256: `e8fc47058103323eb46a3728235b51e4e7869921aed18c104bc9b943df532d9b`

Aggregate artifact:

- ID: `11090363265`
- digest: `sha256:b370602350ab9fa60bba942d5c5b97ef16ef87a153bb13d3e77c7fdc68d5dda9`

## Claim ceiling

Bounded mechanism-discrimination evidence only.

No prevalence estimate.
No reliability certification.
No claim that time-driven hazards are impossible.
