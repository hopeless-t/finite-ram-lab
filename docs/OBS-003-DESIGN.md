# OBS-003 Design Council — Natural Residency Misalignment Map

> **Status:** DESIGN STUDY / MONTE CARLO LAUNCHED

## Research question

Before selecting another control mechanism, quantify how often the unmodified NO_HINT workload naturally loses residency from the semantic region that is known to be needed next.

The bounded question is:

> Across the 160–168 MiB transition region, what is the probability that the future-needed HOT region is not fully resident immediately before reuse?

This is an observation study.

It does not test a hint.

## Why this follows VAL-003

The evidence now separates two facts:

1. **EXP-001:** residency identity can causally change next-use latency by hundreds of times when identity is experimentally swapped;
2. **EXP-002 / VAL-003:** the tested CORRECT_PAGEOUT operation did not establish central-tendency or >=500 ms tail benefit over NO_HINT.

The missing quantity is therefore the **natural opportunity rate**:

```text
How often does the baseline reach reuse
with the future-needed region already misaligned?
```

Without that quantity, another mechanism could be aimed at a problem that is real but too infrequent to provide useful headroom.

## Primary observable

For each NO_HINT trial:

```text
misaligned = HOT resident fraction < 1.0
```

measured by `mincore(2)` immediately before HOT reuse.

The measurement is page-residency observation, not a judgment that every missing page is harmful.

## Proposed map

Candidate MemoryHigh levels:

```text
160, 162, 164, 166, 168 MiB
```

The workload otherwise remains the same as the EXP-002 / VAL-003 NO_HINT arm:

- two 32 MiB semantic regions;
- 96 MiB burst;
- HOT reused next;
- no application hint;
- MemoryMax 320 MiB.

## Pseudo-Council

### Scientific-integrity reviewer

Do not define “headroom” as the performance gain of an untested mechanism.

First measure the baseline frequency of a directly observable residency mismatch.

### Kernel / VM reviewer

Keep the actuator unchanged across the map.

`MemoryHigh` is a memcg pressure threshold, not physical-RAM capacity.

### Statistics reviewer

Runner identity is the top-level replication unit.

Prefer more independent runner blocks over excessive repeats inside one runner when trial budgets are similar.

### Performance reviewer

Record latency and fault/refault/swap counters, but keep residency-misalignment prevalence as the primary mapping quantity.

### Falsification reviewer

The study is informative if misalignment is rare, broad, sharply localized, or runner-dependent.

A near-zero opportunity rate would be a valid result and would argue against spending effort on residency-selection mechanisms for this workload.

### Monte Carlo reviewer

Because prior observations suggest substantial runner heterogeneity, compare block/repeat allocations under several plausible transition shapes before spending physical runner trials.

## Candidate designs

All candidates use five MemoryHigh levels.

```text
D1: 12 blocks x 4 repeats/level = 240 trials
D2: 16 blocks x 4 repeats/level = 320 trials
D3: 24 blocks x 3 repeats/level = 360 trials
D4: 32 blocks x 2 repeats/level = 320 trials
```

## Design Monte Carlo

The simulation uses a logistic misalignment curve with runner-level random intercepts.

Stress scenarios vary:

- transition location;
- transition width;
- runner heterogeneity.

The simulation evaluates:

- absolute error of estimated 164 MiB misalignment prevalence;
- full five-level curve error;
- approximate runner-cluster interval width and coverage;
- probability of observing enough 164 MiB misalignment events and affected runner blocks for useful conditional diagnostics.

No weighted overall score is used.

The final design should be selected from the Pareto-efficient set after the simulation is observed.

## Authority boundary

The design Monte Carlo allocates observation effort.

It does not establish real misalignment prevalence or a performance benefit from any intervention.
