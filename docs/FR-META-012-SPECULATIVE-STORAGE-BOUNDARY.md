# FR-META-012 — Speculative Storage Reliability Boundary

Status: **DOGFOOD PROTOCOL CORRECTION**

Parent: **FR-META-011**

Supersedes the durable-storage assumption in FR-META-007.

## Failure specimen

While FR-META-010 was qualifying, FR-META-011 was assembled as an unreferenced
Git commit:

    5f8b37de4694652064eeef7f468294de5f4c5fb0

By the time the parent receipt was ready, both retrieval routes failed:

- Contents API by commit ref -> 404, no commit found for ref;
- Git commit-object API -> 404 Not Found.

The canonical parent and child branches were unaffected.

## Theory update

An unreferenced Git object may be useful as a very short-lived implementation
detail, but this tool path does not provide a durable retrieval contract for it.

Therefore speculative build-ahead is split into two classes.

### Ephemeral build-ahead

Allowed while parent CI runs:

- design;
- source draft construction;
- exact patch planning;
- calculation;
- test/spec drafting.

None of this is canonical or durable until materialized.

### Durable materialization

Only after the parent receipt is frozen:

1. read the receipt tree;
2. reconstruct/apply the prepared delta;
3. create one final atomic child commit;
4. publish the child branch.

The final commit is the first durable/canonical candidate state.

## Why this is still fast

The expensive cognitive and design work can still overlap parent CI.

The short Git materialization step remains on the critical path, but the
protocol no longer risks losing work by assuming an unreferenced object will be
retrievable later.

## Invariants

- speculative depth remains one;
- no child branch before parent receipt;
- no authority from ephemeral work;
- no retry/promotion based on missing speculative state;
- repository state wins.

## Claim ceiling

**SPECULATIVE_STORAGE_RELIABILITY_BOUNDARY_ONLY**
