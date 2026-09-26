# Bounce Handoff

> **Bounce ID:** B106
> **Status:** COMPLETE / EXP-003 FINDING RECORDED

## Main result

In the prospectively defined misaligned stratum:

- HOT-retouch CORRECT/NO_HINT = 0.01446×;
- exact p = 1.5259e-05;
- bootstrap 95% = [0.00459, 0.04988].

End-to-end work:

- CORRECT/NO_HINT = 0.17723×;
- exact p = 1.5259e-05;
- bootstrap 95% = [0.11443, 0.28538].

Thus EXP-003 supports net benefit in the misaligned stratum.

## Red-Team

WRONG_PAGEOUT strongly harmed already-aligned states:

- HOT WRONG/NO_HINT = 39.35×;
- total WRONG/NO_HINT = 2.439×.

Within the already-misaligned stratum, WRONG was much worse than CORRECT but not worse than NO_HINT.

Therefore wrong-action cost is context-dependent rather than a single universal penalty.

## Scientific transition

The next question is no longer whether semantic information can have value.

It is whether a **selective gate** can safely decide ACT versus NO-ACT using only pre-intervention observable information.

## Next action

Run a fresh pseudo-Council for a gated-intervention experiment.

Do not tune PAGEOUT range and do not introduce a stronger intervention.

## Authority boundary

No deployment or architecture commitment.
