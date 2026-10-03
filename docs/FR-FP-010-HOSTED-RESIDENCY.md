# FR-FP-010 — Hosted physical trajectory residency lifecycle

Status: **HOSTED PHYSICAL CANDIDATE**

Parent: **FR-FP-009**

## Why

FR-FP-002 through FR-FP-009 built a synthetic theory of semantic reclaimability,
deadline feasibility, and reclaimability survival.

The next step is not another synthetic policy.

It is to test whether a semantic lifecycle signal can actually change resident
memory on Linux when it closes real mappings.

## Fixture

Each trajectory state is an 8 MiB anonymous private mmap.

Every OS page is touched so the state is physically faulted into the process.

Twelve states are generated.

Frozen safe step:

    6

Two arms run on the same hosted Linux CI process.

### FULL_TRAJECTORY

Retain all twelve mappings.

Logical peak:

    96 MiB

### GATED_ENDPOINT

Retain history through safe step 6.

At the safe event:

- close every old mapping;
- retain the current endpoint mapping.

For later steps:

- create the new current state;
- close the previous endpoint state.

Logical pre-action peak:

    48 MiB

Final live trajectory:

    one 8 MiB mapping

## Observation

Read process-scoped Linux status fields:

- VmRSS;
- RssAnon;
- RssFile;
- RssShmem.

The qualification uses VmRSS peak delta as the primary physical comparison.

Absolute RSS is not frozen because the hosted runner and Python baseline can
vary.

The physical contract instead requires:

- FULL faults a material fraction of the expected 96 MiB;
- GATED physical peak is less than 70% of FULL physical peak;
- GATED ends with one live mapping;
- GATED final RSS delta is lower than FULL final RSS delta.

## Evidence boundary

The semantic safe step is synthetic.

The following are physical:

- anonymous mmap allocation;
- page faults;
- mapping close;
- process RSS observations;
- hosted Linux kernel memory behavior.

Therefore this PR may establish a hosted physical lifecycle mechanism, but not:

- a local development-machine result;
- a model/KV-cache result;
- SSD performance;
- application correctness;
- universal Linux reclaim behavior.

## Why this matters

If the hosted physical gate passes, the research chain becomes:

    semantic event definition
      -> synthetic deadline theory
      -> survival-law compression
      -> real mapping lifecycle
      -> physical resident-footprint change

That is a stronger bridge toward the North Star than another abstract memory
score.

## Claim ceiling

**HOSTED_LINUX_ANONYMOUS_MMAP_RESIDENCY_LIFECYCLE_ONLY**
