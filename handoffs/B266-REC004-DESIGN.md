# Bounce Handoff

> **Bounce ID:** B266
> **Status:** COMPLETE / REC-004 HYGIENE DESIGN FROZEN

REC-003 established size-dependent observer contamination.

REC-004 freezes a paired within-trial validation:

- capacities 96 / 192 / 384 MiB
- Ubuntu 26.04
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- DONTNEED 64 MiB cadence only
- 4 blocks
- 12 trials

Each trial records:
- post_scan_pre_observer
- existing residency observer
- post_scan_post_observer

Primary metric:
`observer_current_delta = post - pre`.

Historical raw evidence is not rewritten.

Next: implement REC-004 only. Do not launch in implementation bounce.

Hosted research only.
