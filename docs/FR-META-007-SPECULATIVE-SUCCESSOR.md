# FR-META-007 — Speculative Detached Successor

Status: **DOGFOOD PROTOCOL CANDIDATE / v0.2 AFTER ANCESTRY BIOPSY**

Parent: **FR-META-006**

## Bottleneck

A worker can often build the next bounded transition while the parent candidate
is still in CI. Publishing that successor immediately creates unnecessary branch
and workflow debt.

## Protocol

Build the immediate successor as unreferenced Git objects only:

1. create blobs;
2. create a tree based on the current parent candidate;
3. create one detached child commit;
4. create no branch, PR, workflow dispatch, or canonical handoff.

The child remains PROVISIONAL.

## v0.1 dogfood failure biopsy

The first dogfood published FR-META-007 immediately after FR-META-006 reported
PASS.

That was too early.

FR-META-006 still needed its qualification receipt commit. Publishing the child
before that receipt meant the child did not contain the final canonical parent
receipt in its ancestry.

The corrected gate is therefore not merely parent PASS.

It is:

    PARENT_RECEIPT_FROZEN

A qualified parent without its receipt keeps the child detached.

## Publication

Only after the parent receipt is frozen may the child ref be published.

If the parent is FAIL, UNKNOWN, IN_PROGRESS, or PASS-without-receipt:

- no child branch;
- no child workflow;
- no authority promotion.

Speculative depth remains exactly one.

## Repair of the first dogfood specimen

The prematurely published v0.1 branch is repaired by a non-force merge commit
that has both:

- the original child commit;
- the frozen FR-META-006 receipt commit

as parents, with the corrected v0.2 tree.

This preserves the mistake as history while restoring canonical ancestry.

## Claim ceiling

**SPECULATIVE_DETACHED_BUILD_PROTOCOL_ONLY**
