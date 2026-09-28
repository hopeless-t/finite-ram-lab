# MEMCG-003B Non-Consuming Seven-Slot Eviction Probe v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Goal

Retest the source-level `NR_MEMCG_STOCK=7` prediction without consuming target stock during observation and while isolating the orchestration control plane from the stock-test CPU.

## Repairs relative to MEMCG-003

### 1. Non-consuming observation

After each challenger insertion:

- do **not** touch target;
- read target `memory.current` externally;
- record only passive target current.

Define a candidate eviction as a downward step of at least 16 pages between passive target-current samples.

The target performs no new page fault during the challenger sequence.

### 2. One final recharge confirmation

After all challenger insertions are complete:

- touch exactly one previously untouched target page;
- measure target pre/post current;
- report whether a fresh Q64-like charge occurred.

This confirms that target stock was absent at the end without corrupting the eviction threshold.

### 3. CPU isolation

Require at least two allowed CPUs.

- **control CPU C**: Python orchestrator, sudo/systemd-run invocations, passive cgroup reads.
- **stock CPU S**: all wash/target/challenger workers.

Pin the orchestrator to C before any cache priming.
Pin every persistent worker to S.

This minimizes self-induced stock churn on the measured CPU.

## Cache initialization

On stock CPU S:

1. launch 7 persistent wash memcgs sequentially;
2. each touches memory once and remains alive;
3. launch persistent target as the 8th distinct memcg;
4. target touches once and remains idle;
5. record target passive `memory.current` baseline.

Idealized source model:
- target insertion replaces one full-cache slot;
- rotating drain index advances;
- six subsequent distinct insertions replace the other six slots;
- challenger #7 selects target's slot.

## Arms

4 independent runner blocks.

### DISTINCT_CHURN

Launch persistent distinct challengers C1..C8 sequentially on S.

After each reaches READY:
- passive-read target current from C;
- no target touch.

Expected:
- no large target drop through C1..C6;
- target drop near C7;
- final target touch after C8 gives Q64 recharge.

### SIX_ONLY

Only C1..C6.

Expected:
- no large target drop;
- final target touch should normally consume existing stock rather than trigger fresh Q64 recharge.

### SAME_MEMCG_ACTIVITY

One competitor memcg repeatedly touches additional pages.

Expected:
- no target slot eviction threshold.

### NO_CHURN

No competing memcg insertion for matched observation count.

Expected:
- no target stock drop.

## Primary threshold

For each DISTINCT_CHURN block:

`E_drop = first m with passive target current drop >=16 pages`

No recharge event is allowed to define E_drop.

## Primary decision

### SUPPORT_K7_SLOT_MODEL_B

Require:
- at least 3/4 DISTINCT_CHURN blocks with E_drop in {6,7,8};
- modal E_drop = 7;
- median E_drop = 7;
- SIX_ONLY has no passive target drop >=16 pages in at least 3/4 blocks;
- SAME_MEMCG_ACTIVITY and NO_CHURN have no matching systematic drop;
- final target recharge is Q64-like after a detected eviction.

### REJECT_K7_SLOT_MODEL_B

If 0/4 or 1/4 blocks are within {6,7,8} and a stable alternative passive-drop threshold or non-threshold pattern appears.

### INCONCLUSIVE

Otherwise.

## Mathematical analysis

Keep candidate K=1..10.

Use:
- absolute threshold error;
- leave-one-block-out prediction;
- Bayesian discrete K posterior;
- MDL threshold sequence;
- counterexample table.

Secondary MATH-002:
- pmndrs/math QuickHull response/control envelopes;
- seeded permutation null;
- never override primary decision.

## Falsification value

If the repaired passive experiment still prefers K around 1..4, the seven-slot source capacity is not mapping to a simple observable target-eviction threshold under this substrate.

If K=7 emerges only after destructive-probe and CPU-interference removal, MEMCG-003 will have identified the observer effect that hid it.

## Launch boundary

Design only.
No hosted launch in this bounce.
No local-PC execution.
