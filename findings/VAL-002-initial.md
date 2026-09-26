# VAL-002 Initial Finding

> **Status:** OBSERVER EFFECT NOT SYSTEMATICALLY DETECTED / MATERIALITY NOT FULLY BOUNDED  
> **Run:** 36221192958  
> **Source commit:** `af8c6e826d6b496c867a5281c9fdc179510fa114`

## Execution

VAL-002 completed successfully:

- 8 independent hosted-runner blocks;
- 96 total trials;
- 32 FULL and 32 NONE trials at the 164 MiB primary transition level;
- 160/168 MiB endpoint controls in both modes;
- all execution checks passed;
- no OOM event.

## Primary 164 MiB result

The pre-registered log-latency mode comparison produced:

```text
FULL / NONE geometric latency ratio = 1.055
blocked permutation p = 0.856
```

A 5,000-resample cluster bootstrap over whole runner blocks produced:

```text
median ratio = 1.034
95% interval = [0.578, 2.071]
```

The point estimate is close to no average mode effect, but the interval is wide because the transition zone is highly runner-dependent.

Per-runner FULL/NONE ratios ranged from about 0.28 to 7.55.

## Distribution summaries

### 160 MiB

Both modes remained strongly pressured.

- FULL median retouch: about 556 ms;
- NONE median retouch: about 502 ms;
- all 8 trials in each mode exceeded 50 ms.

### 164 MiB

Both modes retained the stochastic transition behavior.

- FULL median retouch: about 9.15 ms;
- NONE median retouch: about 14.60 ms;
- FULL slow-branch count (>50 ms): 12 / 32;
- NONE slow-branch count (>50 ms): 10 / 32.

The p90 tail differed numerically:

- FULL: about 947 ms;
- NONE: about 424 ms.

Given the runner-block heterogeneity and small number of independent blocks, this tail difference is not promoted into a mode-effect finding.

### 168 MiB

Both modes remained in the low-pressure regime.

- FULL median retouch: about 3.93 ms;
- NONE median retouch: about 3.81 ms;
- no slow-branch events;
- no median swap or swap-in activity.

## Pressure-state comparison

At 164 MiB the two modes had similar central pressure-state summaries:

- median swap after burst: about 8.70 MiB FULL vs 8.73 MiB NONE;
- median retouch swap-ins: about 295 FULL vs 332 NONE pages;
- median major faults: about 90 FULL vs 76.5 NONE.

No consistent directional observer-induced pressure shift was identified.

## Pseudo-Council conclusion

The data do **not** support a systematic average timing effect from enabling `mincore`.

However, the cluster-bootstrap interval is too broad to certify `mincore` as behaviorally neutral in the stochastic 164 MiB transition zone.

Therefore:

1. the OBS-002 observational relationship remains useful;
2. `mincore` must not be treated as a perfectly neutral primary causal instrument;
3. the next mechanism experiment should make its **primary outcome independent of pre-retouch mincore**;
4. residency snapshots may be retained only in secondary/validation arms when needed.

This avoids spending additional research effort trying to prove global observer equivalence before testing the mechanism.

## Next research question

> If the same amount of anonymous memory is explicitly paged out, does immediate retouch cost depend on whether the evicted pages belong to the soon-reused hot set or to the burst region?

A matched semantic-region pageout experiment at an otherwise low-pressure condition is the leading candidate.

It must first pass a capability/efficacy probe.

## Authority boundary

VAL-002 does not establish:

- that `mincore` is always neutral;
- that hot-set eviction is causal;
- that Linux made a bad decision;
- that application hints or coordination would improve the system.
