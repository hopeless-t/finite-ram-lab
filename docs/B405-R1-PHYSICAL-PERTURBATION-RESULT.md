# B405 R1 — Physical perturbation matrix result

> Run: 36645745433  
> Launch commit: `a0f4710b7c77c513e4e45540d439ce247c3479b0`  
> Status: PHYSICAL RUN COMPLETE / 14 OF 16 CHALLENGES PASS / INTERVENTION GENERATOR CONFOUND FOUND  
> Claim ceiling: mechanism/classifier diagnostic only.

## Frozen result

- CLEAN: 4/4 PASS
- RELEASE_ONLY: 2/4 PASS
- UNEXPECTED_REFILL: 4/4 PASS
- PTE_GROWTH: 4/4 PASS
- TARGET_FAIL: 0
- matrix_pass: false

R1 is not to be rewritten after the intervention fix.

## What passed

CLEAN behaved as the canonical verified b63 transaction in all four blocks.

UNEXPECTED_REFILL behaved asymmetrically in all four blocks:

- challenge epoch invalidated as UNEXPECTED_REFILL;
- invalidated epoch did not commit;
- hard re-prime opened a new epoch;
- recovery required a fresh epoch-local direct Q64;
- recovery reached SUCCESS.

PTE_GROWTH behaved asymmetrically in all four blocks:

- a deliberately different PTE-table fault produced non-zero VmPTE growth;
- guard precedence invalidated the challenge epoch as PTE_GROWTH;
- invalidated epoch did not commit;
- hard re-prime + fresh direct Q64 recovered to SUCCESS.

No complete path produced TARGET_FAIL.

## RELEASE_ONLY R1

Passing trials:

- 0:1
- 3:1

Both positively grounded one owner 17-page release, preserved expected residual across the OBSERVE event, and subsequently committed the canonical b63 target.

Confounded trials:

- 1:1
- 2:1

Both showed the same sequence inside the OBSERVE window:

```text
frltrig first stock charge
  -> refill_stock
  -> drain_stock on stock CPU
  -> later shared LRU flush
  -> owner page_counter_uncharge(...,17)
```

The intended release was positively grounded.

For both failed RELEASE_ONLY trials:

`expected_residual_before = 46`

and

`expected_residual_after = 46`

at the release observation itself.

However the same window also contained a stock-CPU drain caused by the separate trigger cgroup establishing/refilling its own memcg stock.

The classifier therefore invalidated the epoch as DRAIN_STOCK.

This is the correct fail-closed response to a non-pure intervention.

## Interpretation

R1 did not falsify RELEASE_ONLY semantics.

It falsified the R1 intervention generator assumption that an untouched trigger cgroup could begin its 14-touch LRU trigger without introducing its own memcg-stock transition.

The fix is causal, not classificatory:

1. start the trigger cgroup;
2. before target verification, touch trigger pages until a direct trigger refill establishes fresh trigger stock;
3. then scrub the shared LRU batch back to a known boundary;
4. only then verify the target epoch;
5. target consumes/discards 17 pages;
6. trigger performs 14 stock-cached touches inside OBSERVE;
7. require owner release with no relevant stock drain.

This keeps the intended intervention:

`shared-LRU RELEASE_ONLY`

separate from:

`trigger memcg stock establishment`.

## Evidence

Raw evidence manifest:

- files: 84
- total bytes: 36,356,857
- content-set SHA-256:
  `e6ccab36d5a99cbc2086635853f74a9cdbd6db338ea9a73beadcc032920e60ec`

Aggregate artifact:

- ID: `11067993127`
- digest:
  `sha256:f8f3127511257426a15a1dba0484ec6917e92e0ea5c72cda3b8ccbfb73fdce1a`

Machine-readable result:

- `analysis/inputs/B405-R1-PHYSICAL-RESULT-v1.json`

## Decision

Keep classifier semantics unchanged.

Change only the RELEASE_ONLY intervention generator.

Run B405 R2 with trigger-stock priming before target VERIFY.
