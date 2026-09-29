# B404 R2 — Transactional Spawn Physical Smoke PASS

> **Run:** 36642946787  
> **Launch commit:** `c6c0feb8db7d6314dddddf9b15d2c7ab5f1d19aa`  
> **Status:** PHYSICAL PROTOCOL SMOKE PASS  
> **Claim ceiling:** protocol integrity only; no reliability certification.

## Result

Normal lane:

- 12 / 12 `SUCCESS`;
- b62: 4 / 4;
- b63: 4 / 4;
- b64: 4 / 4;
- `TARGET_FAIL = 0`;
- instrumentation hold = 0;
- normal-lane re-prime = 0.

Sentinel lane:

- epoch 0 deliberately produced `UNEXPECTED_REFILL`;
- epoch 0 was invalidated;
- the invalidating refill did not authorize a commit;
- hard re-prime created epoch 1;
- epoch 1 acquired a fresh direct Q64;
- canonical target completed;
- final `SUCCESS`.

Aggregate:

```text
protocol_smoke_pass = true
normal_success      = 12
target_fail         = 0
instrumentation_hold = 0
sentinel_pass       = true
reprimes_total      = 1
invalidations       = { UNEXPECTED_REFILL: 1 }
```

The single re-prime is the intentional sentinel re-prime.

## Observer correction validated physically

R1 had over-classified `drain_stock` and one owner uncharge as state loss.

R2 used:

- CPU-aware drain attribution;
- direct-Q64 NORMALIZE slot-eviction distinction;
- uncharge17 stack-grounded LRU release attribution;
- normalized evidence-manifest ordering.

In R2 normal-lane packets:

- off-stock-CPU drains ignored as target-state mutations: 4;
- direct-Q64 NORMALIZE internal slot drains ignored: 4;
- classified release-only emissions: 0;
- unknown emissions: 0.

No normal epoch required re-prime.

This is a prospective validation of the corrected observer.

It does not retroactively rewrite R1 outcomes.

## What R2 establishes

R2 supports the operational chain:

```text
fresh worker/cgroup
  -> PTE precondition
  -> stock-CPU migration
  -> NORMALIZE
  -> direct Q64 receipt
  -> VERIFIED
  -> deterministic measured execution
  -> arm-specific TARGET bundle
  -> COMMIT
  -> SUCCESS
```

for all 12 physical normal identities in this smoke panel.

It also physically supports the fail-closed path:

```text
VERIFIED
  -> forced unexpected refill
  -> INVALIDATED
  -> hard re-prime
  -> fresh epoch-local Q64
  -> valid target
  -> COMMIT
```

## What R2 does not establish

Do not infer:

- 100% population reliability;
- zero probability of `TARGET_FAIL`;
- absence of unknown state-changing mechanisms;
- general behavior across arbitrary kernels/hardware/workloads.

The sample was deliberately designed as a protocol smoke.

## Evidence

Raw-evidence manifest:

- file count: **63**
- content-set SHA-256:
  `d5c819b4b7d413faa6f635fc9062f0941ee570afebbb149d5d8c1f33d05127cf`
- manifest timestamp: `2026-09-29T23:03:06Z`

Aggregate artifact:

- ID: `11067486294`
- name: `B404-TRANSACTIONAL-SPAWN-PILOT-36642946787`
- artifact digest:
  `sha256:2a6b9d5fd0af968e89d8ceaca90b468ebd745641b40178ac9f50d09e73ce4e37`

Frozen machine-readable result:

- `analysis/inputs/B404-R2-PHYSICAL-RESULT-v1.json`

## Decision

B404 is complete.

The next physical stage is B405:

`CLEAN / RELEASE_ONLY / UNEXPECTED_REFILL / PTE_GROWTH`

as a causal perturbation matrix.

Age-decoupling remains gated behind B405.
