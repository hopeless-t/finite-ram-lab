# Bounce Handoff

> **Bounce ID:** B281
> **Status:** COMPLETE / MEMCG-001 QUANTIZATION DESIGN FROZEN

EVIDENCE-001 SQL corpus is operational.

MEMCG-001 freezes a direct test of the 64-page / 256-KiB memcg charge-batch candidate.

Hosted design:
- Ubuntu 26.04
- C worker
- fresh cgroup per trial
- CPU pinning
- 4096-byte page requirement
- 256 one-page steps
- touch vs no-touch control
- 4 blocks
- 8 trials

Math:
- first differences
- jump histogram
- lattice search Q={1,2,4,8,16,32,64,128}
- modulo phase search
- jump spacing/change points
- autocorrelation
- control comparison

H64 is preregistered but can be rejected.

Next: implement MEMCG-001 only. Do not launch in implementation bounce.

Local LDC replication remains future and requires a separately bound MVCA execution scope.
