# FR-FP-014 — Warm versus cold restore pilot

Status: **HOSTED PHYSICAL RESTORE PILOT**

Parent: **FR-FP-013**

## Why

FR-FP-013 showed that POSIX_FADV_DONTNEED can preserve a durable cold file while
reducing same-cgroup page-cache pressure.

That is a memory win.

But a tier policy cannot optimize memory alone.

If an older state is needed again, a nonresident cold file may cost more to
restore than a page-cache-resident warm file.

FR-FP-014 measures that cost instead of assuming its direction or magnitude.

## Paired design

Eight paired blocks.

Each block creates the same 8 MiB state twice.

### WARM_PAGECACHE

- write;
- fsync;
- verify;
- close source anonymous mmap;
- leave file pages resident.

### COLD_DONTNEED

- write;
- fsync;
- verify;
- close source mmap;
- POSIX_FADV_DONTNEED;
- wait for advice accounting to settle.

Arm order alternates by block.

## Before restore

Use the existing STRATA mincore-based file-residency observer.

Qualification requires:

- WARM resident fraction >= 95%;
- COLD resident fraction <= 10%.

This proves the two arms are physically distinct before timing the restore.

## Restore

Allocate a fresh 8 MiB anonymous mmap and preadv the full state into it.

Measure:

- mmap allocation time;
- read time;
- total restore time;
- VmRSS / RssAnon delta;
- full byte count;
- sentinel integrity.

File residency is observed again after restore.

## Latency is not pre-ranked

v0.1 does not fail merely because COLD is not slower.

The pilot first establishes:

- true physical residency separation;
- correct restoration;
- paired latency observations.

Only after seeing the distribution should the lab decide whether a stronger
latency law or replication campaign is justified.

This avoids freezing folklore such as "disk is always slower" into the
scientific gate without measurement.

## Governor consequence

Tier selection requires at least two axes:

    residency / pressure cost
    restore cost

A state that is cheap to evict but expensive to restore may belong in WARM
rather than COLD when reuse probability is high.

This begins the bridge toward an expected-cost tier Governor.

## Claim ceiling

**HOSTED_LINUX_WARM_COLD_RESTORE_PILOT_ONLY**
