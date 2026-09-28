# Bounce Handoff

> **Bounce ID:** B206
> **Status:** COMPLETE / STRATA-005 EXTERNAL-VALIDITY DESIGN FROZEN

## Result

Rehydrated B205 and converted its next question into a minimal cross-pressure design.

STRATA-005 varies only MemoryHigh (144 and 176 MiB) while preserving the STRATA-004 workload and runner family. The existing 160 MiB result remains the anchor.

Proposed panel: buffered plus DONTNEED 48 / 64 / 80 / 96 MiB; four independent runner blocks per pressure setting; 40 new hosted trials total.

## Council

Converged on pressure-first external validity. Cross-substrate variation is deferred because varying pressure and substrate together would obscure attribution.

## Monte Carlo

Deferred until cross-pressure empirical observations exist.

## Next action

Implement the frozen STRATA-005 spec/workflow and validation tests without launching it. Keep launch as a separate bounce.

## Authority boundary

Hosted research only. No local-PC execution. No launch inferred. No retry/rerun inferred. No OSS default cadence authorized.
