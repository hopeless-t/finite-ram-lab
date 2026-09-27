# Bounce Handoff

> **Bounce ID:** B145
> **Status:** COMPLETE / CONTINUITY OBSERVER COUNCIL CONVERGED

## Question

Should finite-ram-lab add an automatic GitHub `workflow_run` observer so completed external CI/research runs leave durable evidence even when the active ChatGPT turn ends?

## Fresh external verification

GitHub documents two relevant facts:

1. `workflow_run` can execute after another workflow completes and may run in a more privileged context than the triggering workflow.
2. Explicit `permissions` can reduce unspecified `GITHUB_TOKEN` scopes to `none`.

GitHub also warns not to execute or trust untrusted code/artifacts in a privileged `workflow_run` context.

## Council convergence

### Reliability seat

An automatic completion observation is useful because the B141 incident was a continuation loss after CI had already completed.

### Security seat

**Reject** any observer design that:

- commits to the repository;
- opens/modifies issues or PRs;
- checks out repository code;
- downloads predecessor artifacts;
- reads secrets;
- executes predecessor-controlled content;
- requires repository-content write permission.

### Evidence seat

Adopt a **NON-AUTHORITATIVE OBSERVATION LANE**.

The observer may create only an Actions artifact containing GitHub-supplied run metadata.

It must never promote that metadata into canonical research state automatically.

### Minimal observer contract

- trigger: `workflow_run: completed`;
- selected trusted workflow names only;
- main branch only;
- `permissions: {}`;
- no checkout;
- no cache;
- no downloaded predecessor artifacts;
- no secret references;
- read event payload only from `GITHUB_EVENT_PATH`;
- write one small JSON observation;
- upload that JSON as an Actions artifact;
- retention: 30 days.

Recorded fields:

- schema version;
- observed workflow name;
- observed run id;
- observed run attempt;
- observed event;
- head branch;
- head SHA;
- status;
- conclusion;
- created_at;
- updated_at.

### Authority boundary

Observer artifact:

`OBSERVATION != CANONICAL CHECKPOINT`

A fresh AI turn must still read/reconcile the observed run and explicitly write a canonical handoff.

### Threat-model conclusion

This does not eliminate the special security semantics of `workflow_run`, but it minimizes the exposed authority and avoids processing untrusted predecessor content.

## Decision

**ADOPT** `CONTINUITY-OBSERVER-v1` as a non-authoritative artifact-only lane.

Do not grant repository write authority.

## Next action

Implement the observer workflow and its human-readable contract, then continue research without waiting for observer dogfood completion.

## Authority boundary

Execution-observation only.
No scientific, deployment, provider, or memory-action authority.
