# OBS-001 Initial Finding

> **Status:** INITIAL FINDING  
> **Run:** 36213933759  
> **Source commit:** `e402a8fecd71d97ce8e3e85e1c4c50e22b86aacb`

## Result

OBS-001 passed every declared synchronization and safety check.

The controlled workload exposed explicit application phases while reading cgroup memory state at the same event boundaries.

## Selected observations

| Phase | memory.current | swap.current | memory.events high | pgscan | pgsteal | phase latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BASELINE | 7,192,576 | 0 | 0 | 0 | 0 | — |
| HOTSET_ALLOC | 74,301,440 | 0 | 0 | 0 | 0 | 6.8 ms |
| HOTSET_TOUCH | 74,301,440 | 0 | 0 | 0 | 0 | 3.1 ms |
| BURST_ALLOC | 166,608,896 | 11,603,968 | 5 | 4,270 | 2,188 | 27.2 ms |
| HOTSET_RETOUCH | 167,763,968 | 78,086,144 | 165 | 53,687 | 18,781 | 486.7 ms |
| BURST_RELEASE | 74,575,872 | 73,891,840 | 165 | 53,687 | 18,781 | 213.4 ms |

The cgroup used `MemoryHigh = 160 MiB` and `MemoryMax = 256 MiB`.

No OOM event occurred.

## What this establishes

The project can now place application-semantic state transitions and OS/cgroup memory transitions on the same monotonic timeline.

The observed pressure episode coincided with:

- `memory.high` events;
- swap growth;
- scan/steal activity;
- increased page-fault count;
- a large latency increase during the hot-set retouch phase.

## What this does not establish

The current run does **not** prove that reclaim or swap caused the latency increase.

There is not yet a matched low-pressure control distribution, repeated trial distribution, or causal intervention.

## Next research question

CHAR-001 should compare the same workload across controlled memory-pressure budgets and repeated trials.

The immediate goal is to distinguish:

```text
coincident pressure signal
        from
reproducible performance bottleneck
```

Only after that comparison should the project identify a mechanism-specific target.
