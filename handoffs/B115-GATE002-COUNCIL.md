# Bounce Handoff

> **Bounce ID:** B115
> **Status:** COMPLETE / GATE-002 COUNCIL CONVERGED

## Trigger

B114 showed that the GATE-001 break-even threshold depends strongly on misalignment prevalence q.

A fresh Council then atomized the single semantic-signal accuracy parameter used by GATE-001.

## Atomic decomposition

GATE-001 uses one accuracy parameter `a`, which implicitly sets the two class-conditional correctness rates equal.

For a real selective gate the relevant rates are separate:

- sensitivity `t = P(ACT | truly misaligned)`;
- specificity `s = P(NO-ACT | truly aligned)`.

Using the existing empirical primitives:

- `h = A_W - A_N`: wrong-action harm in aligned states;
- `b = M_N - M_C`: correct-action benefit in misaligned states.

The gate beats NO_HINT when:

`q * t * b > (1 - q) * (1 - s) * h`

or equivalently:

`s > 1 - q*t*b / ((1-q)*h)`

when the empirical signs support the comparison.

## Council convergence

Statistics:
- a single aggregate accuracy value is not a sufficient safety contract under asymmetric error cost.

Systems:
- no new PAGEOUT intervention is required to answer the next question;
- EXP-003 already contains the empirical action-cost primitives.

Red-Team:
- false ACT in aligned states must remain explicit because WRONG_PAGEOUT harm is asymmetric.

Authority:
- fail closed when class-conditional calibration is absent.

Economics:
- reuse the existing 16 runner blocks before spending new experiment budget.

## Decision

Create **GATE-002** as a class-conditional policy-frontier analysis.

It must:

- keep arithmetic and log/geometric cost surfaces separate;
- retain the existing q grid;
- sweep sensitivity explicitly;
- solve the minimum required specificity;
- propagate runner-block uncertainty with 100,000 bootstrap resamples;
- report invalid/sign-unstable bootstrap fractions;
- make no production q or predictor-quality claim.

## Next action

Freeze the GATE-002 analysis contract, then implement and run it before considering any new intervention experiment.

## Authority boundary

Analysis only.
No deployed gate and no new memory intervention is authorized.
