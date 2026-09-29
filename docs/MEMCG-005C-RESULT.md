# MEMCG-005C Atomic First-Touch Integrity Result v1

> **Status:** PASS / REJECT_ATOMIC_PATH
> **Run:** `36551226475`
> **Launch commit:** `d50af917577493dc457aa0439a192ab90e5f90a1`
> **Aggregate artifact id:** `11024981747`
> **Aggregate digest:** `sha256:90b2819f4489dc7f61c1e5581c67b08f4a875c7271801c7482886104c64208ef`

## Primary decision

`REJECT_ATOMIC_PATH`

The preregistered hypothesis that removing the post-migration receipt I/O would restore near-perfect Q64 first-touch behavior was rejected.

## Aggregate results

### ATOMIC

`MIGRATE_TOUCH S` performs:
- self `sched_setaffinity`;
- confirms S;
- immediately touches the measured page;
- only then emits receipt I/O.

Results:

- Q64 successes: **69 / 92**
- failures: **23 / 92**
- success rate: **0.75**
- zero-delta failures: **23**
- other-delta failures: **0**
- perfect blocks: **0 / 4**
- 95% Clopper-Pearson interval for Q64 success:
  **[0.6488574655, 0.8344515379]**

### TWO_STEP

`MIGRATE S -> receipt -> TOUCH_ONE`

Results:

- Q64 successes: **77 / 92**
- failures: **15 / 92**
- success rate: **0.8369565217**
- zero-delta failures: **15**
- other-delta failures: **0**

Thus ATOMIC was worse, not better.

## Blockwise results

| block | ATOMIC failures | TWO_STEP failures | TWO_STEP failure rate - ATOMIC failure rate |
| ---: | ---: | ---: | ---: |
| 0 | 5 / 23 | 4 / 23 | -0.0434783 |
| 1 | 5 / 23 | 3 / 23 | -0.0869565 |
| 2 | 4 / 23 | 1 / 23 | -0.1304348 |
| 3 | 9 / 23 | 7 / 23 | -0.0869565 |

ATOMIC had the higher failure rate in **4 / 4 blocks**.

The preregistered one-sided paired sign test for ATOMIC improvement therefore returned:

`p = 1.0`

with zero positive-improvement blocks.

## Temporal-order check

The runner alternated arm order by block parity:

- blocks 0 and 2: TWO_STEP then ATOMIC;
- blocks 1 and 3: ATOMIC then TWO_STEP.

ATOMIC was worse in all four blocks.

Therefore a simple "the later arm is worse" explanation does not fit the observed direction.

## Failure morphology

Every failure in both arms was exactly:

`delta_pages = 0`

Every success was exactly:

`delta_pages = +64`

No intermediate event magnitude appeared.

Thus Q64 quantization remains intact.

The uncertainty is whether a fresh batch is required at the nominal first measured touch.

## Post-hoc paired-identity diagnostic

Matching arm results by block and identity index gives:

- both pass: 60
- TWO_STEP pass / ATOMIC fail: 17
- TWO_STEP fail / ATOMIC pass: 9
- both fail: 6

This diagnostic was not preregistered and is not used as the primary decision rule.

Its direction is nevertheless consistent with the blockwise result: removing receipt I/O did not improve first-touch Q64 verification.

## Falsified mechanism hypothesis

MEMCG-005B proposed:

**post-migration receipt I/O on S may create/consume stock before the measured page touch.**

MEMCG-005C directly tested the proposed repair.

The repair made the failure rate worse.

Therefore receipt I/O is not supported as the dominant cause of the zero-delta insertion failures.

## Remaining mechanism candidates

ATOMIC still executes the worker's own migration path before the measured touch:

1. worker is running on P;
2. worker calls `sched_setaffinity(0, ..., S)`;
3. scheduler moves/continues the task on S;
4. worker polls `sched_getcpu()`;
5. worker touches the measured page.

Possible remaining sources include:

- activity associated with the worker's self-migration syscall/path;
- scheduler/kernel work coupled to the target memcg during migration;
- pre-existing/background per-CPU stock state for the memcg established independently of status I/O;
- measurement timing around `memory.current`.

These are hypotheses, not conclusions.

## Next experiment

MEMCG-005D should remove the worker's self-migration syscall from the measured path.

Use a prefaulted shared-memory latch:

- worker starts and spins on P without further control I/O;
- controller on C obtains worker PID;
- controller externally applies `sched_setaffinity(pid, S)`;
- controller confirms externally that task runs on S;
- controller flips a prefaulted shared GO flag;
- worker immediately touches one measured anonymous page;
- worker sets DONE in the same prefaulted shared page;
- only after DONE may any receipt/status I/O occur.

Compare:

- SELF_ATOMIC — worker performs its own migration then immediate touch;
- EXTERNAL_ATOMIC — controller migrates worker; worker performs no migration/control syscall before touch.

Do not return to K7 capacity testing until the first-touch insertion primitive is understood.

## Authority boundary

Hosted Linux accounting research only.
No local-PC execution.
No memory-control policy.
