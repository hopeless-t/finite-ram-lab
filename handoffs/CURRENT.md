# CURRENT

> Latest bounce: B412
> Stage: B404 PHYSICAL PROTOCOL SMOKE PASS
> Stop: B404 COMPLETE / READY TO IMPLEMENT B405 PERTURBATION MATRIX

## Chapter II objective

Capture an unexplained verified-epoch boundary shift and distinguish real state mutation from observer contamination before reliability scaling.

## Clean boundary invariant

After a verified direct Q64:

`R_0 = 63`

and, under a complete uninterrupted clean epoch:

`R_t = 63 - t`.

The canonical next direct-Q64 boundary is:

`T_0 = 64`.

Define:

`Delta = T - 64`.

A complete unexplained `Delta != 0` remains the Chapter-II rare specimen.

## B404 R1 — observer falsification

Run:

- 36642120375
- launch commit `0d2a3286f3e0346e101285c52670e0ab817e427c`

Frozen result:

- normal SUCCESS 10/12
- TARGET_FAIL 0
- instrumentation hold 1
- ABORTED 1
- sentinel PASS
- protocol smoke FAIL under observer v1

R1 exposed two observer defects:

1. all observed `drain_stock` events were being treated as target-state mutation without CPU/context attribution;
2. an owner `page_counter_uncharge(...,17)` could fail attribution when its known LRU stack was not captured inside the narrow same-window flush/put envelope.

Raw forensics:

- 12 v1 drain invalidations
- 9/12 off target stock CPU
- 3/12 same stock CPU during direct-Q64 NORMALIZE refill/slot replacement
- zero observed same-stock-CPU post-verification drains

R1 remains frozen and is not rewritten as success.

Artifacts:

- `analysis/inputs/B404-R1-OBSERVER-RECLASSIFICATION-v1.json`
- `docs/B404-R1-TRANSACTIONAL-SPAWN-PHYSICAL-RESULT.md`

## Observer R2 correction

Implemented and CI-tested:

- trace CPU attribution
- off-stock-CPU drain ignored as target-stock mutation
- direct-Q64 NORMALIZE slot eviction distinguished from destruction of the newly established residual
- same-stock-CPU post-verification drain remains invalidating
- owner uncharge17 may be positively grounded by the known LRU/folio stack
- unknown owner uncharge remains fail-closed
- evidence-manifest records sorted by normalized relative path

The target arithmetic and transaction semantics were not changed.

## B404 R2 — physical PASS

Valid run:

- **36642946787**
- launch commit `c6c0feb8db7d6314dddddf9b15d2c7ab5f1d19aa`

Normal lane:

- **12/12 SUCCESS**
- b62 = 4/4
- b63 = 4/4
- b64 = 4/4
- TARGET_FAIL = 0
- instrumentation hold = 0
- normal-lane re-prime = 0

Sentinel:

- forced epoch0 UNEXPECTED_REFILL detected
- invalidated epoch could not commit
- hard re-prime opened epoch1
- epoch1 required a fresh direct Q64
- final SUCCESS
- sentinel PASS

Aggregate:

- `protocol_smoke_pass = true`
- `reprimes_total = 1`
- `invalidation_counts = {UNEXPECTED_REFILL: 1}`

The one invalidation/re-prime is intentional sentinel behavior.

Observer telemetry in the normal lane:

- classified release-only = 0
- unknown emission = 0
- off-stock-CPU drain observations safely ignored = 4
- NORMALIZE internal slot-drain observations safely ignored = 4

## Evidence

Machine result:

- `analysis/inputs/B404-R2-PHYSICAL-RESULT-v1.json`

Narrative:

- `docs/B404-R2-TRANSACTIONAL-SPAWN-PHYSICAL-PASS.md`

Handoff:

- `handoffs/B412-B404-PHYSICAL-PASS.md`

Raw manifest:

- files = 63
- content-set SHA-256 = `d5c819b4b7d413faa6f635fc9062f0941ee570afebbb149d5d8c1f33d05127cf`

Aggregate artifact:

- ID = 11067486294
- digest = `sha256:2a6b9d5fd0af968e89d8ceaca90b468ebd745641b40178ac9f50d09e73ce4e37`

## Claim boundary

B404 proves protocol-smoke behavior for this 13-identity physical panel.

It does **not** prove:

- population-level 100% reliability;
- zero TARGET_FAIL probability;
- absence of unknown state-changing mechanisms.

## Monte Carlo-selected discovery design

B410 remains frozen for the later discovery stage:

Stage A:

- b63 only
- FAST x4
- HOLD32 x12
- target wall-clock exposure ratio F ~= 16

Stage B only if triggered:

- HOLD8 x4
- HOLD32 x4
- HOLD56 x4

Do not run age decoupling before B405.

## Next physical stage

B405 causal perturbation matrix:

- CLEAN x4
- RELEASE_ONLY x4
- UNEXPECTED_REFILL x4
- PTE_GROWTH x4

Goal:

prove that the physical classifier responds asymmetrically:

- RELEASE_ONLY preserves the verified state;
- UNEXPECTED_REFILL invalidates;
- PTE_GROWTH invalidates;
- CLEAN commits normally.

## Authority

B404 physical experiment: COMPLETE / AUTHORIZED.

Next:
B405 implementation and preflight are authorized as continuation of the user-requested experiment program.

No paid runner.
No larger runner.
No local-PC execution.
No age-decoupling launch until B405 passes.
No reliability certification.
