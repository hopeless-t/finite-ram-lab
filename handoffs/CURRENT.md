# CURRENT

> **Latest bounce:** B265
> **Stage:** REC-003 PASS / OBSERVER CONTAMINATION IDENTIFIED
> **Turn stop reason:** READY_FOR_MEASUREMENT_HYGIENE_DESIGN

## Accepted result

STRATA capacity series:

- 96 MiB -> `80 < K <= 88`
- 192 MiB -> `80 < K <= 88`
- 384 MiB -> `80 < K <= 88`

384 MiB exceeds MemoryMax 320 MiB and still completed without OOM under bounded DONTNEED streaming.

Leading empirical model:

`instantaneous RAM demand ~= effective live set + unreleased streaming interval + bounded overhead`

for the tested one-shot streaming workload.

## REC-003 PASS

Run `36442276245`, 12/12.

Observer-only target-size audit found:

- 96 MiB: no measured cgroup-current growth in 4/4
- 192 MiB: approximately +256 KiB in 1/4
- 384 MiB: approximately +256 KiB in 4/4
- 384 median post-GC retained delta: approximately 252 KiB
- file residency remained zero

Therefore the previous sub-MiB post-scan non-hot-floor trend is measurement-contaminated by the residency observer and is no longer a candidate workload law.

The knee is unaffected because MemoryHigh response is captured during scan before post-scan residency observation.

Canonical result:

`docs/REC-003-RESULT.md`

## Next fresh-bounce action

Freeze a measurement-hygiene redesign:

- capture workload floor before any mincore/residency observer;
- preserve a separately named post-observer diagnostic;
- consider observer process/cgroup isolation;
- specify migration of historical summaries without rewriting raw evidence;
- do not launch during design bounce.

After hygiene is validated, resume external validity:
throughput cost, cadence portability, and pressure metrics.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
Proposal != Decision.
Expressibility != Executability.
