# B405 R3 — Full-observability diagnostic

> Run: 36648499202  
> Launch commit: `e970f35293305820cd19ba133a3fa42a09faf0c1`  
> Status: PHYSICAL RUN COMPLETE / OBSERVABILITY CONTRACT FALSIFIED  
> TARGET_FAIL: 0  
> Historical result is frozen and must not be rewritten by R4 fixes.

## Frozen aggregate

- CLEAN challenge: 4/4
- RELEASE_ONLY challenge: 3/4
- UNEXPECTED_REFILL challenge: 4/4
- PTE_GROWTH challenge: 4/4
- challenge classification: 15/16
- completion: 12/16
- TARGET_FAIL: 0
- matrix_pass: false
- end_to_end_pass: false
- fully_observed_matrix_pass: false

## What R3 added

R3 introduced three observability dimensions that did not exist in R1/R2:

1. epoch-local memcg/counter ownership;
2. explicit inter-window continuity scans;
3. explicit kprobe missed-hit accounting.

It also moved the RELEASE_ONLY LRU reset to after target VERIFY and made that setup window a neutral receipt.

## Physical result

The causal classifier itself became substantially cleaner:

- CLEAN was classified correctly in all four blocks;
- UNEXPECTED_REFILL was classified correctly in all four blocks;
- PTE_GROWTH challenge classification was correct in all four blocks;
- RELEASE_ONLY was correct in three of four blocks.

The remaining failures exposed an observer-contract mismatch rather than a new target-pattern contradiction.

## Continuity scanner mismatch

The R3 workflow had already moved drain ownership to the stronger receipt:

`page_counter_uncharge(counter, nr_pages)`

through the all-counter probe:

`frl_pc_uncharge_any`.

However the first inter-window continuity scanner still attempted to resolve gap drains using the older memcg-uncharge path.

Therefore some same-CPU drains became:

`UNRESOLVED`

even when the raw trace contained the page-counter identity needed to classify ownership.

Observed consequences included:

- PTE recovery in blocks 0 and 1 ending SUCCESS while recovery continuity was false;
- RELEASE_ONLY block 3 stopping after a successful neutral post-VERIFY LRU reset because later drains were marked unresolved;
- UNEXPECTED_REFILL block 3 recovery ending SUCCESS while continuity was false.

R4 must use counter identity in both window and gap classification.

## RELEASE_ONLY setup result

The post-VERIFY LRU reset itself was physically demonstrated.

In block 3 RELEASE_ONLY:

- helper stocks had been primed before target VERIFY;
- post-VERIFY scrub reached a new LRU flush boundary;
- no helper refill occurred in the reset window;
- neutral receipt preserved expected residual 63 -> 63.

Thus R2's INTERVENTION_NOT_REALIZED ordering defect was substantially repaired before the later continuity-scanner mismatch stopped the identity.

## Probe coverage finding

R3 kprobe profile totals included:

- page_counter_try_charge64: 45,371 hits / **0 missed**
- all page_counter_uncharge: 106,794 hits / **3 missed**
- refill_stock: 141,438 hits / 319 missed
- legacy 17-page duplicate uncharge probe: 109,332 hits / 3 missed
- drain_stock: 1,217 hits / 3 missed

This showed that the observer had too many overlapping probes.

R4 therefore defines a minimal safety backbone:

- all direct charge64 observations: `frl_pc_try64`
- all page-counter uncharges: `frl_pc_uncharge_any`

and requires zero missed hits on those two probes.

Refill/drain/LRU probes remain enrichment and mechanistic diagnostics. They are not allowed to substitute for a missing counter-backbone receipt.

## R4 architecture

R4 changes observer architecture, not stock arithmetic:

- one unfiltered-by-comm Q64 charge probe, filtered only by nr_pages=64;
- one all-counter uncharge probe;
- conditional stacktrace on that same uncharge event when nr_pages=17;
- one shared refill_stock probe for target/trigger/scrubber;
- gap drain ownership paired directly to epoch-local owner_counter;
- unpaired owner-counter uncharge fails closed unless it is a grounded LRU release;
- target owner-counter charge64 in a gap is a state change;
- zero misses required on the two counter-backbone probes.

## Evidence

Raw manifest:

- files: 96
- bytes: 112,756,209
- content-set SHA-256:
  `ab56a4e1ba458da51cc87c4134aff1c54feff2b797e496f7e9acaa8cd8be46fc`

Aggregate artifact:

- ID: `11069303448`
- digest:
  `sha256:9903f3c8c00efe818fd6a5298a202f4b8ff3fdaa8017c963cb109bff0fa6f1a1`

Machine-readable freeze:

- `analysis/inputs/B405-R3-PHYSICAL-RESULT-v1.json`

## Decision

Do not loosen fail-closed semantics.

Reduce observer interference and make counter identity the continuity backbone.

Proceed to B405 R4 only after CI is green.
