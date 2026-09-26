# CHAR-001 Initial Finding

> **Status:** INITIAL FINDING  
> **Successful run:** 36218018121  
> **Source commit:** `e18c9a1fed8bc93db4314010babb5f1fc5dca09e`

## Experiment

CHAR-001 held the controlled workload constant while sweeping:

```text
MemoryHigh = 96, 112, 128, 144, 160, 192, 224, 256 MiB
```

Each level was repeated 12 times in a deterministically shuffled order on one GitHub-hosted `ubuntu-24.04` runner.

Total valid trials:

```text
96
```

All declared scientific execution checks passed and no OOM event occurred.

## Primary result

The `HOTSET_RETOUCH` phase showed two sharply different regimes.

| MemoryHigh MiB | Median retouch ms | P90 ms | Median swap growth MiB | Median high events | Median pgscan |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 96 | 896.360 | 920.837 | 138.480 | 219.0 | 105469 |
| 112 | 800.820 | 826.648 | 124.230 | 117.0 | 71927 |
| 128 | 788.969 | 839.348 | 107.195 | 74.5 | 68666 |
| 144 | 1057.308 | 1084.064 | 92.236 | 73.0 | 75355 |
| 160 | 960.817 | 1437.181 | 74.238 | 181.5 | 56790.5 |
| 192 | 3.390 | 3.536 | 0.000 | 0.0 | 0 |
| 224 | 3.367 | 3.401 | 0.000 | 0.0 | 0 |
| 256 | 3.344 | 3.399 | 0.000 | 0.0 | 0 |

At 192 MiB and above, the measured retouch phase remained near 3.3–3.9 ms and the trial showed no cgroup-local swap growth, `memory.high` events, scan, or steal activity during the measured interval.

At 160 MiB and below, the same phase was roughly 0.79–1.06 seconds at the median and coincided with substantial swap growth and reclaim activity.

The median latency ratio between 160 MiB and 192 MiB was approximately:

```text
283×
```

## Changepoint calculation

The repository's segmented-regression calculator selected a split between the sampled 160 MiB and 192 MiB levels.

Reported midpoint:

```text
176 MiB
```

and:

```text
delta BIC (single line - segmented model) = 14.158
```

The 176 MiB value must **not** be interpreted as a precisely measured physical critical point.

The current grid only supports the narrower statement:

> A strong regime transition exists somewhere between the sampled 160 MiB and 192 MiB `MemoryHigh` conditions for this workload and runner.

## Important secondary observation

Behavior inside the pressured regime was not monotonic.

For example, the 144 MiB and 160 MiB medians were slower than the 96–128 MiB medians even though the lower limits produced more swap and scan activity.

Therefore the current evidence does **not** support a simple model of:

```text
less MemoryHigh -> proportionally more latency
```

This non-monotonicity is itself a research target.

Possible explanations include differences in reclaim timing, throttling, residency composition, swap timing, or another pressure-state transition.

None is yet established.

## What CHAR-001 establishes

The OBS-001 latency event is reproducible under the declared hosted-runner experiment.

A large performance regime change is associated with crossing from the unpressured sampled region at 192 MiB+ into the pressured sampled region at 160 MiB and below.

## What CHAR-001 does not establish

CHAR-001 does not yet prove that the latency change is caused by:

- swap itself;
- reclaim itself;
- a bad eviction decision;
- fundamental capacity shortage;
- missing application information;
- an application/OS coordination gap.

The secondary counters are correlated observations, not mechanism attribution.

## Council conclusion

The evidence is strong enough to advance from **characterization** to **validation/reproduction**.

The next experiment should:

1. sample the 160–192 MiB boundary more finely;
2. reproduce selected conditions on multiple independent GitHub-hosted runners;
3. preserve the same controlled workload;
4. test whether the boundary location and qualitative pressure/no-pressure split survive runner replacement.

Mechanism-specific intervention remains unauthorized until that validation is complete.
