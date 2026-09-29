# CURRENT

> Latest bounce: B380
> Stage: MATH-008 ALIAS AUDIT COMPLETE / G0 + INDUCTION DRAFTED
> Stop: HUMAN_COMPUTE_APPROVAL

## Critical new finding

The observed capacity signal is aliased with decimal argv width.

Implementation passed capacity as:
`str(max_pages)`

Across the relevant experiments:
- one-digit capacities: 8/9
- two-digit capacities: 10+

In MEMCG-005G-F, the candidate T10 split is exactly identical to this digit-width partition.

Exploratory cross-experiment CMH:
- common OR ~=4.20
- p ~=1.33e-10
- heterogeneity p ~=0.270

This proves the partition is reproducible, not which variable causes it.

Doc:
`docs/MATH-008-ARGV-WIDTH-ALIAS-AND-INDUCTION.md`

## Q64 status

Q64 remains independently supported.

Current Linux source defines a 64-page memcg charge batch, and finite-ram-lab MEMCG-004 reproduced:

fresh Q64 -> residual63 -> 63 stock-consuming touches -> next Q64.

Do not conflate Q64 with T10.

## Next experiment candidate: G0 alias breaker

Draft:
`docs/MEMCG-005G-G0-CAPACITY-ARGV-ALIAS-BREAKER-DRAFT-v0.md`

Preferred discovery scale:
- 32 hosted blocks
- 60 candidates/block
- 1920 candidates total
- 320 candidates/arm

Key change:
capacity is written as binary `max_pages_u32` into shared control memory and removed from capacity-dependent argv text.

Secondary receipts:
region/control addresses and page-table-position diagnostics.

Do not implement/launch without Human compute approval.

## Rare-Pokemon construction track

Revised draft:
`docs/MEMCG-005G-C-CONTROLLED-RARE-INDUCTION-v1.md`

Route:
directly observe Q64 primer -> consume fixed bait pages -> measure target.

Primary operational arm:
`b63`

Prediction:
- one residual stock page before target
- target delta0
- next touch Q64
- exact depth1

This is the preferred route toward near-deterministic capture rather than waiting for natural rare states.

## Large confirmatory replication

Existing draft:
`docs/MEMCG-005G-G-EXACT-ZERO-REPLICATION-DRAFT-v0.md`

Scale:
5760 total candidates.

Status:
DEFERRED until the capacity/argv alias is broken.

## Collaboration

Draft:
`docs/DISTRIBUTED-RARE-STATE-REPLICATION-DRAFT-v0.md`

Hosted research only.
No local-PC execution.
