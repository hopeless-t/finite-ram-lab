# EXP-002 Design Study

> **Status:** DESIGN DECISION SUPPORT  
> **Run:** 36228813323

## Question

How much independent runner replication and within-runner repetition should be allocated to the first semantic PAGEOUT performance experiment?

## Monte Carlo model

The design screen modeled the observed transition-zone structure as:

- fast branch around a few milliseconds;
- slow branch around hundreds of milliseconds;
- runner-level heterogeneity in branch probability;
- additional heavy tail.

Baseline NO_HINT slow-branch probability was modeled as 0.25.

Correct semantic preparation scenarios used:

    null      0.25
    modest    0.15
    material  0.10
    strong    0.05

5,000 simulated experiments were run per design/scenario cell.

The design screen used paired runner-block mean log-latency contrasts with a paired t-test as a computational screening surrogate.

The real experiment will use block sign-flip inference.

## Results

| Design | Blocks | Repeats/arm | Total trials | Null FP | Modest detect | Material detect | Strong detect |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| D1_16x4 | 16 | 4 | 192 | 0.049 | 0.227 | 0.503 | 0.824 |
| D2_20x4 | 20 | 4 | 240 | 0.046 | 0.278 | 0.618 | 0.915 |
| D3_20x6 | 20 | 6 | 360 | 0.051 | 0.403 | 0.779 | 0.981 |
| D4_24x4 | 24 | 4 | 288 | 0.050 | 0.324 | 0.702 | 0.961 |

## Pseudo-Council conclusion

Select **D3_20x6**:

    20 independent runner blocks
    6 repeats per arm per block
    3 arms
    360 total trials

Reasons:

1. transition-zone behavior is demonstrably heavy-tailed, so within-block replication remains valuable;
2. 20 independent blocks already proved operationally stable in HYP-001;
3. D3 materially improves simulated detection over D2 for branch-shift effects;
4. D4 uses fewer total trials and more blocks, but D3 retains higher material/strong detection while allowing the final primary test to remain exact over `2^20 = 1,048,576` block sign assignments;
5. the experiment is still not designed to prove equivalence for modest effects.

## Frozen warning

A null primary result weakens a material semantic benefit under this workload; it does not establish zero value for application semantics.
