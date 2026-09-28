# Bounce Handoff

> **Bounce ID:** B271
> **Status:** COMPLETE / REC-004 PASS / PRE-OBSERVER FLOOR CONTRACT ADOPTED

REC-004 run `36443845901`: PASS, 12/12.

Clean pre-observer non-hot-floor medians:

- 96 MiB: 12.6875
- 192 MiB: 12.8046875
- 384 MiB: 12.935546875

Clean median span: 0.248046875 MiB.

Post-observer median span: 0.369140625 MiB.

Only 1/4 of 384 MiB trials showed a +256 KiB paired observer delta; 96 and 192 had 0/4 positive.

Block-level clean floor is not monotonic across capacity, so no smooth capacity law is accepted.

Prospective measurement contract:
- pre-observer floor = workload floor
- post-observer floor = diagnostic only
- cold verification outside measured cgroup
- historical raw evidence unchanged

Next: freeze a queryable cross-experiment SQL evidence corpus.

Hosted research only.
