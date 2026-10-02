# B490 — Repaired Coverage-Aware Governor v2

Status: **REPAIRED-RUNTIME SOFTWARE GOVERNOR**.

## 1. Why v2 is separate from B475

B475 was calibrated against the old BOOLEAN_INDEX centering implementation.

B486 repaired that primitive and B487 showed a different q frontier.

Therefore B490 does not mutate the old Governor in place.

It creates a new policy tied explicitly to:

`implementation = TILED_WHERE`.

## 2. Qualified repaired calibration

B489 provides 19 independent hosted-runner samples per repaired Pareto q.

### q2

- empirical max = 50,696,192 B
- n = 19
- rank-max one-step coverage floor = 95%
- new-panel median latency ~= 0.395639 s

### q4

- empirical max = 58,941,440 B
- n = 19
- floor = 95%
- median latency ~= 0.387823 s

### q7

- empirical max = 71,507,968 B
- n = 19
- floor = 95%
- median latency ~= 0.386392 s

q1 is excluded because B487 found q2 at the same observed median peak with lower
latency.

## 3. Selection rule

Given:

- declared peak budget B;
- minimum required rank coverage p;

choose the lowest-latency repaired Pareto q satisfying:

```text
pooled_empirical_max_peak(q) <= B
rank_coverage_floor(q) >= p
```

No weighted memory/latency scalar is introduced.

## 4. 95% repaired breakpoints

```text
50,696,192 B -> q2
58,941,440 B -> q4
71,507,968 B -> q7
```

The practical meaning is:

- about 50.70 MB empirical-max budget buys q2;
- another ~8.25 MB admits q4;
- another ~12.57 MB admits q7.

## 5. Comparison with old Governor

Old B475 95%-class breakpoints were roughly:

- q1: 67.12 MB
- q2: 67.19 MB
- q4: 71.39 MB
- q7: 71.54 MB

The repaired runtime changes the low/mid frontier substantially.

In particular q2 moves from ~67.2 MB to ~50.7 MB empirical-max calibration.

q7 changes little because B487 showed its peak is dominated by an earlier
seven-lane residency peak rather than the repaired centering temporary.

## 6. Fail-closed evidence behavior

A 99% minimum coverage request currently has no eligible q because each repaired
Pareto q has only n=19.

99% sample-max rank coverage requires n>=99.

The Governor fails closed rather than reusing 95% evidence.

## 7. Claim ceiling

**EXCHANGEABILITY_CONDITIONAL_REPAIRED_GOVERNOR_V2**

The policy is not a hard worst-case memory guarantee.

## 8. Next

B491 should dogfood Governor v2 at and around its three breakpoints.

The key new question is whether the repaired q2/q4 thresholds remain stable
without the centering temporary, and whether q7's unchanged peak should open a
separate earlier-stage residency-optimization branch.
