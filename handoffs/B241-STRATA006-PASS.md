# Bounce Handoff

> **Bounce ID:** B241
> **Status:** COMPLETE / STRATA-006 PASS / LIVE-SET MECHANISM REPLICATED

## Hosted result

STRATA-006 run `36434232753` completed successfully.

- 48 / 48 trials
- aggregate artifact id `10974842004`
- digest `sha256:4bee6f7e6cd1b0efdc342187d08204513f2f3e05e7422ad8a87c5d05353e6eb7`

## Direct mechanism result

At MemoryHigh=160 MiB:

- hot=56 -> `88 < K <= 96`
- hot=64 prior anchor -> `80 < K <= 88`
- hot=72 -> `72 < K <= 80`

All three map to:

`144 < K + hot <= 152 MiB`

All 4 blocks at hot=56 independently reproduced 88–96.
All 4 blocks at hot=72 independently reproduced 72–80.

DONTNEED post-scan non-hot floor:

- hot=56 median: 12.734375 MiB
- hot=72 median: 12.794921875 MiB

Council promotes effective-live-set headroom to the leading tested mechanism on the current hosted substrate.

## Monte Carlo

Deferred. Current deterministic replication is more informative than a synthetic threshold-jitter distribution.

## Next action

Design a cross-substrate/image external-validity study while holding workload and pressure variables fixed.

Do not launch until design freeze, implementation, and ordinary CI are complete.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
