# FR-META-009 — Superseded CI Cancellation

Status: **DETACHED PROVISIONAL UNTIL FR-META-008 RECEIPT**

Parent: **FR-META-008**

## Observed duplicate work

FR-META-006 receipt head
447a027c7fdc5b91450de8967b28ea4d956e5006 launched two full CI runs:

- push run 37136849854 at 16:26:22Z;
- pull-request run 37136854358 at 16:26:26Z.

They validate the same head SHA.

The push run took about 104 seconds wall elapsed; the PR run took about 70
seconds. Both completed even though the later PR run subsumed the receipt-head
validation need.

## GitHub-supported primitive

GitHub Actions supports workflow-level concurrency groups and
cancel-in-progress. The documented pattern includes github.workflow in the
group so unrelated workflows do not cancel each other.

For this repository the candidate group is based on the head branch:

    group = github.workflow + (github.head_ref || github.ref_name)

and cancellation is disabled on main.

Official references:

- https://docs.github.com/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- https://docs.github.com/actions/reference/workflows-and-actions/workflow-syntax

## Expected clean path

FR-META-005 reduced a clean meta transition to three CI triggers:

1. implementation push;
2. receipt push;
3. PR open.

With branch-group cancellation:

- implementation push completes before receipt by protocol;
- receipt push starts;
- PR open starts the same-head branch group;
- PR CI supersedes the receipt push CI.

Thus triggers remain three, but expected full CI completions fall from three to
two.

Fix commits also supersede stale non-main branch CI.

## Safety boundary

Main is never cancel-in-progress.

The workflow name is part of the group key, so one workflow cannot cancel an
unrelated workflow.

Receipt creation remains forbidden until the implementation CI has already
passed.

The final PR CI validates the receipt head.

## Why no Monte Carlo

The relevant GitHub concurrency behavior is explicit and the duplicated-SHA
specimen is directly observed. There is no uncertain parameter whose simulation
would change the routing decision.

## Claim ceiling

**CI_CONCURRENCY_OPTIMIZATION_ONLY**
