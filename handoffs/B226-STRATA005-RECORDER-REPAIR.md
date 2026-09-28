# Bounce Handoff

> **Bounce ID:** B226
> **Status:** COMPLETE / STRATA-005 RECORDER PATH REPAIRED / CI PENDING

## Readback finding

Post-B225 readback found a semantic contract violation before launch:

- the machine-readable spec declared Recorder enabled;
- the workflow created a JSONL path variable;
- but the workflow invoked `strata004_knee_workload` directly;
- therefore no REC-001 records would have been produced.

No STRATA-005 experiment had launched, so no measurement evidence was contaminated.

## Repair

B226 routes every trial through `strata005_external_validity trial`.

Each trial now:

- creates one exclusive REC-001 JSONL stream;
- writes one run_start;
- writes 24 memory.current checkpoint samples;
- runs the frozen STRATA workload;
- writes one run_end;
- requires exactly 26 records;
- emits trial JSON with raw and normalized outcomes.

Aggregation validates the exact 40-trial design matrix and reports an onset screen in raw MiB and normalized release/high coordinates.

## Launch boundary

Implementation still does not imply launch.

The workflow launches only by manual dispatch or a later commit touching:

`launch/STRATA-005-v1.txt`

## Next action

Read B226 ordinary CI exactly once.

- success -> create explicit STRATA-005 launch marker;
- pending -> EXTERNAL_WAIT;
- failure -> inspect and repair the exposed invariant.

## Authority boundary

Hosted research only. No local-PC execution. No memory-control policy authorized.
