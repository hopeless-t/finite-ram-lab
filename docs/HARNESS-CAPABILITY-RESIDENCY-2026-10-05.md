# Harness Capability Residency — cross-pollination note

Date: 2026-10-05
Status: research intake / hypothesis, not finding

## Trigger

Source discussion: https://gigazine.net/news/20261005-deepseek-harness/

A lifecycle-aware harness suggests a systems analogy directly relevant to Finite RAM Lab: application-level capabilities have semantic value, rebuild cost, and phase-specific demand that the OS cannot fully infer from physical memory access alone.

## Proposed abstraction

For capability `i`, define a semantic residency state:

```text
HOT   runtime + state resident; immediate execution
WARM  lightweight state retained; fast resume
COLD  durable descriptor/checkpoint only
OFF   provider absent / reconstruct from source if requested
```

This is distinct from physical page residency. The research opportunity is to study the mapping:

```text
semantic capability demand
          ↕
application runtime residency
          ↕
OS physical-memory residency
```

## Why this fits the lab

Finite RAM Lab already asks:

> When physical RAM is limited, what should remain in memory, what should be reclaimed, and when?

Capability residency adds information unavailable to a generic reclaim policy:

- expected reuse horizon;
- wake/rebuild cost;
- state reconstructability;
- dependency fan-out;
- external side-effect risk;
- acceptable wake latency;
- whether loss is recoverable from canonical state.

## Candidate model

Let residency choice be:

```text
r_i in {HOT, WARM, COLD, OFF}
```

with cost terms:

```text
M_i(r) = resident-memory cost
W_i(r) = expected wake/restore cost
L_i(r) = latency penalty
R_i(r) = recovery/semantic risk
P_i    = predicted probability of near-term use
```

A first decision model can minimize expected cost under memory and latency constraints:

```text
min sum_i [ M_i(r_i) + P_i * W_i(r_i) + P_i * L_i(r_i) + R_i(r_i) ]

subject to
  total resident bytes <= memory budget
  required capabilities satisfy dependency closure
  correctness/recovery invariants hold
```

This is decision support, not evidence of a better memory manager.

## Bounded experiment candidate

Do not change kernel behavior initially. Build a userspace synthetic harness with capabilities having controlled:

- resident size;
- wake latency;
- rebuild bytes;
- reuse interval;
- dependency graph;
- reconstructable vs non-reconstructable state.

Compare:

1. all resident;
2. LRU-only demotion;
3. semantic fixed policy;
4. demand-paged adaptive policy.

Measure:

- peak and time-integrated RSS;
- faults/refaults;
- swap/reclaim pressure where applicable;
- task p50/p95/p99 latency;
- wake count and thrash;
- invalid restore events;
- total useful work completed under a fixed RAM cap.

## Important boundary

```text
semantic COLD != physical page-cold
semantic HOT  != mlock
```

The first study should test whether semantic hints predict a useful coordination gap; it should not assume the OS is wrong.

## Cross-links

- `harness-component-economics`: verified-success economics of residency.
- `mvca`: lifecycle/authority-safe promotion and resume.
- `next-generation-github`: demand-paged collaboration capabilities.
- `memory-attention-lab`: capacity, active computation and physical residency as separate budgets.

## Non-claim

This note extracts a testable cross-layer hypothesis from the harness discussion. It does not claim that DeepSeek Harness demonstrates a RAM-management improvement.
