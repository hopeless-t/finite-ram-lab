# Bounce Handoff

> **Bounce ID:** B052
> **Status:** COMPLETE / VOI DESIGN FROZEN

## Objective

Freeze a mechanism-agnostic Value-of-Information / decision-headroom analysis after HYP-003.

## Council result

VOI-001 is a computational analysis, not a new experiment and not a mechanism selection.

It parameterizes future-demand conflict frequency q instead of pretending the lab already knows production prevalence.

It uses HYP-003 runner blocks and a 100,000-resample cluster bootstrap to propagate empirical uncertainty.

Wrong/stale information is represented by a separate scenario multiplier k.

The analytic safety threshold is:

    signal accuracy a > 1 - q/k

EXP-002 motivates exploring k > 1 but is not numerically pooled into HYP-003.

## Frozen inputs

- HYP-003 run: 36247200797
- aggregate artifact: 10907254611
- block input snapshot and provenance committed under analysis/inputs/

## GitHub artifacts

- docs/VOI-001.md
- specs/VOI-001.json
- analysis/inputs/VOI-001-HYP003-blocks.csv
- analysis/inputs/VOI-001-HYP003-provenance.json

## Next recommended bounce

Implement the deterministic VOI-001 bootstrap/headroom calculator and run it in GitHub Actions. Record results separately from experimental findings.

## Authority boundary

VOI-001 is bounded decision support. It does not choose a coordinator, hint API, or kernel change.
