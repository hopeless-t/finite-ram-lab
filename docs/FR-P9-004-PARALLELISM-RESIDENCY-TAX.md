# FR-P9-004 — Parallelism residency tax

Status: **HOSTED PSS PROXY / PART 9**

Parent: **FR-P9-003**

## Why this experiment exists

FR-P9-003 showed that keeping a capability WARM and faulting it back in are not
universally ordered without an external price or hard constraint. Both remain
valid typed Pareto alternatives.

The next source of hidden residency is parallelism itself.

A system may increase worker count, slots, agents, generators, or concurrent
requests and accidentally replicate the same immutable capability/context state
inside every worker.

The important distinction is:

```text
parallel workers
    !=
private copies of every capability
```

FR-P9-004 isolates only the residency component of this problem.

## Research question

> If N workers need the same immutable capability, how much resident-state tax is
> created by PRIVATE_COPY, and how much can verified shared immutable backing
> remove?

## Hosted proxy

The dedicated GitHub-hosted Linux experiment uses:

- Ubuntu 24.04;
- a deterministic 16 MiB immutable capability payload;
- worker counts `N={1,4}`;
- three repetitions;
- rotated arm ordering;
- fresh child processes per arm;
- `/proc/<pid>/smaps_rollup` PSS as the process-sharing-aware residency metric;
- SHA256 equality as the semantic gate.

Three arms are measured for the same worker count.

### BASELINE

Worker process with only a tiny placeholder object.

This estimates the process/runtime residency that should not be charged to the
capability itself.

### PRIVATE_COPY

Each worker reads the payload into a private mutable `bytearray`, touches pages,
and verifies the same SHA256 digest.

### SHARED_MMAP

Each worker opens the same file through a read-only `mmap`, touches pages, and
verifies the same SHA256 digest.

The file-backed mapping is intentionally immutable from the experiment's point
of view.

## Metric

For every arm:

```text
total_pss(N) = sum(worker PSS)
```

Capability-associated normalized growth is:

```text
Growth_private(N)
  = median(total_pss_PRIVATE_COPY(N))
  - median(total_pss_BASELINE(N))

Growth_shared(N)
  = median(total_pss_SHARED_MMAP(N))
  - median(total_pss_BASELINE(N))
```

PSS is chosen because shared physical pages are divided across mappings rather
than charged in full to every process, unlike naive summed RSS.

This still remains a hosted Linux process-memory proxy. It is not a universal
hardware-memory accounting law.

## Frozen gates

The first qualification asks only whether the residency effect is large enough
to survive a coarse hosted proxy.

- all private/shared capability digests must match the frozen payload;
- one-worker private/shared normalized growth must both be positive;
- private growth from 1 -> 4 workers must scale by at least 2.5x;
- shared growth from 1 -> 4 workers must scale by at most 2.0x;
- four-worker shared growth must be at most 60% of four-worker private growth.

These are preregistered fixture gates, not universal constants.

If they fail, the lab does not relax them after seeing the result. A failure can
mean either the proxy is too noisy or the sharing hypothesis is weaker than
expected; those cases must be diagnosed separately.

## What this does not measure

FR-P9-004 deliberately does **not** claim that shared mmap is faster or that more
workers are better.

The larger systems objective is:

```text
NetParallelGain
  = QueueReduction
  + UsefulConcurrency
  - ResidencyTax
  - Contention
  - Coordination
  - VerificationOverhead
```

This PR measures only the `ResidencyTax` component.

A shared mapping can reduce PSS while increasing page-fault pressure,
coordination, cache contention, or latency. Those dimensions remain outside this
claim.

## Cross-project interpretation

### Strata / inference slots

More parallel slots can reduce queue wait while increasing session state,
expert/cache pressure, and other per-slot residency. Immutable model/capability
state should not be assumed to require per-slot private copies.

This is an architectural analogy only; FR-P9-004 does not measure Strata.

### PCG

Concurrent chunk generators, validators, render workers, or asset processors may
share immutable recipes, rules, manifests, or source assets while retaining
private mutable work state.

This is a candidate bridge for a later independent PCG experiment, not a game
performance claim.

### AI Workers

Multiple workers may need the same tool schemas, immutable policy capsules,
reference indexes, or model artifacts. Replicating those surfaces per worker is
a candidate semantic-residency tax.

Again, shared availability is not execution authority.

## Authority boundary

```text
shared capability available
    !=
worker authorized to invoke it
```

`authority_effect = NONE`

## Claim ceiling

`HOSTED_GITHUB_LINUX_PROCESS_PSS_PROXY_FOR_PRIVATE_COPY_VS_SHARED_MMAP_ONLY_NO_UNIVERSAL_WORKER_OR_THROUGHPUT_CLAIM`

## Next falsifier

The next step must put the omitted positive and negative parallelism terms back
into the model.

A useful FR-P9-005 surface is:

- worker counts / slots;
- queue delay;
- useful completed work;
- PSS residency tax;
- shared-page fault/refault behavior;
- contention;
- coordination overhead;
- verifier cost.

Only then can the lab ask whether a larger worker count produces positive
`NetParallelGain` under a finite-RAM constraint.
