# Bounce Handoff

> **Bounce ID:** B190
> **Status:** COMPLETE / LLM MEMORY SEMANTICS INTAKE

## Source

https://note.com/npaka/n/n0ee92a316be3

## Decision

ABSORB:

- weight / KV / workspace separation;
- capacity vs bandwidth separation;
- RAM / VRAM / unified-memory placement framing.

## New semantic classes

- PERSISTENT_HOT
- SESSION_HOT
- PHASE_HOT
- STREAM_COLD
- REUSABLE_WARM

## Safety consequence

STRATA-002 DONTNEED must only apply to explicitly one-shot/COLD consumed ranges.

Never generalize it to active mmap-backed model weights.

## Next action

Freeze a read-only local external-validity design using the same STRATA-002 metrics, then wait for an explicit MVCA finite-ram gate before execution.

## Authority boundary

Conceptual / design only.
