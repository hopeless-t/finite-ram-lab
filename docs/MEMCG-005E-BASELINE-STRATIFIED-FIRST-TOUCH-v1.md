# MEMCG-005E Baseline-Stratified First-Touch v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Question

Does the pre-touch `memory.current` level prospectively predict fresh-Q64 first-touch behavior, and is that association specific to the worker's startup CPU?

The threshold is frozen from MEMCG-005D before this experiment:

`LOW iff pre_current_pages <= 110`

`HIGH iff pre_current_pages > 110`

No threshold tuning is allowed after launch.

## CPU roles

Require >=3 allowed CPUs:

- C = controller
- P = startup CPU
- S = remote stock-test CPU

Controller pinned C.

Every worker starts and reaches shared READY on P.

## Shared-latch primitive

Reuse the MEMCG-005D worker protocol.

After READY:
- no FIFO/status I/O;
- control through prefaulted shared page only;
- one measured anonymous page remains untouched.

## Arms

### LOCAL_P

Controller:
1. reads pre-touch `memory.current`;
2. records LOW/HIGH stratum;
3. externally reasserts affinity to P;
4. confirms worker on P;
5. reads mid current;
6. writes shared GO.

Worker:
7. observes GO on P;
8. performs immediate measured touch;
9. writes DONE in shared page.

### REMOTE_S

Controller:
1. reads pre-touch `memory.current`;
2. records LOW/HIGH stratum;
3. externally changes affinity to S;
4. confirms worker on S;
5. reads mid current;
6. writes shared GO.

Worker:
7. observes GO on S;
8. performs immediate measured touch;
9. writes DONE.

Both arms therefore use the same controller-driven affinity path and pre/mid/post decomposition.

## Scale

Use:

`32 identities per arm per block`

with 4 blocks.

Total:

`256 independent probes`

Arm order alternates by block parity.

## Primary outcome

`Q64_PASS = 60 <= touch_delta_pages <= 68`

Preserve:
- pre pages;
- stratum;
- migration/reassert delta;
- touch delta;
- CPU receipt;
- controller affinity-to-GO elapsed microseconds.

## Primary prospective test

Pool both arms.

Compare LOW vs HIGH Q64 success.

### SUPPORT_BASELINE_GATE

Require:
- at least 100 valid LOW observations overall;
- LOW Q64 success >= 95%;
- LOW success >= 90% separately in LOCAL_P and REMOTE_S;
- HIGH Q64 success <= 75%;
- one-sided Fisher exact test LOW > HIGH: `p < 1e-6`;
- zero CPU mismatches.

### REJECT_BASELINE_GATE

If:
- LOW Q64 success < 85%, or
- LOW and HIGH differ by <10 percentage points with >=100 observations in each stratum.

### INCONCLUSIVE

Otherwise.

## Secondary CPU-locality test

Within each stratum compare LOCAL_P vs REMOTE_S.

Report:
- success rates;
- Fisher exact test;
- risk difference.

Interpretation:

- LOW works on both CPUs -> baseline gate may identify a reusable insertion subset.
- HIGH fails mainly on LOCAL_P -> startup-CPU stock is implicated.
- HIGH fails similarly on P and S -> baseline level reflects broader hidden state, not only startup-CPU stock.

This secondary analysis cannot override the primary baseline-gate decision.

## Dwell diagnostic

Record controller time from affinity call to GO.

Report Q64 success by latency quartile separately per arm.

This is descriptive only in v1.

## Successor

Only if SUPPORT_BASELINE_GATE:

use LOW-gated fresh identities for a separately frozen capacity experiment.

Do not infer K7 from MEMCG-005E itself.

## Launch boundary

Design only.
Do not implement or launch in this bounce.
No local-PC execution.
