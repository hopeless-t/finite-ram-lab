# FR-META-007 — Speculative Detached Successor

Status: **DOGFOOD PROTOCOL CANDIDATE / v0.3 AFTER MATERIALIZATION BIOPSY**

Parent: **FR-META-006**

## Goal

Overlap successor construction with parent CI without creating branch sprawl,
workflow fan-out, or authority on top of an unqualified parent.

## Prepared delta

While the parent is still qualifying, the worker may create blobs, a tree, and
a detached child commit.

That detached commit is not the final child.

It is a prepared delta / compilation cache.

No branch, PR, workflow dispatch, or canonical handoff is created.

## Two dogfood corrections

v0.1 published after parent PASS but before the parent receipt. That was too
early.

v0.2 waited for the receipt, but still described publication as pointing a ref
at the already-built pre-receipt child SHA. That SHA still has the old parent,
so merely waiting does not repair ancestry.

v0.3 freezes the correct rule.

## Correct publication rule

After the parent qualification receipt is frozen:

1. use the receipt commit tree as the new base;
2. reapply the prepared child file delta;
3. create a new final child commit whose parent is the receipt commit;
4. publish the branch ref to that final commit.

The pre-receipt detached SHA is never directly published as the final child.

If the parent is FAIL, UNKNOWN, IN_PROGRESS, or PASS-without-receipt, the
prepared delta remains non-canonical and launches no workflow.

Speculative depth remains exactly one.

## Why this still hides latency

The expensive work is usually source/test/spec/doc construction. That can be
done during parent CI.

After the receipt freezes, only deterministic Git materialization and branch
publication remain on the critical path.

## Claim ceiling

**SPECULATIVE_DETACHED_BUILD_PROTOCOL_ONLY**
