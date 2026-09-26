# OPS-002 — Recovery Semantics for Interrupted Bounces

> **Status:** CONVERGED / OPERATING DECISION

## Problem

The phrase "discard everything after the last atomic commit" was too strong.

It could be read as requiring useful calculations, code, or externally launched work to be destroyed merely because the handoff commit did not happen.

That is not the intended provenance rule.

## Converged distinction

```text
Uncheckpointed work
!= erased work

Uncheckpointed work
= not-yet-authoritative work
```

### PROVISIONAL

Reasoning or drafts that exist only in an interrupted session.

They may be reused only after re-verification.

### RECOVERABLE CANDIDATE

Code, files, calculations, or datasets still present in a recoverable workspace.

They may be inspected, validated, and promoted in a dedicated recovery bounce.

### UNRECORDED SIDE EFFECT

Something external already happened:

- GitHub commit;
- workflow launch;
- artifact creation;
- remote mutation.

It must be reconciled. It must never be treated as if it did not happen.

## Recovery outcomes

```text
surviving uncheckpointed state
          ↓ verify
      RECONCILED
       ├─ CANONICAL
       └─ NON-CANONICAL / AUDIT ONLY
```

## Default authority

Until reconciliation completes, the last atomic GitHub checkpoint remains authoritative.

## Principle

> **Lack of a checkpoint removes authority, not necessarily information.**
