# VOI-001 Implementation

> **Status:** IMPLEMENTED / NOT YET EXECUTED

The calculator implements the frozen B052 model.

## Mathematical split

Empirical uncertainty:

- 100,000 runner-cluster bootstrap resamples over the 16 HYP-003 blocks.

Analytic safety boundary:

- signal correctness threshold a > 1 - q/k.

No invented probability prior is sampled.

## Outputs

For each frozen opportunity frequency q:

- resident-fraction headroom;
- HOT-not-fully-resident risk reduction;
- geometric log-latency headroom factor;
- bootstrap 95% intervals.

For each q and wrong-action penalty k:

- minimum semantic-signal correctness threshold.

## Boundary

The geometric headroom factor is a model quantity under aligned-equivalent, zero-action-cost assumptions.

It is not an achieved speedup.
