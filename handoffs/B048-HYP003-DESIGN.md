# Bounce Handoff

> **Bounce ID:** B048
> **Status:** COMPLETE / DESIGN FROZEN

## Objective

Design the direct same-experiment information-gap test after CHAR-002.

## Canonical inputs

- handoffs/B047-CHAR002-FINDING.md
- findings/CHAR-002-initial.md

## Council result

HYP-003 uses a single shared 64 MiB VMA split into lower/upper halves.

Independent factors:

    MemoryHigh: 160 / 162 MiB
    initial fault order: lower→upper / upper→lower
    future HOT position: lower / upper

Frozen allocation:

    16 runner blocks
    8 cells per block
    128 total trials

## Primary contrast

    HOT residency(aligned with second-faulted cue)
    - HOT residency(misaligned / first-faulted)

Exact one-sided sign-flip plus runner-cluster bootstrap.

## Key secondary

    log latency(misaligned) - log latency(aligned)

Positive values mean the information mismatch has reuse cost.

## Monte Carlo decision

No design Monte Carlo. The complete factorial is directly affordable and the relevant fault-order effect was already large in CHAR-002.

## GitHub artifacts

- docs/HYP-003.md
- specs/HYP-003.json

## Next recommended bounce

Implement HYP-003 exactly as frozen, add schedule/analysis tests, commit, and stop before launch.

## Authority boundary

No HYP-003 evidence exists yet.
