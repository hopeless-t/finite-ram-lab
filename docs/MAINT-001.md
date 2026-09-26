# MAINT-001 — GitHub Actions Node24+ Refresh

> **Status:** COMPLETE
> **Scientific authority:** NONE

## Problem

Current workflows still reference action majors whose action metadata targets Node.js 20.

Recent GitHub-hosted runs emit:

```text
Node.js 20 is deprecated.
actions targeting Node.js 20 are being forced to run on Node.js 24.
```

The runner is already forcing those actions onto Node.js 24, so this is not a claim that scientific jobs are still executing under Node.js 20.

It is a repository maintenance debt: workflow declarations lag the currently supported action majors.

## Inventory

Current default-branch references:

- `actions/checkout@v4`: 30 workflows;
- `actions/setup-python@v5`: 30 workflows;
- `actions/upload-artifact@v4`: 29 workflows;
- `actions/download-artifact@v4`: 17 workflows.

Latest official releases observed on 2026-09-26:

- `actions/checkout`: v7.0.1;
- `actions/setup-python`: v7.0.0;
- `actions/upload-artifact`: v7.0.1;
- `actions/download-artifact`: v8.0.1.

## Migration target

Keep the repository's existing major-tag style while moving to supported Node24+ action generations:

```text
actions/checkout@v4         -> actions/checkout@v7
actions/setup-python@v5     -> actions/setup-python@v7
actions/upload-artifact@v4  -> actions/upload-artifact@v7
actions/download-artifact@v4-> actions/download-artifact@v8
```

## Micro-bounce rollout

Do not mass-edit all workflows before a canary passes.

### Canary

Update only `.github/workflows/ci.yml`.

Acceptance:

- CI completes successfully;
- the Node.js 20 forced-upgrade warning disappears for checkout/setup-python;
- Python install / compile / unit tests / Monte Carlo smoke / environment probe remain PASS.

### Batch migration

After canary success, update workflows in small maintenance batches.

Each batch must:

1. modify only action-version references;
2. commit immediately;
3. write a handoff;
4. wait for ordinary CI only after the checkpoint exists.

### Artifact validation

At least one workflow using both upload and download artifact must be run after its migration.

Acceptance:

- upload succeeds;
- download succeeds;
- aggregate step succeeds;
- produced artifact is readable.

## Non-goals

MAINT-001 does not change:

- experiment specifications;
- scientific seeds;
- workloads;
- memory limits;
- statistical estimands;
- findings;
- authority boundaries.

## Rollback

If a canary or migrated workflow fails because of an action-major change, revert only that maintenance batch and record the incompatibility before proceeding.

## Principle

> Infrastructure migrations must not become unrecorded changes to the experimental apparatus.


## Completion record

MAINT-001 completed successfully.

Validated canaries:

- core CI: run 36248941088;
- artifact upload: run 36249019795;
- artifact upload/download roundtrip: run 36249163157;
- post-migration repository CI: run 36249625397.

All pre-existing workflow files were migrated to the validated action generations and directly audited in B074-B079.

The Node.js 20 forced-upgrade warning is no longer caused by the repository's checkout/setup-python declarations.

A separate `Buffer()` deprecation warning was observed inside `download-artifact@v8` during the maintenance canary. Artifact transfer and digest verification passed; this is tracked as upstream action-runtime noise rather than a repository version-selection defect.
