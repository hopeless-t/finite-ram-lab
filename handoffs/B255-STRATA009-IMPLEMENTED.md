# Bounce Handoff

> **Bounce ID:** B255
> **Status:** COMPLETE / STRATA-009 IMPLEMENTED / NOT LAUNCHED

Implemented the frozen dataset-over-MemoryMax bounded-policy study.

Files:

- spec
- scheduler/trial/aggregate module
- Ubuntu 26.04 workflow
- tests

Frozen execution remains:

- cold file 384 MiB
- MemoryMax 320 MiB
- MemoryHigh 160 MiB
- hot anon 64 MiB
- DONTNEED 64 / 72 / 80 / 88 / 96
- 4 blocks
- 20 trials
- Recorder 98 records/trial
- no buffered arm

No launch marker exists.

Next: read ordinary CI exactly once. Success permits a separate explicit launch.

Authority remains hosted repository/research only.
