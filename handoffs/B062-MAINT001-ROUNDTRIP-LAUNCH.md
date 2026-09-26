# Bounce Handoff

> **Bounce ID:** B062
> **Status:** COMPLETE / ARTIFACT ROUNDTRIP LAUNCHED

## Objective

Validate upload-artifact@v7 and download-artifact@v8 without re-running a scientific workflow.

## Added

`.github/workflows/maint-artifact-roundtrip.yml`

The workflow creates a deterministic payload, uploads it, downloads it in a separate job, and verifies its SHA-256.

## Next recommended bounce

Read the roundtrip run only and record PASS/FAIL.

## Authority boundary

Maintenance validation only. Produced artifact is not scientific evidence.
