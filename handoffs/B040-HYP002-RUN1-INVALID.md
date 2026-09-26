# Bounce Handoff

> **Bounce ID:** B040  
> **Status:** COMPLETE / INVALID RUN PATCHED

## Objective

Classify the failed first HYP-002 launch, identify root cause, patch only the implementation defect, and preserve the frozen scientific contract.

## Failed run

- run: `36243199948`;
- all 16 block jobs failed during the first trial;
- aggregate skipped;
- scientific status: **INVALID / NO EVIDENCE**.

## Root cause

Content-integrity baseline digest was captured before the experiment's intentional recency-preparation writes.

Therefore the designed writes themselves guaranteed a final digest mismatch.

## Patch

Moved integrity-baseline capture to after recency preparation and before the measured burst/pressure phase.

Patch:

```text
a27a6ec9707c053ae41f5fe410f4f92ea0f88fcc
```

## Scientific contract

Unchanged:

- 16 runner blocks;
- 128 trials;
- 160 / 162 MiB;
- recent A/B;
- HOT A/B;
- exact sign-flip primary;
- no hint/intervention.

No scientific data from run 36243199948 may be used.

## Repository updates

- `analysis/HYP-002-run1-invalid.md`
- patched `src/finite_ram_lab/hyp002_workload.py`

## Next recommended bounce

> Relaunch HYP-002 from the unchanged frozen design, preferably preserving per-trial stdout/stderr for easier audit, write a launch handoff, and stop.

## Authority boundary

This bounce fixes experiment validation plumbing only.

It does not change or test the HYP-002 hypothesis.
