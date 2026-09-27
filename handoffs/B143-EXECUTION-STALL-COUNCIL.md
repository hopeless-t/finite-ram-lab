# Bounce Handoff

> **Bounce ID:** B143
> **Status:** COMPLETE / EXECUTION-STALL COUNCIL CONVERGED

## Incident

After B141 implementation commit:

- B139: 2026-09-27 02:39:13 JST
- B140: 2026-09-27 02:40:17 JST
- B141: 2026-09-27 02:42:18 JST
- B141 CI completed SUCCESS: 2026-09-27 02:42:47 JST
- no new canonical write occurred until B142 at 2026-09-27 11:02:09 JST

The gap was about 8 hours 19 minutes.

## Eliminated causes

### GitHub failure — NOT SUPPORTED

B141 commit exists on main and prior writes were succeeding normally.

### CI hang — NOT SUPPORTED

CI run 36259973882 completed successfully only 29 seconds after the B141 commit.

### Research ambiguity / Human gate — NOT SUPPORTED

B141 had a deterministic next action: read ordinary CI exactly once.

### Tool safety block — NOT OBSERVED AT B141

An earlier B129 write was blocked once and explicitly reconciled, but no analogous error was observed at B141.

## Best-supported classification

**TURN_CONTINUATION_LOSS / exact platform mechanism unknown**

The active AI execution did not perform the already-defined next bounce after B141.

We cannot prove whether the underlying trigger was a runtime/time/context/tool budget, scheduler termination, or another turn-lifecycle boundary.

## Major contributing factors

### 1. Too many micro-bounces inside one assistant turn

B111 through B141 placed roughly thirty canonical bounces into one active execution turn.

Micro-bounces reduced per-bounce cognitive load but did not bound cumulative turn load.

### 2. Excessive tool-result payload

Several GitHub REST reads emitted the entire workflow-run JSON, including repeated repository metadata, instead of extracting only:

- run id;
- workflow;
- status;
- conclusion;
- head SHA;
- attempt.

This unnecessarily consumed conversation/tool context.

### 3. Large low-level Git operations

Atomic Git tree/blob operations are useful, but repeated source-sized payloads plus full readbacks compounded turn pressure.

### 4. No explicit turn-level stop budget

The protocol bounded individual bounces but had no maximum number of bounces per assistant turn.

The worker could therefore continue until the execution environment stopped it unexpectedly.

## Council convergence

### Runtime seat

Assume a ChatGPT turn is finite and non-background.

Do not treat “continue indefinitely” as an available primitive.

### Research seat

Preserve micro-bounces, but add a larger **turn envelope** around them.

### Tool-economics seat

Parse external API responses inside the tool call and emit only decision-relevant fields.

Never dump full REST payloads into model context unless required for diagnosis.

### Reliability seat

Prefer an intentional, canonical turn boundary over an unexpected runtime loss.

### Audit seat

Every intentional stop must have an explicit stop reason.

If a future turn sees a stale ACTIVE state with no close marker, classify it as RUNTIME_LOSS and reconcile before continuing.

## Decision

Adopt **EXECUTION-CONTINUITY-v1**.

Core controls:

1. maximum 8 canonical bounces per assistant turn;
2. maximum 3 external/tool calls between user-visible progress updates;
3. external run status read at most once per bounce;
4. no full API payload emission by default;
5. reserve the final bounce of a turn for checkpoint/close only;
6. explicit stop reason at every planned turn boundary;
7. fresh-turn rehydrate/reconcile before new work;
8. no retry after unknown-delivery writes;
9. external side effects remain reconciled, never erased.

## Optional future hardening

A GitHub workflow_run observer could record external CI completion in a non-authoritative observation lane.

It is not adopted automatically because granting GitHub Actions write authority changes the trust surface and deserves a separate Council.

## Next action

Freeze EXECUTION-CONTINUITY-v1 as machine-readable and human-readable operational policy.

## Authority boundary

This is execution-process governance only.
It does not change research authority or authorize memory interventions.
