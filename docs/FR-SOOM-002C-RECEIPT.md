# FR-SOOM-002C — Rare-Tail Policy Qualification Receipt

Status: **PASS / SYNTHETIC RARE-TAIL POLICY DIVERGENCE VALIDATED**

## Frozen qualification

- workflow run: 37014090804
- job: 110860580902
- execution head: 50e06fcd209ed68678c20bf78aeacb9975e515b0
- targeted tests: 7/7 PASS
- artifact ID: 11229475543
- artifact ZIP SHA256: 79dc37b2675ff92ceb1e5c4c66c0da75cf43511d84287b25e8a44dc4e2c30239
- spec SHA256: 4ba4f6b99315f2de49df688ca67c09a00d1911bbc7bc2853b3d307b3981c92aa
- result SHA256: ec8a5bd0b6f42247264a71695a3e0ad063b027f579bb52d7905d2061c9a8ff8f

## Frozen episode

- relief target: 3000 MiB
- response deadline: 200 ms
- replicates per plan: 8192
- reliability qualification:
  - point deadline-success rate >= 0.99
  - Wilson 95% lower bound >= 0.99

## Result

| plan | deadline success | Wilson95 lower | mean latency | p95 | p99 | semantic loss | hard kills | current task |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| MEAN_COOPERATIVE | 7525/8192 = 0.918579 | 0.912459 | 190.26 ms | 310 ms | 495 ms | 9 | 0 | survives |
| TAIL_AWARE_MIXED | 8168/8192 = 0.997070 | 0.995644 | 100.69 ms | 118 ms | 120 ms | 14 | 1 | survives |
| KILL_FIRST | 8192/8192 = 1.000000 | 0.999531 | 19.97 ms | 25 ms | 25 ms | 280 | 1 | lost |

## Primary finding

The mean-cooperative plan has:

`mean completion latency < deadline`

but still fails the frozen 99%-class qualification.

Therefore:

`mean-fast != tail-safe`.

The tail-aware mixed plan accepts five more synthetic semantic-loss points and
one background hard kill, but qualifies the 99%-class deadline-reliability floor
while preserving the current task.

The kill-first control remains fastest and most reliable in the frozen model,
but destroys the current task and has much higher synthetic semantic loss.

This produces the intended three-way tradeoff:

`deadline reliability x semantic preservation x destructive intervention`.

## Failure decomposition

The mean-cooperative arm retains separate counts and biopsies for:

- deadline miss;
- insufficient-relief miss;
- tail-event replicate;
- under-relief replicate.

The distinction matters:

`late enough relief != insufficient relief`.

They imply different controller repairs.

## Pre-qualification failures

Two qualification attempts were intentionally preserved rather than hidden.

### Attempt 1

- workflow run: 37013861349
- result: FAIL
- observed MEAN_COOPERATIVE successes: 7580
- frozen reference: 7525

Cause:

The pilot used hash-domain tags `lat` and `under`, while the initial
implementation used `latency` and `under_relief`.

The probability parameters were unchanged, but the deterministic sample stream
was different.

### Attempt 2

- workflow run: 37013943011
- result: FAIL
- observed MEAN_COOPERATIVE successes: 7554
- frozen reference: 7525

Cause:

The pilot hash included short frozen action draw IDs such as `CHROME_RICH`,
while the implementation hashed human-readable action labels such as
`CHROME_TRIM_AND_IDLE_RENDERERS`.

Again the probability model was unchanged, but the deterministic sample stream
was different.

### Repair

No threshold, probability, latency range, relief value, or acceptance criterion
was changed.

The repair instead separated:

- human-readable action label;
- frozen random-stream draw-domain ID.

The final spec now freezes:

- seed;
- hash-domain tags;
- action draw-domain IDs;
- replicate index;
- distribution parameters.

This yields a broader reproducibility rule:

> A stochastic reference vector is not defined by its probability distribution
> alone. Its deterministic random-stream identity is part of the fixture.

## Controller implication

A future live controller should optimize something closer to:

```text
minimize expected semantic loss
subject to:
  P(relief before deadline) >= required reliability
  current-task damage <= policy bound
```

The probability model must eventually come from host-bound observations rather
than synthetic priors.

## Claim ceiling

**SYNTHETIC_RARE_TAIL_POLICY_ONLY**

No live process was signaled or controlled.

The synthetic 200-ms deadline is not a host recommendation.

## Next

FR-SOOM-002D should add a shared BAD pressure state so multiple cooperative
actions become slow together.

That tests whether:

`matched marginal action-tail rates != matched controller risk shape`.

This directly connects the Semantic OOM lane with the earlier temporal
correlation / burst-risk result.
