# REC-003 Residency Observer Footprint Design v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Motivation

STRATA-007/008/009 produced a robust unchanged knee while cold capacity scaled:

- 96 MiB
- 192 MiB
- 384 MiB

However, the measured post-scan non-hot floor increased by about 0.2421875 MiB at each capacity doubling.

The post-scan sequence is measured only after `_file_residency()`, which:

1. mmaps the entire file;
2. creates a ctypes view over the mapping;
3. allocates a one-byte-per-page mincore vector;
4. calls `mincore`;
5. counts the vector;
6. closes the mapping.

The fine floor trend may therefore include observer footprint.

## Question

How much transient and retained cgroup memory does the residency observer itself consume as target-file size scales?

## Sizes

Measure:

- 96 MiB
- 192 MiB
- 384 MiB

These exactly match the existing capacity series.

## Isolation

Each observer trial runs in a fresh transient systemd unit.

File preparation occurs before the measured unit and is followed by POSIX_FADV_DONTNEED.

No streaming workload.
No hot anonymous allocation.
No Recorder sampling inside the observer phases beyond compact cgroup snapshots.

## Phase snapshots

Capture `memory.current` and selected `memory.stat` fields at:

1. baseline after Python startup;
2. after mmap creation;
3. after ctypes char-buffer view creation;
4. after mincore vector allocation;
5. immediately after mincore;
6. after resident-page counting;
7. after deleting the ctypes view and closing mmap;
8. after `gc.collect()` plus a short settle interval.

Also capture final `memory.peak`.

Selected memory.stat fields:

- anon
- file
- kernel
- pagetables
- slab
- sock
- shmem

## Outcomes

For each size derive:

- peak minus baseline current;
- post-cleanup minus baseline current;
- post-GC-settle minus baseline current;
- per-phase current deltas;
- per-phase pagetable/kernel/anon/file deltas;
- mincore vector bytes = file_pages bytes.

## Trial budget

- 3 file sizes
- 4 independent runner blocks
- 12 trials

## Interpretation rules

### Observer-size effect

If retained or peak deltas increase with target-file size, the fine STRATA post-scan floor trend is at least partly observer-induced.

### No observer-size effect

If observer deltas remain flat while STRATA floors rise, the fine floor trend remains a workload/substrate candidate.

### Mixed

If only transient peak scales but post-GC retained delta is flat, keep the knee result and prefer a post-cleanup floor measurement in future studies.

## Pseudo-Council

- **Measurement:** inspect the instrument before promoting a sub-MiB law.
- **Systems:** preserve the exact mmap/mincore mechanics used by the current observer.
- **Causal inference:** remove streaming and hot allocations; vary target size only.
- **Statistics:** four fresh units per size are enough for a directional observer audit.
- **Authority:** this is hosted measurement only and grants no local execution or memory policy.

Consensus:

**freeze REC-003 as an observer-only 96/192/384 MiB footprint audit.**

## Launch boundary

Design only.
Implementation and launch are separate bounces.
No local-PC execution.
