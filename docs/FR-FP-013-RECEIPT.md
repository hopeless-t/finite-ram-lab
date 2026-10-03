# FR-FP-013 Receipt

Status: **PASS / HOSTED COLD-SPILL PAGE-CACHE RELEASE QUALIFIED**

Parent: **FR-FP-012**

- workflow run: 37145139000
- job: 111267405393
- execution head: f4bbf6a6159849d7fd4c8deee7e09524f03e2a9d

Frozen fixture:
- state size: 8 MiB
- hot-state budget: 4
- process RSS budget: 32 MiB
- synthetic safe step: 9
- five durable cold states / 40 MiB

PLAIN_FSYNC:
- peak process RSS delta: 32 MiB
- peak cgroup memory.current delta: 76,808,192 bytes = 73.25 MiB
- final cgroup delta: 8,364,032 bytes = 7.977 MiB

DONTNEED_AFTER_FSYNC:
- peak process RSS delta: 32 MiB
- POSIX_FADV_DONTNEED calls: 5 / 5 successful
- peak cgroup memory.current delta: 42,205,184 bytes = 40.25 MiB
- final cgroup delta: 8,368,128 bytes = 7.980 MiB

Comparative result:
- DONTNEED / plain cgroup peak ratio: 0.549488
- cgroup peak reduction: 45.05%

Both arms:
- kept no more than four hot states;
- kept the same five 8 MiB durable cold files before safe collapse;
- verified every spill sentinel;
- ended with one hot state and zero cold files.

Interpretation:

Regular-file durability and page-cache residency are separable.

The cold file can continue to exist while POSIX_FADV_DONTNEED removes a large
fraction of its same-cgroup resident cache footprint.

The remaining DONTNEED peak includes the transient point after fsync while the
source anonymous mmap is still hot and the newly written file pages exist. This
peak is observed rather than hidden.

Decision:

**ADVISE_DURABLE_COLD_FILES_DONTNEED_WHEN_THE_GOAL_INCLUDES_SAME_CGROUP_MEMORY_PRESSURE**

Next:

Measure the restore cost of a WARM cached file versus a COLD DONTNEED file when
a previously spilled state must become hot again.

Claim ceiling:

**HOSTED_LINUX_CGROUP_PAGE_CACHE_RELEASE_FOR_THIS_COLD_SPILL_FIXTURE_ONLY**
