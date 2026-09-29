# MEMCG-005G-C Controlled Rare Induction v2 — PTE-Preconditioned Spawn

> **Status:** IMPLEMENTED-CANDIDATE / CI PENDING / NOT LAUNCHED
> **Primary arm:** b63
> **Authority:** HOSTED_RESEARCH_ONLY
> **Supersedes:** v1 for the next controlled-spawn pilot

## Scientific question

Can a verified Q64 batch be transformed into an exact chosen residual-stock phase once target-time page-table allocation is removed?

## Worker requirements

A dedicated induction worker may differ from MEMCG-005D because this is a construction experiment, not a layout-comparison experiment.

Required capabilities:

1. anonymous VMA of 1024 pages;
2. expose VMA base address;
3. choose a 128-page safe span inside one PTE table;
4. expose guard and sequence page indexes;
5. on Prep CPU P, touch the guard before stock-CPU migration;
6. accept one controller GO per explicit sequence page;
7. report observed CPU, touched count, and errors.

The worker must not autonomously perform the Q64/bait loop; the controller measures each touch.

## CPU topology

Require at least 3 CPUs:

- controller C
- prep P
- stock S

C, P, S must be distinct.

## PTE preparation

Before READY_FOR_MIGRATION:

- map VMA;
- choose safe span;
- record region base and safe-span geometry;
- touch guard on P;
- report VmPTE-compatible geometry receipt.

Controller records VmPTE after guard.

After migration to S, VmPTE must remain stable throughout the measured sequence.

## Primer

Sequentially touch fresh calibration pages on S.

For each:

- memory.current pre/post/delta;
- VmPTE pre/post/delta;
- CPU receipt.

Stop calibration at first Q64 in the frozen Q64 window.

That page is primer page 1 of the new batch.

If the bounded calibration page budget expires first:

`PRIMER_NOT_FOUND`

No retry within identity.

## Arms

Randomize by block.

### b62
After primer, consume 61 additional bait pages.

Then:
- target expected 0
- next1 expected 0
- next2 expected Q64

### b63
After primer, consume 62 additional bait pages.

Then:
- target expected 0
- next1 expected Q64

### b64
After primer, consume 63 additional bait pages.

Then:
- target expected Q64

All pages belong to the preconditioned PTE span.

## Pilot scale

Frozen first physical pilot design:

- 8 hosted blocks
- 9 raw scientific identities per block
- 3 identities/arm/block
- **72 raw candidates total**
- **24 raw candidates/arm**
- replacement trials: **false**

Primer discovery failures, PTE contamination, CPU errors, and phase failures remain part of the 72 outcomes.

Do not add replacement identities to reach a desired number of valid specimens.
Do not dynamically increase the candidate ceiling after observing scientific outcomes.

## Primary decision

Mechanism support requires:

1. zero CPU mismatches among counted trials;
2. zero measured-phase PTE growth among exact-recovery trials;
3. arm phase ordering consistent with:
   - b62 depth2
   - b63 depth1
   - b64 target boundary;
4. no unexplained nonzero non-Q64 morphology dominating failures.

Pilot is not a reliability certification.

## Reliability follow-up

Only after pilot mechanism support:

run b63-only fixed-N reliability stages.

Suggested checkpoints:

- 59 primer-qualified successes for >95% one-sided lower bound if no failures;
- 299 for >99% lower bound if no failures.

A single failure changes the bound and must remain visible.

## Evidence residency

Use EVIDENCE-RESIDENCY v1.

- raw blocks HOT: 7 days
- aggregate HOT: 30 days
- full raw COLD: Google Drive and/or local
- restored-copy SHA verification before GitHub expiry is relied upon

## Safety / authority

No local-PC run.

No larger GitHub runner.

No paid resource.

No physical launch without a new Human-scoped launch receipt.

## Implementation

Worker:
`experiments/memcg005gc_spawn_worker.c`

Controller:
`src/finite_ram_lab/memcg005gc_controlled_spawn.py`

Frozen spec:
`specs/MEMCG-005G-C-PTE-PRECONDITIONED-SPAWN-v2.json`

Tests:
`tests/test_memcg005gc_controlled_spawn.py`

Workflow:
`.github/workflows/memcg-005g-c-v2-controlled-spawn.yml`

No launch marker exists.
