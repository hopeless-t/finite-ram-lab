# FR-P9-005 — Shared-capability concurrency frontier

Status: **HOSTED CONCURRENCY PROXY / PART 9**

Parent: **FR-P9-004**

## Why this experiment exists

FR-P9-004 isolated a real residency component of parallelism tax. In the hosted
PSS proxy, a 16 MiB immutable capability privately copied by four workers grew
almost exactly with worker count, while read-only shared mmap kept the
capability-associated summed PSS close to the one-worker level.

That result removes one tax. It does not prove that more workers are better.

Once immutable capability replication is shared, parallelism still pays for:

- worker/process residency;
- scheduling and queue structure;
- CPU/cache/memory-bandwidth contention;
- coordination;
- verification;
- phase transitions and faults.

FR-P9-005 therefore asks a narrower question:

> With the immutable capability already shared, what typed tradeoff appears
> across worker counts 1, 2, and 4 for one fixed batch of verified work?

## Hosted proxy

The dedicated GitHub-hosted Linux lane uses:

- Ubuntu 24.04;
- one deterministic 4 MiB read-only shared mmap capability;
- worker counts `1, 2, 4`;
- 12 deterministic jobs arriving at one start barrier;
- eight SHA256 rounds over the same capability per job;
- two repetitions;
- worker-count order ascending in one repetition and descending in the other.

The capability is prefaulted before the start barrier so this lane focuses on
concurrent useful work and residual process residency rather than cold loading.

Each job has a deterministic digest keyed by job ID. Qualification requires the
same complete job->digest map across every repetition and worker count.

## Observables

The typed vector is:

```text
C(N) = (
  total worker PSS,
  batch wall time,
  p95 queue wait,
  p95 service time,
  p95 sojourn time
)
```

where:

- queue wait = start(job) - common batch start;
- service = end(job) - start(job);
- sojourn = end(job) - common batch start;
- total PSS is sampled after workers map/prefault the capability but before the
  batch starts.

`jobs/sec` is also reported as a descriptive throughput projection, but the
Pareto test uses cost directions directly rather than mixing units.

## Why there is no frozen winner

The experiment intentionally does **not** preregister:

```text
4 workers must beat 2
2 workers must beat 1
```

Those would turn a measurement question into a benchmark expectation and make
runner topology an accidental universal law.

Instead, the hosted result is reduced to the non-dominated worker counts under
the typed vector.

A worker count is removed only when another measured count is no worse in every
cost dimension and strictly better in at least one.

## Decision rule

```text
SELECT_CONCURRENCY_FROM_A_MEASURED_TYPED_FRONTIER_OR_EXPLICIT_CONSTRAINTS
NOT_BY_MAXIMIZING_WORKER_COUNT
```

The lab does not emit a scalar gain:

```text
scalar_gain = null
```

A caller may later choose from the frontier using a real constraint such as:

- RAM/PSS ceiling;
- queue deadline;
- latency SLO;
- explicit resource price;
- power envelope.

Without that external requirement there is no universal optimal worker count.

## Relation to Part 9

The Part 9 decomposition is now:

```text
Canonical Semantic State
        ↓
Minimum Sufficient Projection       # P9-001
        ↓
Resource-Certified Placement        # P9-002
        ↓
Phase Residency Frontier            # P9-003
        ↓
Shared-vs-Private Parallelism Tax   # P9-004
        ↓
Typed Concurrency Frontier           # P9-005
```

This is becoming less like a RAM-only governor and more like a compiler for
**when, where, in what representation, and at what concurrency a verified
semantic projection should exist**.

## Cross-project bridge

### Strata / inference slots

Parallel slots can reduce queueing while increasing session and runtime state.
The worker-count frontier idea transfers as a test design, not as a claim about
Strata's current optimum.

### PCG

Chunk generation, collision validation, asset conversion, and background world
work can be treated as bounded jobs sharing immutable world rules/assets while
retaining private mutable work state. A later PCG experiment must measure frame
or generation outcomes independently.

### AI workers

Multiple workers can share immutable tool/policy/reference surfaces while worker
count is selected from a resource/performance frontier instead of being treated
as free scaling.

## Authority boundary

Shared capability residency and an admissible worker count are resource facts.
They do not authorize tool invocation or external effects.

`authority_effect = NONE`

## Claim ceiling

`HOSTED_GITHUB_LINUX_SHARED_MMAP_BATCH_CONCURRENCY_PROXY_ONLY_NO_UNIVERSAL_WORKER_COUNT_OR_APPLICATION_THROUGHPUT_CLAIM`

## Next falsifier

FR-P9-006 should couple concurrency and phase residency under a finite memory
budget.

Instead of independently choosing:

```text
worker_count
residency_policy
```

the planner should solve a joint typed frontier over combinations such as:

```text
(N=1, KEEP_WARM)
(N=2, KEEP_WARM)
(N=4, KEEP_WARM)
(N=1, FAULT_IN)
(N=2, FAULT_IN)
(N=4, FAULT_IN)
```

and test whether the independently optimal choices can become jointly
infeasible or dominated when memory pressure, fault-in traffic, and queueing are
coupled.
