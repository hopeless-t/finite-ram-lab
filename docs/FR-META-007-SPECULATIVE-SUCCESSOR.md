# FR-META-007 — Speculative Detached Successor

Status: **DOGFOOD PROTOCOL CANDIDATE / PROVISIONAL UNTIL PARENT PASS**

Parent: **FR-META-006**

## Bottleneck

After an atomic candidate is published, the worker often has useful next work
but must wait for CI before it may safely promote that next work.

Waiting wastes the reasoning / implementation lane. Publishing the successor
immediately is worse because it creates branch sprawl, workflow fan-out, and
authority on top of an unqualified parent.

## Protocol

Build the immediate successor as Git objects only:

1. create blobs;
2. create a tree whose base is the current parent candidate;
3. create one detached child commit;
4. create no branch, tag, PR, workflow dispatch, or canonical handoff yet.

The child remains PROVISIONAL.

When the parent reaches a qualified PASS, create one branch ref pointing to the
already-built child commit.

If the parent is FAIL, UNKNOWN, or still IN_PROGRESS, do not publish the child.

## Bound

Speculative depth is exactly one.

Do not recursively create a chain of grandchildren while the parent remains
unqualified. That would convert latency hiding into speculative branch debt.

## Why this is safe

An unreferenced commit:

- launches no workflow;
- creates no PR;
- changes no canonical branch;
- grants no execution authority.

It is build-ahead, not promotion.

## Dogfood specimen

FR-META-007 itself is assembled as a detached child of the FR-META-006
candidate while FR-META-006 CI is still running.

Its branch may be published only after FR-META-006 reports PASS.

## Claim ceiling

**SPECULATIVE_DETACHED_BUILD_PROTOCOL_ONLY**
