# TX-ARCHIVE-001 — Epoch-local transactional archive replay

> Status: PREFLIGHT IMPLEMENTED / NO PHYSICAL RUN  
> Purpose: bind observer identity, reducer state, hazard coordinates, and re-prime boundaries into one replayable transaction archive.

## 1. Why an archive object is necessary

The transactional reducer already rejects stale packet epochs.

That is necessary but not sufficient for Chapter II.

Observer-side state also exists:

- owner_counter
- verified_at_ns
- next touch index since verification

If caller code forgets to clear these values at REPRIME, a logically new epoch could inherit observational authority from the previous worker/cgroup.

Therefore epoch reset must be centralized.

## 2. Archive state

Implementation:

`src/finite_ram_lab/transaction_epoch_archive.py`

The archive owns:

- Transaction reducer state
- epoch-local owner counter
- verification timestamp
- hazard touch index
- v2 receipt packets
- control events

## 3. Hard re-prime semantics

On:

`INVALIDATED -> REPRIME`

the archive:

1. increments the reducer epoch;
2. records the re-prime control event;
3. sets owner_counter to NULL;
4. sets verified_at_ns to NULL;
5. sets next_touch_index_since_verified to NULL.

The invalidating Q64/refill event cannot become the next epoch primer.

A new NORMALIZE direct-Q64 pair is required.

## 4. Synthetic sentinel replay

The test sequence is:

### Epoch 0

- NORMALIZE direct Q64 on counter 0xaaa
- VERIFIED
- unexpected direct Q64/refill during CONSUME
- INVALIDATED / UNEXPECTED_REFILL

### Hard re-prime

- epoch becomes 1
- owner counter cleared
- hazard clock cleared
- stale epoch-0 packet rejected

### Epoch 1

- fresh NORMALIZE direct Q64 on counter 0xbbb
- VERIFIED
- canonical b64 TARGET bundle
- COMMIT
- SUCCESS

The epoch-0 counter cannot authorize epoch 1.

## 5. Release-only replay

A separate synthetic path verifies:

- verified owner counter is carried across touches;
- a source-grounded shared-LRU release increments release telemetry;
- residual arithmetic decrements only for the measured data-page consume;
- release itself does not consume stock.

## 6. Guard precedence replay

A b64 terminal packet can contain the expected direct Q64 pair and therefore have:

`target_match = true`

while VmPTE simultaneously grows.

Required outcome:

`INVALIDATED / PTE_GROWTH`

not SUCCESS.

This confirms that target-pattern agreement never overrides a state-validity guard.

## 7. Implemented tests

- tests/test_transaction_epoch_archive.py

The tests freeze:

- owner identity reset
- stale epoch rejection
- fresh-Q64 requirement after re-prime
- release-only residual invariance
- PTE guard precedence
- eventual COMMIT only after a valid new epoch

## 8. Claim ceiling

Synthetic replay proves protocol composition, not physical reliability.

The remaining gap is physical wiring of FRL_TX markers and trace probes into the successor controlled-spawn runner.
