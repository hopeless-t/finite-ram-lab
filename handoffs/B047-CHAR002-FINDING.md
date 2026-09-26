# Bounce Handoff

> **Bounce ID:** B047
> **Status:** COMPLETE / FINDING RECORDED

## Objective

Record the frozen CHAR-002 result after validating execution.

## Evidence

- workflow run: 36246723145
- conclusion: SUCCESS
- aggregate artifact: 10907138130
- 16 runner blocks
- 192 trials
- all execution checks passed

## Result

Separate-VMA fault-order contrast:

    second-faulted - first-faulted = +0.081242
    exact two-sided p = 6.1035e-05
    bootstrap 95% = [+0.045693, +0.131753]

Shared-VMA fault-order contrast:

    second-faulted - first-faulted = +0.099680
    exact two-sided p = 3.0518e-05
    bootstrap 95% = [+0.062176, +0.142443]

Separate creation-order effect was not supported.

Shared-VMA address-position evidence was mixed and remains unresolved.

## Finding

The prior A/B residency asymmetry substantially follows initial fault/touch order.

## Repository updates

- findings/CHAR-002-initial.md
- README status advanced through CHAR-002

## Next recommended bounce

Design HYP-003 to independently randomize initial fault/touch order and future semantic HOT identity at 160–162 MiB.

Formal Value-of-Information remains paused until that direct mismatch is measured.
