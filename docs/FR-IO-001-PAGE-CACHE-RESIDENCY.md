# FR-IO-001 — File-backed Page-cache Residency

Status: **HOSTED LINUX PHYSICAL EXPERIMENT**

Parent: **FR-REMAT-001**

## Question

If semantic state is "on SSD", is it absent from RAM?

No.

A file can be backed by storage while its pages are simultaneously resident in
the Linux page cache.

That distinction matters for every out-of-core design.

## Source-grounded primitives

### `mincore()`

Linux `mincore()` returns page-by-page residency information for a mapped
virtual-memory range.

A resident page can be accessed without first requiring disk I/O.

FR-IO-001 uses `mincore()` as the primary physical residency measurement.

### `POSIX_FADV_DONTNEED`

Linux documents `POSIX_FADV_DONTNEED` as advice that the specified file region
will not be needed soon and says the kernel attempts to free associated cached
pages.

It is advisory, not a hard eviction command.

### `MADV_COLD` / `MADV_PAGEOUT`

Linux also exposes memory-range advice that can make pages colder or request
reclaim.

This lane does not invoke those operations.

They remain future controlled experiments.

## Frozen physical protocol

Four repetitions.

Each repetition:

1. create a fresh 32 MiB clean file;
2. `posix_fallocate()` backing storage;
3. issue `POSIX_FADV_DONTNEED`;
4. map the file;
5. measure initial residency with `mincore()`;
6. read one byte from every page;
7. measure residency again;
8. unmap;
9. issue `POSIX_FADV_DONTNEED`;
10. remap without touching;
11. measure residency again.

No sysfs setting is changed.

## Qualification gates

Each repetition must satisfy:

[
R_{cold}le0.10
]

[
R_{touch}ge0.95
]

[
R_{after DONTNEED}le0.25.
]

These are experiment qualification gates, not universal kernel guarantees.

## Why this matters

An application may say:

```text
weights -> SSD
```

but the real physical path can become:

```text
SSD backing
    ↓ read
page cache in RAM
    ↓ map / copy
application working set
```

So:

[
oxed{
	ext{backing tier}

eq
	ext{current residency tier}
}
]

and:

[
oxed{
	ext{offloaded bytes}

eq
	ext{RAM-free bytes}
}
]

## Interaction with Strata / out-of-core inference

This explains why unbuffered or carefully managed file tiers can matter.

An SSD-backed expert system that allows the ordinary page cache to grow without
budget accounting may accidentally maintain:

- explicit resident state;
- file-cache copies;
- staging buffers;

at the same time.

That is a hidden (P+X) tax in the FR-ATOM memory equation.

## Next

### FR-IO-002

Compare matched read paths:

- mmap/page cache;
- pread;
- optional `O_DIRECT` where the filesystem and alignment permit;
- sequential/readahead policies.

Measure:

- resident page fraction;
- process RSS/PSS;
- read latency;
- CPU time;
- bytes read;
- page-fault counts.

### FR-COMP-001

Then attack compressed RAM as its own resource:

`compression ratio × CPU × latency tail × reclaim benefit`.

## Claim ceiling

**HOSTED_LINUX_CLEAN_FILE_PAGE_CACHE_RESIDENCY_ONLY**
