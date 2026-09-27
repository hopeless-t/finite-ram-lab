# Bounce Handoff

> **Bounce ID:** B147
> **Status:** COMPLETE / LABEL-001 COUNCIL CONVERGED

## Trigger

SIG-001 calibration currently treats the historical EXP-003 `aligned / misaligned` stratum as the class label underlying gate reliability.

That label is assignment-derived:

- initial fault order;
- future HOT position.

A real semantic provider ultimately needs a label grounded in the natural memory state that would occur without intervention.

## Existing evidence available

EXP-003 aggregate run:

- run: `36253713012`
- aggregate artifact: `10910048127`
- artifact SHA-256: `08bfd999833274db962f9a017933aa53216d8fdff8ea003a54b81ce33ebed4d3`
- 384 total trials;
- 16 runner blocks;
- pressure: 160 / 162 MiB.

The aggregate `trials.csv` already contains:

- `hot_fraction`;
- `cold_fraction`;
- `hot_first16_fraction`;
- `cold_first16_fraction`;
- `hot_retouch_ms`;
- assignment-derived `aligned`.

## Contamination boundary

Only the `NO_HINT` arm may be used to define the natural residency outcome.

CORRECT_PAGEOUT and WRONG_PAGEOUT modify residency before `residency_pre_retouch` is measured and therefore cannot define the no-intervention ground-truth class.

## Exploratory intake

The verified aggregate artifact was inspected only to determine whether the label-audit question is worth formalizing.

NO_HINT gives 128 trials:

- assignment-aligned: 64;
- assignment-misaligned: 64.

Define exploratory observable natural misalignment as:

`hot_fraction < cold_fraction`

Observed confusion counts for assignment-misaligned as a proxy:

- TP = 58;
- FP = 6;
- FN = 9;
- TN = 55;
- agreement = 113 / 128 = 0.8828125;
- sensitivity = 0.8657;
- specificity = 0.9016;
- observable-misalignment prevalence = 0.5234.

A runner-block bootstrap exploratory check gave approximate 95% ranges:

- sensitivity: 0.756–0.968;
- specificity: 0.812–0.983;
- agreement: 0.789–0.961.

The continuous natural residency gap also tracks reuse cost strongly in the exploratory intake:

- `hot_fraction - cold_fraction` vs log HOT-retouch Spearman rho ≈ -0.700.

Descriptively:

- observable HOT-underresident group: geometric HOT-retouch ≈ 185.9 ms;
- observable HOT-not-underresident group: geometric HOT-retouch ≈ 1.46 ms.

These exploratory numbers are **not yet promoted findings**.

## Council convergence

### Scientific seat

The assignment label is informative but not identical to actual natural residency.

A real provider should ultimately be calibrated against an observable no-intervention outcome, not against the experimental assignment proxy alone.

### Causal seat

Use NO_HINT only for the class-label audit to avoid post-action contamination.

### Measurement seat

Primary natural residency outcome:

`observable_misaligned = hot_fraction < cold_fraction`

Exact ties are `AMBIGUOUS` and must not be silently forced into either class.

Primary continuous score:

`residency_gap = hot_fraction - cold_fraction`

### Statistics seat

Formal analysis must:

- retain runner-block clustering;
- report pooled and pressure-stratified confusion matrices;
- bootstrap assignment-proxy sensitivity, specificity, prevalence and agreement by runner block;
- quantify association between continuous residency gap and log HOT-retouch latency;
- keep whole-region residency primary;
- treat first-16-MiB residency as secondary sensitivity analysis only.

### Authority seat

This is retrospective label validation only.

It must not:

- train a provider;
- choose a new threshold from the observed data;
- execute PAGEOUT;
- reinterpret the assignment label as useless if imperfect.

## Decision

Create **LABEL-001 — Natural Residency Outcome Audit**.

Use the already-existing EXP-003 aggregate artifact and no new physical experiment.

## Next action

Freeze LABEL-001 analysis contract, then implement/run it as a bounded offline analysis.

## Authority boundary

Retrospective label audit only.
No provider, gate deployment, or memory intervention is authorized.
