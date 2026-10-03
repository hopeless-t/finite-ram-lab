# FR-SOOM-002L — Cross-Tier Pressure Qualification Receipt

Status: **PASS / SYNTHETIC CROSS-TIER PRESSURE COUPLING VALIDATED**

## Frozen qualification

- workflow run: 37094776073
- job: 111122354011
- execution head: 66fd85da65c40cafdbd50221b2f269e80ab5985c
- targeted tests: 6/6 PASS
- artifact ID: 11263950496
- artifact ZIP SHA256: 5e0e654193d6450c87b0db3e563ef3706ff40ec3da8ef715ebbfea93c6668068
- spec SHA256: a98e2737851222e77fb4e500d997c455b0679f7d262d20d6c6c7289ce5b7611f
- result SHA256: 09a9cfe0c41b83febc10f1d6c719d734a3154efd8702904889a942fefff9aba9

## Source role

Architectural inspiration only:

- Niko1221/Strata
- commit: b48aad2a9d96eceb749b4f06ffd6607f9b00be7f

The Strata observation motivates cross-tier coupling. No upstream reserve value
is transferred into this fixture.

## Frozen result

| policy | current-task losses | survival rate | Wilson95 lower | mean semantic loss | p99.9 semantic loss |
|---|---:|---:|---:|---:|---:|
| TIER_LOCAL_GREEDY | 106 | 0.993530 | 0.992182 | 1.8115 | 280 |
| REACTIVE_SHRINK | 17 | 0.998962 | 0.998339 | 4.2905 | 284 |
| CROSS_TIER_HEADROOM | 0 | 1.000000 | 0.999766 | 12.0000 | 12 |

Reliability requires both the point survival rate and Wilson95 lower bound to
be at least 0.999.

Only CROSS_TIER_HEADROOM qualifies.

## Spill surface

TIER_LOCAL_GREEDY:

- initial model cache: 10000 MiB
- synthetic accelerator headroom: 384 MiB
- mean initial synthetic GTT spill: 1197.72 MiB
- p95 initial spill: 3052.48 MiB
- p99 initial spill: 3896.33 MiB

REACTIVE_SHRINK begins with the same exposure but shrinks the cache by 4000 MiB
after spill is observed.

Its final mean spill falls below 1 MiB, yet 17 episodes have already crossed
the frozen foreground-survival boundary before the reaction is considered
timely.

CROSS_TIER_HEADROOM:

- initial model cache: 5200 MiB
- synthetic accelerator headroom: 5184 MiB
- synthetic spill: 0 in the frozen panel

## Primary finding

Expected semantic cost alone prefers the unsafe local-greedy policy:

`1.8115 < 4.2905 < 12.0`.

But the local-greedy and reactive policies fail the task-survival reliability
constraint.

Therefore:

`tier-local relief != global semantic relief`.

A coupled memory controller must treat headroom in adjacent tiers as a
constraint rather than optimizing every tier independently.

## Reproducibility correction

Before the 002L qualification, a provisional branch used human-readable random
draw labels that did not match the pilot draw-domain identity.

No probability, threshold, capacity, semantic cost, or acceptance criterion was
relaxed.

The final spec explicitly freezes:

- seed;
- draw-domain IDs;
- episode index;
- distribution parameters;
- policy parameters.

## Numbering correction

FR-SOOM-002K was already assigned to the demand-folding governor in PR #71.

The provisional cross-tier PR was therefore renumbered to FR-SOOM-002L before
qualification was finalized.

## Claim ceiling

**SYNTHETIC_CROSS_TIER_PRESSURE_COUPLING_ONLY**

No live VRAM, GTT, RAM, swap, process, or cgroup control is performed.
