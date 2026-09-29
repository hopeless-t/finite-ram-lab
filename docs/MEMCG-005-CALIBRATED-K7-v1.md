# MEMCG-005 Calibrated Seven-Slot Boundary v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Scientific question

After every participating memcg has been normalized to a known empty-stock state and every slot insertion is directly verified by a fresh +64 charge, does the source-level seven-slot rotating cache produce the predicted target survival boundary:

- target survives six later distinct insertions;
- target is evicted by the seventh?

This is the first seven-slot experiment built on an experimentally validated stock-state primitive.

## Accepted primitive from MEMCG-004

MEMCG-004 run `36541998246` established:

- condition on an observed fresh +64-page charge;
- stop immediately;
- the next fresh +64 appears on the 64th subsequent one-page touch in 4/4 blocks;
- validation touches 1..63 do not cause another batch charge.

This is source-consistent with 63 residual cached pages.

Therefore a calibrated **empty** state can be constructed as:

1. observe a fresh +64 charge;
2. issue exactly 63 subsequent one-page touches;
3. stop before the 64th.

The source model predicts the cached stock is then zero and the cached memcg pointer is removed.

The next one-page touch should therefore produce a fresh +64 charge.

## Key design principle

**Do not infer slot insertion from process creation.**

Every worker process is started before the measured slot sequence.

Startup effects happen before normalization.

Every measured insertion is accepted only if its first post-normalization one-page touch produces a fresh +64 charge.

Thus:
- pre-insertion state is empirically empty;
- post-insertion state is empirically calibrated;
- insertion order is observed, not assumed.

## Hosted substrate

- Ubuntu 26.04
- cgroup v2
- base page size 4096
- at least two allowed CPUs
- controller pinned to CPU C
- all stock workers pinned to distinct CPU S
- no MemoryHigh / MemoryMax
- fresh independent replica for every tested challenger count

## Worker population per replica

Prestart and keep alive on CPU S:

- 7 wash memcgs: W0..W6
- 1 target memcg: T
- 8 potential challenger memcgs: C1..C8

Total:

`16 persistent memcg identities`

All workers must reach:

`READY touched=0`

before normalization begins.

## Phase A — normalize every worker to EMPTY

For each of the 16 workers, one at a time:

1. issue one-page touches while externally reading that worker's `memory.current`;
2. stop at the first fresh charge in [60,68] pages;
3. record calibration touch and exact delta;
4. issue exactly 63 additional one-page touches;
5. stop.

No worker receives further activity until its measured insertion or target probe.

### Normalization validity

A worker is not assumed empty merely because 63 touches were issued.

Its later measured insertion must itself validate the state:

**first insertion touch must be a fresh +64-like charge.**

If not, the replica is INVALID_STATE and excluded from scientific threshold scoring, while preserved as a counterexample.

## Phase B — fill the seven calibrated wash slots

Sequentially for W0..W6:

- external pre-current sample;
- issue exactly one TOUCH_ONE;
- external post-current sample;
- require delta in [60,68] pages.

Each successful insertion leaves approximately 63 cached pages.

After W6:

the ideal source model has all seven stock slots occupied by calibrated wash memcgs.

## Phase C — insert calibrated target

For T:

- issue exactly one measured insertion touch;
- require fresh +64-like charge.

With seven wash slots already occupied, source model predicts:
- one wash slot is drained/replaced;
- target occupies that slot;
- drain_idx advances to the next slot.

T now has calibrated residual stock and is left untouched.

## Phase D — calibrated challengers

Insert C1..Cm sequentially.

For each challenger:
- exactly one measured insertion touch;
- require fresh +64-like charge;
- then leave challenger idle.

Because each challenger was previously normalized empty, a successful fresh +64 event verifies that the challenger insertion occurred at the intended step.

## Phase E — one-shot target state probe

After exactly m challenger insertions:

- read target current;
- issue exactly one target TOUCH_ONE;
- read target current.

Classify:

### TARGET_PRESENT

`target_probe_delta < 16 pages`

Interpretation:
target still has consumable cached stock.

### TARGET_ABSENT

`60 <= target_probe_delta <= 68 pages`

Interpretation:
target no longer has consumable stock and the target demand triggers a fresh batch.

Other deltas:

`AMBIGUOUS`

The replica ends immediately after this one-shot probe.

No sequential probing is allowed.

## Tested boundary counts

Independent replicas test:

`m in {0, 5, 6, 7, 8}`

Each of 4 hosted runner blocks executes all five counts.

Total scientific replicas:

`4 blocks × 5 m-values = 20 replicas`

Each replica starts with fresh worker/cgroup identities.

## Source-level prediction

After target insertion:
- target occupies the slot selected by current drain_idx;
- drain_idx advances;
- C1..C6 replace the six other slots;
- C7 returns to target's slot and drains/replaces it.

Therefore:

| challenger count m | predicted target state |
| ---: | --- |
| 0 | PRESENT |
| 5 | PRESENT |
| 6 | PRESENT |
| 7 | ABSENT |
| 8 | ABSENT |

This is the primary causal signature.

## Primary block criteria

A block supports the source seven-slot boundary only if all valid replicas show:

- m=0: PRESENT
- m=5: PRESENT
- m=6: PRESENT
- m=7: ABSENT
- m=8: ABSENT

and every wash/target/challenger measured insertion in those replicas was verified by a fresh +64-like charge.

## Preregistered decision

### SUPPORT_CALIBRATED_K7

Require:
- at least 3/4 blocks match the complete boundary signature;
- m=6 PRESENT in at least 3/4 blocks;
- m=7 ABSENT in at least 3/4 blocks;
- no systematic INVALID_STATE pattern that preferentially removes contrary replicas.

### REJECT_CALIBRATED_K7

If 0/4 or 1/4 blocks match the complete boundary signature and a stable alternative boundary appears.

### INCONCLUSIVE

Otherwise.

## Discrete boundary model competition

For every valid one-shot replica encode:

- PRESENT = 0
- ABSENT = 1

Candidate eviction boundary:

`K in {1,2,3,4,5,6,7,8,9}`

Model K predicts:

`ABSENT iff m >= K`

Score candidates by:

1. classification errors;
2. Bernoulli log loss with fixed error floor epsilon;
3. MDL including candidate-ID bits + exception locations;
4. leave-one-block-out selected K and held-out classification accuracy.

Source prediction:

`K=7`

The sparse tested m panel means some K values may be observationally equivalent.

Report equivalence classes explicitly rather than tie-breaking them into false precision.

## Counterexample preservation

Always report:

- insertion touch not +64-like;
- target absent at m<=6;
- target present at m>=7;
- ambiguous probe;
- block-specific boundary drift;
- CPU receipt mismatch.

Do not silently discard invalid-state replicas.

## Why this experiment is stronger than MEMCG-003 / 003B

MEMCG-003:
- destructive repeated target probing.

MEMCG-003B:
- passive proxy did not directly expose stock loss;
- initial slot state was not calibrated.

MEMCG-005:
- startup noise happens before normalization;
- every participant is normalized to a known empty phase;
- every measured insertion is directly verified;
- target is probed exactly once;
- each challenger count uses an independent replica.

The tested observable is now the demand behavior that MEMCG-004 proved can reveal calibrated stock presence.

## Successor

Only if SUPPORT_CALIBRATED_K7:

MEMCG-006 may test:
- exact rotating eviction order under alternative insertion sequences;
- multiple targets;
- CPU migration of a calibrated slot set;
- local Lubuntu replication under separately authorized MVCA -> LDC scope.

## Launch boundary

Design only.
Do not implement or launch in this bounce.
No local-PC execution.
No memory-control policy.
