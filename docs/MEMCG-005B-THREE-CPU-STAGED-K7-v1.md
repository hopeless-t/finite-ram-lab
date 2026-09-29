# MEMCG-005B Three-CPU Staged K7 Boundary v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Scientific question

Can the seven-slot boundary be observed when future memcg identities are prevented from interacting with the measured stock CPU before their actual insertion?

MEMCG-005 showed that preparing many identities on the stock CPU changes the same shared cache being studied.

MEMCG-005B removes that compositional interference.

## CPU roles

Require at least three allowed CPUs.

Assign:

- **C** — controller/orchestrator CPU
- **P** — startup/preparation CPU
- **S** — stock-test CPU

Recommended deterministic choice from the allowed set:

- C = lowest CPU
- P = second-lowest CPU
- S = highest CPU

The controller remains pinned to C.

All workers start pinned to P.

No participating worker may execute on S before its measured insertion.

## Worker state

Dedicated zero-touch interactive worker.

READY must report:

`touched=0`

Supported commands:

### MIGRATE <cpu>

- call `sched_setaffinity` to the requested CPU;
- wait until `sched_getcpu()` reports that CPU;
- emit a deterministic MIGRATE receipt;
- perform no measured-page touch.

### TOUCH_ONE

Touch exactly one previously untouched 4 KiB page and emit receipt.

### STOP

Exit cleanly.

No dynamic allocation is allowed in the measured command path.

## Why migration replaces same-CPU pre-normalization

A worker started on P may have arbitrary startup-related memcg accounting state on P.

That is acceptable.

The experiment does not use P's stock state.

Immediately before insertion:

1. worker migrates from P to S;
2. worker has never executed measured-page demand on S;
3. controller samples worker `memory.current`;
4. worker performs exactly one TOUCH_ONE on S;
5. controller samples again.

The insertion is accepted only if:

`60 <= delta_pages <= 68`

Thus the first demand on S directly verifies the insertion.

No prior EMPTY assumption on S is required.

## Robust cache washout

Unknown initial S-cache occupancy and unknown `drain_idx` remain possible.

Therefore each independent replica inserts **14 distinct wash memcgs** before the target.

Wash identities:

`W0..W13`

Each:
- starts on P;
- migrates to S only at insertion;
- first S touch must be fresh +64;
- then remains idle on S with residual stock.

### Source-level washout argument

The source cache has seven slots.

Regardless of initial empty/full occupancy:

- the cache becomes full no later than the 7th distinct verified wash insertion;
- after it becomes full, seven further distinct insertions are sufficient to advance replacement through every slot once.

Therefore after 14 distinct verified wash insertions, under the source model and absent external interference, all seven slots are participant-owned wash entries regardless of initial occupancy or initial `drain_idx`.

This removes the need to know the starting cache state.

## Target insertion

Target T:
- starts on P;
- migrates to S only after all 14 washes;
- first S touch must be +64-like.

With the cache full, target insertion replaces one wash slot and advances `drain_idx`.

Target then remains untouched.

## Challenger insertion

Potential challengers:

`C1..C8`

Each starts on P.

For challenger i:
- migrate Ci to S;
- first S touch must be +64-like;
- leave Ci idle on S.

No later worker startup occurs on S.

## One-shot target probe

After exactly m challengers:

- sample target current;
- issue one target TOUCH_ONE on S;
- sample target current.

Classify:

### PRESENT

`abs(delta_pages) < 16`

### ABSENT

`60 <= delta_pages <= 68`

### AMBIGUOUS

anything else.

The replica ends immediately after this probe.

## Independent replica panel

Test:

`m in {0,5,6,7,8}`

Four hosted blocks.

Total:

`4 x 5 = 20 independent replicas`

For a replica with challenger count m, only the required workers are started:

- 14 washes
- 1 target
- m challengers

All begin on P.

## Source K7 prediction

After 14-wash stabilization and target insertion:

- target occupies the current replacement slot;
- replacement pointer advances;
- C1..C6 replace the six other slots;
- C7 returns to target's slot.

Therefore:

| m | target |
|---:|---|
| 0 | PRESENT |
| 5 | PRESENT |
| 6 | PRESENT |
| 7 | ABSENT |
| 8 | ABSENT |

## Validity requirements

A replica is scientifically valid only if:

- controller affinity receipt = C;
- every worker READY on P with touched=0;
- every measured participant insertion migrates to S successfully;
- every wash insertion delta is Q64-like;
- target insertion delta is Q64-like;
- every used challenger insertion delta is Q64-like;
- target probe is PRESENT or ABSENT, not AMBIGUOUS.

All invalid replicas remain reported.

## Interference diagnostic

For each insertion record:

- identity
- source CPU before migration
- target CPU after migration
- pre/post `memory.current`
- delta pages
- elapsed sequence index

Report any:
- non-Q64 insertion;
- unexpected CPU;
- large passive change before target probe.

A high invalid rate is itself evidence of stock-CPU interference.

## Primary decision

### SUPPORT_STAGED_K7

Require:
- at least 3/4 blocks with all five valid replicas matching:
  - m0 PRESENT
  - m5 PRESENT
  - m6 PRESENT
  - m7 ABSENT
  - m8 ABSENT
- no systematic insertion-invalid pattern at one m.

### REJECT_STAGED_K7

If:
- at least 3 complete-valid blocks exist;
- 0/4 or 1/4 complete-valid blocks match K7;
- and a stable alternative boundary is selected.

### INCONCLUSIVE

Otherwise.

## Boundary model competition

Candidates:

`K in {1,2,3,4,5,6,7,8,9}`

Predict:

`ABSENT iff m >= K`

Score by:
- classification errors;
- fixed-epsilon log loss;
- MDL with exception locations;
- leave-one-block-out accuracy.

Report sparse observational equivalence classes explicitly.

## Falsification meaning

If staged first-touch verification is clean but K7 still fails, the result directly challenges the simple rotating-seven-slot observable model.

If invalid insertions remain common even with P->S staging, then background or non-page memcg activity on S is materially perturbing the per-CPU stock cache.

Either result is informative.

## Launch boundary

Design only.
Do not implement or launch in this bounce.
No local-PC execution.
No memory-control policy.
