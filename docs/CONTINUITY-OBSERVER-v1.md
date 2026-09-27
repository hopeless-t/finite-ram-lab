# CONTINUITY-OBSERVER-v1

> **Status:** IMPLEMENTED / NON-AUTHORITATIVE

## Purpose

Leave a durable, metadata-only observation when selected GitHub Actions workflows complete, even if the active ChatGPT execution turn ends before it can perform a readback.

## Security model

The observer intentionally has no repository authority.

It uses:

```yaml
permissions: {}
```

It does not:

- check out repository code;
- read or download predecessor artifacts;
- restore or write caches;
- reference repository secrets;
- mutate repository contents;
- open or modify issues or pull requests;
- promote observations into canonical research state.

The only produced side effect is an Actions artifact containing a small JSON object derived from GitHub's `workflow_run` event payload.

## Observation artifact

Artifact name:

`continuity-observer-<observed-run-id>`

Retention:

30 days.

Fields:

- schema_version;
- observer_id;
- authority;
- workflow_name;
- run_id;
- run_attempt;
- event;
- head_branch;
- head_sha;
- status;
- conclusion;
- created_at;
- updated_at.

## Branch restriction

Only predecessor runs whose `head_branch` is `main` are observed.

## Canonicality

`observer artifact != canonical checkpoint`

A later AI turn must still reconcile the predecessor run and explicitly update the repository handoff.

The observer exists to preserve external completion evidence, not to make decisions.

## Threat boundary

GitHub documents that `workflow_run` can execute in a privileged context. This implementation reduces that risk by:

- granting no `GITHUB_TOKEN` permissions;
- not executing repository or predecessor-provided code;
- not consuming predecessor artifacts;
- not using secrets.

Any future expansion of observer authority requires a new Council.
