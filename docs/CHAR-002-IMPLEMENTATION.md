# CHAR-002 Implementation Notes

> **Status:** IMPLEMENTED / NOT YET LAUNCHED

The executable implementation follows the frozen `specs/CHAR-002.json` design.

## Components

- `char002_workload.py`
  - separate-VMA construction order;
  - independent initial fault order;
  - actual virtual-address capture;
  - shared-VMA lower/upper range observation;
  - post-burst residency and cgroup telemetry;
  - content integrity and OOM checks.

- `char002_study.py`
  - deterministic 12-cell schedule per runner block;
  - fail-closed factorial completeness;
  - four frozen block-level mechanism contrasts;
  - exact two-sided sign-flip inference;
  - runner-cluster bootstrap;
  - separate-VMA creation/address collinearity report.

## Important implementation boundary

The shared-VMA family uses physical lower/upper halves directly.

No arbitrary A/B semantic relabeling is introduced.

The workload performs no semantic reuse before the primary residency snapshot.

## Launch boundary

Implementation readiness is not evidence.

The GitHub Actions experiment must be launched in a fresh bounce after CI validates this code.
