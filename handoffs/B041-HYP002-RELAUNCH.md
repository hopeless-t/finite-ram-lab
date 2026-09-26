# Bounce Handoff

> **Bounce ID:** B041  
> **Status:** COMPLETE / COMPUTE RELAUNCHED

## Objective

Relaunch HYP-002 from the unchanged frozen scientific contract after the B040 integrity-baseline implementation fix.

## Canonical inputs

- `handoffs/B040-HYP002-RUN1-INVALID.md`
- `analysis/HYP-002-run1-invalid.md`
- `specs/HYP-002.json`
- `docs/HYP-002.md`

## Changes in this bounce

Scientific design:

```text
UNCHANGED
```

Workflow auditability only:

- trial stdout is no longer discarded;
- future block failures will retain workload summaries in job logs.

## Relaunch

- workflow/audit commit: `87fa695e3141020056da24452b178f6ed97218cf`
- run: `36243341566`

## Frozen exclusion

Run `36243199948` remains INVALID and must never be pooled.

Only the relaunched run may contribute HYP-002 scientific evidence if execution checks pass.

## Next recommended bounce

> Read the completed retry using the frozen HYP-002 analysis. If valid, record the scientific finding. If invalid, classify and record the failure before any further patch.

## Authority boundary

This bounce only relaunches the pre-registered experiment.
