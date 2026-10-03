# FR-GFX-002 — Read-only Low-end Game Observation Plane

Status: **READ-ONLY SCHEMA + SYNTHETIC IDENTIFIABILITY PANEL**

Parent: **FR-GFX-001**

## Why observation comes before control

A 100 ms frame does not tell us why the frame took 100 ms.

At least four different conditions can collapse into the same visible symptom:

- GPU compute saturation;
- shared-memory / UMA pressure;
- CPU / driver bottleneck;
- shader compilation / pipeline activity.

Applying the same treatment to every low-FPS frame is therefore unsafe as a
research method.

## Read-only contract

FR-GFX-002 does not:

- write sysfs;
- change GPU clocks;
- change game settings;
- modify DXVK configuration;
- inject into the game process;
- kill processes.

It defines a normalized observation stream only.

## Source grounding

### Frame timing

MangoHud can monitor FPS / frametimes and supports logging with a configurable
log interval.

Pinned source:

`flightlessmango/MangoHud @ 8bd15ed92667a31427af2c219bc8d2847702f274`

### Intel GPU activity

`intel_gpu_top` exposes Intel GPU PMU information and can emit JSON or CSV.
Its documentation notes that metrics vary by platform and non-root access is
controlled by `perf_event_paranoid`.

The collector must therefore represent unsupported counters as missing data,
not as zero.

### Process memory

`/proc/<pid>/smaps_rollup` provides pre-summed process memory fields such as
RSS, PSS, and Swap.

### System memory

`/proc/meminfo` provides `MemAvailable`, an estimate of memory available for
new applications without swapping.

### Pressure

Linux PSI exports CPU, memory, and IO stall information through
`/proc/pressure/*`.

For memory, both `some` and `full` pressure are relevant.

### Backend identity

DXVK exposes HUD / logging metadata including API, GPU / driver identity,
frametimes, memory and compiler activity.

Pinned source:

`doitsujin/dxvk @ d30be2baea02a67b9502bffda0ec8b0d915bb3d2`

For Proton experiments, backend identity is part of the experimental state.

A D3D11 trace and a D3D12/VKD3D trace must not silently enter the same arm.

## Normalized record

A canonical sample carries:

- timestamp;
- FPS / frametime;
- process RSS / PSS / swap;
- MemAvailable / swap free;
- memory PSI;
- Intel render busy / frequency / bandwidth when available;
- translation backend / API / Proton identity.

The schema intentionally permits missing GPU counters.

## Synthetic identifiability panel

16,384 deterministic samples are generated across four latent states:

- NORMAL;
- GPU_BOUND;
- UMA_PRESSURE;
- CPU_DRIVER.

The purpose is not to create a realistic hardware simulator.

It asks a narrower question:

> Is frametime alone sufficient to choose the right class of intervention?

### FPS-only arm

The FPS-only arm can only choose:

- OBSERVE;
- DOWNSCALE_RENDER.

Its frametime threshold is frozen so that GPU-bound recall exactly matches the
multi-signal arm.

Frozen result:

- GPU-bound recall: 86.1534%;
- GPU-downscale false-positive rate: **30.6028%**;
- overall action-class accuracy: **69.6960%**.

Most false GPU downscales are actually UMA-pressure or CPU/driver samples.

### Multi-signal arm

The multi-signal arm uses:

- frametime;
- GPU busy;
- MemAvailable;
- memory PSI;
- CPU busy / compiler activity proxy.

At the same frozen GPU-bound recall:

- GPU-downscale false-positive rate: **0%**;
- overall action-class accuracy: **94.9219%**.

This is a synthetic identifiability result, not a real-hardware classifier
claim.

## Main invariant

[
oxed{
	ext{low FPS} 
eq 	ext{GPU-bound}
}
]

Therefore a low-end graphics governor should not be driven by FPS alone.

The observation plane must distinguish at least:

[
	ext{frame symptom}
	imes
	ext{GPU evidence}
	imes
	ext{memory evidence}
	imes
	ext{pressure evidence}
	imes
	ext{backend identity}.
]

## Instrumentation overhead

The observer itself consumes resources.

This is especially important on a machine already near 10 FPS.

FR-GFX-003 must therefore measure or model:

- sampling interval;
- collector CPU time;
- collector RSS;
- bytes written per second;
- GPU PMU sampling overhead;
- logging overhead on frametime tails.

A metric is not free merely because it is read-only.

## Next

### FR-GFX-003 — Observer overhead and signal ablation

Compare:

- frametime only;
- frametime + system memory;
- frametime + GPU;
- frametime + memory PSI;
- full observation plane.

Target:

find the cheapest signal set that retains bottleneck identifiability.

### FR-GFX-004 — Offline trace replay

Replay captured low-end traces through the Happy-iGPU controller without
changing the running game.

Only after replay qualification should live setting changes be considered.

## Claim ceiling

**READ_ONLY_SCHEMA_AND_SYNTHETIC_IDENTIFIABILITY_ONLY**
