# Bounce Handoff

> **Bounce ID:** B042  
> **Status:** COMPLETE

## Objective

Read the valid HYP-002 retry using the frozen analyses, record the scientific finding, update repository status, and stop.

## Valid evidence

Workflow:

- valid run: `36243341566`;
- conclusion: SUCCESS;
- 16 independent runner blocks;
- 128 factorial trials;
- all execution checks passed;
- no OOM;
- content integrity preserved.

Excluded:

- run `36243199948` remains INVALID and contributes no evidence.

## Primary result

Runner-block mean:

```text
recent resident fraction - older resident fraction
= -0.009035
```

Exact one-sided sign-flip:

```text
p = 0.913574
```

Cluster-bootstrap 95% interval:

```text
[-0.020865, +0.003025]
```

The randomized final-recency hypothesis is **not supported**.

## Key secondary

HOT=older / HOT=recent geometric mean latency ratio:

```text
0.9624x
```

Exact one-sided p:

```text
0.571365
```

Secondary semantic-alignment latency effect is also not supported.

## Falsification check

The residency contrast remained strongly tied to mapping identity:

```text
recent=A:
  mean recent-older = -0.16939
  positive rate     = 0.0625

recent=B:
  mean recent-older = +0.15132
  positive rate     = 0.953125
```

Exploratory reconstruction across all trials:

```text
mean B - A resident fraction = +0.1604
B > A in 94.5% of trials
```

## Frozen finding

The OBS-003 A/B asymmetry cannot be promoted to a clean past-recency-versus-future-semantics information gap.

Randomizing final recency did not move the residency asymmetry.

A lower-level mapping/layout factor remains unresolved.

## Frozen decision

Pause semantic Value-of-Information calculation.

Return to mechanism characterization before another information/control claim.

## Repository updates

- `findings/HYP-002-initial.md`
- README status updated through HYP-002.

## Next recommended bounce

> Design CHAR-002 to decompose mapping creation order, initial fault/touch order, and virtual-address/VMA ordering while measuring A/B residency under 160–162 MiB pressure. Use pseudo-Council first; use Monte Carlo only if sample allocation is non-obvious.

## Authority boundary

HYP-002 does not establish the cause of the stable A/B asymmetry.

It only falsifies the tested final-recency explanation in this bounded workload.
