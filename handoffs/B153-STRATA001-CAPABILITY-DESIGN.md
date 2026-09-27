# Bounce Handoff

> **Bounce ID:** B153
> **Status:** COMPLETE / STRATA-001 CAPABILITY CONTRACT FROZEN

## Frozen files

- `specs/STRATA-001-CAPABILITY.json`
- `docs/STRATA-001-CAPABILITY.md`

## Probe

Compare on fresh files:

- MMAP;
- BUFFERED_PREAD;
- DIRECT_PREAD / O_DIRECT.

Validate the page-cache mechanism before any memory-pressure claim.

## Fail-closed conditions

- warm file before scan;
- O_DIRECT unsupported;
- alignment error;
- silent fallback;
- direct arm materially populates page cache.

Unsupported direct I/O is `CAPABILITY_HOLD`, not a negative scientific result.

## Next action

Implement the capability probe, unit tests, and a manual-only GitHub Actions workflow.

## Authority boundary

Capability testing only.
