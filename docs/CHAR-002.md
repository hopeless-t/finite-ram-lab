# CHAR-002 — Mapping / Fault / Address Decomposition

> **Status:** FROZEN DESIGN  
> **Scientific evidence:** NONE YET

## Question

What lower-level factor best explains the stable A/B residency asymmetry that survived HYP-002 final-recency randomization under 160–162 MiB memcg pressure?

Candidate mechanisms:

- separate-mapping creation order;
- initial page-fault/touch order;
- virtual-address position;
- another stable per-mapping state.

CHAR-002 is characterization, not a semantic-demand or control experiment.

## Pseudo-Council convergence

The Council re-ran the interrupted B043 draft from canonical GitHub state and converged after four review rounds.

### Round 1 — Keep semantic demand out

The kernel/VM reviewer required residency to be measured **after the burst and before any semantic reuse**.

No HOT/COLD performance hypothesis is primary here.

### Round 2 — Separate creation order from address position

The memory-layout reviewer rejected a separate-VMA-only design.

Two anonymous mappings may make creation order and numeric virtual-address order highly correlated.

Therefore CHAR-002 uses two complementary families:

1. **Family S — Separate VMAs**
2. **Family H — Shared VMA halves**

Actual base addresses are always recorded.

### Round 3 — Reduce the shared-VMA design

The B043 draft proposed A/B label orientation inside the shared VMA.

The Council rejected that factor as unnecessary duplication.

Kernel behavior cannot depend on an arbitrary Python label unless the label changes an operation.

The shared-VMA family therefore uses physical positions directly:

- lower half;
- upper half.

This reduces the design from the draft 256 trials to **192 trials** without removing a mechanism contrast.

### Round 4 — Monte Carlo decision

The Council considered design Monte Carlo and rejected it for this stage.

Reason:

- all scientifically relevant factorial cells fit directly in every runner block;
- HYP-002 exposed a large, common asymmetry rather than a rare event;
- the dominant uncertainty is **mechanism identity / confounding structure**, not an unknown rare-event rate;
- simulating invented mechanism amplitudes would add model assumptions without improving orthogonality.

The correct mathematical tool here is a balanced factorial decomposition with block-level contrasts.

## Frozen design

### Runner replication

```text
16 independent GitHub-hosted runner blocks
```

Runner is the top-level replication unit.

### Pressure levels

```text
MemoryHigh = 160 / 162 MiB
MemoryMax  = 320 MiB
```

### Region and burst sizes

```text
region A = 32 MiB
region B = 32 MiB
burst    = 96 MiB
```

## Family S — Separate VMAs

Two independent 32 MiB anonymous private mappings.

Factors:

```text
MemoryHigh:
160 / 162

creation order:
A→B / B→A

initial fault/touch order:
A→B / B→A
```

Cells per block:

```text
2 × 2 × 2 = 8
```

Record:

- base virtual address of A;
- base virtual address of B;
- lower-address identity;
- first/second-created identity;
- first/second-faulted identity;
- A/B residency after burst;
- cgroup memory/reclaim/swap state.

## Family H — Shared VMA halves

Create one 64 MiB anonymous private mapping.

Logical physical regions:

```text
lower = first 32 MiB of the VMA
upper = second 32 MiB of the VMA
```

Factors:

```text
MemoryHigh:
160 / 162

initial fault/touch order:
lower→upper / upper→lower
```

Cells per block:

```text
2 × 2 = 4
```

There is no arbitrary A/B label factor.

This family removes separate-VMA creation order while preserving a direct lower-versus-upper virtual-address comparison.

## Total evidence budget

```text
Family S:  8 trials / block
Family H:  4 trials / block
          ----------------
          12 trials / block

16 blocks × 12 = 192 total trials
```

## Primary mechanism contrasts

For each runner block calculate these four contrasts.

### S1 — Separate-VMA creation-order effect

```text
resident fraction(second-created)
-
resident fraction(first-created)
```

Average across both pressure levels and both fault orders.

### S2 — Separate-VMA fault-order effect

```text
resident fraction(second-faulted)
-
resident fraction(first-faulted)
```

Average across both pressure levels and both creation orders.

### H1 — Shared-VMA address-position effect

```text
resident fraction(upper)
-
resident fraction(lower)
```

Average across both pressure levels and both fault orders.

### H2 — Shared-VMA fault-order effect

```text
resident fraction(second-faulted)
-
resident fraction(first-faulted)
```

Average across both pressure levels.

## Inference

For each contrast independently:

- exact two-sided sign-flip over all (2^{16}=65,536) runner-block sign assignments;
- 20,000-resample cluster bootstrap over runner blocks;
- raw runner-block contrast distribution;
- level-specific descriptive contrasts.

No weighted grand score is permitted.

## Required confounding report

Family S must report the observed relationship between:

```text
creation order
and
numeric virtual-address order
```

If these are perfectly collinear in the hosted environment, CHAR-002 must say so.

Family H exists specifically to provide an address-position test without separate-VMA creation order.

## Falsification logic

A **creation-order** explanation is weakened if S1 is near zero or inconsistent while another factor is stable.

A **fault-order** explanation is weakened if both S2 and H2 are near zero or inconsistent.

A **virtual-address-position** explanation is weakened if H1 is near zero or inconsistent.

If none of these explain the asymmetry, the next candidate class is another stable per-mapping/kernel state.

## Measurements

Each trial records:

- family;
- MemoryHigh;
- mapping creation order where applicable;
- fault/touch order;
- numeric base virtual addresses;
- page size;
- post-burst region residency fractions;
- memory.current;
- memory.swap.current;
- memory.stat;
- memory.events;
- content-integrity checks;
- OOM checks.

## No intervention

CHAR-002 uses no:

- MADV_PAGEOUT;
- MADV_COLD;
- proactive reclaim;
- mlock;
- semantic memory hint;
- coordinator;
- kernel modification.

## Authority boundary

A CHAR-002 factor association is evidence about this bounded hosted memcg workload.

It is not yet a general Linux reclaim-policy claim and does not authorize semantic Value-of-Information calculation unless the relevant confound is explained or neutralized.
