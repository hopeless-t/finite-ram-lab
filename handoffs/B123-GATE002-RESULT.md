# Bounce Handoff

> **Bounce ID:** B123
> **Status:** COMPLETE / GATE-002 NUMERICAL RESULT RECORDED

## Evidence

GATE-002 Class-Conditional Frontier run `36258745313` completed successfully.

Artifact:

- id: `10911731381`
- name: `GATE-002-FRONTIER-36258745313`
- ZIP SHA-256: `2e5e11ab504ebef0790667f229e9cdab9d3ad5adfbaf55b026bf8c297b5b86bd`
- local verification matched the GitHub artifact digest exactly
- analysis status: `PASS`
- runner blocks: `16`
- bootstrap resamples: `100000`
- bootstrap seed: `2026092701`
- source EXP-003 trials SHA-256: `29aa46c700b817785bdc67ae4a6eb3c3330887ff5a06efd1f7516aa6ed53ba66`

## Selected class-conditional frontier

Minimum specificity required to beat NO_HINT.

| q | sensitivity | Arithmetic point | Arithmetic 95% | Log point | Log 95% |
| ---: | ---: | ---: | --- | ---: | --- |
| 0.10 | 0.50 | 0.781 | [0.593, 0.853] | 0.892 | [0.866, 0.907] |
| 0.10 | 0.80 | 0.650 | [0.349, 0.765] | 0.827 | [0.785, 0.851] |
| 0.10 | 1.00 | 0.563 | [0.187, 0.707] | 0.784 | [0.732, 0.814] |
| 0.25 | 0.50 | 0.344 | [-0.220, 0.560] | 0.677 | [0.598, 0.721] |
| 0.25 | 0.80 | -0.050 | [-0.952, 0.296] | 0.482 | [0.356, 0.553] |
| 0.25 | 1.00 | -0.312 | [-1.440, 0.120] | 0.353 | [0.195, 0.442] |
| 0.50 | 0.50 | -0.968 | [-2.660, -0.319] | 0.030 | [-0.207, 0.162] |
| 0.50 | 0.80 | -2.150 | [-4.856, -1.111] | -0.553 | [-0.931, -0.340] |
| 0.50 | 1.00 | -2.937 | [-6.321, -1.639] | -0.941 | [-1.414, -0.675] |

At q >= 0.75 the selected raw thresholds are well below zero for both metrics across the sampled sensitivity range.

## Sign stability

- arithmetic bootstrap valid/sign-stable fraction: `0.99992`;
- log/geometric bootstrap valid/sign-stable fraction: `1.0`.

Raw negative thresholds are preserved as mathematical evidence.
They mean the point-estimate requirement lies below the feasible specificity interval [0,1]; they are not probabilities and must not be clipped silently.

## Interpretation

GATE-002 confirms that aggregate semantic-signal accuracy is not an adequate safety contract under asymmetric wrong-action cost.

At low misalignment prevalence, false ACT on truly aligned states dominates the reliability requirement:

- q=0.10 remains specificity-sensitive even at sensitivity=1.0;
- the log/geometric surface is materially more conservative than the arithmetic surface.

At higher q, the observed misaligned-state benefit can dominate aligned-state wrong-action harm in the empirical mixture, but this remains a policy projection over the frozen EXP-003 environment.

## Next action

Run a fresh pseudo-Council over whether any new execution experiment is justified or whether the next uncertainty is predictor/calibration evidence.

## Authority boundary

Policy-frontier evidence only.
No production q, sensitivity, or specificity is estimated.
No deployed gate or new memory intervention is authorized.
