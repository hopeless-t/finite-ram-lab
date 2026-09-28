# MEMCG-003 Seven-Slot Occupancy Intervention v1

> **Status:** DESIGN FROZEN / NOT LAUNCHED
> **Authority:** hosted Linux accounting research only

## Question

Does controlled occupancy pressure from distinct memcgs expose the source-derived seven-slot capacity of the per-CPU memcg charge cache?

This is a falsification experiment for the mechanism candidate raised by MEMCG-002. Source inspection is prior information, not experimental confirmation.

## Source-derived prior

Linux `mm/memcontrol.c` at `72d3fcf802c45d00b300f25b848a93c3a2bd7c7e` defines `NR_MEMCG_STOCK = 7` and a per-CPU `memcg_stock_pcp` containing seven cached memcg pointers, seven page counters, and rotating `drain_idx`.

## Atomic hypotheses

H7:
A target entry can survive occupancy by fewer than seven distinct cached memcgs on the same CPU, but becomes eviction-eligible when the cache is full and another distinct memcg requires insertion.

Hsame:
Repeated work in the same helper memcg should not emulate distinct-slot occupancy.

Hnone:
No-helper control should preserve the target state absent unrelated drain activity.

Hnet:
Total target `memory.current` is only a net-accounting proxy; absence of a visible discontinuity is not proof of absence of local refill/eviction.

## Arms

For helper-count `k = 0..10`:
1. create/prime target memcg on CPU A;
2. keep target alive;
3. sequentially create and touch `k` distinct helper memcgs pinned to CPU A;
4. re-touch target and record accounting response;
5. destroy helpers only after the measured target re-touch.

Controls:
- no-churn k=0;
- same-memcg repeated helper work matched for pages/touches;
- CPU-B helper churn, while target remains CPU-A, as locality control.

Randomize arm order within blocks where setup semantics permit. Record actual affinity and cgroup identity.

## Measurements

Required:
- target `memory.current` before/after each insertion and target re-touch;
- helper `memory.current`;
- `memory.stat` anon/file/kernel where available;
- `memory.events` deltas;
- PSI memory `some`/`full` totals when readable;
- wall-clock insertion and re-touch latency;
- pages touched and pages/sec;
- cgroup creation/destruction cost;
- kernel, page size, cgroup mode, CPU set, runner receipt.

Optional diagnostic:
- `memory.pressure` scoped PSI;
- repeated reads around a suspected discontinuity, provided measurement overhead is separately characterized.

## Decision rule

Do not declare H7 from a single jump.

Primary support requires:
- a reproducible change-point concentrated at the source-derived occupancy boundary across >=3/4 blocks;
- distinct-memcg arm stronger than same-memcg and CPU-B locality controls;
- no material pressure event explaining the discontinuity;
- throughput/latency evidence showing the effect is not solely cgroup setup noise.

Compare candidate capacities 1..10. Report the complete score surface, not only the winning capacity.

If no sharp boundary is recovered, record `NO_VISIBLE_SLOT_BOUNDARY`; do not reinterpret absence as proof that the kernel structure is absent.

## Monte Carlo pre-launch stress test

A simple change-point selector was stress-tested before launch:
- helper counts 0..10;
- independent 3% observation flips;
- independent 5% missing observations;
- 50,000 simulated sweeps;
- candidate boundaries 1..10 selected by minimum mismatch, ties randomized.

When the true visible boundary was 7:
- exact boundary 7 selected in **86.6%** of sweeps;
- adjacent 6 selected in **4.9%**;
- adjacent 8 selected in **4.7%**.

Under a no-boundary null:
- spurious exact boundary 7 selected in about **0.29%** of sweeps.

Interpretation:
one sweep is useful for discovery but not sufficient for mechanism acceptance. Four independent blocks plus controls materially reduce false-boundary risk. Real runner noise may be correlated, so these values are design diagnostics, not p-values.

## Pseudo-Council convergence

Mechanist:
Test seven because source says seven.

Skeptic:
A visible net-accounting boundary may be shifted or erased by unrelated drains and shared-runner activity.

Measurement reviewer:
Collect target/helper accounting, pressure, and timing around every insertion; preserve negative results.

OSS reviewer:
Include throughput and cgroup lifecycle cost so any future mitigation can be judged for practical use.

Authority reviewer:
Design freeze does not authorize execution. Hosted launch requires a separate explicit marker after implementation CI passes.

### Decision

APPROVE design freeze.
Do not yet approve launch.

## External validity

A positive result is specific to the tested kernel/configuration and memcg implementation. Re-run on at least one materially different kernel line before making portability claims. The experiment concerns Linux memcg accounting behavior, not physical DRAM allocation granularity.

## Authority boundary

Proposal != Decision.
Expressibility != Executability.
No local-PC execution.
No Remote Desktop Commander.
No memory-control policy.
No blind retry after unknown delivery.
