# Bounce Handoff

> **Bounce ID:** B154
> **Status:** COMPLETE / STRATA-001 CAPABILITY PROBE IMPLEMENTED

## Added

- `src/finite_ram_lab/strata001_probe.py`
- `tests/test_strata001_probe.py`
- `.github/workflows/strata-001-capability.yml`

## Probe properties

- independent implementation;
- explicit Strata attribution;
- separate fresh file per arm;
- fsync + POSIX_FADV_DONTNEED preparation;
- mincore file-residency observation;
- same fixed reusable buffer for buffered/direct preadv;
- page-aligned anonymous mmap buffer for O_DIRECT;
- no direct-I/O fallback;
- filesystem/mount context recorded;
- unsupported O_DIRECT => CAPABILITY_HOLD.

## Workflow authority

The capability workflow is manual-only (`workflow_dispatch`).

Committing it does not automatically launch the experiment.

## Next action

Read ordinary repository CI for B154 exactly once.

If CI passes, launch one bounded STRATA-001 capability workflow under the user's explicit authorization to try the study.

## Parallel lane

LABEL-001 fix remains preserved; no result was erased.

## Authority boundary

Capability probe only.
