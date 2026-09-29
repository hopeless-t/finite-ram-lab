# MEMCG-005G-C Controlled Rare-State Induction v1

> **Status:** REVISED DRAFT / DEPENDENCY RESOLVED / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Why v1

The original draft waited for MEMCG-005G-B.

005G-B completed with `SUPPORT_FOOTPRINT_EFFECT`.

Subsequent work also established that the capacity series is confounded by capacity-dependent argv representation, but that does not invalidate the independently calibrated Q64 stock staircase.

This v1 therefore treats controlled induction as a separate positive-control/state-construction experiment.

## Source-consistent state machine

For a one-page memcg charge with no usable local stock:

1. kernel charges a batch of 64 pages;
2. one page satisfies the allocation;
3. the unused 63 pages refill same-CPU memcg stock;
4. later one-page charges can consume that stock.

Finite-ram-lab MEMCG-004 reproduced:

fresh Q64 -> residual63 -> 63 stock-consuming touches -> next Q64.

## Key design improvement

Do not assume the trial begins with empty stock.

Instead, on the selected CPU and memcg:

1. touch fresh pages one at a time;
2. measure each `memory.current` delta;
3. wait until a directly observed Q64 occurs;
4. define that observed Q64 as the primer and reset the experimental phase;
5. construct the desired residual depth from that verified primer.

Thus pre-primer history is calibration, not evidence.

## Bait definition

Let `b` be total pages already consumed from the verified 64-page batch, including the primer page.

Before target:

`R_target = 64 - b`

Candidate arms:

| bait total b | predicted residual at target | predicted target | predicted first later Q64 |
| ---: | ---: | --- | --- |
| 16 | 48 | delta0 | after 48 residual-consuming target/biopsy touches |
| 19 | 45 | delta0 | depth45 |
| 30 | 34 | delta0 | depth34 |
| 50 | 14 | delta0 | depth14 |
| 63 | 1 | delta0 | depth1 |
| 64 | 0 | Q64 | boundary control |

Primary operational arm for "rare Pokemon catch rate -> 100%":

`b63`

Prediction:

- target delta = 0;
- next touch = Q64;
- exact biopsy depth = 1.

## Capacity/argv hygiene

Do not use a capacity-dependent decimal argv token.

Use the G0 alias-breaker shared-control integer mechanism or a single fixed mapping capacity sufficient for the full sequence.

The induction result must not be interpretable through argv digit width.

## Primary endpoint

For each valid primer-qualified trial:

`EXACT_RECOVERY := observed target morphology and next-Q64 depth exactly equal the prespecified arm prediction`

Report:

- primer acquisition attempts;
- valid primer-qualified trials;
- exact recovery count/rate by bait arm;
- all unexpected nonzero deltas;
- CPU receipts;
- pre/primer/target memory.current sequence.

## Pilot scale

A small mechanism pilot can use:

- 16 valid primer-qualified trials per arm;
- six arms;
- 96 valid trials total.

This is for falsification and instrument validation, not a near-100% reliability claim.

## Reliability calibration for b63

Literal 100% probability cannot be proven from finite data.

If all b63 trials succeed, one-sided exact 95% lower bounds are approximately:

- 59/59 -> >95% true success probability;
- 96/96 -> >96.9%;
- 299/299 -> >99%.

Therefore a practical progression is:

1. small multi-depth mechanism pilot;
2. b63-focused reliability replication;
3. only then consider operational admission/state-construction use.

## Failure interpretation

Any of these falsifies the simple deterministic constructor for that trial:

- verified primer is not Q64;
- target delta is nonzero when residual was predicted;
- next Q64 arrives at wrong depth;
- CPU changes unexpectedly;
- unrelated charge/uncharge activity changes the measured sequence.

Do not silently retry failed exact-recovery trials after primer qualification.

## Non-claims

This experiment does not claim natural deep specimens share the same cause.

It tests whether the same observable morphology can be deliberately constructed from a verified Q64 state.

No local-PC execution.
No launch without Human compute approval.
