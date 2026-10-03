# FR-META-009 Receipt

Status: **PASS / NON-MAIN CI CONCURRENCY QUALIFIED**

Implementation qualification:

- workflow run: 37137465848
- job: 111244801652
- execution head: a6d30be099e74ed4e5512a2127c73704b3c94321
- qualification artifact ID: 11279475710
- artifact ZIP SHA256: a408eb394b87f04741d1961df15647942cf4bbbddb286e34540fdaa4e5b419e7
- auto-qualified module: fr_meta_009_ci_concurrency
- qualifier status: PASS

Observed duplicate motivating specimen:

- head SHA: 447a027c7fdc5b91450de8967b28ea4d956e5006
- receipt push CI: 37136849854
- PR CI: 37136854358
- start separation: 4 seconds
- both validated the same head SHA

Concurrency policy:

    group = github.workflow + (github.head_ref || github.ref_name)
    cancel-in-progress = github.ref_name != main

Safety:

- main CI is never cancel-in-progress;
- workflow name remains in the group, preventing cross-workflow cancellation;
- implementation CI must PASS before a receipt is written;
- the later PR CI validates the receipt head if it supersedes receipt-push CI.

Decision:

**CANCEL_SUPERSEDED_NON_MAIN_CI_BY_HEAD_BRANCH**

The immediate receipt+PR dogfood is intentionally performed after this commit.
Its cancellation result is an operational observation, not a precondition for
this implementation qualification receipt.

Claim ceiling:

**CI_CONCURRENCY_OPTIMIZATION_ONLY**
