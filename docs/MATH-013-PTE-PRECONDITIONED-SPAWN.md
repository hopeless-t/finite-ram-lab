# MATH-013 — PTE-Preconditioned Rare-State Spawn Construction

> **Status:** DESIGN COMPLETE / NOT IMPLEMENTED / NOT LAUNCHED
> **Input:** G0 Stage A, MATH-009, MATH-011, MATH-012
> **Authority:** HOSTED_RESEARCH_ONLY

## Goal

Turn the naturally rare LOW exact-zero/depth1 state into a deliberately constructed state.

The construction must remove the newly observed PTE-allocation suppressor before manipulating memcg stock.

## 1. New fact from G0

G0 Stage A observed first-fault VmPTE +4 KiB only for H32:

- H32: 8/160
- all other arms: 0/800

Within LOW:

- PTE growth: 5
- Q64: 5/5
- exact-zero: 0/5

Therefore page-table allocation is not merely theoretical noise.

It is an observed state transition capable of stealing charge before the data-page charge.

## 2. Key construction trick

Allocate the target PTE table on a different CPU before stock construction.

Use three CPUs:

- C = controller
- P = preparation CPU
- S = stock / measured CPU

On P:

1. worker maps a sufficiently large anonymous VMA;
2. worker identifies a safe contiguous span fully inside one x86 PTE page;
3. worker touches one sacrificial guard page inside that span;
4. verify VmPTE grew if the table was not already present;
5. keep the guard page resident.

Then migrate worker to S.

The guard's data charge and any PTE-page charge occurred on P's per-CPU memcg stock.

The page table remains part of the mm and is available when later data pages in that span fault on S.

This isolates S from target-time PTE allocation.

## 3. Safe-span construction

One x86 PTE page covers 512 base pages = 2 MiB.

Use a VMA large enough to guarantee a long safe subspan even under arbitrary page-granular mmap placement.

Suggested VMA:

`1024 pages = 4 MiB`

After mmap, the worker knows its virtual base address.

Compute page-table index:

`pte_index = (address >> 12) & 511`

Select a contiguous safe span of at least 128 untouched pages whose PTE indexes do not wrap.

Reserve within the same PTE table:

- guard page
- calibration pages
- bait pages
- target
- next1
- next2

No measured touch may cross a PTE boundary.

## 4. Why 128 safe pages is enough

The construction needs:

- one precondition guard;
- an unknown number of calibration touches until a fresh Q64 is directly observed;
- at most 63 post-primer bait/target steps for the b62/b63/b64 local bracket;
- two follow-up pages.

A 128-page safe span is sufficient for a bounded pilot if calibration is capped appropriately.

If the fresh Q64 is not reached before the safe calibration budget is exhausted, mark the trial:

`PRIMER_NOT_FOUND`

Do not silently remap/retry within the same scientific identity.

## 5. Primer semantics

On S, touch fresh data pages one at a time inside the already-existing PTE table.

Measure `memory.current` delta after each touch.

The first directly observed Q64 is the primer.

Source model:

- the primer data page consumes one page from a newly charged 64-page batch;
- residual stock immediately after primer is expected to be 63 pages.

All pre-primer history is calibration only.

## 6. Local off-by-one bracket

Use three randomized arms.

### b62

Total pages consumed from the verified Q64 batch including primer:

`62`

Expected stock before target:

`R=2`

Prediction:

- target: delta0
- next1: delta0
- next2: Q64

### b63

Total consumed including primer:

`63`

Expected stock before target:

`R=1`

Prediction:

- target: delta0
- next1: Q64

This is the primary rare-state spawn arm.

### b64

Total consumed including primer:

`64`

Expected stock before target:

`R=0`

Prediction:

- target: Q64

This is the boundary control.

## 7. PTE exclusion receipts

For every calibration, bait, target, and follow-up touch:

record:

- VmPTE before
- VmPTE after
- VmPTE delta

Required for an exact mechanistic specimen:

`VmPTE_delta = 0`

after the initial P-side guard preconditioning.

Any measured-phase PTE growth produces:

`PTE_CONTAMINATED`

and the trial is retained as evidence but excluded from exact stock arithmetic.

No silent retry.

## 8. Exact-recovery endpoints

### b62 exact recovery

- verified Q64 primer
- all required bait touches valid
- no measured-phase VmPTE growth
- target delta0
- next1 delta0
- next2 Q64

### b63 exact recovery

- verified Q64 primer
- all required bait touches valid
- no measured-phase VmPTE growth
- target delta0
- next1 Q64

### b64 exact recovery

- verified Q64 primer
- all required bait touches valid
- no measured-phase VmPTE growth
- target Q64

The three-arm pattern is stronger than b63 success alone because it verifies the expected one-page phase shift.

## 9. Why guard preconditioning belongs before migration

If the guard is touched on S, it may consume the same stock being calibrated.

If guard/PTE preparation occurs on P and the worker later migrates to S:

- PTE state is preserved in the mm;
- P's stock absorbs preparation charges;
- S begins calibration without that preparation charge.

This exploits the per-CPU nature of memcg stock rather than fighting it.

## 10. Reliability ladder

Pilot:

- 24 valid primer-qualified trials per arm
- 72 valid trials total
- mechanism and off-by-one validation only

If b63 is all-success:

one-sided exact 95% lower bound after 24/24 is only about 88.3%.

Reliability stages for b63 alone:

- 59/59 successes -> lower bound >95%
- 96/96 -> lower bound about 96.9%
- 299/299 -> lower bound >99%

Formula for all-success one-sided 95% lower bound:

`0.05^(1/n)`

Do not call observed 100% literal certainty.

## 11. Failure taxonomy

Every primer-qualified failure is retained.

Classes:

- PRIMER_NOT_FOUND
- CPU_MISMATCH
- PTE_CONTAMINATED
- BAIT_NONZERO
- TARGET_UNEXPECTED_Q64
- TARGET_UNEXPECTED_ZERO
- NEXT_PHASE_MISMATCH
- OTHER_NONZERO_NONQ64
- WORKER_ERROR

No automatic retry after primer qualification.

## 12. Council conclusion

The G0 result changes the controlled-induction design materially.

The strongest route to near-deterministic rare-state capture is now:

`P-side PTE precondition -> migrate to S -> observe fresh Q64 -> consume to residual1 -> target zero -> next Q64`

The PTE suppressor is converted from an uncontrolled confound into an explicit precondition and receipt.

No physical run is authorized by this document.
