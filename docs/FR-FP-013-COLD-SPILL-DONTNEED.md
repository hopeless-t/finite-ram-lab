# FR-FP-013 — Release cold-spill page cache with DONTNEED

Status: **HOSTED PHYSICAL PAGE-CACHE CANDIDATE**

Parent: **FR-FP-012**

## Failure found by FR-FP-012

FR-FP-012 successfully bounded process RSS, but the same cgroup still reached a
memory.current delta of about 74.75 MiB.

The hot process held only about 33.5 MiB RSS.

The difference was the file-backed cold tier remaining in page cache.

Therefore:

    process RSS control
    !=
    same-cgroup memory-pressure control

## Existing primitive

This repository already qualified POSIX_FADV_DONTNEED in the STRATA research
line for releasing consumed COLD file-cache ranges.

FR-FP-013 bridges that existing primitive into semantic cold spill instead of
inventing a new mechanism.

## Arms

PLAIN_FSYNC
: write each 8 MiB cold state, fsync, verify, unmap the hot source.

DONTNEED_AFTER_FSYNC
: perform the same durable write and verification, then advise the full
  page-aligned file range with POSIX_FADV_DONTNEED.

Both arms retain the cold file until the synthetic safe step.

DONTNEED changes cache residency, not durable state lifetime.

## Transient pressure is observed

The experiment records memory.current:

- after fsync while the source mmap is still hot;
- after source unmap;
- after DONTNEED;
- after the next hot allocation.

This prevents the experiment from hiding a transient peak that occurs before
cache advice.

## Frozen gate

The primary physical gate is comparative:

    peak memory.current delta with DONTNEED
      <
    75% of the plain-spill peak delta

Both arms must also:

- obey the four-state process hot budget;
- obey the process RSS budget margin;
- write and verify all five cold states;
- keep the same 40 MiB logical cold history;
- end with one hot state and zero cold files.

## Why this matters

A useful COLD tier must separate three concepts:

1. durable state existence;
2. process residency;
3. cgroup / system cache residency.

FR-FP-012 separated 1 from 2.

FR-FP-013 tests whether DONTNEED can separate 1 from 3 in the same hosted
fixture.

If it passes, the memory hierarchy becomes physically closer to:

    HOT semantic state
      -> anonymous resident memory

    COLD durable state
      -> file exists
      -> page cache may be evicted

without deleting the cold state itself.

## Claim ceiling

**HOSTED_LINUX_CGROUP_PAGE_CACHE_RELEASE_FOR_THIS_COLD_SPILL_FIXTURE_ONLY**
