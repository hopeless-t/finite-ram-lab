# FR-GFX-003 — Observation Signal Ablation

Status: **SYNTHETIC SIGNAL ABLATION**

Parent: **FR-GFX-002**

## Question

If the full observation plane is informative, do we actually need every signal
all the time?

On a low-end system, observation has cost.

A research-grade controller should therefore search for the smallest signal set
that preserves enough identifiability.

## Signal families

The frozen panel compares:

- FRAME: frametime only;
- FRAME_MEM: frametime + MemAvailable + memory PSI;
- FRAME_GPU: frametime + GPU busy;
- FRAME_CPU: frametime + CPU busy / compiler proxy;
- FRAME_GPU_MEM: frametime + GPU busy + memory evidence;
- FULL: all of the above.

The acquisition-cost numbers in this lane are **abstract units**.

They are not measured collector CPU time.

Live overhead remains a future qualification requirement.

## Frozen result

| signals | abstract cost | action accuracy | GPU recall | false GPU downscale |
|---|---:|---:|---:|---:|
| FRAME | 1.0 | 71.20% | 92.85% | 32.52% |
| FRAME_MEM | 1.2 | 88.39% | 92.85% | 10.36% |
| FRAME_GPU | 1.8 | 69.70% | 86.15% | 2.34% |
| FRAME_CPU | 1.2 | 79.24% | 92.85% | 22.16% |
| FRAME_GPU_MEM | 2.0 | 86.88% | 86.15% | **0%** |
| FULL | 2.2 | **94.92%** | 86.15% | **0%** |

## Resource gates

With:

- action accuracy >= 85%;
- false GPU-downscale <= 1%;

the cheapest frozen set is:

`FRAME_GPU_MEM`.

If the accuracy floor is raised to 90%, the cheapest surviving set becomes:

`FULL`.

So the correct signal set depends on the reliability requirement.

## Interpretation

Memory evidence is extremely valuable because UMA pressure can look like a slow
GPU frame.

GPU-busy evidence prevents memory / CPU stalls from being misread as GPU
compute saturation.

CPU / compiler evidence matters when the controller needs to distinguish
CPU/driver stalls rather than merely avoid harmful GPU downscaling.

This yields a two-stage observation strategy candidate:

1. cheap base plane;
2. escalate to the full plane only when diagnosis remains ambiguous.

That is the same bounded-expense architecture appearing elsewhere in Finite RAM
Lab.

## Next

FR-GFX-004 should model / measure the **observer itself**:

- per-source CPU time;
- resident memory;
- output bytes;
- sampling cadence;
- missed transient events;
- perturbation of frame-time p95/p99.

For a ~10 FPS machine, instrumentation overhead is not a rounding error.

## Claim ceiling

**SYNTHETIC_SIGNAL_ABLATION_ONLY**
