# B411 — Successor transactional-spawn runner

## Status

IMPLEMENTED / PHYSICAL LAUNCH READY.

## Human authorization

The user explicitly authorized starting the experiment on 2026-09-30.

The repository is public and the physical workflow uses only the standard `ubuntu-26.04` GitHub-hosted runner, not a larger paid runner.

## Implemented

- src/finite_ram_lab/transactional_spawn_pilot.py
- tests/test_transactional_spawn_pilot.py
- .github/workflows/b404-transactional-spawn-pilot.yml
- README.md updated for Chapter II

## B404 physical topology

Four independent GitHub-hosted runner blocks.

Each block runs:

- b62 x1
- b63 x1
- b64 x1

Across four blocks:

- b62 x4
- b63 x4
- b64 x4

Block 0 additionally runs:

- FORCED_UNEXPECTED_REFILL_THEN_HARD_REPRIME sentinel x1

Total:

- 12 scientific normal identities
- 1 non-scientific sentinel

## Native receipts

Each measured touch is wrapped by:

FRL_TX PRE
-> frozen Chapter-I _touch()
-> FRL_TX POST

Trace probes:

- page_counter_try_charge(...,64)
- refill_stock(...,63)
- page_counter_uncharge(...,17)
- folio_batch_move_lru nr=31
- folios_put_refs nr=31
- drain_stock

The transaction observer additionally records:

- VmPTE delta
- CPU match
- worker error
- owner_counter
- touch age
- wall-clock age
- expected residual before/after
- trace completeness

## Normal identity behavior

Each epoch:

1. starts a fresh PTE-preconditioned worker/cgroup;
2. migrates it from prep CPU to stock CPU;
3. NORMALIZEs for at most 64 touches;
4. requires a direct charge64/refill63 pair to enter VERIFIED;
5. consumes the arm-specific bait count;
6. evaluates the b62/b63/b64 TARGET bundle;
7. COMMITs only from COMMIT_READY.

Retriable state invalidations:

- UNEXPECTED_REFILL
- DRAIN_STOCK
- PTE_GROWTH
- NORMALIZE_EXHAUSTED

use HARD_NEW_WORKER_CGROUP subject to max_reprimes=2.

Instrumentation invalidations:

- TRACE_GAP
- CPU_MISMATCH
- WORKER_ERROR

stop the identity rather than being retried away.

TARGET_FAIL is terminal.

## Sentinel behavior

Epoch 0:

- acquire verified direct Q64;
- execute 64 ordinary CONSUME transitions;
- require the next Q64 to appear as UNEXPECTED_REFILL;
- invalidate without COMMIT.

Then HARD_REPRIME.

Epoch 1:

- start a fresh worker/cgroup;
- require a fresh epoch-local direct Q64;
- execute canonical b63 target;
- COMMIT only from the fresh epoch.

Acceptance requires:

- epoch0 UNEXPECTED_REFILL;
- epoch1 fresh direct Q64;
- final SUCCESS.

## Aggregate acceptance

B404 protocol smoke passes only if:

- exactly 12 normal identities are present;
- all 12 end SUCCESS;
- zero TARGET_FAIL;
- zero instrumentation hold;
- sentinel passes.

Natural invalidation followed by a valid hard re-prime does not itself fail the protocol smoke.

## Evidence

Each block uploads:

- raw trial JSON
- epoch packet archives
- environment receipt
- raw trace.log
- kprobe formats
- kprobe profile

Aggregate freezes a raw-evidence manifest and summary.

## Next

After workflow CI is green:

1. commit launch/B404-TRANSACTIONAL-SPAWN-PILOT-v1.txt
2. observe four blocks
3. inspect any early infrastructure/instrumentation failure immediately
4. aggregate evidence
5. decide B405 only from the B404 result
