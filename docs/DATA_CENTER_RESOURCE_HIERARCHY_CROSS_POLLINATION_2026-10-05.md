# Data-center resource hierarchy cross-pollination — 2026-10-05

## Research question

Finite RAM Lab asks what should remain resident when physical memory is scarce. Recent data-center resource reporting suggests a broader systems question:

> **How much electricity, data movement, and cooling demand is downstream of unnecessarily large resident working sets?**

The lab should not assume that reducing resident memory automatically reduces energy or water. The measurable hypothesis is narrower: semantic working-set control may reduce memory traffic, storage/network movement, and re-computation under a fixed verified-work target.

Primary context:

- Google Data Centers efficiency: https://datacenters.google/intl/en/efficiency/
- IEA, *Energy and AI*: https://www.iea.org/reports/energy-and-ai
- Existing Finite RAM Lab Strata lane: `docs/STRATA-INSPIRATION.md`

## Core transfer

The existing principle generalizes cleanly:

```text
addressable universe != resident working set
```

For AI workloads the addressable universe can include:

- model weights;
- KV/cache-like state;
- repository/history state;
- embeddings/indexes;
- generated artifacts;
- evidence and provenance;
- intermediate tensors/results.

Only a subset must be resident in the fastest/most expensive tier at any moment.

## Proposed hierarchy model

```text
L0  immediately active / latency-critical
L1  hot reusable state
L2  warm reconstructible state
L3  cold file/object storage
L4  remote/archive source of truth
```

Each object should carry at least:

```text
ResidencyObject {
  object_id
  size_bytes
  semantic_role
  rebuild_cost
  transfer_cost
  reuse_distance
  expected_next_use
  evidence_criticality
  authority_class
  current_tier
}
```

The operating system sees pressure and physical behavior; the application can know semantic value, rebuild cost, phase, and future-use likelihood. The research opportunity is still the coordination gap between those views.

## Candidate new metrics

Do not optimize "free RAM". Add resource-normalized observables around a fixed useful-work target:

- verified tasks completed;
- resident GiB-seconds;
- major/minor faults;
- reclaim/refault activity;
- bytes read from storage;
- bytes written to storage;
- bytes transferred across process/network boundaries where observable;
- recomputation count;
- p95/p99 latency;
- optional calibrated power/energy measurement when hardware access permits.

A useful derived quantity is:

```text
verified useful work / resident GiB-second
```

but it must never replace correctness, tail latency, or evidence integrity as a hard constraint.

## Candidate experiment FRL-DC-001

### Goal

Test whether semantic HOT/WARM/COLD intent can reduce residency and churn under fixed task completion requirements.

### Baselines

```text
A  ordinary demand-driven residency
B  fixed-size application cache
C  semantic phase-aware HOT/WARM/COLD policy
D  C + page-cache bypass for explicitly COLD sequential/file-backed data where safe
```

### Fixed conditions

- same workload trace;
- same task completion target;
- same correctness oracle;
- same memory limit;
- no claim of general data-center savings from one host experiment.

### Observe

- `memory.current` and relevant memcg transitions;
- page-fault/reclaim/refault behavior;
- storage I/O;
- elapsed time;
- task completion/correctness;
- amount of state moved between tiers;
- intervention overhead itself.

### Falsification

The hypothesis is weakened if semantic tiering merely shifts cost from RAM into excessive I/O/recomputation, worsens tail latency, or provides no reproducible reduction in resident/churn cost at equal useful work.

## Coupling to AI model routing

A larger model is also a residency decision. Future cross-project experiments can treat model tier as another object class:

```text
rule/exact tool
  -> tiny model resident
  -> larger model warm/cold
  -> frontier model remote/on-demand
```

Finite RAM Lab should remain focused on measurable memory/resource mechanisms; model-quality policy belongs elsewhere. The transferable question is whether expensive state must stay resident continuously.

## Water boundary

Cooling water is not a direct function of allocated RAM. Any future "water-equivalent" metric must preserve the causal chain:

```text
workload
  -> component power
  -> heat
  -> facility cooling topology
  -> site-specific water use
```

Do not infer water savings from token, RAM, or power savings without the facility-side model.

## Research principle

> **Do not make scarce memory cheaper by moving waste elsewhere. Remove or demote state only when total verified-work cost improves under explicit latency and correctness constraints.**
