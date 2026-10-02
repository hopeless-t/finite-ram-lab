# FR-CLM-001D — Trajectory Survival Qualification Receipt

Status: **PASS / SYNTHETIC TRAJECTORY HARNESS VALIDATED**

## Frozen qualification

- workflow run: 37004570370
- job: 110829715752
- execution head: 8ea44a1c51b9b86a3e5fe19d69a65cb773f56461
- targeted tests: 6/6 PASS
- selector error probability: 0.01
- replicates per budget: 2,048
- budgets: 2, 4, 6
- maximum trajectory length: 32
- artifact ID: 11224707542
- artifact ZIP SHA256: 9649f494fb8fcfc77ec7a6ae20619b1b59f90c7eb020e284d90e85e3ff6b45a0
- spec SHA256: f9c136ec0e2577345ab0c12536920129796526322e424aef558251b27b096181
- result SHA256: 3b4ec302bc1f5339e2db8bb283ae4af5e626a7af2b76f12977138848a57bd649

## Primary result

One-step and endpoint-only measurements substantially overstate uninterrupted
trajectory survival in the frozen synthetic rewrite process.

At length 32:

| budget | trajectory survival | endpoint success | masking gap | recovered trajectories |
|---:|---:|---:|---:|---:|
| 2 | 0.270020 | 0.958008 | 0.687988 | 1,468 |
| 4 | 0.571289 | 0.999512 | 0.428223 | 877 |
| 6 | 0.625977 | 1.000000 | 0.374023 | 766 |

Larger resident budget improves uninterrupted survival, but none of the tested
finite budgets makes a 32-step trajectory equivalent to its endpoint score.

## Cold-start benchmark blindness

Budget 4 and budget 6 are both exact on the one-step cold-start benchmark:

- budget 4, length 1: 1.0
- budget 6, length 1: 1.0

Yet at length 32:

- budget 4 trajectory survival: 0.571289
- budget 6 trajectory survival: 0.625977

For those two budgets, the naive cold-start independence projection is:

`1.0 ^ 32 = 1.0`

which is dramatically wrong.

The failure is not arithmetic. The per-step hazard changes as the resident
working set is repeatedly rewritten and the candidate ecology evolves.

Therefore:

`one-step exactness is not a sufficient estimator of long-run semantic survival`.

## Refresh-boundary masking

Required state is refreshed every 8 steps.

This creates a strong distinction between current-state correctness and
trajectory correctness.

Representative budget-4 values:

| length | trajectory survival | endpoint success |
|---:|---:|---:|
| 7 | 0.883301 | 0.883301 |
| 8 | 0.882324 | 0.998535 |
| 15 | 0.758301 | 0.863281 |
| 16 | 0.757812 | 0.999023 |
| 31 | 0.571289 | 0.871094 |
| 32 | 0.571289 | 0.999512 |

At each refresh boundary, endpoint correctness jumps toward 1.0 while
all-steps trajectory survival cannot erase prior failures.

Budget 6 shows the same pattern and reaches endpoint success 1.0 at lengths
8, 16, and 32 despite length-32 trajectory survival of only 0.625977.

## Budget effect

At length 32:

`budget 2 < budget 4 < budget 6`

for uninterrupted trajectory survival.

This preserves the FR-CLM-001C finding that resident redundancy can compensate
for imperfect selection, but adds an important qualification:

the benefit must be measured across the trajectory, not only at a final
checkpoint.

## Recovery is real, and that is exactly why endpoint-only scoring is unsafe

At length 32, many trajectories are currently correct after having failed
earlier:

- budget 2: 1,468 recovered trajectories
- budget 4: 877
- budget 6: 766

These are not false positives in the endpoint metric. The endpoint is genuinely
correct.

The information loss is historical:

`endpoint correct != uninterrupted semantic validity`.

The appropriate metric depends on whether the task can tolerate temporary
semantic corruption and later recovery.

## Relation to Low-interference cognition

This synthetic result gives the trajectory-survival hypothesis a concrete
measurement contract.

A small local interference probability can matter in two distinct ways:

1. it can accumulate across repeated rewrites;
2. later refresh can hide earlier loss from endpoint-only evaluation.

Therefore long-running agent evaluation should retain:

- first failure step;
- all-steps survival;
- endpoint success;
- recovery events;
- failure-state biopsy.

## Important non-claim

This is a synthetic finite-state rewrite process.

It does not establish a failure rate for any CLM, language model, provider, Pi,
or KITten implementation.

The periodic refresh mechanism and 1% selector error are experimental controls.

## Claim ceiling

**SYNTHETIC_TRAJECTORY_SURVIVAL_ONLY**

## Next

FR-CLM-001E should hold the marginal rewrite-error rate approximately fixed
while changing temporal dependence:

- independent errors;
- persistent bad-state episodes;
- bursty errors.

The question is whether matched one-step error rates can produce materially
different long-run trajectory survival.
