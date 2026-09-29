# MATH-016 — Shared per-CPU LRU-batch handoff model

> **Status:** CONTROLLED MECHANISM RESULT
> **Input:** OBS-005 run 36625036954
> **Goal:** turn the naturally observed cross-task -17 effect into a deliberately constructed state transition.

## 1. Construction

Three tasks/cgroups share one target CPU:

- S = scrubber
- A = producer / folio owner
- B = trigger

Protocol:

1. S adds pages until a recent LRU-add batch flush is observed.
2. A adds exactly 17 anonymous folios.
3. A unmaps those pages but stays alive in its own cgroup.
4. B adds exactly 14 anonymous folios.

Linux LRU-add batch capacity:

\`N = 31\`

Frozen construction:

\`A = 17\`

\`B = 14\`

Thus:

\`17 + 14 = 31\`

## 2. Frozen classifier

16 trials:

- CONTROLLED_HANDOFF_PASS: 10
- HANDOFF_NONCANONICAL_TIMING: 1
- NO_HANDOFF_UNCHARGE: 1
- COUNTER_UNKNOWN: 3
- SCRUB_NO_FLUSH: 1

Keep this frozen classifier unchanged.

## 3. Derived mechanism view

The frozen classes mix mechanism outcomes with receipt quality.

### Precondition success

15/16 trials produced the required scrubber flush.

One trial is a clean precondition HOLD and is not interpreted.

### Raw producer current

Among the 15 scrub-success trials:

- 15/15 show an exact -17 page drop in producer A's memory.current during the trigger phase.

Timing:

- B touch14: 13
- B touch13: 1
- B touch4 window, but current flusher is a third-party provjobd task: 1

### Counter-grounded subset

12 scrub-success trials retained producer page-counter identity receipts.

All 12/12 show:

\`page_counter_uncharge(..., 17)\`

on a counter pointer observed from producer A.

Trigger identity:

- B / frltrig: 11
- third-party provjobd: 1

Among B-triggered cases:

- touch14: 10
- touch13: 1

Thus the controlled experiment directly demonstrates:

> a task/cgroup that does not own the dead folios can trigger their release from a shared per-CPU LRU batch, causing the owner's page counter and memory.current to fall.

## 4. Occupancy equation

Let:

- \(N = 31\): LRU-add batch capacity
- \(A = 17\): producer-owned entries after construction
- \(E\): external entries inserted after scrub preconditioning and before/during B
- \(k\): B touch that fills the batch

Then:

\[
A + E + k = N
\]

so

\[
k = 14 - E.
\]

Observed:

### Canonical

10 counter-grounded B-triggered trials:

\`k=14\`

therefore:

\`E=0\`

### One-step drift

One counter-grounded B-triggered trial:

\`k=13\`

therefore the simplest occupancy interpretation is:

\`E=1\`

### External trigger

Trial 2:2:

- producer counter known;
- A memory.current falls by 17 at trigger touch4;
- the 17-page uncharge uses A's counter;
- current task is \`provjobd...\`, not B;
- stack is the LRU/folio-batch path.

This is an intentional experiment being preempted by a real third-party flush.

It is not a failure of the shared-batch model.

It demonstrates that the transition trigger is globally competitive among tasks scheduled on that CPU.

## 5. Counter-receipt loss

Three block-3 trials show the canonical raw touch14 -17 but are classified COUNTER_UNKNOWN.

Block 3 trace load was extremely high:

- page_counter_try_charge kprobe hits: 54,642
- page_counter_uncharge: 126,589
- lru_flush: 111,737
- folios_put: 527,380

The saved trace contains zero pc_try lines inside those trial windows despite the kprobe profile recording tens of thousands of hits.

The parsimonious interpretation is trace-ring overwrite.

Do not promote these three into the counter-grounded set.

They remain receipt-limited, mechanism-compatible observations.

## 6. Mechanism conclusion

The recurrent -17 phenomenon is no longer merely correlated with LRU flushes.

It is **constructible**:

\[
\text{A owns 17 deferred dead folios}
\rightarrow
\text{B / C fills shared per-CPU batch}
\rightarrow
\text{flush}
\rightarrow
\text{A counter uncharge17}
\]

This establishes four distinct roles:

1. logical owner — producer memcg A
2. staging location — per-CPU LRU-add batch
3. trigger actor — B or another task on that CPU
4. accounting target — A's page counter

These roles need not coincide.

## 7. Implication for Q64 observation

\`memory.current\` is a net accounting observation.

A measured data-page touch can coincide with:

- its own charge;
- release of deferred folios owned by the same cgroup;
- a flush triggered by another task;
- memcg stock drain;
- PTE charge.

Therefore exact per-touch stock inference must use event receipts, not net \`memory.current\` alone.

The controlled Q64 phase result remains intact because LRU release is an observation contaminant, not residual-stock consumption.

## 8. Generic finite-memory lesson

A finite-resource controller must distinguish:

\`owner != staging scope != transition trigger != accounting recipient\`

This generalizes beyond Linux LRU batches to:

- shared caches;
- staging rings;
- asynchronous eviction queues;
- remote/offloaded state;
- multi-tenant accelerator memory.

## 9. Next

The -17 mechanism is sufficiently closed for the Q64 lane.

Next core task:

**OBS-006 / decontaminated charge observer**

Goal:
represent each measured touch as separate charge and release emissions rather than one net memory.current delta.

Only after that observer is validated should b63 reliability scaling resume.
