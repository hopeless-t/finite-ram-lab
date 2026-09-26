# VOI-001 Bounded Decision-Headroom Finding

> **Status:** DECISION HEADROOM PRESENT / SAFETY-ACCURACY CONSTRAINT MATERIAL
> **Run:** 36247715310

## Question

Given the HYP-003 same-experiment information gap, how much idealized decision headroom remains as future-demand conflict frequency changes, while keeping wrong/stale-information risk separate?

## Computation

VOI-001 used:

- the 16 HYP-003 runner blocks;
- an immutable block-level input snapshot with provenance;
- 100,000 deterministic runner-cluster bootstrap resamples;
- opportunity-frequency scenarios q = 0.10, 0.25, 0.50, 0.75, 0.90;
- analytic wrong-action penalty scenarios k = 1, 2, 4, 8, 16, 32.

No parametric latency distribution or invented future-workload prior was sampled.

## Empirical HYP-003 gaps entering the model

    aligned - misaligned HOT resident fraction = +0.083124
    misaligned - aligned HOT-not-full risk      = +0.750000
    misaligned / aligned geometric latency      = 77.83x

## Perfect-information headroom scenarios

The model asks what would happen if conflict cases could be converted to aligned-equivalent outcomes at zero action cost.

This is an upper-bound decision model, not an achieved mechanism.

| Conflict q | Resident-fraction gain | HOT-not-full risk reduction | Geometric latency headroom | Bootstrap 95% latency factor |
| ---: | ---: | ---: | ---: | ---: |
| 0.10 | 0.0083 | 0.0750 | 1.55x | [1.36x, 1.72x] |
| 0.25 | 0.0208 | 0.1875 | 2.97x | [2.15x, 3.90x] |
| 0.50 | 0.0416 | 0.3750 | 8.82x | [4.63x, 15.24x] |
| 0.75 | 0.0623 | 0.5625 | 26.20x | [9.96x, 59.49x] |
| 0.90 | 0.0748 | 0.6750 | 50.35x | [15.78x, 134.69x] |

At the HYP-003 randomized design point q=0.50, bootstrap uncertainty was:

    resident-fraction gain median = 0.04140
    95% = [0.01642, 0.06690]

    HOT-not-full risk reduction median = 0.375
    95% = [0.2578, 0.4688]

    geometric latency headroom median = 8.96x
    95% = [4.63x, 15.24x]

## Wrong/stale-information boundary

The simplified asymmetric-loss model uses:

    q = conflict frequency of history-only cue
    a = semantic signal correctness
    k = wrong-action excess-loss multiplier

A signal-driven action beats the history-only baseline only when:

    a > 1 - q/k

At q=0.50:

| Wrong-action multiplier k | Minimum signal accuracy |
| ---: | ---: |
| 1 | > 50.0% |
| 2 | > 75.0% |
| 4 | > 87.5% |
| 8 | > 93.75% |
| 16 | > 96.875% |
| 32 | > 98.4375% |

This makes the asymmetry exposed by EXP-002 architecturally important without numerically pooling EXP-002 into HYP-003.

EXP-002 showed that some wrong semantic actions can be much more harmful than correct actions are beneficial.

VOI-001 therefore shows why a useful mechanism may need not just information, but **high-confidence information plus bounded failure behavior**.

## Interpretation

The information gap is not merely detectable; under the declared HYP-003 loss model it leaves substantial idealized headroom even when conflicts are not universal.

At the same time, the value is fragile to asymmetric wrong-action cost.

The project should therefore avoid the simplistic conclusion:

> more semantic information => automatically better memory management

The evidence instead supports:

> semantic information is potentially valuable when conflict opportunity is material, but the mechanism consuming that information must control stale/wrong-signal downside.

## Relationship to architecture

VOI-001 does not select a userspace coordinator, application hint API, or kernel change.

It narrows the next intervention question.

The earlier EXP-002 correct PAGEOUT test ran at 164 MiB, where later OBS-003 showed much less natural residency-selection headroom than at 160–162 MiB.

A new intervention study at the high-headroom 160–162 MiB conditions is now scientifically justified, provided it retains a wrong-hint Red-Team arm and measures total action cost.

## Next research direction

Design EXP-003:

- strong-pressure levels 160 / 162 MiB;
- independent initial fault order and future HOT semantics;
- CORRECT existing low-authority action;
- NO_HINT baseline;
- WRONG/stale action Red-Team;
- total cost as well as HOT-reuse cost;
- runner-block randomization;
- Monte Carlo design sizing before launch because heavy tails and asymmetric harm matter.

## Authority boundary

VOI-001 is bounded decision support.

The reported headroom factors are not achieved speedups and are not production EVPI.

It authorizes a carefully Red-Teamed intervention study, not deployment or architecture commitment.
