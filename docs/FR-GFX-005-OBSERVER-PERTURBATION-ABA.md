# FR-GFX-005 — Observer Perturbation A-B-A Protocol

Status: **SYNTHETIC OBSERVER-PERTURBATION PROTOCOL**

Parent: **FR-GFX-004**

## Why this gate exists

A read-only observer still consumes:

- CPU time;
- resident memory;
- kernel / PMU work;
- file-system writes;
- scheduler time.

On a machine already near 100 ms per frame, measurement overhead is part of the
workload.

So:

[
oxed{
	ext{read-only} 
eq 	ext{zero perturbation}
}
]

## A-B-A model

Use three matched segments:

1. A1: observer off;
2. B: observer on;
3. A2: observer off.

Model a metric as:

[
y(t)=mu+eta t+delta I_B+epsilon.
]

Here:

- beta is linear thermal / scene / system drift;
- delta is observer perturbation.

The naive estimator:

[
B-A1
]

contains both drift and observer effect.

Use:

[
hat{delta}
=
B-rac{A1+A2}{2}.
]

Under the linear model, beta cancels exactly in expectation.

## Frozen synthetic fixture

- 8,192 deterministic episodes;
- 120 frames per A/B/A segment;
- nominal baseline: 100 ms;
- random linear drift;
- ordinary frame noise;
- 5% baseline tail events.

Three observers are injected synthetically:

- NULL: zero overhead;
- LIGHT: 0.5 ms constant + rare 2 ms tail overhead;
- HEAVY: 2 ms constant + rare 12 ms tail overhead.

The equivalence margin is **1 ms** for this fixture only.

That is 1% of the synthetic 100 ms baseline.

It is not a universal live threshold.

## Why one run is not enough

For the NULL observer, one A-B comparison falsely exceeds the 1 ms margin in:

**53.89%** of episodes.

One drift-corrected A-B-A block reduces this to:

**23.54%**.

Better, but still too noisy.

After averaging eight matched A-B-A blocks, the frozen NULL panel has:

**0%** false >1 ms perturbation calls.

This does not prove eight blocks are sufficient on real hardware.

It proves the number of matched blocks is itself a statistical control
variable.

## Frozen observer classification

Using eight matched A-B-A blocks:

- NULL observer: 100% of grouped decisions stay inside ±1 ms;
- LIGHT observer: 93.26% stay inside ±1 ms;
- HEAVY observer: 0% stay inside ±1 ms.

The LIGHT expected mean overhead is 0.56 ms.

The estimated frozen mean is about 0.545 ms.

The HEAVY expected mean overhead is 2.36 ms.

The estimated frozen mean is about 2.348 ms.

## Live protocol

Before a live run, freeze:

- game build;
- map / scene;
- camera or repeatable path;
- resolution;
- graphics settings;
- D3D / Vulkan translation backend;
- Proton version;
- power state;
- background workload policy.

Then repeat:

```text
A1 observer OFF
B  observer ON
A2 observer OFF
```

multiple times.

Compute drift-corrected effects for:

- median frametime;
- p95 / p99 frametime;
- game RSS / PSS;
- MemAvailable;
- memory PSI;
- observer CPU;
- observer RSS;
- bytes written per second.

## Pre-registration rule

The perturbation margin must be chosen **before looking at B**.

Otherwise the observer can always be declared "cheap enough" after seeing the
result.

For a ~10 FPS machine, 1 ms is approximately 1% of a 100 ms frame, but
FR-GFX-005 does not prescribe 1% as the universal live budget.

## Qualification rule

No live control experiment may use an observer until:

1. the observer's own perturbation budget is frozen;
2. repeated A-B-A runs are complete;
3. median and tail frametime gates pass;
4. CPU/RSS/logging gates pass;
5. backend and scene identity are verified.

## Next

FR-GFX-006 should turn this protocol into a runnable **read-only collector
harness** that emits one normalized JSONL stream and a self-overhead receipt.

No graphics setting writes should be added yet.

## Claim ceiling

**SYNTHETIC_OBSERVER_PERTURBATION_PROTOCOL_ONLY**
