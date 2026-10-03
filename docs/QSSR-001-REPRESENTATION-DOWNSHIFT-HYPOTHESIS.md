# QSSR-001 — Representation-Downshift Hypothesis

> Status: HYPOTHESIS INTAKE / NOT YET PHYSICALLY TESTED  
> Scope: inspired-research lane; does not change the active Chapter-II memcg frontier  
> Date: 2026-10-03

## 1. Motivation

Sony's public description of Quick Spectral Super Resolution (QSSR) says that the base-PS5 implementation uses:

- a **streamlined neural-network architecture**; and
- a **hand-tuned implementation** that maximizes performance on PS5.

Sony's SIGGRAPH 2026 description of upgraded PSSR gives a broader architectural clue: move work that has efficient closed-form solutions out of the learned model and let the model focus on the pattern-recognition work it is best suited for. Sony describes the result as reducing runtime, memory, and training cost by giving the model **less to do, not more**.

Sources:

- https://blog.playstation.com/2026/10/01/ai-upscaling-is-coming-to-ps5/
- https://advances.realtimerendering.com/s2026/index.html

This document does **not** claim that QSSR's unpublished internal layer graph, tensor shapes, weight layout, precision schedule, or exact low-resolution feature hierarchy are known.

Instead, QSSR motivates a narrower Finite RAM Lab question:

> Can expensive state estimation / decision work be pushed onto a smaller sufficient representation, while large state is retained only as cheap-to-reconstruct, cheap-to-reload, or explicitly cold material?

The systems analogue is not "use an AI upscaler for RAM."

The analogue is:

```text
large state
   |
   +--> small sufficient state ------> expensive semantic decision
   |
   +--> reconstructible/cold state --> cheap reconstruction / reload
```

The research target is whether this factorization can move the finite-memory pressure knee without unacceptable tail latency, I/O, or quality loss.

## 2. Claim ceiling

The current claim is only:

> **Representation downshift is a testable design hypothesis for finite-memory systems.**

Not claimed:

- that QSSR itself uses the exact equations below;
- that a low-resolution neural feature pyramid has been reverse-engineered from PS5 binaries;
- that compression/offload is always beneficial;
- that reconstructible state should always be evicted;
- that an application-local policy should override kernel memory authority;
- that this lane supersedes Chapter-II memcg work.

QSSR is an external architectural inspiration, not evidence for a Linux memory-management result.

## 3. Core abstraction

Let the full application state have size:

```text
N
```

and let a downshifted sufficient representation retain fraction:

```text
rho,  0 < rho <= 1
```

of the expensive decision surface.

Let:

- `c_e` = expensive per-unit semantic/decision cost;
- `c_r` = cheap per-unit reconstruction cost;
- `C_mig` = compression / demotion / promotion / bookkeeping cost;
- `p_miss` = probability that downshifted state is insufficient for the next demand;
- `C_miss` = expected cost of a miss, including reload, rebuild, refault, and latency penalty.

A full-state baseline has approximate cost:

```text
C_base = c_e * N
```

A one-level downshift has:

```text
C_shift = c_e * rho * N
        + c_r * N
        + C_mig
        + p_miss * C_miss
```

The simplest benefit condition is:

```text
c_e * N * (1 - rho)
    > c_r * N + C_mig + p_miss * C_miss
```

This is intentionally generic. It says that the expensive work removed by shrinking the semantic representation must exceed reconstruction, movement, and miss penalties.

## 4. Ozaki lane: dimensionless threshold model

Normalize all penalty terms by the expensive work removed:

```text
S = c_e * N * (1 - rho)
```

Define:

```text
Pi_reconstruct = (c_r * N) / S
Pi_migration   = C_mig / S
Pi_miss        = (p_miss * C_miss) / S
```

Then the first-order break-even condition is:

```text
Pi_reconstruct + Pi_migration + Pi_miss < 1
```

This is the first Ozaki-style target, not a final law.

The useful research question is the phase diagram:

```text
(rho, p_miss, C_miss, c_r, C_mig, memory_budget)
                    |
                    v
         beneficial / neutral / harmful
```

The hypothesis predicts that a non-trivial beneficial region exists and that its boundary can be measured.

## 5. Multi-level form

For a hierarchy of representations:

```text
N_0 = N
N_l = rho_l * N_(l-1)
```

with semantic computation concentrated at lower-volume levels, define:

```text
C_sem = sum_l c_e,l * N_l
```

and:

```text
C_total = C_sem
        + C_reconstruct
        + C_migrate
        + E[C_miss]
```

The research problem becomes:

```text
minimize C_total
subject to:
  peak_memory <= K
  quality_loss <= epsilon_q
  p99_latency <= L_max
  correctness >= required_floor
```

This permits an explicit comparison between:

1. full-state residency;
2. compressed residency;
3. reconstructible-state dropping;
4. RAM -> SSD demotion;
5. tiered combinations;
6. small semantic summaries that guide what is worth keeping.

## 6. Finite-RAM mapping

The graphics analogy maps into Finite RAM Lab only at the level of resource allocation:

| Graphics-side abstraction | Finite-RAM analogue |
|---|---|
| large output representation | large application state / working set |
| lower-volume learned representation | compact demand / phase / importance state |
| expensive learned inference | expensive residency or semantic decision |
| cheap reconstruction | rebuild / reload / decompression / regeneration |
| temporal history | recent demand and phase history |
| quality loss | latency, refault, rebuild, correctness, or user-visible degradation |

The important candidate principle is:

> **Keep the expensive semantic decision surface small; let large reconstructible state be governed by cheap mechanisms.**

This may interact with existing Finite RAM Lab ideas such as application intent, regenerable caches, value-of-information measurements, and explicit RAM/SSD tiering.

## 7. Pressure-knee prediction

Let:

```text
K_base*
```

be the smallest memory budget at which the baseline remains within the accepted performance envelope.

Let:

```text
K_shift*
```

be the corresponding knee under representation downshift.

The hypothesis is useful only if a treatment can achieve:

```text
K_shift* < K_base*
```

while satisfying the same correctness and quality constraints.

A smaller RSS by itself is not a success.

A valid result must include at least:

- knee movement;
- p50 / p95 / p99 latency;
- rebuild / reload counts;
- refaults;
- bytes moved across RAM / storage boundaries;
- CPU/GPU cost if applicable;
- quality or correctness loss;
- invalidator and rare-tail classification.

## 8. First experiment family

Do not modify the current Chapter-II physical program yet.

Start with a model/simulation lane.

### QSSR-001-A — parameter sweep

Variables:

- `rho`: semantic downshift fraction;
- `h`: irreducible hot-state fraction;
- `p_miss`: insufficient-summary probability;
- reconstruction cost;
- compression/decompression cost;
- storage latency and bandwidth;
- phase-change hazard;
- prefetch accuracy;
- memory budget `K`.

Outputs:

- predicted pressure knee;
- mean and tail latency;
- peak resident memory;
- reload/rebuild traffic;
- expected total cost;
- break-even class.

Use the existing toolbox where applicable:

- Sobol / Latin-hypercube design;
- PRCC screening;
- changepoint / knee detection;
- exact offline residency MILP as an oracle;
- conditional information gain for compact-state usefulness;
- generalized Pareto fitting for tail penalties.

### QSSR-001-B — synthetic physical prototype

Only after the model identifies a stable beneficial region:

- generate a workload with a declared hot semantic core;
- add a large reconstructible state;
- compare full-resident versus downshift/tiered treatment;
- preserve identical logical outputs;
- sweep memory budget through the predicted knee;
- capture tail regressions and rare misses separately from mean improvement.

## 9. Falsifiers

The hypothesis weakens or fails if complete experiments show that:

1. the compact state requires so much metadata that residency savings vanish;
2. reconstruction bandwidth or CPU time dominates the saved expensive work;
3. miss/reload tails dominate even when mean cost improves;
4. the memory pressure knee does not move;
5. the same knee movement is achievable with a simpler existing Linux mechanism;
6. quality/correctness loss exceeds the declared bound;
7. the compact state has too little conditional information about near-future demand to guide useful decisions.

A negative result is a valid outcome.

## 10. Interaction with existing research

This lane is complementary to, not a replacement for:

- Chapter-II memcg state-transition work;
- STRATA-001 page-cache bypass / semantic HOT-memory preservation;
- future application-intent / OS-global-state coordination;
- RAM / SSD tiering experiments.

A particularly important future comparison is:

```text
plain eviction
vs
semantic downshift
vs
semantic downshift + SSD tier
vs
offline MILP oracle
```

The oracle comparison prevents a clever mechanism from being credited for gains that come only from a favorable workload.

## 11. Current decision

Accept QSSR as an architectural inspiration and freeze the initial hypothesis:

> **QSSR-001 / Representation-Downshift Hypothesis**  
> Under finite resource pressure, it may be cheaper to perform expensive semantic work on a deliberately reduced sufficient representation and handle the large reconstructible representation with cheaper mechanisms, provided reconstruction, movement, and rare-miss penalties remain below the expensive work removed.

Next research action:

> Build the QSSR-001-A phase diagram before authorizing a physical memory-control mechanism.
