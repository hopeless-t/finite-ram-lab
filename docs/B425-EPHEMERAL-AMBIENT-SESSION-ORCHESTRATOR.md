# B425 — Ephemeral one-canary ambient session orchestrator

Date: 2026-09-30

## Goal

Connect the frozen canary geometry, count-only tracefs backend, source-neutral
receipt reducer, and conservative classifier into one bounded session.

This bounce implements the orchestrator but does not launch it physically.

## Session lifecycle

```text
fresh epoch
  -> VERIFY R0=63
  -> exactly 32 measured target touches
  -> require residual=31
  -> remove setup stacktrace trigger
  -> switch qualified probes to count-only owner mode
  -> 60 second ambient window
  -> freeze histograms before target resumes
  -> switch to owner-Q64-only diagnostic mode
  -> bounded final boundary chase
  -> JSONL receipt stream
  -> reducer
  -> classifier
  -> cleanup and exit
```

No helper memcg is created.
No synthetic memory pressure is injected.
No daemon or persistent system service is installed.

## Why 60 seconds

The current Local Desktop Commander process surface has a synchronous process
timeout around two minutes. A first-run 600-second session would not fit the
existing bounded execution plane and would also conflict with the project's
short-bounce operating model.

v1 therefore uses:

- synchronous capability session: 60 seconds;
- later qualification target: 600 seconds;
- hard design maximum: 1800 seconds, not authorized for the first LDC action.

Multiple complete 60-second receipts can accumulate evidence without one long
opaque run.

## Canary quiescence is measured

The ambient target-touch count is not assumed from control flow.

Immediately before and after the ambient window the orchestrator reads:

- shared worker touched counter;
- worker error field;
- VmPTE;
- worker last CPU.

The pure quiescence reducer checks:

- touched counter did not regress;
- target touch delta is zero;
- worker error remains zero;
- CPU remains the stock CPU;
- VmPTE remains unchanged.

Any positive target-touch delta becomes AMBIENT_TARGET_TOUCH and therefore
CANARY_CONTAMINATED.

Counter regression fails closed through health.

## Ambient owner Q64 reset

A further ambiguity was found during B425 design.

If owner Q64 occurs while the target performs zero touches, the stock state has
crossed a reset/charge boundary during the ambient interval. Final boundary
arithmetic can no longer be treated as a simple continuation from residual31.

A new conservative class was added:

```text
AMBIENT_Q64_RESET
```

It takes precedence over direct consume/drain promotion.

This prevents a hidden mid-window reset from being misreported as a simple
T=64-d fingerprint.

## Boundary diagnostic

After ambient histogram receipts are frozen, histogram triggers are removed and
only the owner-filtered Q64 event is enabled.

The diagnostic performs at most 64 fresh target touches.

If the first diagnostic touch emits owner Q64:

```text
T = 32 + 1 = 33
Delta = -31
```

If no Q64 is observed within the bounded chase while all observation invariants
remain clean, the result is BOUNDARY_CENSORED rather than failure.

CPU mismatch, worker error, PTE growth, incomplete markers, or multiple Q64
events in one diagnostic window make the health receipt non-clean.

## Frozen files

- src/finite_ram_lab/ambient_stock_session.py
- tests/test_ambient_stock_session.py
- src/finite_ram_lab/ambient_stock_tracefs_backend.py
- src/finite_ram_lab/ambient_stock_log_reducer.py
- src/finite_ram_lab/ambient_stock_catcher.py
- specs/TX-AMBIENT-STOCK-CATCHER-v1.json

## Software replay coverage

The test surface includes:

- PREVERIFY_HOLD receipt construction;
- immediate diagnostic Q64 -> T33;
- clean bounded censoring;
- CPU mismatch;
- multiple-Q64 ambiguity;
- clean quiescence;
- unexpected target touch;
- touched-counter regression;
- CPU/PTE drift.

The earlier classifier fuzz design remains deterministic and bounded.

No claim in this document is physical evidence.

## Next atomic bounce

Wire a new fixed Local MCP Gateway action around this exact orchestrator.

The action must:

- accept no model-supplied command/path/duration;
- pin exact finite-ram source bytes;
- run on the local machine only;
- use a private tracefs instance;
- reuse the qualified probe identities;
- set the ambient duration from the frozen spec (60 seconds);
- use no network;
- use no paid resource;
- perform no retry;
- emit one durable receipt;
- clean up all probe/event state before returning.

Only after that action passes software qualification should one physical
60-second canary session be dispatched.
