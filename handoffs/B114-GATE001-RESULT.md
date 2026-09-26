# Bounce Handoff

> **Bounce ID:** B114
> **Status:** COMPLETE / GATE POLICY NUMERICAL RESULT RECORDED

## Evidence

GATE-001 Empirical Policy Analysis run `36258282271` completed successfully.

Artifact:

- id: `10911541394`
- name: `GATE-001-POLICY-36258282271`
- ZIP SHA-256: `15f97f57146b8d86330b23d8a875e2cf2137a66904330a3a111b1c7e5cf6ba2f`
- local verification matched the GitHub artifact digest exactly
- analysis status: `PASS`
- runner blocks: `16`
- bootstrap resamples: `100000`
- bootstrap seed: `2026092646`

## Break-even semantic-signal accuracy vs NO_HINT

| q | Arithmetic point | Arithmetic 95% | Log point | Log 95% |
| ---: | ---: | --- | ---: | --- |
| 0.10 | 0.696 | [0.551, 0.774] | 0.823 | [0.789, 0.843] |
| 0.25 | 0.432 | [0.290, 0.532] | 0.607 | [0.555, 0.642] |
| 0.50 | 0.203 | [0.120, 0.275] | 0.340 | [0.294, 0.374] |
| 0.75 | 0.078 | [0.043, 0.112] | 0.147 | [0.122, 0.166] |
| 0.90 | 0.027 | [0.015, 0.040] | 0.054 | [0.044, 0.062] |

## Interpretation boundary

The required signal accuracy is strongly prevalence-dependent.

At low misalignment prevalence, especially q=0.10, the log/geometric surface requires substantially higher semantic-signal accuracy than the arithmetic surface.

This analysis does not estimate production q or production signal accuracy and therefore does not authorize a deployed gate.

## Next action

Run a fresh pseudo-Council over the GATE-001 result before authorizing any new intervention experiment.

## Authority boundary

Policy-surface evidence only.
No deployment or GATE-001 intervention experiment is authorized.
