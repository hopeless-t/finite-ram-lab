# FR-META-004 — Loop-Speed Governor

Status: **DOGFOOD PROTOCOL CANDIDATE**

Parent: **FR-META-003**

## First speed biopsy

The first recursive dogfood found a concrete self-inflicted bottleneck.

PRs #103, #104, and #105 each reached a qualified receipt, but each used:

- 6 commits;
- 8 push-triggered workflow runs;
- 2 pull-request-triggered runs;
- 10 total workflow runs.

The repeated pattern came from creating code, tests, spec, documentation,
workflow, and receipt as separate commits.

That is useful provenance, but it is unnecessary CI fan-out for one coherent
durable transition.

## Protocol change

For a new coherent research transition:

1. create all file blobs without publishing a branch;
2. create one tree on the canonical parent;
3. create one detached commit;
4. publish the branch directly at that final commit;
5. let ordinary CI and the dedicated qualification workflow run once;
6. open the PR only after that commit exists;
7. if qualification fails, preserve the failed commit and add exactly one
   explicit fix commit.

No force push is required.

## Exact fan-out effect

Historical mean:

- commits: 6;
- workflow runs: 10;
- push runs: 8.

Candidate expectation:

- commits: 1;
- workflow runs: 3;
- push runs: 2.

Therefore the expected structural reductions are:

- commits: 83.33%;
- total workflow runs: 70%;
- push workflow runs: 75%.

These are fan-out reductions, not wall-clock speed claims.

## Failure / diagnosis trade-off

Atomic publication can make a failing change larger than an incremental commit.
FR-META-004 therefore runs a synthetic rework sensitivity rather than pretending
the trade-off does not exist.

Across defect probabilities 5%, 15%, and 30%, and diagnosis penalties of 1, 3,
and 6 equivalent run units, the frozen toy model retains positive mean run-unit
savings.

This does not prove every future bundle should be large. The unit remains one
coherent durable transition. Unrelated research questions must still be split.

## Governor rule

Promote:

    ASSEMBLE_DETACHED_ATOMIC_COMMIT_THEN_PUBLISH_BRANCH

Fallback:

    IF_QUALIFICATION_FAILS_CREATE_ONE_EXPLICIT_FIX_COMMIT

Never optimize speed by:

- skipping tests;
- treating UNKNOWN as success;
- force-overwriting failed evidence;
- widening execution authority;
- combining unrelated scientific questions into one commit.

## Why this matters for recursive improvement

The self-improvement loop now has a concrete operational target:

    qualified durable transitions
    -----------------------------
      repository / CI fan-out

The numerator is protected by evidence and qualification gates.
The denominator is where speed optimization is allowed.

## Dogfood experiment

FR-META-004 itself must be created as one detached atomic commit containing its
source, tests, spec, documentation, and dedicated workflow, then published as a
new branch.

That makes the implementation itself the first A/B specimen.

## Claim ceiling

**REPOSITORY_WORKFLOW_FANOUT_OPTIMIZATION_ONLY**
