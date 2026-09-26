# Bounce Handoff

> **Bounce ID:** B134
> **Status:** COMPLETE / SIG-001 LOW-Q TAIL SPEC FROZEN

## Frozen artifact

- `specs/SIG-001-LOWQ-TAIL-MC.json`

## Tail grid

- q: `0.10`
- sensitivity: `0.90`
- specificity:
  - `0.85` borderline
  - `0.90` intermediate
  - `0.75` unsafe control
- sample sizes:
  - 2048
  - 4096
  - 8192
  - 16384
  - 32768
  - 65536
  - 131072
- 20,000 repetitions per cell

All statistical confidence settings and empirical action-cost bootstrap settings are unchanged from the canonical SIG-001 Design-MC.

The workflow must include a copy of this exact spec in its result artifact.

## Stop rule

No automatic sample-size extension after this study.

## Next action

Launch only the frozen low-q tail Monte Carlo using the already-CI-validated SIG-001 calculator.

## Authority boundary

Offline calibration design only.
