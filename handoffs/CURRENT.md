# CURRENT

> Latest bounce: B383
> Stage: EVIDENCE RESIDENCY v1 COMPLETE / CI PASS
> Stop: G0 IMPLEMENTATION PREP / SCIENTIFIC LAUNCH REQUIRES HUMAN APPROVAL

## Evidence residency

Lifecycle:

`HOT -> WARM -> COLD -> RESTORE -> VERIFY`

Core rule:

`location != evidence identity`

Manifest identity:
- relative path
- byte size
- SHA-256
- stable content-set SHA-256

Implementation:
`src/finite_ram_lab/evidence_residency.py`

Schema:
`schemas/EVIDENCE-RESIDENCY-MANIFEST-v1.schema.json`

Contract:
`docs/EVIDENCE-RESIDENCY-v1.md`

Commands:
- `frl evidence-manifest`
- `frl evidence-verify`

## Storage policy

HOT / GitHub:
- result
- spec
- aggregate
- manifest
- rare specimen receipts
- short-lived raw block artifacts

WARM/COLD:
- private Google Drive and/or local archive

Proposed new-run retention:
- raw block artifacts: 7 days
- aggregate artifact: 30 days

Do not intentionally remove HOT raw evidence until at least one restored off-GitHub copy passes manifest verification.

Prefer two verified COLD replicas for high-value runs:
- local
- Google Drive

No Drive credentials or private URLs in the public repo.

## G-F sizing anchor

Run `36577573774`:
- 49 artifacts total
- 48 blocks
- total compressed size ~=1.395 MiB
- block mean ~=29.0 KiB
- aggregate = 37,159 bytes

Current MEMCG artifact volume is small; residency is for durable integrity and future scaling.

## Validation

CI run:
`36589409532 = success`

Compile, unit tests, Monte Carlo smoke, and environment probe all PASS.

## Research mechanism state

B382 remains valid:

PTE page charge reaches the same per-CPU memcg stock before anonymous data allocation.

G0 minimal alias breaker:
- C8=8
- P8=08
- C9=9
- P9=09
- H10=10
- H32=32

Primary:
`P8+P9 vs C8+C9`

Failure-only two-touch VmPTE/stock biopsy remains part of G0.

## Next

Implement G0 Stage A workflow with Evidence Residency v1.

Scientific hosted launch:
NOT YET AUTHORIZED.

No local-PC execution.
Large 5760-candidate G-G remains DEFERRED.
