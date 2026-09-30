# B423 — Ambient catcher receipt reducer

Date: 2026-09-30

## Purpose

Separate physical capture from scientific classification.

The ambient catcher now has three layers:

```text
capture backend
  -> source-neutral JSONL receipt stream
  -> deterministic reducer
  -> conservative ambient-stock classifier
```

This prevents ftrace, eBPF, LDC, or a future observer implementation from
silently changing scientific classification semantics.

## Receipt classes

The reducer understands only these v1 records:

- SESSION_START
- HEALTH
- COVERAGE
- HISTOGRAM
- AMBIENT_TARGET_TOUCH
- CONSUME_SUCCESS
- REFILL
- DRAIN_ATTRIBUTED
- OWNER_UNCHARGE
- BOUNDARY
- SESSION_END

Unknown record types are not ignored. They create a structural error and force
OBSERVATION_HOLD.

Duplicate coverage rows, duplicate singleton rows, or mixed session IDs also
fail closed through the structural-error path.

Missing required critical coverage is distinct from structural corruption:

- missing consume/refill/uncharge/q64 miss receipt -> INSTRUMENTATION_HOLD;
- malformed session structure -> OBSERVATION_HOLD.

## Why drain is optional

Long-window direct drain_stock logging remains optional because it cannot be
owner-memcg filtered directly.

A DRAIN_ATTRIBUTED row can be used only when a future capture backend has a
qualified attribution method. Direct drain promotion additionally requires an
explicit zero-miss drain coverage receipt.

Without that coverage, even:

```text
DRAIN_ATTRIBUTED 31
OWNER_UNCHARGE 31
T=33
```

remains UNKNOWN_COMPLETE.

## Frozen replay cases

The reducer tests preserve four scientifically important shapes:

```text
no mechanism + no owner uncharge + T64
  -> STABLE_RESIDUAL

consume31 + T33
  -> DIRECT_STOCK_CONSUMPTION_FINGERPRINT

drain31 + owner_uncharge31 + drain coverage0 + T33
  -> DIRECT_SLOT_EVICTION_FINGERPRINT

owner_uncharge31 + no classified drain/consume/refill + T33
  -> UNATTRIBUTED_OWNER_UNCHARGE
```

The last case intentionally matches the semantic shape that motivated this
branch without rewriting the historical R2 block2 result.

## Files

- src/finite_ram_lab/ambient_stock_log_reducer.py
- tests/test_ambient_stock_log_reducer.py
- src/finite_ram_lab/ambient_stock_catcher.py
- tests/test_ambient_stock_catcher.py

## Claim ceiling

This bounce validates receipt semantics and classification separation only.

No physical ambient session has run.
No background daemon has been installed.
No system service has been created.
No persistent probes have been armed.

## Next atomic bounce

Build one capture backend that emits this receipt stream from a private tracefs
instance.

The backend should:

- create one verified canary;
- establish residual31;
- use owner-filtered/count-only observers during the ambient interval;
- emit v1 JSONL receipts;
- perform the bounded final Q64 chase;
- exit and clean up all probes;
- never become a persistent daemon in v1.

The first live session remains one canary for 600 seconds with no synthetic
pressure.
