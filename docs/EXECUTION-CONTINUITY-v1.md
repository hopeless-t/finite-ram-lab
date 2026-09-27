# EXECUTION-CONTINUITY-v1

> **Status:** FROZEN OPERATIONAL POLICY

## Problem

Micro-bounces reduced the amount of state lost by one failure, but they did not bound the cumulative size of a single ChatGPT execution turn.

The B141 incident showed that a long chain of successful micro-bounces can still end without performing the already-defined next bounce.

## Operating model

A **bounce** and an **assistant turn** are different scopes.

- bounce = small canonical research/implementation unit;
- assistant turn = finite execution envelope containing several bounces.

The turn itself must now be bounded.

## Turn envelope

Maximum total canonical bounces in one assistant turn:

`8`

The final bounce is reserved for checkpoint/close work.

Therefore a normal turn should perform at most seven work bounces before deliberately closing.

This is a reliability limit, not a research-authority limit.

## Tool-output discipline

External tools should emit only fields required for the current decision.

For GitHub workflow/run reads, prefer summaries such as:

- run id;
- workflow name;
- status;
- conclusion;
- head SHA;
- run attempt.

Do not emit the full REST payload by default.

Large repository metadata repeated inside API responses is treated as context waste.

## Progress visibility

Do not perform more than three external/tool calls without a short user-visible progress update.

This does not require a GitHub commit for every progress message.

## External-state observation

A specific external run/status should be read at most once per bounce.

Do not busy-poll.

If the external state is not ready:

1. checkpoint the observed state;
2. close or advance only through a fresh bounded bounce.

## Unknown delivery

If a write may have reached an external system but delivery is unknown:

`retry_count = 0`

First reconcile the external state.

Only after observing absence may a new write be considered.

## Fresh-turn start

Every new assistant turn must begin by rehydrating the latest canonical checkpoint and reconciling any external side effects named there before performing new research work.

## Planned turn close

Every intentional turn boundary must record one stop reason:

- `TURN_CAP`
- `EXTERNAL_WAIT`
- `TOOL_FAILURE`
- `HUMAN_GATE`
- `COMPLETE`

The final turn-close bounce should update the canonical handoff before the assistant response ends.

## Unplanned stop detection

If the next fresh turn finds:

- a stale canonical next action;
- no planned stop marker;
- no Human gate;
- and the external dependency has already completed,

classify the interruption as:

`RUNTIME_LOSS`

The exact platform cause may remain unknown.

Reconcile first; do not invent missing work.

## External side effects

Uncheckpointed external side effects are never erased.

They must be observed and classified as:

- recovered canonical evidence;
- non-canonical/audit-only;
- or unresolved.

## Optional hardening not yet adopted

A GitHub `workflow_run` observer could automatically record CI completion in a non-authoritative observation lane.

That is intentionally deferred because giving GitHub Actions repository write authority changes the trust surface.

## Authority boundary

This policy changes execution reliability only.

It does not:

- expand research authority;
- authorize experiments;
- authorize deployment;
- authorize memory actions.
