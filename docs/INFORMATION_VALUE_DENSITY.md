# Information-Value Density as a Candidate Residency Signal

## Status

Research note only. This does **not** propose replacing the kernel's reclaim policy and does not claim that semantic memory hints improve Linux memory management.

## Motivation

Finite RAM Lab asks what should remain resident when physical memory is scarce.

A useful abstraction from information economics is:

```text
bytes occupied != value preserved
```

A small object may be disproportionately valuable if losing it forces an expensive recomputation, destroys provenance, or removes information needed for a near-future decision. A large object may be cheap to reconstruct and have little near-term consequence.

This suggests studying a candidate metric called **information-value density**.

## Candidate decomposition

For memory object `m`:

```text
V(m) =
    expected_future_use(m)
    * consequence_of_miss(m)
    * reconstruction_cost(m)
    * freshness(m)
    * confidence(m)
    + option_value(m)
    - retention_cost(m)
```

Then:

```text
value_density(m) = V(m) / resident_bytes(m)
```

This is a semantic research signal, not a kernel truth.

## Why information gain matters

Some resident state exists primarily to prevent future uncertainty.

Examples in an application-level research harness might include:

- a compact provenance index that avoids re-reading a large evidence corpus;
- a summary state that determines which experiment should run next;
- a small cache entry whose presence prevents an expensive remote lookup;
- a model state whose eviction destroys continuity and forces re-validation.

The value of such objects is not captured by size alone.

## Connection to current Finite RAM Lab principles

The repository already distinguishes application-side meaning from OS-side observable pressure.

Information-value density fits that split:

```text
Application knows:
  meaning
  rebuild cost
  lifecycle
  likely next use
  decision consequence

OS knows:
  pressure
  residency
  faults / refaults
  reclaim competition
  global constraints
```

The research question is not whether the application should control reclaim directly. It is whether the mismatch between these views is measurable and useful.

## Candidate synthetic experiment

Before any physical-memory intervention, build an offline trace experiment.

Each object carries:

```text
size
access trace
rebuild cost
future decision impact
provenance sensitivity
freshness decay
```

Compare eviction policies:

1. LRU-like recency baseline;
2. size-aware baseline;
3. rebuild-cost-aware baseline;
4. value-density heuristic;
5. exact offline optimum for the declared trace where tractable.

Measure:

- total miss cost;
- decision-changing misses;
- bytes retained;
- rebuild work;
- regret versus exact offline optimum;
- sensitivity to wrong semantic predictions.

## Important failure cases

A semantic signal is dangerous if treated as ground truth.

Test at least:

- predicted future use is wrong;
- high-value labels become stale;
- two low-value objects jointly unlock a high-value computation;
- one process overstates its own value;
- value metadata costs more memory than it saves;
- semantic prioritization harms system-wide fairness;
- value density improves one workload while increasing total refault cost.

## Option value

A resident object can be valuable because a future event may make it important, even if it is cold now.

This is analogous to keeping an option alive:

```text
cold now
+ cheap enough to retain
+ expensive / impossible to reconstruct later
+ plausible future state transition
=> non-zero retention option value
```

The model needs explicit decay so option value does not justify retaining everything forever.

## Relation to STRATA-style tiering

This abstraction can complement explicit RAM / SSD / storage tiering without assuming a particular implementation.

A candidate tier decision could consider:

```text
HOT: high near-term decision value / low miss tolerance
WARM: meaningful option value / moderate rebuild cost
COLD: low near-term value / cheap reconstruction
ARCHIVE: provenance needed, latency tolerated
DROP: reproducibly reconstructible and low-value
```

This is intentionally richer than hot/cold access frequency.

## Scientific boundary

The next step should be an offline, reproducible simulation using declared traces and exact-oracle comparisons where possible.

Do not jump directly from this note to kernel hooks or production memory-control authority.

## Candidate principle

> **Under finite RAM, preserve the bytes whose loss creates the greatest expected future regret—not merely the bytes touched most recently.**
