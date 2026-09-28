# Bounce Handoff

> **Bounce ID:** B249
> **Status:** COMPLETE / STRATA-008 IMPLEMENTED / NOT LAUNCHED

Implemented the frozen 192 MiB cold-capacity study:

- spec
- scheduler/trial/aggregate
- Ubuntu 26.04 workflow
- repaired systemd receipt using `systemd-run --version`
- regression tests

Important Recorder-density change:

The file is 192 MiB with 4 MiB checkpoints, so each trial emits 48 scan samples plus start/end = 50 REC-001 records. This is a mechanical consequence of the frozen checkpoint-per-chunk policy, not a change in observation semantics.

No launch marker exists.

Next: read ordinary CI exactly once; success permits a separate explicit launch.

Authority remains hosted research only; no local execution or memory-control policy.
