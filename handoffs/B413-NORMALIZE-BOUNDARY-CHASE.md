# B413 — Normalize boundary chase

## Status

R9 DESIGN IMPLEMENTED / PHYSICAL LAUNCH PENDING CI.

## Trigger

B405 R8 run 36681393399 reached complete critical observer coverage:

- frl_pc_try64 missed = 0
- frl_pc_uncharge_owner missed = 0

The perturbation matrix result was 15/16 because CLEAN trial 0:0 never reached VERIFIED:

- 64 NORMALIZE touches
- no target direct Q64 in those measured windows
- no PTE growth
- no CPU mismatch
- no worker error
- final NORMALIZE_EXHAUSTED
- TARGET_FAIL = 0

This is an initial-state acquisition specimen, not a target contradiction.

## New state name

PREVERIFY_S64 / MAX_STOCK_BOUNDARY

The distinction is now explicit:

- measured direct-Q64 primer -> verified residual R0=63
- natural pre-VERIFY stock -> legal S in [0,64]

Linux refill_stock drains the matching slot only when the merged stock would be greater than MEMCG_CHARGE_BATCH, so S=64 is legal before the experiment establishes its own primer.

## 65-touch theorem

For one-page fresh faults on one CPU:

T = S0 + 1

with:

0 <= S0 <= 64

therefore:

T <= 65.

Classification:

- T=1..64: WITHIN_BOUND
- T=65: MAX_STOCK_BOUNDARY
- T=66..80: STOCK_BOUND_VIOLATION_CANDIDATE
- no T by 80: BOUNDARY_NOT_FOUND

PTE growth, CPU mismatch, worker errors, trace gaps and multiple target Q64 events are classified separately.

## R9 physical design

Experiment:

TX-NORMALIZE-BOUNDARY-CHASE-v1

- 4 blocks
- 8 identities/block
- 32 fresh cgroup/worker identities
- one critical page_counter_try_charge(...,64) probe
- Q64 attribution by trace task PID + stock CPU
- primary horizon 65 touches
- diagnostic horizon 80 only after a primary-bound violation
- zero critical probe misses required

No transactional target arm is executed.

This experiment isolates normalization ecology from transactional correctness.

## Planning sensitivity

R8 observed one 64-touch exhaustion among 16 identities.

Using that only as a weak design signal with Jeffreys Beta(0.5,0.5), the posterior-predictive chance of at least one recurrence in 32 additional identities is approximately 81%.

This is not a population rate estimate.

## Files

- specs/TX-NORMALIZE-BOUNDARY-CHASE-v1.json
- src/finite_ram_lab/normalize_boundary_chase.py
- tests/test_normalize_boundary_chase.py
- docs/MATH-024-PREVERIFY-STOCK-BOUND-65-TOUCH-THEOREM.md
- .github/workflows/normalize-boundary-chase.yml
- analysis/inputs/B405-R8-PHYSICAL-RESULT-v1.json

## Authority

Physical continuation is authorized by the user.

Use only standard public-repository GitHub-hosted runners.

No larger paid runner.
No local-PC execution.
No reliability certification.
