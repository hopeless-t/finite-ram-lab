# FR-GFX-001 — Happy iGPU / UMA Governor

Status: **SYNTHETIC UMA / iGPU CONTROL EXPERIMENT**

Parent: **KSLA-003**

## Motivation

An integrated GPU does not have the same memory economics as a large discrete
GPU.

CPU memory demand, graphics resources, render targets, texture residency, and
OS/background pressure all compete inside a shared finite physical-memory
system.

Linux DRM memory-management documentation explicitly covers both UMA devices
and devices with dedicated VRAM.

Vulkan sparse residency also demonstrates that graphics resources need not
always be treated as all-or-nothing residency when device support exists.

This makes integrated graphics a natural Finite RAM Lab target.

## Research question

Can a cheap controller keep frame-time tails and shared-memory headroom under
control without exhaustively searching every graphics configuration each frame?

The control dimensions in FR-GFX-001 are deliberately small:

- render scale;
- texture-residency tier.

Future lanes can add:

- shadows;
- post-processing;
- geometry / mesh LOD;
- sparse texture pages / mip residency;
- dynamic resolution;
- upscaler choice;
- frame-generation policy;
- CPU background load;
- shader / pipeline cache pressure.

## Policies

### NATIVE_STATIC

Always use full scale and full texture residency.

### UPSCALE_STATIC

Always use a low render scale and reduced texture residency.

### EXPERT_FULL_SCAN

Evaluate every candidate configuration every frame.

This is the expensive expert oracle.

### LOCAL_ONLY

Normally hold the current configuration.

When risk is detected, examine only adjacent settings.

### BOUNDED_PROBE_4

Run the same local controller.

Only when the best local adjustment is still deadline/headroom risky, inject
four ignorant global configuration probes.

The probes know nothing about the local search path.

The shared objective / validator decides whether one survives.

This is the graphics analogue of bounded idiocy.

## Frozen synthetic trace

The 5,000-frame trace contains:

- ordinary scene-load variation;
- rare GPU-scene spikes;
- OS shared-memory variation;
- memory spikes;
- shared-bandwidth contention.

The synthetic memory budget is 8192 MiB.

The target is a 33.3 ms frame budget.

These are **not** measurements of any real integrated GPU.

## Frozen results

| policy | deadline misses | memory violations | control evaluations |
|---|---:|---:|---:|
| NATIVE_STATIC | 706 | 185 | 5,000 |
| UPSCALE_STATIC | 224 | 0 | 5,000 |
| EXPERT_FULL_SCAN | 41 | 0 | 60,000 |
| LOCAL_ONLY | 69 | 0 | 6,970 |
| **BOUNDED_PROBE_4** | **53** | **0** | **7,379** |

The bounded-probe controller therefore reduces deadline misses by about 23.2%
relative to LOCAL_ONLY while increasing control evaluation work by only about
5.9%.

Relative to EXPERT_FULL_SCAN, it uses about 87.7% fewer control evaluations.

The cost is slightly lower mean visual-quality proxy than LOCAL_ONLY in this
fixture.

That negative trade is preserved deliberately.

## Main interpretation

The goal is not to prove that random global probing beats full expert search.

It does not.

The full expert oracle remains stronger on quality and frame-time tail.

The narrower result is:

> local control can be cheap, but it has blind spots; a small number of
> externally verified nonlocal probes can reduce rare tail failures without
> paying the cost of exhaustive global search.

That is exactly the bounded-idiocy pattern discovered in KSLA.

## Why this belongs in Finite RAM Lab

The controller must price these jointly:

[
J =
lambda_t T_{frame}
+
lambda_q L_{quality}
+
lambda_m P_{memory}
+
lambda_c C_{control}.
]

On UMA hardware, lowering render scale or texture residency can simultaneously:

- reduce GPU work;
- reduce shared-memory demand;
- increase CPU/OS headroom;
- alter bandwidth contention.

So:

[
oxed{
graphics quality

eq
independent of memory residency
}
]

The correct target is not maximum quality.

It is maximum acceptable visual quality under a frame-time reliability floor
and shared-memory headroom constraint.

## Real-game validation path

A live game should not reuse this synthetic 33.3 ms target blindly.

A low-end machine that currently runs a title around 10 FPS should first freeze
its actual baseline:

- median frame time;
- p95 / p99 frame time;
- render resolution;
- graphics backend;
- process RSS;
- system available RAM / swap;
- GPU busy / frequency / memory-bandwidth proxy;
- map / scene identity.

Then compare controlled interventions one at a time.

For MECCHA CHAMELEON on Linux/Proton, graphics-backend identity must also be
frozen because community evidence shows a D3D11 launch path can behave very
differently from the default path on Intel integrated graphics.

## Next

### FR-GFX-002 — Live low-end trace adapter

Define an observation schema for MangoHud / present timing / system memory /
GPU counters without changing the game.

### FR-GFX-003 — Controller replay

Replay a captured trace offline and choose:

- static quality;
- local governor;
- bounded nonlocal probes;
- exhaustive oracle.

### FR-GFX-004 — Live opt-in governor

Only after replay validation, test reversible live settings.

## Claim ceiling

**SYNTHETIC_UMA_IGPU_GOVERNOR_ONLY**
