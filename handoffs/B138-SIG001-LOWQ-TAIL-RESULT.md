# Bounce Handoff

> **Bounce ID:** B138
> **Status:** COMPLETE / SIG-001 LOW-Q TAIL RESULT RECORDED

## Evidence

SIG-001 Low-Q Tail Monte Carlo run `36259509674` completed successfully.

Artifact:

- id: `10910819749`
- name: `SIG-001-LOWQ-TAIL-36259509674`
- ZIP SHA-256: `614367b9ea36e6ba89d0237cac913c0b0be761bba3a5f1806ef86043a2cf261a`
- local ZIP verification matched the GitHub artifact digest exactly
- embedded `spec.json` SHA-256: `b1eb71dddb9129c6a42b786a8da6b31aaf24fbd303d4cc3e72b56fadda8e6b55`
- embedded spec matched the frozen B134 spec byte-for-byte
- analysis status: `PASS`
- unsafe controls pass: `true`

## Primary low-q tail result

All scenarios:

- q = `0.10`
- sensitivity = `0.90`
- primary surface = log/geometric total-work
- conservative action-cost ratio lower bound = `1.643195`
- target certification probability = `0.80`

### Borderline specificity 0.85

| N | Certification rate |
| ---: | ---: |
| 2,048 | 0.00285 |
| 4,096 | 0.00970 |
| 8,192 | 0.04130 |
| 16,384 | 0.17705 |
| 32,768 | 0.57745 |
| 65,536 | 0.96380 |
| 131,072 | 0.99990 |

First tested N meeting the frozen 80% target: **65,536**.

### Intermediate specificity 0.90

| N | Certification rate |
| ---: | ---: |
| 2,048 | 0.83450 |
| 4,096 | 0.99815 |
| 8,192 | 1.00000 |

First tested N meeting the frozen target: **2,048**.

### Unsafe specificity 0.75

False certification remained `0.0` at every tested N through 131,072.

## Interpretation

The calibration burden has a sharp low-q evidence cliff near the conservative admission frontier.

A modest specificity improvement from 0.85 to 0.90 changes the first tested 80%-certification sample size from 65,536 to 2,048 labeled windows under the frozen q=0.10, sensitivity=0.90 scenario.

Therefore calibration sample size should not be treated as a fixed universal constant. Admission should remain evidence-driven and fail closed.

## Stop rule honored

Do not automatically extend the sample-size tail again.

## Next action

Run a fresh Council to freeze the practical observational calibration protocol before any real semantic provider is measured.

## Authority boundary

This is synthetic calibration-design evidence.
No real provider has been measured.
No predictor, deployed gate, or memory intervention is authorized.
