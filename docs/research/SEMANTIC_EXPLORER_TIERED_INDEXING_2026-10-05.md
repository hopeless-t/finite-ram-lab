# Semantic Explorer under finite RAM — tiered indexing note — 2026-10-05

## Trigger

A symbolic Explorer namespace (`~` -> contextual target) suggests that users can interact with logical objects without knowing their physical storage. Under finite RAM, the same separation lets indexes and providers move between memory, SSD and remote/cold tiers without changing the user-facing namespace.

Source signal: https://forest.watch.impress.co.jp/docs/news/insiderpre/2145484.html

## Core thesis

Do not require a permanently resident semantic index to provide semantic exploration.

Use a ladder:

```text
L0 literal metadata/path lookup
L1 grep/ripgrep targeted scan
L2 compact local index
L3 richer semantic index
L4 remote/cold provider
```

The planner chooses the cheapest tier that can satisfy the query's selectivity, freshness and latency requirements.

## Why grep matters

Grep-like scanning has poor asymptotic reuse compared with an index, but near-zero persistent RAM and excellent cold-start properties. It is therefore not an obsolete primitive; it is a valuable **finite-memory fallback/oracle**.

A semantic query can first narrow scope using cheap metadata, then dispatch exact leaf searches only where needed.

## Memory model

Let:

- `M_i` = resident memory of tier/index `i`
- `C_i` = cold activation cost
- `Q_i` = expected query work
- `R_i` = reuse probability within horizon `H`
- `F_i` = freshness penalty

Explore policies that minimize something like:

```text
J = alpha * peak_RAM
  + beta * latency
  + gamma * bytes_read
  + delta * stale_risk
  + epsilon * activation_churn
```

subject to correctness and authority constraints.

## Tiering opportunities

- keep alias/name maps resident; evict embeddings
- retain compact Bloom/term summaries; spill postings to SSD
- generate semantic vectors only for hot scopes
- use grep/ripgrep to reconstruct evicted detail on demand
- persist canonical object IDs separately from expensive projections
- keep query history as compact statistics rather than full result caches

## Virtual folders without materialization

Views such as `?changed since yesterday` or `?failed experiments` should remain query definitions + small cached summaries, not eagerly materialized directory trees.

## Experiments

### FR-SE-01 — grep vs resident index frontier
Replay the same query corpus under 256/512/1024 MB budgets and compare scan, compact-index and semantic-index policies.

### FR-SE-02 — index demotion
Move rich index data from RAM -> SSD while keeping scope summaries resident. Measure latency and peak RSS.

### FR-SE-03 — adaptive promotion
Promote only repeatedly queried scopes into richer indexes and measure whether hit-rate gains justify RAM residency.

### FR-SE-04 — semantic fallback correctness
Evict semantic state and force literal reconstruction. Compare normalized evidence against the indexed path.

## Metrics

- peak and steady-state RSS
- SSD bytes read/write
- remote bytes transferred
- cold activation count
- p50/p95 query latency
- result equivalence
- index bytes per canonical object
- useful hits per resident MB

## North-star question

Can an AI-native semantic Explorer behave as if the whole workspace is indexed while physically keeping only a small, adaptive working set resident?
