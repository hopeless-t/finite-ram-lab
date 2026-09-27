# CURRENT

> **Latest bounce:** B173
> **Stage:** STRATA-002 / COUNCIL COMPLETE

## Parent result

STRATA-001 pilot is canonicalized and showed:

- zero HOT-residency headroom in tested file-pressure cells;
- large page-cache / MemoryHigh-pressure difference between buffered and direct I/O.

## New study

STRATA-002 — Advisory Cold-Stream Cache Control

See:

- `docs/STRATA-002-COUNCIL.md`

## Next action

Freeze STRATA-002-PILOT-v1.

## Individual-PC direction

Test whether ordinary buffered reads plus standard Linux COLD/one-shot advice can capture much of O_DIRECT's memory-pressure benefit without O_DIRECT's operational constraints.

## Authority boundary

Research only.
