# FR-SOOM-002 — Read-Only Semantic OOM Shadow Mode

Status: **HARNESS QUALIFICATION / NO LIVE CONTROL**

## Goal

FR-SOOM-001 established a synthetic counterexample showing that equal memory
relief can have very different user-task consequences.

FR-SOOM-002 converts that idea into a reusable observation-only adapter.

The adapter consumes a frozen process snapshot and emits multiple hypothetical
victim rankings.

It does not send a signal.

It does not change process priority.

It does not change cgroups.

It does not stop or restart a service.

## Input contract

Snapshot schema:

`finite-ram-lab.semantic-oom-snapshot/v0.1`

The snapshot carries:

- snapshot identity;
- capture time;
- host fingerprint;
- pressure telemetry;
- candidate process metadata;
- explicit semantic annotations.

Frozen pressure fields:

- MemAvailable;
- free swap;
- memory PSI full avg10.

Frozen process fields:

- pid;
- name;
- RSS;
- oom_score;
- oom_score_adj;
- current-task membership;
- hard-protection bit;
- task value;
- reconstruction cost;
- unsaved-state bit.

The semantic annotations are explicit inputs. The shadow adapter does not infer
them from process names.

## Shadow policies

The receipt computes:

- EARLYOOM_LIKE_OOM_SCORE;
- RSS_FIRST;
- SEMANTIC_MIN_LOSS.

The earlyoom-like arm is still a narrow synthetic comparator. It models only
highest-`oom_score` victim ordering.

## Output contract

Receipt schema:

`finite-ram-lab.semantic-oom-shadow/v0.1`

Every receipt must assert:

- `observation_only = true`;
- `signals_sent = 0`;
- `control_changes = 0`;
- `authority_effect = NONE`.

It also records:

- each hypothetical victim set;
- expected relief;
- semantic loss;
- current-task survival;
- whether rankings disagree.

## Frozen qualification fixture

For a 2048 MiB relief target:

- oom-score-like ranking selects active Chrome;
- semantic ranking selects batch-compressor + background-indexer;
- both satisfy the relief target;
- semantic-loss delta = 262 points;
- current-task survival changes from false to true.

The point is not that these exact numbers are universal.

The point is to prove that the observation-only receipt preserves enough
information to expose a ranking disagreement.

## Live execution gate

The adapter can only become a target-host experiment when an appropriate
MVCA/LDC read binding exists.

Required rule:

`UNKNOWN or DOMAIN_DENIED -> DO_NOT_RETRY`.

A live shadow run must still have:

- no signal capability;
- no service mutation;
- no process mutation;
- no authority effect.

## Current local status

A pre-run MVCA/LDC readback found canonical MVCA state CURRENT, but the available
LDC observation configuration returned an operator-tool mismatch for this lane.

Therefore no local snapshot was requested and no retry was attempted.

This is the intended behavior.

## Why shadow mode matters

A replacement daemon should not be justified from synthetic examples alone.

The first real question is observational:

> During actual memory-pressure episodes, do memory-only and semantic rankings
> disagree often enough to matter?

The second is causal:

> When they disagree, would the semantic choice still relieve pressure in time?

FR-SOOM-002 answers only the first part of the instrumentation problem.

## Claim ceiling

**READ_ONLY_SHADOW_RANKING_ONLY**

## Next

When a matching operator binding exists:

1. collect a bounded read-only target-host snapshot;
2. compute all shadow rankings;
3. store a receipt;
4. repeat across pressure states;
5. estimate disagreement prevalence and semantic-loss distribution.

No intervention should be authorized from a single shadow observation.
