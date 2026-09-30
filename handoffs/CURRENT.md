# CURRENT

> Latest bounce: B413
> Stage: NORMALIZE BOUNDARY CHASE PREFLIGHT
> Stop: READY TO LAUNCH TX-NORMALIZE-BOUNDARY-CHASE-v1 AFTER CI

## Chapter II current frontier

B405 causal classification is now largely separated from normalization ecology.

R8 run 36681393399 produced:

- CLEAN 3/4
- RELEASE_ONLY 4/4
- UNEXPECTED_REFILL 4/4
- PTE_GROWTH 4/4
- challenge pass 15/16
- completion pass 15/16
- TARGET_FAIL 0

Critical observer coverage passed for the first time:

- frl_pc_try64 missed = 0
- frl_pc_uncharge_owner missed = 0

The sole R8 failure was CLEAN trial 0:0:

- NORMALIZE_EXHAUSTED
- 64 complete normalization touches
- no measured target direct Q64
- no PTE growth
- no CPU mismatch
- no worker error
- target transaction never reached VERIFIED

This remains frozen as a normalization specimen, not TARGET_FAIL.

## Named natural state-changing event

TARGET_STOCK_EVICTION remains established from B405 R6 trial 0:0:

verified target residual is asynchronously drained from the per-CPU memcg stock before the next measured transition.

Its full-residual fingerprint is:

Delta = -d

for an eviction of d cached pages.

## New pre-VERIFY state distinction

Verified direct-Q64 primer:

R0 = 63.

Natural pre-VERIFY stock:

0 <= S <= 64.

Linux refill_stock permits an existing same-memcg slot to reach exactly MEMCG_CHARGE_BATCH and drains only if the merged stock is greater than the batch.

Therefore define:

PREVERIFY_S64 / MAX_STOCK_BOUNDARY.

## 65-touch theorem

For one-page fresh data faults on one CPU, with a complete direct-Q64 observer:

T = S0 + 1

and:

0 <= S0 <= 64

therefore:

1 <= T <= 65.

Interpretation:

- T=1..64 -> WITHIN_BOUND
- T=65 -> MAX_STOCK_BOUNDARY
- T>65 -> STOCK_BOUND_VIOLATION_CANDIDATE

A valid no-Q64-through-65 specimen would falsify the current one-slot stock-bound model or expose an unmodeled charge path.

## R9 experiment

TX-NORMALIZE-BOUNDARY-CHASE-v1

Design:

- 4 blocks
- 8 fresh identities/block
- 32 total identities
- primary horizon 65 touches
- diagnostic horizon 80 only after bound violation
- target Q64 attribution by trace task PID + stock CPU
- one critical page_counter_try_charge(...,64) probe
- zero critical probe misses required
- no transactional target arm

Files:

- specs/TX-NORMALIZE-BOUNDARY-CHASE-v1.json
- src/finite_ram_lab/normalize_boundary_chase.py
- tests/test_normalize_boundary_chase.py
- docs/MATH-024-PREVERIFY-STOCK-BOUND-65-TOUCH-THEOREM.md
- handoffs/B413-NORMALIZE-BOUNDARY-CHASE.md
- .github/workflows/normalize-boundary-chase.yml

## Frozen evidence

B405 R8:

- analysis/inputs/B405-R8-PHYSICAL-RESULT-v1.json
- raw files = 80
- raw bytes = 9,669,832
- raw content-set SHA-256 = 31a9d3adbb979415e2dffba0a9117df066bf422a61753e39035db914f244bb3a
- aggregate artifact ID = 11082146184
- artifact digest = sha256:3ce31c90588f32f7f2cc2d89d8875980c650213a182f88af615eae0702a9f87c

Historical B405 generations remain frozen and must not be rewritten by R9.

## Authority

R9 physical continuation is authorized.

Standard public-repository GitHub-hosted runner only.
No paid larger runner.
No local-PC execution.
No reliability certification.
