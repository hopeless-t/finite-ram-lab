# FR-FP-012 Receipt

Status: **PASS / HOSTED CALIBRATED HOT BUDGET WITH DURABLE FILE COLD SPILL QUALIFIED**

Parent: **FR-FP-011**

Successful run:
- workflow run: 37144897005
- job: 111266699570
- execution head: 7cd6f4f84683b40c7a033e306937266ef8e8af24

Preceding implementation failure:
- workflow run: 37144791432
- root cause: exported memoryview prevented mmap close
- scientific hypothesis was not reached
- fixed with bounded 1 MiB write copies; scientific contract unchanged

Frozen fixture:
- state size: 8 MiB
- process trajectory RSS budget: 32 MiB
- calibrated hot-state budget: 4
- trajectory length: 12
- synthetic safe step: 9

Physical hot/cold result:
- peak hot states: 4
- peak process VmRSS delta: 34,300 KiB = 33.496 MiB
- peak process RssAnon delta: 34,300 KiB
- spilled states: 5
- spilled bytes: 41,943,040 = 40 MiB
- peak cold-file bytes: 40 MiB
- all durable spill sentinels verified before hot mmap close: PASS
- total measured spill time: about 229.4 ms
- mean measured spill time per 8 MiB state: about 45.9 ms

Safe collapse:
- final hot states: 1
- final cold files: 0
- final process VmRSS delta: 9,724 KiB = 9.496 MiB

Critical accounting split:

cgroup memory.current was available.

- baseline memory.current: 1,042,522,112 bytes
- peak delta: 78,376,960 bytes = 74.746 MiB
- final delta: 9,936,896 bytes = 9.477 MiB

Interpretation:

The calibrated spill policy successfully bounded the process resident trajectory
set near the 32 MiB target.

However, durable regular-file spill did not immediately remove the cold bytes
from the same cgroup's memory pressure. The file-backed cold tier was still
represented in memory.current, consistent with page-cache charging.

Therefore:

    process RSS budget
    !=
    cgroup total-memory budget

and:

    durable file spill
    !=
    immediate physical RAM release

Decision:

**CONVERT_CALIBRATED_RSS_BUDGET_TO_HOT_STATE_BUDGET_AND_SPILL_LIVE_HISTORY_BEFORE_ALLOCATING_THE_NEXT_STATE**

Next:

Apply the already-researched STRATA POSIX_FADV_DONTNEED primitive after fsync
and compare cgroup memory.current while preserving the durable cold files.

Claim ceiling:

**HOSTED_LINUX_PROCESS_RSS_BUDGET_AND_FILE_COLD_SPILL_ONLY**
