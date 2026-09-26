# MAINT-001 Artifact Roundtrip — Run 1

> **Status:** INVALID CANARY / VERIFIER BUG
> **Run:** 36249088056

## What succeeded

- upload-artifact@v7 uploaded artifact 10908582128;
- download-artifact@v8 downloaded the same artifact successfully;
- GitHub reported matching artifact digest.

## Why the job failed

The maintenance verifier generated `payload.sha256` from the repository root, so the checksum file contained:

```text
maint-artifact/payload.txt
```

The consume job then changed directory into `maint-artifact/` before verification, causing it to look for:

```text
maint-artifact/maint-artifact/payload.txt
```

This is a canary-script bug, not evidence of upload/download corruption.

## Additional observation

The previous Node.js 20 forced-upgrade warning did not appear.

`download-artifact@v8` emitted a separate Node deprecation warning for legacy `Buffer()` usage. This is an upstream action-runtime warning and is not classified as a failed artifact transfer.

## Decision

Fix the checksum-path bug and rerun the roundtrip before authorizing bulk download-artifact migration.
