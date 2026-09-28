# Bounce Handoff

> **Bounce ID:** B231
> **Status:** STRATA-005 PORTABLE SPEC-PATH REPAIR / CI PENDING

## Rehydration and failed run

Canonical predecessor: B230.

STRATA-005 run `36430416271` was read exactly once in the fresh bounce and had:

- status: completed
- conclusion: failure
- 8 / 8 matrix jobs failed in the same step
- aggregate skipped

One representative failed job log was inspected.

The failure occurred before the first scientific trial could load its spec:

`FileNotFoundError: specs/STRATA-005-EXTERNAL-VALIDITY-v1.json`

Therefore:

- valid STRATA-005 trials from this run: 0
- pressure inference from this run: NONE
- no DONTNEED/headroom conclusion is authorized

## Root cause

The trial executes inside `systemd-run`, whose working directory is not an admissible implicit repository-path contract.

The workflow passed a relative spec path to that child.

Other trial-critical paths were already absolute.

## Pseudo-Council convergence

Options considered:

1. depend on inherited/current working directory;
2. set the systemd unit working directory;
3. make the required spec path explicit and absolute.

Council converged on option 3 because it changes only the exposed interface invariant and does not widen child-process assumptions.

## Repair

The panel now defines:

`SPEC="$GITHUB_WORKSPACE/specs/STRATA-005-EXTERNAL-VALIDITY-v1.json"`

and passes:

`--spec "$SPEC"`

A regression test asserts that the systemd trial panel does not pass the old relative spec path.

No frozen scientific parameter changed.

## Monte Carlo

Not run. There are still no cross-pressure observations.

## Next action

Read ordinary CI for B231 exactly once.

- success -> create a distinct explicit STRATA-005 relaunch marker change;
- pending -> checkpoint EXTERNAL_WAIT;
- failure -> inspect only the newly exposed invariant.

Do not rerun failed run `36430416271`; a future launch, if validated, is a new explicit execution.

## Authority boundary

Hosted research/repository work only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
