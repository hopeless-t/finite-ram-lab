# OBS-002 Design Council — Region-Resolved Residency

> **Status:** DESIGN STUDY

## Evidence entering the Council

VAL-001 replicated the pressure regime across six independent runner blocks.

The key new feature is the 164 MiB transition zone:

- most trials remained fast;
- a minority became tens of milliseconds to seconds slower;
- slow trials had much more swap already present after `BURST_ALLOC`;
- slow retouches showed thousands of anonymous swap-ins/refaults and many major faults.

This raises a narrower question than “is swap slow?”:

> Did `BURST_ALLOC` evict pages from the soon-reused hot set?

## Pseudo-Council

### Kernel / VM reviewer

Aggregate cgroup counters cannot identify which application region lost residency. Add region-resolved observation before considering policy changes.

### Application/runtime reviewer

The workload already has semantic regions — hot set and burst — so expose those identities only to the observer. Do not send hints to the kernel yet.

### Measurement reviewer

Use `mincore(2)` because it can report page residency for the process mapping. Treat each result as a snapshot and record the call overhead.

### Falsification reviewer

The candidate mechanism fails if slow retouches occur while the hot set remained resident, or if hot-set residency loss does not predict retouch cost.

### External-validity reviewer

The current pressure actuator is cgroup v2 `memory.high`, which triggers throttling and heavy reclaim. Results remain memcg-pressure results until global physical-RAM pressure is tested separately.

### Experimental-design reviewer

Changing the allocation mechanism from Python `bytearray` to anonymous `mmap` may alter behavior. Preserve 160 MiB and 168 MiB controls in every runner block.

### Monte Carlo reviewer

Use the observed transition-zone branch frequency only for sample-size planning, not as a scientific threshold.

## Candidate observation design

The sample-size Monte Carlo compares 6, 8, and 10 independent runner blocks.

Each runner carries:

- one 160 MiB control;
- several 164 MiB transition-zone repetitions;
- one 168 MiB control.

The preferred design should have enough transition-zone trials to capture multiple slow-branch events under the current uncertainty while retaining independent runner replication.

## Measurement target

For anonymous `mmap` regions, record at each semantic phase:

```text
hot-set resident pages / total pages
burst resident pages / total pages
mincore call duration
cgroup pressure / reclaim / swap counters
phase latency
```

The critical snapshot is immediately after `BURST_ALLOC` and before `HOTSET_RETOUCH`.

## No intervention

OBS-002 must not use:

- `madvise`;
- `mlock`;
- application priority hints;
- a coordination agent;
- kernel modifications.

It is observation only.
