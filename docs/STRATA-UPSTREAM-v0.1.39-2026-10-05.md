# Strata upstream v0.1.39 cross-pollination — 2026-10-05

> Status: upstream intake / research candidate, not a local result
> Upstream: `Niko1221/Strata` v0.1.39, observed main `6f32ec070f23ced9f50e704d854d775da52591ab`

## Why this matters after STRATA-001..009

The previous local STRATA series already established bounded-working-set and cold-capacity ideas. v0.1.39 adds a more explicit runtime-allocation layer that is useful for the next finite-RAM questions.

## Extracted atoms

1. **Bytes, not object counts, are the canonical memory budget.** Strata changed its streamed expert ring from a fixed slot count to a byte budget because the same number of expert blobs can consume very different memory across quantizations.
2. **Phase-specific scheduling matters.** Prefill and decode have different bottlenecks; one scheduler objective should not be assumed optimal for both.
3. **Placement is runtime state, not static configuration.** Hot experts can live in VRAM while colder data remain in RAM/SSD-backed paths.
4. **Topology is part of the resource model.** Primary GPU, helper/peer GPU, layer split, CPU and storage are different roles, not interchangeable devices.
5. **Parallelism spends cache.** Concurrent sessions reduce queueing latency but can reduce per-request throughput by shrinking the expert cache.
6. **Graceful degradation is a design target.** Older CUDA paths, HIP/SYCL and lower CPU ISA floors preserve capability with reduced performance instead of turning hardware mismatch into hard failure.

## Candidate canonical IR

```text
ResourceTier {
  capacity_bytes
  read_bandwidth
  write_bandwidth
  latency
  compute_capability
  transfer_cost
  eviction_cost
  persistence
  topology_links[]
}

WorkingObject {
  size_bytes
  access_probability
  reuse_distance
  compute_cost_by_tier
  transfer_cost_by_link
  phase
  mutability
}
```

Candidate placement objective:

```text
minimize(transfer_cost + compute_cost + miss_penalty + queue_penalty)
subject to per-tier capacity and correctness constraints
```

## Next research candidates

- **STRATA-010 / Byte-Canonical Budgeting:** test whether decisions based on bytes outperform object/slot-count heuristics across heterogeneous object sizes.
- **STRATA-011 / Phase-Separated Scheduler:** freeze distinct policies for burst/prefill-like work vs iterative/decode-like work and test crossover knees.
- **STRATA-012 / Topology Utility:** model CPU/RAM/NVMe/GPU links explicitly and test whether placement chosen from measured topology beats a static tier order.
- **STRATA-013 / Parallelism Tax:** quantify when an extra concurrent worker/session reduces total verified work because its resident-state footprint evicts higher-value hot state.

## Important non-claims

- Upstream benchmark results are not local evidence.
- Strata-specific CUDA/MoE mechanisms are not assumed to generalize directly.
- This note imports design hypotheses, not performance claims.

## Cross-repo hooks

- `mvca-runtime`: capability/topology-aware worker placement.
- `next-generation-github`: byte-budgeted hot/warm/cold repository context.
- `harness-component-economics`: measure cache/context/parallelism as components with explicit cost and verified utility.
- `catfood-pcg-lab` / `catfood-jev-cua-lab`: asset/world-state streaming with a bounded hot set.
