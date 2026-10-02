# News Intake 2026-10-02 — Magnitude and Linux Steal Governor

Status: RESEARCH INTAKE / NO LOCAL HARDWARE BENCHMARK

Primary sources:
- Magnitude: https://github.com/magnitudedev/magnitude
- Magnitude engine rewrite discussion: https://github.com/magnitudedev/magnitude/discussions/100
- Magnitude launch benchmark / author post: https://news.ycombinator.com/item?id=49911995
- Linux steal governor v14:
  https://lkml.iu.edu/2609.3/08049.html

## Why these belong in finite-ram-lab

Magnitude and steal_governor attack different resources, but share one control pattern:

    measure pressure
        -> shrink active/resident working set
        -> retain semantic capability
        -> re-expand when pressure falls

Magnitude applies this to model/session memory and prefix reuse. Linux steal_governor
applies it to the set of preferred vCPUs when host contention makes excess concurrency
counterproductive.

The portable atom is not "less resources is always faster". It is:

> Above some pressure, reducing the active working set can improve effective throughput
> by reducing interference, preemption, cache/TLB disruption, or duplicated residency.

## Source observations

Magnitude currently advertises:
- per-device kernel tuning,
- dynamic memory that is freed when agents stop,
- 27% less per-agent memory on CUDA and 28% less on Metal in the authors' launch benchmark,
- shared prefix caches for concurrent sessions,
- future expert streaming in the engine rewrite design.

These are upstream claims and require local reproduction before being treated as
finite-ram-lab evidence.

Linux steal_governor v14 documents:
- default sampling interval: 1000 ms,
- low threshold: 2% steal,
- high threshold: 5% steal,
- high steal -> reduce preferred CPUs by one core,
- low steal -> increase preferred CPUs by one core,
- at least one preferred core remains,
- pure independent CPU workloads may not benefit and can regress from governor overhead.

The 2%-5% gap is a hysteresis deadband intended to avoid oscillation.

## Atomic model — pressure-aware active set

Let n_t be the active/preferred working-set size and p_t measured pressure.

A generic step controller:

    if p_t > H:
        n_{t+1} = max(n_min, n_t - 1)
    elif p_t <= L:
        n_{t+1} = min(n_max, n_t + 1)
    else:
        n_{t+1} = n_t

with L < H.

This describes the control shape, not a universal policy.

## Hypothesis FR-GOV-H1 — Hysteresis reduces thrashing

For a noisy pressure trace near a single threshold, a deadband controller should perform
fewer active-set transitions than a controller with L=H, while accepting some response
delay.

Falsifier:
- matched traces show no transition reduction,
- or reduced transitions cost more task utility than they save.

## Hypothesis FR-GOV-H2 — There is an interval knee

Sampling too frequently increases controller overhead/noise sensitivity.
Sampling too slowly misses useful pressure transitions.

For interval T:

    NetValue(T)
      = throughput_gain(T)
        - controller_overhead(T)
        - delayed_response_loss(T)

A finite optimum is expected only for workloads where pressure changes on a compatible
timescale.

## Hypothesis FR-MAG-H1 — shared-prefix residency has a concurrency dividend

For N sessions sharing prefix memory P and each owning suffix S:

    naive_residency = N(P+S)
    shared_residency = P + NS

so ideal logical savings are:

    1 - (P+NS)/(N(P+S))

This ignores fragmentation, metadata, allocator rounding, KV layout, and backend-specific
duplication. It is a bound/model, not an observed Magnitude result.

## Hypothesis FR-MAG-H2 — memory savings can become capacity gains

If per-session memory falls from M to alpha*M and all else is memory-bound, ideal
concurrency capacity scales by:

    1/alpha

For alpha=0.73, the ideal upper-bound multiplier is ~1.37x.

Real throughput can be lower because compute, bandwidth, KV growth, and scheduling become
new bottlenecks.

## Proposed experiments

### FR-GOV-001 — deterministic hysteresis trace

Compare:
- Linux-shaped L=2%, H=5% step controller,
- single-threshold controller,
- static active set.

Sweep:
- pressure noise amplitude,
- pressure trend speed,
- sampling interval.

Measure:
- transition count,
- time above high pressure,
- time below target capacity,
- controller actions.

### FR-MAG-001 — Magnitude vs reference runtime

Only after local execution is available through the authorized MVCA -> LDC path.

Freeze:
- model bytes / quantization,
- prompt corpus,
- context lengths,
- machine power/performance mode.

Compare:
- Magnitude,
- llama.cpp/reference runtime where compatible.

Sweep:
- 1/2/4/... concurrent sessions,
- cold/warm,
- shared-prefix fraction,
- context length,
- imposed memory pressure.

Measure:
- TTFT,
- decode tok/s,
- RSS/cgroup peak,
- bytes reclaimed after idle,
- prefix reuse,
- correctness.

No local machine command is authorized or executed by this intake.

## Relationship to B494-B500 Governor

The existing finite-ram Governor work already treats pressure response as an evidence-
bound local policy. Linux steal_governor adds a simple, externally-developed hysteresis
reference. It should be used as a comparison arm, not copied as a universal threshold.

## Claim ceiling

    PRESSURE_GOVERNOR_AND_SHARED_PREFIX_HYPOTHESES_DEFINED

No Magnitude performance claim is locally reproduced here.
