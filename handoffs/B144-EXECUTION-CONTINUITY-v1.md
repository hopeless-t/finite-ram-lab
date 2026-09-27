# Bounce Handoff

> **Bounce ID:** B144
> **Status:** COMPLETE / EXECUTION-CONTINUITY-v1 FROZEN

## Added

- `ops/EXECUTION-CONTINUITY-v1.json`
- `docs/EXECUTION-CONTINUITY-v1.md`

## Main controls

- at most 8 canonical bounces per assistant turn;
- final bounce reserved for checkpoint/close;
- at most 3 external/tool calls between progress updates;
- one external status read per bounce;
- no full API payloads by default;
- zero retry after unknown delivery;
- mandatory fresh-turn rehydrate/reconcile;
- explicit planned stop reason;
- stale unexplained continuation loss classified as `RUNTIME_LOSS`.

## Expected effect

The system may still encounter platform/runtime limits, but it should stop **deliberately before** reaching them far more often.

If an unexpected stop still happens, the next turn should have enough canonical information to identify it immediately and resume safely.

## Next action

Resume finite-ram-lab research from B144 under EXECUTION-CONTINUITY-v1.

## Authority boundary

Execution-process governance only.
