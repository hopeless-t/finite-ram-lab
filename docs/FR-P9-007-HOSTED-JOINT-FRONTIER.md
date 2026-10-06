# FR-P9-007 — Hosted same-surface residency × concurrency frontier

Status: **HOSTED JOINT PROXY / PART 9**

Parent: **FR-P9-006**

## Why this experiment exists

FR-P9-006 established a synthetic composition failure:
independently attractive concurrency and residency choices can violate one shared
finite-memory constraint when composed.

That result was intentionally bounded because its worker and residency shapes
came from different experimental surfaces.

FR-P9-007 removes that comparability gap.

The same hosted runner now measures all six combinations:

```text
workers = {1,2,4}
residency = {KEEP_WARM, FAULT_IN}
```

under one payload, one job set, one PSS metric, and one barrier protocol.

## Same-surface protocol

Frozen fixture:

- GitHub-hosted Ubuntu 24.04;
- deterministic 8 MiB immutable capability;
- 12 deterministic jobs;
- six SHA256 rounds per job;
- worker counts 1, 2, 4;
- two repetitions;
- target idle gap 0.20 s;
- six combinations in forward order, then exact reverse order.

Every process uses the same read-only mmap capability once active.

## Three barriers

### 1. READY

`KEEP_WARM` workers map, touch, and SHA256-verify the capability before READY.

`FAULT_IN` workers reach READY without mapping the capability.

The parent samples summed worker PSS here:

```text
prestart_pss_kib
```

This is the idle-phase residency surface.

### 2. LOAD / RESUME

After the idle gap, the parent opens the load barrier.

- KEEP_WARM already has the capability and reports zero child resume work.
- FAULT_IN maps, touches, and verifies the same capability.

After all workers report LOADED, the parent samples:

```text
active_pss_kib
```

and records the joint resume delay.

### 3. WORK

Only after all workers are capability-ready does the parent open the common work
barrier.

Each deterministic job emits a digest keyed by job ID. The full job->digest map
must be identical across all six arms and both repetitions.

## Typed cost vector

No synthetic score is used.

```text
C = (
  prestart_pss_kib,
  active_pss_kib,
  resume_ns,
  work_wall_ns,
  p95_sojourn_ns,
  logical_fault_span_bytes,
  idle_capability_byte_seconds
)
```

The frontier is computed only after semantic equality is established.

## Fault-span boundary

For FAULT_IN, every worker maps and touches the full capability after the resume
barrier.

The experiment therefore reports:

```text
logical_fault_span_bytes = payload_bytes * worker_count
```

This is **not** measured SSD/NVMe traffic.

Shared page cache or filesystem behavior may make physical traffic much smaller
than the logical per-worker span. The experiment deliberately does not infer
hardware I/O from this number.

## Idle byte-time boundary

KEEP_WARM reports capability byte-time across the measured idle gap:

```text
payload_bytes * observed_idle_seconds
```

Because the immutable capability is shared, this is one logical capability
surface, not N private copies.

The actual process-sharing-aware resident footprint is separately represented by
summed PSS.

## Frozen qualification gates

The experiment passes only if:

- capability identities are stable;
- job identities are stable within each arm;
- all six arms produce exactly the same job digest map;
- FAULT_IN has lower prestart PSS than KEEP_WARM at N=1,2,4;
- KEEP_WARM has zero logical fault span;
- FAULT_IN has positive fault span and positive resume work;
- KEEP_WARM pays positive idle capability byte-time;
- the typed Pareto frontier is non-empty;
- no joint winner is preregistered;
- no scalar gain is invented.

The memory-direction gate is preregistered before hosted execution. If it fails,
the gate is not relaxed after seeing the result.

## Decision rule

```text
PLAN_RESIDENCY_AND_CONCURRENCY_ON_ONE_MEASURED_SURFACE
DO_NOT_IMPORT_CROSS_PROXY_OPTIMA_AS_IF_PHYSICALLY_COMPOSABLE
```

This does not mean the hosted proxy yields a universal policy. It means a future
planner may now reason from one internally comparable evidence surface instead
of joining unlike measurements and silently promoting them to physical truth.

## Part 9 accumulation

```text
P9-001  minimum sufficient semantic projection
P9-002  resource-certificate replan
P9-003  phase-residency typed frontier
P9-004  private-vs-shared parallelism residency tax
P9-005  shared-capability concurrency frontier
P9-006  synthetic joint-composition falsifier
P9-007  same-surface hosted joint frontier
```

The emerging compiler is no longer a RAM eviction policy. It is a constrained
materialization compiler over:

- semantic requirement;
- representation;
- placement;
- lifetime/phase;
- concurrency;
- evidence freshness;
- verification and recovery obligations.

## Authority boundary

A resource-preferred joint plan does not authorize execution or external side
effects.

`authority_effect = NONE`

## Claim ceiling

`HOSTED_GITHUB_LINUX_SAME_SURFACE_PSS_AND_LATENCY_PROXY_ONLY_NO_UNIVERSAL_JOINT_POLICY_OR_DEVICE_IO_CLAIM`

## Next falsifier

FR-P9-008 should add an explicit finite PSS admission cap and intentionally
change the observed resource certificate between idle and work phases.

The joint planner must then demonstrate:

```text
plan joint policy
    -> idle/materialize
    -> observe changed resource certificate
    -> reject stale joint plan if needed
    -> replan residency + concurrency together
    -> preserve semantic job results
```

This reconnects the joint planner to the P9-002 replan invariant instead of
allowing Part 9 to become a static benchmark table.
