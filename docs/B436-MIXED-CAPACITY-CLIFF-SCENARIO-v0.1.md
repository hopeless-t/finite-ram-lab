# B436 — Mixed Capacity-Cliff Scenario v0.1

Status: **source-anchored mixed normalized controller scenario**. It is not one executable application and no physical benchmark ran.

## 1. Purpose

B435 showed that bounded Pareto beam search can approximate an exact tiny-window oracle.

B436 asks the next question:

> When several previously studied memory transformations compete for finite RAM and VRAM, does increasing capacity merely improve one plan smoothly, or does it change which kinds of plans are even available?

The answer in this controlled scenario is discrete:

**capacity activates qualitatively different frontier arms.**

## 2. Scenario components

The scenario intentionally combines mechanisms from several earlier bounces.

### Source-backed Strata INT8 KV anchor

From B432:

- 12 QSA layers
- max_cells = 131072
- resident_cells = 32768
- full INT8 pool = 1584 MiB
- resident GPU subset = 396 MiB
- authoritative host pool when streamed = 1584 MiB

Two options:

1. full_int8_vram
2. stream_int8

The streamed option pays normalized traffic/latency cost because the exact workload-dependent transfer amount is not known here.

### Source-anchored Strata expert placements

Strata docs describe the Q2_0 expert volume as approximately 34 GB.

B436 uses a **normalized 34-GiB logical proxy** only to study controller geometry.

Options partition that proxy as:

- 20 GiB GPU + 14 GiB RAM
- 12 GiB GPU + 22 GiB RAM
- 8 GiB GPU + 26 GiB RAM
- 8 GiB GPU + 8 GiB resident RAM + file backing for the remainder

The last option does not charge file-backing size to resident RAM.

These are controller proxies, not measured Strata allocations.

### Prompt cache borrowing

The public 2026-09-30 RTX 5090 log reports approximately 4.62 GiB of expert-cache slots borrowed by the prompt path.

B436 converts that rounded value to a 4731-MiB proxy.

Options:

- dedicate additional prompt scratch;
- borrow already allocated expert-cache capacity and pay normalized refill/latency cost.

### Semantic reduction

A normalized FlashAttention-pattern state has:

- materialized form: 1024 MiB
- proven future-sufficient summary: 256 MiB

The summary option is marked release_proven=true.

These numbers are normalized and are not FlashAttention kernel measurements.

### Temporalization

A normalized GEMMul8-pattern workspace has:

- wide frontier: 2048 MiB
- blocked frontier: 512 MiB

Blocking pays normalized traffic/compute/latency cost.

This represents the B430 frontier-width versus sweep-count exchange and is not a GEMMul8 performance model.

### Idle lifetime

A normalized state-exposure term compares:

- always loaded;
- idle unload plus reload cost.

It changes byte-seconds without changing the scenario's peak-capacity requirement.

## 3. Exact tight-capacity cliff

The smallest resident plan under only 8192 MiB of RAM is:

- full INT8 KV in VRAM
- 8-GiB expert GPU cache + 8-GiB resident RAM + file backing
- prompt cache borrowing
- future-sufficient summary
- blocked temporalized frontier

Its VRAM requirement is:

8192
+ 1584
+ 256
+ 512
=
10544 MiB.

Therefore:

- RAM = 8192 MiB
- VRAM = 10543 MiB

is infeasible.

At:

- RAM = 8192 MiB
- VRAM = 10544 MiB

the exact feasible frontier appears.

The only remaining choice at that exact capacity is the idle lifetime exchange:

- always loaded;
- idle unload.

## 4. One RAM threshold changes the required VRAM

Streaming KV needs the expert RAM budget plus the authoritative host KV:

8192 + 1584 = 9776 MiB RAM.

Therefore:

### At RAM <= 9775 MiB

the streamed-KV option cannot coexist with the minimum expert resident budget.

Minimum VRAM remains:

10544 MiB.

### At RAM = 9776 MiB

streamed KV becomes feasible.

The minimum VRAM becomes:

8192
+ 396
+ 256
+ 512
=
9356 MiB.

So one additional MiB at this boundary changes the minimum feasible VRAM by:

10544 - 9356 = 1188 MiB.

That 1188 MiB is exactly the B432 INT8 KV VRAM avoided by streaming:

1584 - 396 = 1188 MiB.

This is a useful structural consistency check.

## 5. The first real capacity-cliff result

The scenario therefore has two minimal capacity vectors:

- (RAM=8192 MiB, VRAM=10544 MiB)
- (RAM=9776 MiB, VRAM=9356 MiB)

Neither dominates the other.

This means there is no single minimum-memory point.

The true minimum resource boundary is already a two-dimensional antichain.

More RAM can substitute for VRAM, but only after a legal MOVE transformation becomes possible.

## 6. Frontier arms appear at different capacities

At RAM=8192 MiB:

- future-sufficient summary appears at VRAM 10544;
- materialized semantic state appears at 11312;
- wide temporalization appears at 12080;
- dedicated prompt scratch appears at 16811;
- streamed KV is impossible.

At RAM=24576 MiB:

- streamed KV appears at 9356 VRAM;
- full INT8 KV appears at 10544;
- the 12-GiB GPU / 22-GiB RAM expert arm appears at 13452;
- dedicated prompt scratch appears later;
- the 20-GiB GPU / 14-GiB RAM expert arm appears at still higher VRAM.

Thus capacity relaxation does not just improve one fixed schedule.

It changes the set of physically and semantically meaningful choices visible to the controller.

## 7. Capacity-grid evaluation

The frozen grid contains:

- 15 VRAM capacities
- 11 RAM capacities
- 165 total capacity points

150 points have a non-empty exact frontier.

Across them the exact controller exposes:

- 3506 distinct frontier objective vectors in total.

## 8. Beam controller on the mixed scenario

### Beam 16

- mean exact-point coverage: 77.48%
- minimum coverage: 20%
- returned-point dominated fraction: 0%
- exact recovery on 82 / 150 capacity points

### Beam 32

- mean coverage: 91.27%
- minimum coverage: 40%
- dominated fraction: 0%
- exact recovery on 114 / 150 points

### Beam 64

- mean coverage: 99.01%
- minimum coverage: 80%
- dominated fraction: 0%
- exact recovery on 141 / 150 points

### Beam 96

- exact-point coverage: 100%
- dominated fraction: 0%
- exact recovery on 150 / 150 points

This mixed scenario is small enough that beam 96 is effectively exact.

## 9. Interpretation

The important result is not that one configuration wins.

The important result is:

> **capacity changes the topology of the decision set.**

Near a cliff, one additional unit of one tier can unlock a transformation that removes a much larger requirement from another tier.

This produces discrete strategy transitions such as:

RAM increase
-> host KV becomes legal
-> VRAM resident KV shrinks
-> new semantic/temporalization combinations fit
-> Pareto frontier changes shape.

This is more informative than a single memory-utilization percentage.

## 10. New hypothesis H436 — Capacity-Activated Strategy

> In a multi-tier finite-memory system, the marginal value of added capacity is discontinuous when that capacity crosses the minimum requirement of a previously infeasible transformation.

This refines H426-2.

The capacity cliff is not only a performance phenomenon caused by paging/reclaim.

There is also a **combinatorial policy cliff**:

a legal plan exists on one side of the boundary and does not exist on the other.

## 11. Artifacts

Frozen on branch:

- research/mixed-capacity-cliff-b436

Files:

- src/finite_ram_lab/mixed_capacity_cliff.py
- tests/test_mixed_capacity_cliff.py
- analysis/inputs/B436-MIXED-CAPACITY-CLIFF-EVAL-v0.1.json
- docs/B436-MIXED-CAPACITY-CLIFF-SCENARIO-v0.1.md

Claim ceiling:

SOURCE_ANCHORED_MIXED_NORMALIZED_CONTROLLER_SCENARIO.

No physical benchmark ran.
No B425 ambient canary ran.
No paid resource was used.

## 12. Next bounce B437

The B436 result suggests a more mathematical representation.

Every safe plan has a capacity requirement vector:

r(plan) = (RAM_required, VRAM_required, ...).

That plan is feasible for every capacity vector C satisfying:

C >= r(plan)

componentwise.

Therefore the total feasibility region is a union of upper orthants.

B437 should compute the minimal antichain of requirement vectors and call it the **capacity activation frontier**.

For B436 it should recover exactly the two minimal points:

- (8192, 10544)
- (9776, 9356)

This will separate two different kinds of cliffs:

1. combinatorial activation cliffs — a new legal plan becomes possible;
2. runtime pressure cliffs — latency/traffic changes sharply near a tier limit.

That distinction should make later physical experiments much cleaner.
