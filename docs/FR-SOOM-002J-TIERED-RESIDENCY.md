# FR-SOOM-002J — Tiered Semantic Residency Shadow Planner

Status: **SYNTHETIC SHADOW OPTIMIZATION**

## Goal

FR-SOOM-002J combines the semantic-OOM control line with the explicit VRAM/RAM/SSD tiering question already isolated by STRATA-001.

The question is not "can swap use SSD?"

It is:

> When memory pressure rises, can the controller deliberately move semantically reconstructible state through RAM compression, SSD residency, drop/rebuild, and process sacrifice while respecting latency and tail-risk constraints?

No live host control is performed.

## State representation

Each semantic region chooses exactly one representation.

- KV: KEEP, Q8, Q4, SSD_COLD
- PREFIX: KEEP, SSD, DROP
- AUX_EXPERTS: KEEP, SSD
- BROWSER_CACHE: KEEP, DROP
- BACKGROUND_JOB: KEEP, EXIT
- ACTIVE_TASK: KEEP, KILL

This is a multiple-choice residency problem rather than a victim score.

## Mathematical model

Let x[i,j] be 1 when semantic region i selects representation j.

Minimize:

J =
  sum semantic_loss[i,j] * x[i,j]
  + 0.01 * E[T_restore]
  + 0.02 * CVaR_0.95(T_restore)
  + 0.001 * SSD_write_MiB

Subject to:

1. Exactly one representation per semantic region:

   sum_j x[i,j] = 1

2. Required relief:

   sum relief[i,j] * x[i,j] >= 4096 MiB

3. SSD tail-bandwidth deadline:

   sum SSD_write[i,j] * x[i,j] / B_p05
   + sum apply_time[i,j] * x[i,j]
   <= pressure_deadline

4. Per-event SSD write budget:

   sum SSD_write[i,j] * x[i,j] <= W_max

The p05 bandwidth constraint intentionally uses a tail quantity rather than mean bandwidth.

## Recovery-tail model

The synthetic refault distribution contains:

- no refault: 0.80
- KV only: 0.05
- prefix only: 0.05
- auxiliary experts only: 0.05
- KV + auxiliary experts: 0.03
- KV + prefix + auxiliary experts: 0.02

The planner scores both expected recovery latency and CVaR95 recovery latency.

This prevents a plan with attractive mean cost but catastrophic hot-return behavior from being treated as free.

## Frozen panel

### RAM_ONLY

SSD actions are forbidden.

Selected plan:

- KV -> Q4
- PREFIX -> DROP
- BROWSER_CACHE -> DROP
- active task -> KEEP

Relief: 4096 MiB.

Synthetic semantic loss: 45.

### FAST_SSD_TIERED

Synthetic p05 SSD write bandwidth: 2500 MiB/s.

Deadline: 1600 ms.

Selected plan:

- KV -> Q8
- AUX_EXPERTS -> SSD
- active task -> KEEP

Relief: 4096 MiB.

SSD write: 3072 MiB.

Migration time at p05 bandwidth: 1244.8 ms.

Synthetic semantic loss: 12.

Expected restore latency: 26 ms.

CVaR95 restore latency: 260 ms.

The selected plan is deliberately hybrid: RAM-side quantization and SSD offload are both used.

### Analytic SSD bandwidth knee

For the selected FAST_SSD_TIERED plan:

- SSD bytes = 3072 MiB;
- non-SSD apply time = 16 ms;
- deadline = 1600 ms.

Therefore the minimum qualifying p05 write bandwidth is:

B_min = 3072 / ((1600 - 16) / 1000)
      = 1939.3939 MiB/s.

The synthetic 2500 MiB/s arm is above the knee. A 1000 MiB/s device is below it.

This gives a concrete pressure-dependent boundary rather than a global rule that SSD is either "fast" or "slow".

### WRITE_BUDGET_2G

The per-event SSD write budget is tightened to 2048 MiB.

The 3072-MiB AUX_EXPERTS spill becomes infeasible.

The optimizer changes plan rather than disabling SSD entirely:

- KV -> Q4
- PREFIX -> SSD
- BROWSER_CACHE -> DROP
- SSD write = 1024 MiB
- synthetic semantic loss = 36

This is intentionally between the unrestricted tiered arm (loss 12) and RAM-only arm (loss 45). It models endurance / write-amplification pressure as another hard resource constraint.

### SLOW_SSD_TIERED

Synthetic p05 SSD bandwidth: 1000 MiB/s.

Deadline: 800 ms.

SSD migration cannot qualify under the frozen deadline, so the optimizer falls back to the RAM-only plan.

### EMERGENCY_SHORT_DEADLINE

Synthetic p05 SSD bandwidth: 2500 MiB/s.

Deadline: 150 ms.

Again SSD is rejected by the hard deadline and the RAM-only plan wins.

## Finding

The useful abstraction is not:

RAM -> SSD whenever RAM is full.

It is:

semantic state
  -> candidate representations
  -> pressure deadline
  -> tail bandwidth
  -> refault risk
  -> semantic cost
  -> exact feasible plan

In the frozen synthetic fixture, SSD creates a lower-loss escape route only when its tail bandwidth is fast enough for the current pressure deadline.

When the SSD is slow or the deadline is short, the same planner refuses the SSD path automatically.

## Connection to an earlyoom successor

A resident controller could eventually ask applications to advertise bounded actions such as:

- quantize KV to Q8;
- quantize KV to Q4;
- spill cold KV or experts to SSD;
- drop rebuildable prefix state;
- release disposable cache;
- exit background work;
- kill the active task only as an emergency action.

The OS-facing daemon would optimize over advertised capabilities rather than guessing which anonymous pages are valuable.

That is the intended bridge between semantic application knowledge and global pressure telemetry.

## Important non-claim

All costs, deadlines, bandwidths, refault probabilities, and semantic-loss values in this experiment are synthetic controls.

This experiment qualifies the planning architecture only.

It does not recommend a host SSD setting, a swap policy, a KV quantization threshold, or a process-kill threshold.

## Claim ceiling

**SYNTHETIC_TIERED_RESIDENCY_SHADOW_PLANNER_ONLY**

## Next

The next physical step should not immediately enable control.

First collect read-only host distributions for:

- actual SSD sequential and random write bandwidth under memory pressure;
- p05/p01 migration bandwidth;
- SSD queue latency;
- zram compression throughput and ratio;
- PSI memory stall;
- refault latency after SSD spill;
- write amplification / bytes written;
- action-specific RAM relief.

Those distributions can replace the synthetic controls and feed the existing Monte Carlo / tail-fit toolchain before any live governor action is authorized.
