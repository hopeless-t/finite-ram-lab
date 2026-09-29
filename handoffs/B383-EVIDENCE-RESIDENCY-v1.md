# B383 — Evidence Residency v1

## Status

COMPLETE / CI PASS.

No scientific hosted experiment launched.
No local-PC execution.
No Google Drive mutation or GitHub artifact deletion performed.

## Goal

Turn GitHub into the HOT research index while preserving full evidence outside GitHub without breaking chain of custody.

Lifecycle:

`HOT -> WARM -> COLD -> RESTORE -> VERIFY`

Core invariant:

`location != evidence identity`

Evidence identity is the sorted set of:
- relative path
- byte length
- SHA-256

plus a stable `content_set_sha256`.

## Implementation

Module:
`src/finite_ram_lab/evidence_residency.py`

Schema:
`schemas/EVIDENCE-RESIDENCY-MANIFEST-v1.schema.json`

Contract:
`docs/EVIDENCE-RESIDENCY-v1.md`

Tests:
`tests/test_evidence_residency.py`

CLI:

`frl evidence-manifest`

`frl evidence-verify`

## Integrity behavior

The implementation:
- recursively hashes evidence files;
- rejects symlinks;
- sorts manifest paths;
- records size + SHA-256 per file;
- derives a stable content-set digest;
- detects missing files;
- detects modified files;
- detects extra files unless explicitly allowed;
- excludes an in-bundle output manifest from its own content set.

## Storage references

Manifest storage references use:

`TIER:PROVIDER:LOCATOR`

Example:

`COLD:google-drive:frl-cold/MEMCG-005G-G0/run-123`

Locators are intentionally opaque.

Do not commit:
- private bearer URLs;
- credentials;
- absolute local paths containing private/user-specific details.

The repository does not embed Google Drive credentials or APIs.

## G-F sizing audit

Run:
`36577573774`

Artifacts:
- 48 block artifacts
- 1 aggregate artifact
- total compressed size = 1,462,488 bytes ~= 1.395 MiB
- block mean ~= 29,694 bytes
- aggregate = 37,159 bytes

Conclusion:

current MEMCG artifacts are small.

Residency is primarily an integrity/lifecycle improvement and future-scale safeguard, not an emergency storage-cost fix.

## Recommended new-run policy

HOT:
- Git-tracked result/spec/manifest/rare specimens
- raw GitHub block artifacts as short transient cache

Default proposal:
- raw block artifact retention: 7 days
- aggregate artifact retention: 30 days

WARM/COLD:
- full evidence on private Google Drive and/or local archive

Before intentional deletion/expiry reliance:
1. manifest exists;
2. off-GitHub copy exists;
3. restored files pass `frl evidence-verify`.

Important evidence should preferably have both local and Drive replicas verified.

## CI

Validation run:
`36589409532`

Result:
`success`

Passed:
- install
- compile
- unit tests
- Monte Carlo smoke
- environment probe smoke

## Next

Integrate EVIDENCE-RESIDENCY into MEMCG-005G-G0 implementation:
- raw block retention 7 days;
- aggregate retention 30 days;
- generate aggregate manifest;
- do not automate destructive artifact deletion;
- archive externally after run.

G0 Stage A scientific launch still requires Human compute approval.
