# FR-META-004 — Loop-Speed Governor

Status: **DOGFOOD PROTOCOL CANDIDATE / v0.2 AFTER FAILURE BIOPSY**

Parent: **FR-META-003**

## First speed biopsy

PRs #103, #104, and #105 each used 6 commits, 8 push-triggered runs,
2 pull-request-triggered runs, and 10 total workflow runs.

The repeated pattern came from publishing code, tests, spec, documentation,
workflow, and receipt as separate commits.

## First model bug caught by the recursive loop

The initial FR-META-004 model predicted 10 -> 3 workflow runs.

That omitted the post-qualification receipt commit.

The omission was caught before the result was frozen and is preserved as a
failure-biopsy result rather than rewritten away.

The corrected full qualified lifecycle is:

1. detached atomic implementation bundle -> ordinary CI + dedicated workflow;
2. one receipt commit after qualification -> ordinary push CI;
3. open PR only after the receipt -> one PR CI.

Therefore the current safe expectation is:

- 2 commits instead of 6: **66.67% fewer**;
- 4 workflow runs instead of 10: **60% fewer**;
- 3 push runs instead of 8: **62.5% fewer**.

These are structural fan-out reductions, not wall-clock claims.

## Protocol

For one coherent research transition, create all implementation blobs/tree in
one detached commit, then publish the branch at the final commit.

If qualification passes, create exactly one receipt commit and only then open
the PR. If qualification fails, preserve the failed commit and add one explicit
fix commit.

No force push is required.

## Synthetic rework sensitivity

A bundle can make a failing change larger than an incremental commit, so the
governor retains a defect/rework sensitivity model.

Across defect probabilities 5%, 15%, and 30%, and diagnosis penalties of
1, 3, and 6 equivalent run units, mean modeled savings remain positive.

This is synthetic decision support only.

## Hard speed boundary

Never gain speed by skipping tests, collapsing UNKNOWN into success,
force-overwriting evidence, widening authority, or combining unrelated
scientific questions into one transition.

## Dogfood

FR-META-004 itself was first published as one 5-file detached atomic commit.
That publication produced exactly two push workflows: ordinary CI and the
dedicated FR-META-004 qualification workflow.

The initial dedicated workflow passed. The v0.2 correction is an explicit
theory-update commit caused by the receipt-tax biopsy.

## Claim ceiling

**REPOSITORY_WORKFLOW_FANOUT_OPTIMIZATION_ONLY**
