# OBS-003 — Idle accounting drop discriminator v1

> **Status:** FROZEN-CANDIDATE DESIGN / NOT YET LAUNCHED
> **Purpose:** distinguish a pre-existing accounting/stock component from touch-triggered data-page behavior without privileged kernel tracing.

## Core question

After reproducing the controlled-spawn startup and CPU migration sequence, does an observed +17 starting mode lose about 17 pages while the worker performs no measured page touches?

## Why this is informative

MATH-015 found:
- a reproducible +17 pre_current mode
- +17 mode strongly predicts later -17
- -17 occurs near global measured touch 13-14 even when the scientific phase changes
- subtracting 17 returns almost all specimens to clean pre_current modes

If -17 can occur while the worker is idle, it cannot be caused by a special calibration/bait page touch.

## Worker

Reuse `experiments/memcg005gc_spawn_worker.c` unchanged.

The worker:
- maps the same anonymous region
- preconditions one PTE-table guard on preparation CPU P
- reaches READY
- is migrated to stock CPU S
- receives no GO/touch command during the idle observation.

## Measurements

Immediately before migration, immediately after migration, and at fixed idle offsets after migration:

`0, 1, 2, 4, 8, 12, 16, 20, 30, 50, 100 ms`

record:
- monotonic timestamp
- memory.current
- `/proc/<pid>/status`: VmRSS, RssAnon, RssFile, RssShmem, VmPTE
- full cgroup memory.stat at start, first detected current drop, and final sample
- observed worker CPU

No anonymous data page in the safe span is touched after READY.

## Primary classifications

### IDLE_CURRENT_DROP_NO_RSS_DROP

memory.current falls by >= 2 pages while total RSS and RssAnon/RssFile/RssShmem stay within frozen tolerance.

Interpretation: supports disappearance of precharged/accounting state rather than worker resident pages.

### IDLE_CURRENT_DROP_WITH_RSS_DROP

memory.current fall is accompanied by matching process RSS/category loss.

Interpretation: supports ordinary resident-page reclaim/uncharge.

### IDLE_NO_DROP

No meaningful memory.current decrement by 100 ms.

Interpretation: -17 may require measured-touch activity, a longer delay, or external activity not present in that identity.

### OTHER

Any morphology outside frozen rules.

## +17 hypothesis

Freeze the +17 modal region from MATH-015:
- 114..117 pages
- 179..180 pages

Primary comparison:

`P(idle -17-like drop | +17 mode)` vs `P(idle -17-like drop | other start modes)`

Do not redefine the modal region after seeing OBS-003.

## Pilot scale

Preferred bounded hosted pilot:
- 4 independent blocks
- 12 identities per block
- 48 total identities
- standard ubuntu-26.04 runner
- no replacement identities
- no dynamic scale expansion

Expected +17-mode count from the previous 72-trial cohort is roughly 17/48, enough for a directional mechanism pilot but not certification.

## Observer effect

This design removes the normal touch loop and therefore does not estimate controlled-spawn reliability.

It is an observation-mechanism experiment only.

## Decision

If +17 mode repeatedly produces idle -17-like drops with stable RSS, prioritize the stock/precharge hypothesis and design a direct CPU-stock biopsy.

If idle drops track RSS loss, prioritize ordinary folio/file reclaim.

If idle drops do not occur, next discriminate elapsed time from touch-induced external activity.

No b63 reliability scaling follows automatically.
