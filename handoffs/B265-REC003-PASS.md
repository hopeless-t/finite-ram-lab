# Bounce Handoff

> **Bounce ID:** B265
> **Status:** COMPLETE / REC-003 PASS / FINE-FLOOR HOLD RESOLVED

REC-003 run `36442276245`: success, 12/12.

Observer-only result:
- 96 MiB: 4/4 zero cgroup-current delta
- 192 MiB: 1/4 approximately +256 KiB, 3/4 zero
- 384 MiB: 4/4 approximately +256 KiB
- 384 median post-GC retained delta: 252 KiB
- cold file residency: 0

Conclusion: the residency observer has a size-dependent coarse allocation footprint. The prior sub-MiB post-scan floor-growth sequence is contaminated and is retired as a candidate workload law.

The main knee remains accepted:
`80 < K <= 88 MiB` at 96 / 192 / 384 MiB.

Next: freeze measurement-hygiene redesign before more external-validity experiments.

Hosted research only.
