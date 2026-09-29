# EXT-2026-09-30 — Memory systems reconnaissance

> **Status:** EXTERNAL RECONNAISSANCE / NO PHYSICAL RUN
> **Cut:** 2026-09-30 JST
> **Purpose:** compare finite-ram-lab findings against current Linux-mm and AI-memory systems work.

## 1. Linux memcg stock abstraction is actively being moved upstream — policy change was pulled back

A v5 patch series posted 2026-08-31 proposed both:
- moving stock from `mem_cgroup` into `page_counter`;
- changing the allocation/draining topology.

**Correction / update at the 2026-09-30 cut:** v6 and the 2026-09-28 v6 RESEND
explicitly narrow the series to the abstraction move. v6 retains the existing seven-slot
per-CPU design and drain policy.

Therefore:
- implementation ownership may move `memcg -> page_counter`;
- current stock semantics must not be assumed to change merely because that move lands;
- a receipt must distinguish implementation location from runtime stock policy.

Relevant series:

- Joshua Hahn, "[PATCH v5 0/7] move stock from mem_cgroup to page_counter"
- "[PATCH v5 6/7] mm/memcontrol: convert memcg to use page_counter_stock"

The current upstream tree inspected at this cut still contains:

- `NR_MEMCG_STOCK = 7`
- `MEMCG_CHARGE_BATCH = 64`
- the existing `memcg_stock` implementation

and does not yet contain `page_counter_stock`.

Therefore this is **active proposed work, not yet current mainline behavior** at this cut.

### Why this matters to finite-ram-lab

Our hosted experiments used Ubuntu kernel:

`7.0.0-1012-azure`

and directly exploited/observed the current design:

- shared per-CPU memcg stock;
- 64-page batch;
- stock drain/refill behavior;
- PTE charge consuming the same stock.

v5 would have removed the seven-memcg shared-slot topology, but v6 deliberately does not.

The correct compatibility boundary is therefore multi-axis rather than a single
`OLD_MEMCG_STOCK vs PAGE_COUNTER_STOCK` bit:

- stock implementation owner: memcg vs page_counter;
- stock policy: seven-slot shared per-CPU topology vs any future policy;
- charge batch size;
- drain policy;
- tier-aware counters/limits enabled or disabled.

Any future cross-kernel reproduction must record these semantics separately.

## 2. The patch discussion independently confirms stock-drain observability matters

Separate 2026 discussion around trimming vs draining per-CPU charge stock reports workloads
spending very large fractions of CPU time in memcg charge/uncharge paths for particular request sizes.

This reinforces two finite-ram-lab lessons:

- charge-stock behavior can have narrow size-dependent knees;
- draining is not a negligible bookkeeping detail.

It does **not** identify our observed `-17 pages` signature by itself.

## 3. mzCache — restoration-oriented memory management

Paper:

`mzCache: On-Device LLM Memory Management under Multitasking`
(arXiv:2609.01338, MobiCom 2026)

Key idea:

Instead of optimizing only eviction, organize memory around **fast restoration from arbitrary partial-eviction states**.

Mechanisms include:

- fine-grained shared buffers;
- elastic partial eviction/restoration;
- concurrent CPU restoration and GPU inference;
- hybrid swap;
- backward-out eviction.

Reported result:

- 2.1x–5.5x TTFT reduction vs storage-backed partial offload.

### finite-ram-lab connection

This independently supports a design principle already emerging from Evidence Residency and Strata:

`eviction policy < recoverable-state transition design`

The relevant variable is not simply "what remains resident", but whether any reachable cold state has a cheap,
well-defined restoration path.

## 4. Tiered KV cache is becoming a first-class systems layer

Recent sources:

- vLLM: "Tiered KV Cache Offloading in vLLM" (2026-09-10)
- TierKV (arXiv:2609.21172)
- "The KV Cache Is the New Memory Wall" (arXiv:2609.30854)

vLLM's current direction treats KV as a hierarchy spanning:

- accelerator memory;
- host memory;
- filesystem;
- object store;
- remote peer.

TierKV predicts future demand before decoding and assigns KV state across multiple representations/tiers under
memory and quality budgets.

The KV-memory-wall survey frames long-context inference as three regimes where the dominant bottleneck shifts
from weights to KV traffic and then to interconnect/tiering limits.

### finite-ram-lab connection

This strengthens the hypothesis that a useful finite-memory controller needs:

1. explicit tier identity;
2. predicted future demand;
3. transition cost;
4. restoration cost;
5. bottleneck-regime detection.

A single scalar "free memory" is insufficient.

## 5. SSD-LLaMA — SSD as executable model memory

Paper:

`SSD-LLaMA: SSD-Native Inference for Trillion-Parameter MoE at 1+ Token/s on a Consumer PC`
(arXiv:2609.18110)

It explicitly coordinates:

`SSD -> RAM -> VRAM`

for dynamic expert delivery and CPU-GPU hybrid execution.

Reported result includes >1 token/s for a trillion-parameter MoE on a single RTX 5090 with <=32 GB RAM.

### finite-ram-lab connection

This independently converges with Strata on three-tier executable residency.

Important abstraction:

`capacity tier != passive backing store`

A lower tier can be an active execution participant if scheduling and delivery are designed around it.

## 6. Cache-aware MoE routing changes demand, not only cache policy

Paper:

`Cache-Aware Joint Router Adaptation for Memory-Efficient MoE Inference`
(arXiv:2609.04895)

Instead of treating expert demand as fixed, the model/router is adapted so future expert requests become more
cache-friendly.

Reported effects include higher adjusted hit rate and reduced expert traffic.

### finite-ram-lab connection

This introduces a stronger control loop:

`observe demand -> place memory`

can become

`observe residency + shape future demand -> place memory`.

This is analogous to controlling hidden-state transitions rather than merely observing them.

## 7. New external convergence

Across Strata, vLLM tiered KV, TierKV, mzCache and SSD-LLaMA, a common design pattern is now visible:

```
state classification
      |
      v
HOT / WARM / COLD / EVICTED
      |
      +--> predicted next use
      +--> transfer cost
      +--> restore cost
      +--> phase ownership
      +--> interference / pressure
      |
      v
controlled transition
```

This is closely aligned with the conceptual transition in finite-ram-lab:

`rare-state observation -> hidden-state inference -> state construction`.

## 8. Important separation

The external AI-memory work does **not** validate the specific memcg/Q64 mechanism.

It validates the broader systems thesis:

> finite memory is best treated as a controlled state-transition problem rather than a static capacity problem.

The Q64 work remains Linux-specific evidence.

## 9. New hypotheses worth retaining after the current research pause

### EXT-H1 — Kernel-semantics transition

A source-code relocation of stock into page_counter is **not** sufficient to predict a changed rare-state
distribution if the seven-slot/drain policy is preserved.

The natural rare-state distribution should be expected to change only when a behaviorally relevant stock or
tier-accounting semantic changes. This must be established from receipts/source audit, not kernel version or
struct ownership alone.

### EXT-H2 — Restoration cost is a state variable

Two COLD states with equal byte footprint are not equivalent if one can be restored incrementally while the other
requires recomputation/full reload.

### EXT-H3 — Demand shaping can dominate cache replacement

If future demand itself can be altered, cache policy alone is an incomplete optimization surface.

### EXT-H4 — Bottleneck phase transitions matter more than peak capacity

Optimization should explicitly detect when the binding resource changes:
weights -> KV -> PCIe/storage/network -> compute/synchronization.

### EXT-H5 — Lower tiers can be active

SSD/RAM need not be passive overflow; they can participate in execution via bounded streaming and overlap.

## 10. Research consequence

Do not launch a new experiment from this reconnaissance.

When physical work resumes, kernel architecture must become an explicit receipt:

- kernel version;
- old `memcg_stock` vs new `page_counter_stock`;
- `MEMCG_CHARGE_BATCH`;
- number/topology of stock slots if applicable.

This protects the Q64/rare-state model from silently crossing a kernel semantic boundary.


## 11. Tiered memcg limits — a direct bridge to finite-ram-lab's general tier work

A separate RFC v3 series, `Introduce tiered memcg limits`, proposes per-tier page counters and
tier-proportional memcg limits for systems with HBM/DRAM/CXL/PMEM-style memory tiers.

The RFC explicitly argues that total-footprint limits do not provide performance isolation when workloads can
occupy different fractions of fast memory. It adds tier-aware accounting/enforcement, tier-targeted reclaim,
allocation steering, migration accounting, and promotion gating.

This is **not mainline behavior at this cut**.

The important research connection is structural:

`total capacity != placement entitlement != performance isolation`

This is a kernel-level analogue of the same distinction seen in Strata, TierKV and vLLM tiering.

It should enter finite-ram-lab as an external semantics branch, not be mixed into the existing Q64 evidence.
