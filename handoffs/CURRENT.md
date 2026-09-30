# CURRENT

> Latest bounce: B419
> Stage: SAME-CPU STOCK-SLOT PRESSURE PILOT IMPLEMENTATION
> Stop: IMPLEMENT 4-IDENTITY SAMECPU PILOT; DO NOT LAUNCH FULL 3-ARM PANEL

## Chapter II frontier

Historical SUCCESS/FAIL has been decomposed into named state transitions.

Established:

- VERIFIED_DIRECT_Q64_RESET: one-page direct Q64 establishes verified residual R0=63.
- PREVERIFY_S64 / MAX_STOCK_BOUNDARY.
- STARTUP_STOCK_SEED.
- SMALL_RESIDUAL_REFILL.
- SLAB_FREE_OBJCG_REFILL1.
- TARGET_STOCK_EVICTION.
- RELEASE_ONLY.

No complete verified target path has produced TARGET_FAIL.

## Age-Decoupling Stage A v2

R1 run 36702673576 is a wiring-only failure:

- duplicate owner-uncharge trigger bind
- no scientific panel executed
- no HOLD exposure executed

Frozen diagnostic:

- analysis/inputs/AGE-DECOUPLING-STAGE-A-R1-WIRING-DIAGNOSTIC-v1.json

The duplicate bind was fixed prospectively.

R2 run 36703139110 completed successfully.

Physical panel:

- FAST x4
- HOLD32 x12
- b63
- requested dwell 22.077060 s
- no automatic Stage B
- no automatic sample expansion

All 16 physical identities reached:

- T=64
- final state SUCCESS
- target result MATCH

Frozen strict classification:

- CANONICAL_SUCCESS = 12
- INSTRUMENTATION_HOLD = 4
- KNOWN_STATE_CHANGE = 0
- UNEXPLAINED_BOUNDARY_DEVIATION = 0
- UNKNOWN_COMPLETE_EMISSION = 0
- TRUE_TARGET_FAIL = 0

By arm:

FAST:
- n=4
- zero-miss canonical=3
- instrumentation hold=1
- T64=4/4

HOLD32:
- n=12
- zero-miss canonical=9
- instrumentation hold=3
- T64=12/12

Stage B trigger=false.

## Realized exposure

Historical exact-b63 calibration:

- tau_fast median = 1.471804 s
- requested dwell = 22.077060 s

R2 zero-miss canonical medians:

- FAST verified -> first Q64 = 1.868684 s
- HOLD32 verified -> first Q64 = 25.001723 s
- realized exposure factor = 13.3793209552819
- observed HOLD checkpoint median = 22.077272 s

Interpretation:

Large wall-clock separation was achieved while measured target touches were fixed.

No complete verified-state hazard or unexplained boundary deviation was captured.

This is bounded no-specimen evidence, not evidence of absence.

## Instrumentation holds

Four identities:

- 0:3 HOLD32 refill_stock missed=1
- 2:3 HOLD32 refill_stock missed=2
- 3:0 HOLD32 refill_stock missed=1
- 3:2 FAST refill_stock missed=6

For all four:

- Q64 probe missed=0
- owner-uncharge probe missed=0
- T=64
- final state SUCCESS
- continuity clean

Do not retroactively promote them.

The only completeness bottleneck was the owner-memcg refill_stock observer.

## Frozen no-event sensitivity

Using only complete zero-miss identities:

- FAST n=3
- HOLD32 n=9
- events=0
- realized F=13.3793

B410 sensitivity replay:

- LOW BF TOUCH/TIME ~= 1.48
- CENTRAL BF TOUCH/TIME ~= 2.59
- HIGH BF TOUCH/TIME ~= 10.08

Interpretation:

- no-event evidence is more compatible with TOUCH than TIME in all frozen sensitivity ranges;
- rare TIME hazards remain weakly constrained;
- high-frequency pure TIME hazards are more strongly disfavored.

This is a design-sensitivity calculation, not an objective model probability.

## New mechanistic target: memcg stock-slot pressure

Linux source at commit 551c722f40809618230001baccf219193e22fc5a has:

- NR_MEMCG_STOCK = 7 per CPU
- per-CPU memcg_stock slots
- refill_stock first reuses a matching memcg slot
- otherwise it uses an empty slot
- if no empty slot exists, refill_stock selects stock->drain_idx, drains that slot, advances drain_idx modulo 7, and installs the new memcg

This gives a deterministic causal direction:

passive wall-clock age
versus
CPU-local stock-slot occupancy/eviction pressure.

Worst-case helper bound after target verification:

- target occupies one of 7 slots
- at most 6 new distinct helper memcgs are needed to fill remaining empty slots
- after the array is full, at most 7 additional distinct helper insertions cycle drain_idx across every slot
- therefore <=13 distinct same-CPU helper insertions are sufficient to force selection of the target slot, absent intervening slot changes

Candidate next arms:

- QUIET
- OFFCPU_SLOT_PRESSURE
- SAMECPU_SLOT_PRESSURE

Preferred target geometry:

1. verify target R0=63;
2. consume exactly 32 measured pages -> expected residual=31;
3. apply intervention with no target touches;
4. continue measurement.

Predictions:

- QUIET: canonical next Q64 T=64
- OFFCPU_SLOT_PRESSURE: canonical T=64 if CPU locality is causal
- SAMECPU_SLOT_PRESSURE: source-grounded target stock drain; after full residual-31 eviction, next target Q64 should occur at T=33, Delta=-31

The experiment must stop helper generation as soon as a source-grounded target drain is observed; cap at 13 distinct helper memcgs.

## Observer lesson for next experiment

Do not remove refill observation entirely.

refill_stock can change per-CPU target stock without an immediate owner page_counter_uncharge, including objcg/socket uncharge paths.

R2 shows full refill event logging is the main observer-load bottleneck.

Investigate a count-only / histogram-style owner refill observer before the full slot-pressure panel:

- dynamically bind to owner_memcg after VERIFY
- aggregate refill sizes/counts without writing every event into the trace ring
- retain kprobe missed-hit receipt
- keep Q64 and owner-uncharge as ordinary event receipts
- preserve UNKNOWN rather than collapsing to FAIL

## Frozen evidence

- analysis/inputs/AGE-DECOUPLING-STAGE-A-R2-PHYSICAL-RESULT-v1.json
- analysis/inputs/AGE-STAGE-A-R2-NO-EVENT-SENSITIVITY-v1.json
- docs/AGE-STAGE-A-R2-BOUNDED-NO-SPECIMEN.md

Raw R2 manifest:

- files=68
- bytes=7,056,729
- content-set SHA-256=e8fc47058103323eb46a3728235b51e4e7869921aed18c104bc9b943df532d9b
- aggregate artifact ID=11090363265
- aggregate digest=sha256:b370602350ab9fa60bba942d5c5b97ef16ef87a153bb13d3e77c7fdc68d5dda9

## Authority

Physical continuation remains authorized by the user.

Standard public-repository GitHub-hosted runner only.
No paid larger runner.
No local-PC execution.
No automatic sample expansion.
No reliability certification.


## B419 observer pilot and next bounded intervention

Owner-refill histogram pilot run 36705123852 completed SUCCESS.

Frozen result:

- LOG n=4, valid=4, refill misses=0, owner refill counts=[0,0,0,0]
- HIST n=4, valid=4, refill misses=0
- HIST owner refill counts=[403,1385,682,596]
- histogram Dropped=0 for all HIST identities
- pilot_pass=true

Interpretation:

A soft-disabled tracefs histogram can aggregate owner-memcg refill_stock sizes/counts while ordinary refill event logging is disabled. This establishes observer capability only; it does not prove a lower miss rate than LOG because LOG identities had zero owner refill activity in this small panel.

Frozen evidence:

- analysis/inputs/OWNER-REFILL-HIST-PILOT-R1-RESULT-v1.json
- artifact ID=11091860816
- digest=sha256:24fe08ecedf10dcd569515ba98fff2e640319c3b7937c2c9022068e0cf3daaa2

Source derivation:

- docs/MATH-028-CPU-LOCAL-MEMCG-STOCK-SLOT-PRESSURE.md
- NR_MEMCG_STOCK=7 per CPU
- <=13 distinct same-CPU helper insertions are a worst-case bound to force selection of the target slot, absent intervening slot changes

Frozen next pilot:

- specs/TX-SAMECPU-STOCK-SLOT-PRESSURE-PILOT-v1.json
- four identities only
- VERIFY target R0=63
- consume 32 -> expected residual31
- no further target touches during pressure
- create distinct helper memcgs on target stock CPU with AllowedCPUs restricted from unit creation
- require each helper insertion to be physically realized by helper direct-Q64 evidence unless target drain occurs earlier
- stop helper generation immediately when target-owner drain is observed
- cap=13
- keep helpers alive through target diagnostic touch
- predicted clean fingerprint: target drain31 followed by immediate owner Q64 at T=33 / Delta=-31

Do not run the full QUIET/OFFCPU/SAMECPU panel until this four-identity causal pilot passes.
