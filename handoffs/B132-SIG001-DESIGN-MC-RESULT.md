# Bounce Handoff

> **Bounce ID:** B132
> **Status:** COMPLETE / SIG-001 DESIGN-MC RESULT RECORDED

## Evidence

SIG-001 Calibration Design Monte Carlo run `36259298807` completed successfully.

Artifact:

- id: `10911966633`
- name: `SIG-001-DESIGN-36259298807`
- ZIP SHA-256: `88d6932267b7f0dfcb103166d4e168c9b97169ef15180d709484793ddb1f748a`
- local verification matched the GitHub artifact digest exactly
- analysis status: `PASS`
- simulation repetitions: `20000` per scenario/sample-size cell
- family-wise alpha: `0.05`
- Bonferroni component alpha: `0.0125`
- unsafe controls pass: `true`

## Conservative empirical action-cost ratios

Primary log/geometric total-work:

- point b/h: `1.940698`
- conservative lower ratio: `1.643195`
- bootstrap 95%: `[1.676194, 2.404999]`
- valid fraction: `1.00000`

Secondary arithmetic total-work:

- point b/h: `3.936937`
- conservative lower ratio: `2.504307`
- bootstrap 95%: `[2.644877, 7.319733]`
- valid fraction: `0.99991`

## Primary certification result

Target: at least 80% certification probability.

| Scenario | q | sensitivity | specificity | Minimum N | Rate at minimum N |
| --- | ---: | ---: | ---: | ---: | ---: |
| LQ_STRONG | 0.10 | 0.90 | 0.95 | 512 | 0.827 |
| LQ_LOW_SENS | 0.10 | 0.70 | 0.95 | 1024 | 0.857 |
| MQ_MODERATE | 0.25 | 0.80 | 0.80 | 512 | 0.909 |
| MQ_STRONG | 0.25 | 0.90 | 0.90 | 256 | 0.997 |
| HQ_MODERATE | 0.50 | 0.50 | 0.80 | 256 | 0.992 |

Low-q borderline provider:

- q=0.10
- sensitivity=0.90
- specificity=0.85
- point GATE-002 requirement: `0.80593`
- no tested N reached the 80% certification target
- certification at N=8192: `0.04175`

Unsafe controls:

- q=0.10, t=0.90, s=0.75: false certification = `0.0` at all tested N;
- q=0.25, t=0.80, s=0.40: false certification = `0.0` at all tested N.

## Interpretation

The fail-closed calibration rule strongly separates clearly safe and clearly unsafe synthetic provider regimes.

Low-q operation is expensive to certify when true specificity is only slightly above the conservative action-cost frontier.

This is desirable safety behavior but implies that a borderline low-q provider may require far more than 8,192 labeled windows before ACT can be admitted.

## Next action

Run a fresh pseudo-Council.

The Council should decide whether to:

1. extend only the low-q borderline sample-size tail to locate its calibration burden; or
2. stop sizing and freeze a practical provider admission requirement that excludes borderline regimes.

Do not launch any PAGEOUT experiment.

## Authority boundary

Calibration-design evidence only.
No real provider has been measured.
No predictor, deployed gate, or memory intervention is authorized.
