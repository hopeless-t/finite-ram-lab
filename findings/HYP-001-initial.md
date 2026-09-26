# HYP-001 Initial Finding

> **Status:** NEGATIVE / INCONCLUSIVE FOR SMALL EFFECTS  
> **Run:** 36224708512  
> **Frozen design:** 20 runner blocks, 240 primary trials, 40 endpoint-control trials

## Question

At the same 164 MiB memcg pressure condition, does next-use cost become larger when future reuse targets the region that was made less recent rather than the region that was made more recent?

## Execution

All frozen execution checks passed:

- 20 independent runner blocks present;
- 280 total trials present;
- no OOM events;
- 120 ALIGNED and 120 MISALIGNED primary trials;
- recent physical-mapping identity balanced within each arm.

Endpoint controls preserved the intended pressure split:

- 160 MiB control: median retouch latency ≈ 62.25 ms, median swap after burst ≈ 12.27 MiB;
- 168 MiB control: median retouch latency ≈ 1.94 ms, median swap after burst = 0.

## Primary result

At 164 MiB:

| Arm | Trials | Median latency | P90 latency | Median retouch swap-ins |
| --- | ---: | ---: | ---: | ---: |
| ALIGNED | 120 | 11.91 ms | 159.99 ms | 381.5 pages |
| MISALIGNED | 120 | 11.36 ms | 109.18 ms | 542.5 pages |

The pre-registered block-level analysis used mean log latency within each runner block.

Result:

```text
geometric mean latency ratio
MISALIGNED / ALIGNED = 0.941
```

Exact sign-flip inference over all:

```text
2^20 = 1,048,576
```

block sign assignments gave:

```text
two-sided p = 0.704
```

Cluster-bootstrap ratio interval:

```text
95% interval ≈ [0.696, 1.275]
```

## Interpretation

The experiment does **not** support the pre-registered prediction that retouching the less-recent region is systematically slower than retouching the more-recent region.

The observed point estimate was slightly in the opposite direction and highly compatible with no arm difference.

The result is not evidence that future semantic information has zero value.

The design study explicitly showed limited sensitivity to small effects, and the transition zone remains heavy-tailed.

## What was falsified

The following simple model is weakened:

> Equal-access regions can be steered into meaningfully different next-use cost merely by changing their final pre-burst recency order, with the less-recent region then becoming systematically more expensive to reuse.

That model did not survive the frozen test.

## What remains

OBS-002 still showed a strong relationship between actual post-burst hot-set residency and retouch latency.

HYP-001 shows that **manipulating a simple access-order proxy did not reliably manipulate the later cost**.

Therefore:

```text
observed residency loss predicts cost
        does not imply
simple pre-burst recency ordering controls that residency loss
```

This distinction is important.

## Secondary observations

Descriptive secondary counters did not rescue the hypothesized direction. Mean block differences for swap-ins, anonymous refaults, and major faults were not larger in the MISALIGNED arm.

No post-hoc mechanism claim is promoted from those secondary metrics.

## Council conclusion

Do not build a coordination mechanism from HYP-001.

The next useful question is whether semantic-region residency can be **directly and selectively perturbed** while preserving matched workload conditions.

The existing low-pressure `MADV_PAGEOUT` probe created swap backing but did not make the range nonresident according to `mincore`.

A bounded capability test using explicit cgroup reclaim is justified before any matched causal intervention.

## Authority boundary

HYP-001 does not show:

- that Linux lacks useful recency information;
- that application semantics have no value;
- that a kernel defect exists;
- that a coordination plane is needed or unnecessary.

It rules against one specific, pre-registered access-order mechanism at the sensitivity of this experiment.
