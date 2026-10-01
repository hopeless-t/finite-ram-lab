# B475 — Coverage-Aware q Governor v1 Receipt

Status: **PASS / COVERAGE-AWARE GOVERNOR QUALIFIED**

## Frozen execution

- workflow run: 36935103431
- job: 110613400182
- execution head: 5952b5f631ebed512431548730be9d51d10bbdd8
- tests: 4/4 PASS
- artifact ID: 11198290633
- artifact ZIP SHA256: 25ae7c6bfab05237930dd547911f8739a1beb534196a866052402bd84c90406f
- governor SHA256: 7727853f56ecf95c265e207adae0318b2aeb0ddccdd8750a24fc8d242914b365

## 95% coverage-aware breakpoints

```text
67,117,056 B -> q=1
  n=20
  rank floor=20/21 ~=95.238%

67,194,880 B -> q=2
  n=19
  rank floor=95%

71,389,184 B -> q=4
  n=19
  rank floor=95%

71,544,832 B -> q=7
  n=19
  rank floor=95%
```

Latency ordering remains sourced from the balanced B469 sweep.

## Example decision

Input:

- minimum rank coverage = 0.95
- peak budget = 67,194,880 B

Output:

- selected q = 2
- pooled empirical max = 67,194,880 B
- sample count = 19
- rank-max one-step predictive coverage floor = 0.95
- balanced-sweep median latency = 0.400696726 s

The decision explicitly carries the exchangeability assumption and states that it
is not a worst-case memory guarantee.

## Fail-closed behavior

A caller requesting 99% rank coverage currently receives no eligible q.

Reason:

- sample-max 99% coverage requires n>=99;
- current q sample counts are 19 or 20.

The governor does not relabel 95% evidence as 99%.

## Milestone

The resource contract has evolved:

```text
peak budget only
-> observed-upper heuristic
-> empirical max + sample count
-> explicit rank coverage requirement
-> q selection under memory + evidence constraints
```

This is the first Governor version where the confidence/evidence budget is part
of the executable decision surface.

## Claim ceiling

**EXCHANGEABILITY_CONDITIONAL_COVERAGE_AWARE_GOVERNOR_V1**

## Next

B476 should dogfood v1 at its calibrated boundaries.

Any exceedance is compatible with the declared 5%-class one-step tail risk and
must be recorded.

The important next distinction is:

- ordinary exchangeable tail exceedance;
- systematic drift indicating the calibration population is no longer
  exchangeable with current execution.
