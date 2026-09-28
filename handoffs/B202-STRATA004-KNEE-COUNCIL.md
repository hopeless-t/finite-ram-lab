# Bounce Handoff

> **Bounce ID:** B202
> **Status:** COMPLETE / STRATA-004 KNEE-REFINEMENT COUNCIL CONVERGED

## Parent evidence

- B201 / STRATA-003 PILOT PASS
- 56 / 56 valid trials
- observed pressure-avoidance bracket: `32 MiB < knee <= 96 MiB`

## Explore / atomized findings

1. The 4 / 8 / 16 / 32 MiB arms show an approximately linear increase in median max-scan memory with release interval.
2. A simple least-squares heuristic over those four points is approximately:
   - peak MiB ~= 77.91 + 0.998 * cadence MiB
3. Under the frozen 160 MiB MemoryHigh condition, that heuristic places the transition region near ~82 MiB.
4. This model is only a design heuristic. It is not evidence that the physical knee is 82 MiB.
5. 96 MiB / end-of-stream already demonstrates that final cleanup can succeed after transient pressure has occurred.
6. Throughput timing on hosted runners remains noisy; pressure/capacity behavior stays primary.

## Pseudo-Council

### Minimalist
Use only 32 / 64 / 96 plus buffered, then adaptively launch a second study.

Concern: fewer first-run trials, but adds another external-run state transition and more orchestration/wait overhead.

### Resolution-first
Use a one-shot denser upper sweep because prior evidence already suggests the transition is likely in the upper half.

Candidate cadences:
32 / 48 / 64 / 72 / 80 / 88 / 96 MiB.

### Reproducibility
Keep the STRATA-003 workload shape unchanged:
- GitHub-hosted Ubuntu 24.04;
- MemoryHigh 160 MiB;
- MemoryMax 320 MiB;
- HOT anonymous 64 MiB;
- COLD file 96 MiB;
- 4 MiB read chunk;
- 4 MiB in-process scan checkpoints.

### External validity
Capture runner/kernel/cgroup environment metadata in the next contract, but do not mix portability replication into the knee-refinement run.

## Convergence

Use one bounded hosted response-surface refinement with:

- buffered paired baseline;
- DONTNEED 32 MiB anchor;
- 48 MiB;
- 64 MiB;
- 72 MiB;
- 80 MiB;
- 88 MiB;
- 96 MiB anchor.

8 runner blocks x 8 arms = 64 trials.

O_DIRECT is not required in this refinement because STRATA-003 already established the reference behavior and it contributes little information about the location of the buffered DONTNEED transition. This is a study-design reduction, not a product decision.

## Primary outcomes

- MemoryHigh event delta during scan;
- maximum scan-time memory.current;
- post-scan memory.current;
- post-scan file residency.

## Secondary / OSS-facing outcomes

- advice-call count and density;
- scan time / throughput as noisy secondary evidence;
- pgscan / pgsteal;
- HOT residency / retouch;
- swap / OOM;
- runner/kernel/cgroup environment metadata.

## Knee interpretation rule

If tested intervals show a monotone transition, report the narrowest adjacent tested bracket between a pressure-free cadence and a pressure-producing cadence.

If the response is non-monotone across blocks or cadences, preserve that ambiguity. Do not force a single knee.

No OSS default cadence is authorized by this Council.

## Monte Carlo disposition

DEFER for this bounce.

Reason: the next uncertainty is an unmeasured physical response surface. Simulating that surface before measuring it would mostly encode assumptions. Use Monte Carlo later for adaptive headroom-policy robustness after the empirical transition is better localized.

## Next action

Freeze STRATA-004-KNEE-v1 exactly from this converged design.

## Authority boundary

Hosted research only.
No local-PC execution.
No OSS default selection.
Proposal != Decision.
Expressibility != Executability.
