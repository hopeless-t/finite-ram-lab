# B407 — Epoch-local archive replay

## Status

COMPLETE / SYNTHETIC END-TO-END PREFLIGHT / NO PHYSICAL RUN.

## Implemented

- src/finite_ram_lab/transaction_epoch_archive.py
- tests/test_transaction_epoch_archive.py
- docs/TX-ARCHIVE-001-EPOCH-LOCAL-REPLAY.md

## Main invariant

REPRIME resets both:

- transaction state authority;
- observer state authority.

On REPRIME the archive clears:

- owner_counter
- verified_at_ns
- hazard touch index

A stale old-epoch packet is rejected.

## Synthetic sentinel

Epoch 0:

- direct Q64 on owner 0xaaa
- VERIFIED
- forced unexpected refill
- INVALIDATED

Hard re-prime:

- epoch -> 1
- owner -> NULL
- hazard clock -> NULL
- stale epoch0 packet rejected

Epoch 1:

- fresh direct Q64 on owner 0xbbb
- canonical target
- COMMIT
- SUCCESS

The invalidating refill cannot become the next epoch's primer.

## Other replay coverage

- release-only preserves residual arithmetic
- unrelated counters are not attributed to target owner
- PTE growth overrides a matching b64 target
- unknown emissions fail closed

## CI

Epoch archive source and end-to-end synthetic replay tests passed CI.

## Next

Wire FRL_TX markers and source probes into the successor controlled-spawn runner.

Physical execution remains paused.
