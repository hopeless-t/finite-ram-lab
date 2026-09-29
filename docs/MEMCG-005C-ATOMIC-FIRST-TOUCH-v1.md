# MEMCG-005C Atomic First-Touch Integrity v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Question

Does post-migration control-path activity explain the zero-delta insertion failures seen in MEMCG-005B?

Compare the old two-step path against an atomic migrate-and-touch path.

## CPU roles

Require >=3 allowed CPUs:

- C controller
- P startup
- S stock-test

Controller pinned C.

Every worker starts on P with:

`READY touched=0`

## Arms

Four independent hosted blocks.

Each block runs two independent arms with fresh cgroups and workers.

### TWO_STEP

For each fresh identity:

1. worker starts on P;
2. command `MIGRATE S`;
3. worker arrives on S;
4. worker emits MIGRATE receipt on S;
5. controller reads pre-current;
6. command `TOUCH_ONE`;
7. controller reads post-current.

This reproduces MEMCG-005B's control path.

### ATOMIC

For each fresh identity:

1. worker starts on P;
2. controller reads pre-current while worker is still on P;
3. command `MIGRATE_TOUCH S`;
4. worker calls `sched_setaffinity`;
5. confirms `sched_getcpu()==S` without status I/O;
6. immediately touches exactly one pre-mapped 4 KiB measured page;
7. only after the touch emits one combined receipt;
8. controller reads post-current.

No status write, getrusage call, or other intentional syscall is allowed between arrival on S and the measured page touch.

## Identity count

Use:

`N = 23 fresh identities per arm per block`

Reason:

14 washes + 1 target + 8 challengers equals the maximum participant count of the staged K7 experiment.

Total first-touch probes:

`4 blocks x 2 arms x 23 = 184`

## Outcome

For each identity:

`Q64_PASS = 60 <= delta_pages <= 68`

Otherwise preserve exact delta as a counterexample.

Per arm/block report:

- Q64 pass count
- zero-delta count
- other-delta count
- ordered delta sequence

## Primary causal statistic

For each block compute:

`failure_rate = 1 - Q64_pass_count / 23`

Compare ATOMIC versus TWO_STEP.

Primary aggregate:

- total failures by arm;
- paired blockwise failure-rate difference;
- exact binomial confidence interval for ATOMIC success rate;
- permutation/sign test over paired block differences where appropriate.

## Preregistered decision

### SUPPORT_ATOMIC_PATH

Require:

- ATOMIC Q64 success >= 90 / 92 identities overall;
- at least 3/4 ATOMIC blocks have 23/23 Q64;
- ATOMIC has fewer failures than TWO_STEP overall;
- no CPU-receipt mismatch.

### REJECT_ATOMIC_PATH

If ATOMIC has >=8 / 92 failures or a stable non-Q64 pattern comparable to TWO_STEP.

### INCONCLUSIVE

Otherwise.

The thresholds deliberately leave a gray zone.

## Interpretation

If SUPPORT_ATOMIC_PATH:

post-migration control-path activity is strongly implicated in MEMCG-005B insertion failures, and a successor K7 experiment may use only MIGRATE_TOUCH.

If REJECT_ATOMIC_PATH:

migration itself or external S-side memcg activity can establish/alter stock before the measured page demand, requiring a lower-level isolation strategy.

## Successor

Only after SUPPORT_ATOMIC_PATH:

run MEMCG-006 staged K7 using:
- C/P/S roles;
- 14 wash insertions;
- atomic MIGRATE_TOUCH only;
- one-shot target probe.

## Launch boundary

Design only.
Do not implement or launch in this bounce.
No local-PC execution.
