# Bounce Handoff

> **Bounce ID:** B036  
> **Status:** COMPLETE

## Objective

Read OBS-003 using the frozen prevalence analysis, record the natural-misalignment finding, and decide whether a formal decision-headroom / Value-of-Information line is warranted.

## Evidence

Workflow:

- run: `36242552339`;
- conclusion: SUCCESS;
- 32 independent runner blocks;
- 320 NO_HINT trials;
- all execution checks passed;
- no OOM;
- content integrity preserved.

Primary natural HOT-misalignment rates:

```text
160 MiB  38/64 = 0.5938  [0.5313, 0.6719]
162 MiB  37/64 = 0.5781  [0.5156, 0.6406]
164 MiB   7/64 = 0.1094  [0.0313, 0.2031]
166 MiB   4/64 = 0.0625  [0.0000, 0.1563]
168 MiB   1/64 = 0.0156  [0.0000, 0.0469]
```

Misaligned HOT reuse was descriptively much slower than fully resident HOT reuse at every sampled level.

All >=500 ms OBS-003 events occurred in misaligned trials.

## Frozen finding

Natural residency-selection headroom is not uniformly distributed.

It is frequent at the stronger-pressure 160–162 MiB conditions and becomes much rarer by 164–168 MiB.

This helps explain why the tested 164 MiB semantic PAGEOUT mechanism could have little aggregate benefit even though wrong residency identity is very costly.

## Exploratory signal

At 160–162 MiB, the missing region was strongly associated with the fixed A-before-B touch/order identity.

Because future HOT identity was balanced independently, this raises a direct information-gap hypothesis:

> past recency/order may guide natural reclaim, while the application knows future semantic need that is not encoded in that cue.

This was not the pre-registered OBS-003 primary analysis.

## Frozen decision

A Value-of-Information / decision-headroom line is warranted.

Do not compute a grand cross-study scalar yet.

First confirm the apparent past-recency versus future-semantics separation in one balanced factorial experiment.

## Repository updates

- `findings/OBS-003-initial.md`
- README status updated through OBS-003.

## Next recommended bounce

> Design HYP-002 as a balanced factorial study with semantic HOT identity A/B, recent/last-touched identity A/B, and MemoryHigh 160/162 MiB. Use direct mincore residency observation before reuse. Run design Monte Carlo if runner/repeat allocation is non-obvious.

No new memory-management intervention is authorized.

## Authority boundary

OBS-003 does not prove that recency is globally wrong or that Linux lacks useful future-demand inference.

It identifies a testable information-gap candidate in the declared workload.
