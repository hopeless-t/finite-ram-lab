# OBS-006 — Masked-Q64 charge-side observer v1

> **Status:** FROZEN DESIGN / NOT YET LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Question

Can a direct charge-side observer identify a Q64 stock refill when the net per-touch
\`memory.current\` delta is deliberately masked by a simultaneous 17-page LRU release?

## Construction

Use one measured worker cgroup Q and one scrubber cgroup S on the same target CPU.

The measured worker is PTE-preconditioned on a distinct preparation CPU.

### Stock state

1. Touch fresh pages on Q until a direct \`refill_stock(...,63)\` event is observed.
2. This is the Q64 reset anchor: batch64 charged, current page consumed, residual stock ~=63.
3. Consume exactly 33 additional data pages.

Expected residual:

\`63 - 33 = 30\`

### LRU state

4. S touches pages until it causes an LRU-add batch flush.
5. Keep S alive but idle after the flush.
6. Q touches exactly 17 new pages.

Q residual:

\`30 - 17 = 13\`

LRU-add batch occupancy:

\`17\`

7. Q discards those 17 pages with \`MADV_DONTNEED\` while their LRU-add batch references can keep them deferred/dead.

### Collision

8. Q touches 14 new pages.

Touches 1..13 consume the remaining stock.

Touch14 should simultaneously:

- fail \`consume_stock\`;
- charge a new 64-page batch;
- execute \`refill_stock(...,63)\`;
- add the 14th collision folio to the shared LRU batch;
- fill \`17 + 14 =31\`;
- flush the batch;
- uncharge the 17 dead Q-owned folios.

Predicted net:

\`+64 -17 = +47 pages\`

## Primary endpoint

Do not define Q64 by net \`memory.current\`.

Primary MASKED_Q64_PASS requires, on collision touch14:

1. direct Q-worker \`refill_stock(...,63)\`;
2. Q-worker \`page_counter_try_charge(...,64)\`;
3. \`page_counter_uncharge(...,17)\` on a counter charged by Q in that touch;
4. Q-worker LRU flush nr=31;
5. Q-worker \`folios_put\` nr=31;
6. no measured VmPTE growth.

The net delta is a secondary receipt.

Expected secondary receipt:

\`memory.current delta = +47 pages\`

## Fail-closed classes

- PRIMER_NOT_FOUND
- SCRUB_NO_FLUSH
- DISCARD_FAILED
- PTE_CONTAMINATED
- STOCK_STATE_LOST
- EARLY_RELEASE
- MASKED_Q64_PASS
- Q64_DIRECT_RELEASE_MISSING
- LRU_RELEASE_Q64_MISSING
- COLLISION_CHAIN_MISSING

No replacement trials.

## Scale

- 4 hosted blocks
- 4 identities/block
- 16 total trials

This is mechanism validation, not reliability certification.

## Promotion rule

If the direct charge-side chain is observed, future Q64 analysis should use a charge receipt as the reset token and
treat net \`memory.current\` only as a secondary observation.

b63 reliability scaling remains blocked until this observer is validated.
