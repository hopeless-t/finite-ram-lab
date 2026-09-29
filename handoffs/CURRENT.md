# CURRENT

> Latest bounce: B379
> Stage: MEMCG-005G-F COMPLETE / MATH-007 ROBUSTNESS COMPLETE
> Stop: HUMAN_COMPUTE_APPROVAL_FOR_005G-G

## MEMCG-005G-F

Run:
`36577573774`

Artifact:
`11037439387`

Digest:
`sha256:da5eb0c5b3ab3bd17d078dda7ff052c2ed6d70af1949fb4145b0f150daf4f346`

Frozen decision:
`REJECT_OR_UNRESOLVED_HARD_STEP`

Reason:
two valid REMOTE_LOW non-{0,Q64} failure morphologies violated the frozen invariant.

Restricted threshold signal:
- MAP T=10
- posterior 95.58%
- MAP/second odds 34.3:1
- T10 split Fisher p=2.268e-4

## MATH-007

`docs/MATH-007-T10-ROBUSTNESS-AND-MORPHOLOGY.md`

Exploratory robustness:
- remove two nonzero morphologies -> T10 posterior 97.50%
- block-conditioned permutation 300k -> p ~=3.50e-4
- leave-one-block-out -> T10 MAP in 48/48 fits

Accepted:
exact-zero and nonzero anomalous first-touch deltas must be treated as separate phenotypes prospectively.

## Next candidate

Draft:
`docs/MEMCG-005G-G-EXACT-ZERO-REPLICATION-DRAFT-v0.md`

Preferred scale:
96 hosted blocks x60 candidates =5760 total.
960 candidates/arm.

Monte Carlo calibration:
- P(MAP=T10) ~97.7%
- P(T10 posterior >=.90) ~90.3%

This is materially larger hosted compute.
Do not implement/launch until Human explicitly approves the compute scale.

## Collaboration

Draft:
`docs/DISTRIBUTED-RARE-STATE-REPLICATION-DRAFT-v0.md`

Hosted research only.
No local-PC execution.
