# FR-SOOM-002L — Cross-Tier Pressure Coupling

Status: **SYNTHETIC CROSS-TIER CONTROL QUALIFICATION**

Parent: **FR-SOOM-002J**

## Motivation

A current Strata upstream change provides a useful real-world motivation for a
new Semantic OOM question.

Source:

- repository: `Niko1221/Strata`
- commit: `b48aad2a9d96eceb749b4f06ffd6607f9b00be7f`

The upstream report describes an AMD Linux desktop condition where aggressive
expert-cache VRAM use left too little headroom. Later desktop VRAM demand could
push GPU memory into system RAM/GTT and contribute to whole-system memory
pressure severe enough to damage desktop components.

FR-SOOM-002L does **not** reproduce that event and does not transfer its
recommended reserve value.

It extracts only the architectural hypothesis:

`tier-local relief != global semantic relief`.

## Question

Can a policy that maximizes one memory tier become globally unsafe because its
overflow is charged to another tier that contains high-value foreground state?

The synthetic chain is:

```text
larger model cache in VRAM
       |
       v
less accelerator headroom
       |
       v
desktop VRAM demand
       |
       v
synthetic GTT/system-RAM spill
       |
       v
host RAM pressure
       |
       v
foreground/current-task loss
```

## Frozen policies

### TIER_LOCAL_GREEDY

Maximize model cache in the accelerator tier.

The policy pays no synthetic base semantic cost because it represents the best
model-local residency configuration.

It does not reserve global foreground headroom.

### CROSS_TIER_HEADROOM

Use a smaller model cache and preserve a large synthetic accelerator headroom
budget.

The fixture assigns a +12 semantic cost to represent model-local performance
opportunity lost by keeping less cache resident.

The value is synthetic.

### REACTIVE_SHRINK

Start from the greedy cache.

When synthetic GTT spill appears, shrink the model cache by 4000 MiB.

The reaction usually removes final spill, but a sufficiently deep initial host
RAM overage is modeled as too late to prevent current-task damage.

This tests:

`eventual relief != relief before the semantic deadline`.

## Frozen fixture

- episodes: 16,384
- synthetic VRAM: 16,384 MiB
- fixed model VRAM: 6,000 MiB
- synthetic host RAM: 32,768 MiB
- model host RAM: 19,000 MiB
- foreground host RAM: 4,500 MiB

Desktop VRAM demand is a deterministic synthetic mixture with an 8% high-demand
state.

Background host RAM also contains a 5% burst state.

These numbers exist only to create a reproducible cross-tier pressure surface.

They are not measurements of Strata, amdgpu, the user's PC, or Chrome.

## Reliability qualification

Current-task survival qualifies only when both:

- point survival rate >= 0.999;
- Wilson95 lower bound >= 0.999.

## Frozen result

| policy | current-task losses | survival | Wilson95 lower | mean semantic loss | p99.9 semantic loss |
|---|---:|---:|---:|---:|---:|
| TIER_LOCAL_GREEDY | 106 | 0.993530 | 0.992182 | 1.812 | 280 |
| REACTIVE_SHRINK | 17 | 0.998962 | 0.998339 | 4.291 | 284 |
| CROSS_TIER_HEADROOM | 0 | 1.000000 | 0.999766 | 12.000 | 12 |

Only CROSS_TIER_HEADROOM passes the frozen reliability contract.

## Spill result

TIER_LOCAL_GREEDY begins with only 384 MiB of synthetic accelerator headroom.

Its mean synthetic initial GTT spill is about 1198 MiB and p99 spill is about
3896 MiB.

REACTIVE_SHRINK begins with the same exposure but shrinks enough cache that its
final mean spill is below 1 MiB in the frozen panel.

Despite that eventual relief, 17 episodes have already crossed the synthetic
foreground-survival boundary before the reaction is considered timely.

CROSS_TIER_HEADROOM produces no synthetic spill in this fixture.

## Primary finding

Expected synthetic semantic loss alone selects the unsafe greedy policy:

`1.812 < 4.291 < 12.0`.

But the greedy and reactive policies fail the frozen current-task reliability
constraint.

Therefore:

`tier-local optimization requires a global semantic headroom constraint`.

The controller should optimize across coupled resources:

```text
maximize useful residency
subject to:
  current-task survival reliability
  global host-memory headroom
  accelerator headroom
  spill / migration deadline
  evidence completeness
```

## Relation to earlyoom

An emergency userspace OOM killer reacts after host memory pressure has already
become severe.

This experiment motivates an earlier control plane:

```text
cross-tier pressure forecast
   -> proactive low-value residency reduction
   -> preserve foreground headroom
   -> emergency victim selection only if needed
```

The aim is not to replace the kernel.

It is to prevent a locally rational cache/residency policy from manufacturing a
later global OOM crisis.

## Relation to FR-SOOM-002J

FR-SOOM-002J treats RAM / compressed RAM / SSD as representations chosen under a
deadline.

FR-SOOM-002L adds another rule:

> the receiving and source tiers cannot be modeled independently when overflow
> from one consumes semantic headroom in another.

A later physical planner should treat RAM, VRAM/GTT, zram/swap, and SSD as a
coupled resource graph rather than a linear ladder.

## Claim ceiling

**SYNTHETIC_CROSS_TIER_PRESSURE_COUPLING_ONLY**

No live resource setting is changed.

No Strata threshold is adopted.

## Next

A useful next lane is an offline **coupled-resource graph planner**.

Instead of hardcoding VRAM -> GTT -> RAM, represent migration edges explicitly:

```text
VRAM
  -> shared/GTT RAM
RAM
  -> zram
  -> swap
RAM / application state
  -> SSD semantic tier
```

Every edge should carry:

- capacity effect;
- latency distribution;
- bandwidth distribution;
- semantic cost;
- shared failure domain;
- write / endurance cost where applicable.

The solver can then ask whether a proposed relief action actually creates global
headroom or merely moves pressure to another constrained node.
