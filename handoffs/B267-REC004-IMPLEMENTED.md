# Bounce Handoff

> **Bounce ID:** B267
> **Status:** COMPLETE / REC-004 IMPLEMENTED / NOT LAUNCHED

Implemented paired measurement-hygiene validation.

Important hygiene change:

- cold residency verification runs outside the measured transient unit;
- no pre-scan mincore occurs inside the measured cgroup;
- measured unit captures post_scan_pre_observer;
- then runs the historical _file_residency observer;
- then captures post_scan_post_observer.

Frozen study:
- sizes 96 / 192 / 384 MiB
- DONTNEED 64 MiB
- hot anon 64 MiB
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- 4 blocks
- 12 trials

No launch marker exists.

Next: read B267 ordinary CI exactly once.

Hosted research only.
