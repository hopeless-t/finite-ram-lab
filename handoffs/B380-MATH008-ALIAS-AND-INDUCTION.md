# B380 — MATH-008 argv-width alias audit + induction route

## What changed

A new design alias was identified across MEMCG-005G-B/D/E/F:

capacity was passed as a decimal argv token via `str(max_pages)`.

The observed split is therefore aligned with decimal token width:

- one-digit capacities: 8/9
- two-digit capacities: 10+

In MEMCG-005G-F the restricted T10 split is exactly identical to the one-digit/two-digit partition.

## Exploratory cross-experiment audit

Two-digit vs one-digit exact-zero/capture partition:

- 005G-B OR ~=9.21
- 005G-D OR ~=5.90
- 005G-E OR ~=7.01
- 005G-F exact-zero OR ~=2.85

CMH common OR ~=4.20.
CMH p ~=1.33e-10.
Equal-odds heterogeneity p ~=0.270.

Interpretation:

strong reproducibility of the partition, but existing experiments cannot identify whether the cause is mapping capacity or argv/launch representation.

## New docs

- `docs/MATH-008-ARGV-WIDTH-ALIAS-AND-INDUCTION.md`
- `docs/MEMCG-005G-G0-CAPACITY-ARGV-ALIAS-BREAKER-DRAFT-v0.md`
- `docs/MEMCG-005G-C-CONTROLLED-RARE-INDUCTION-v1.md`

## G0 alias breaker

Remove capacity from argv.

Controller writes `max_pages_u32` into shared control memory before worker launch.

Also record region/control virtual addresses and page-table-position diagnostics.

Preferred discovery scale:
32 hosted blocks x60 =1920 candidates.

No launch authorized.

## Rare-state construction route

Controlled induction is revived because its original G-B dependency is resolved.

Use a directly observed Q64 primer, then consume a fixed number of pages.

For b63:
- predicted residual before target =1
- target delta=0
- next touch=Q64
- predicted exact depth=1

This is the main route from rare natural capture to constructible state.

## Authority

The larger 5760-candidate 005G-G remains deferred.

No hosted compute launched in B380.
No local-PC execution.
