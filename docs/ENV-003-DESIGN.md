# ENV-003 Design Council — Anonymous Pageout Capability

> **Status:** FROZEN DESIGN

## Bounce objective

Determine whether the GitHub-hosted Linux runner can apply a bounded, non-destructive anonymous-memory pageout operation predictably enough to support a later semantic-region mechanism experiment.

## Why a capability probe first

The next candidate mechanism test needs the same nominal amount of memory to be removed from one of two semantic regions.

Before using that operation scientifically, the repository must establish that the hosted runner:

- supports the operation;
- actually reduces residency in the requested anonymous range;
- preserves contents;
- permits the pages to become resident again on access;
- does not require whole-runner pressure.

## Pseudo-Council

### Kernel / VM reviewer

Use Linux `MADV_PAGEOUT` on anonymous private `mmap` memory.

The Linux manual describes this advice as reclaiming pages in the requested range; anonymous pages are swapped out.

### Measurement reviewer

Run the probe under a deliberately low-pressure cgroup condition.

Use `mincore(2)` only to verify the probe itself:

```text
resident before
resident after pageout
resident after retouch
```

The later primary mechanism outcome must not depend on pre-retouch `mincore`.

### Data-integrity reviewer

The operation must be non-destructive.

Record a deterministic content digest before pageout and verify the same contents after the region is faulted back in.

### Falsification reviewer

Do not use this mechanism in the next scientific experiment if:

- the call is unavailable;
- residency does not change meaningfully;
- contents change;
- behavior differs radically across independent hosted runners.

### Scope reviewer

ENV-003 is a capability/efficacy probe, not a memory-policy experiment.

## Frozen design

Hosted runner blocks:

```text
4
```

Within each block:

```text
hot-set target x1
burst target   x1
```

Cgroup:

```text
MemoryHigh = 256 MiB
MemoryMax  = 320 MiB
```

Workload mappings:

```text
hot set = 64 MiB
burst   = 96 MiB
```

Explicit pageout target:

```text
16 MiB
```

The 16 MiB range is page-aligned and begins at the start of the selected mapping.

## Required observations

For the target region:

- total pages;
- resident pages before pageout;
- resident pages after pageout;
- resident pages after retouch;
- pageout call duration;
- time until the minimum observed residency snapshot;
- swap usage before/after;
- retouch latency;
- content digest before/after;
- syscall return / errno;
- kernel and cgroup provenance.

## Capability classification

Do not force one arbitrary success threshold into a scientific claim.

Report:

- **UNAVAILABLE** — the operation cannot be invoked successfully;
- **EFFECTIVE** — the requested range shows substantial residency reduction and data integrity is preserved;
- **PARTIAL** — the call succeeds but residency reduction is weak or inconsistent.

The fresh post-run Council decides whether observed efficacy is sufficient for the later matched-region experiment.

## Authority boundary

ENV-003 cannot establish that page identity causes application latency.

It only validates a research instrument.

## References

- Linux madvise(2): MADV_PAGEOUT reclaims the specified range and swaps anonymous pages.
- Linux mincore(2): reports page residency snapshots for the calling process.
