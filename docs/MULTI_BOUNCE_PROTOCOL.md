# Multi-Bounce Research Protocol

> **Status:** FROZEN OPERATING PROTOCOL

Finite RAM Lab uses a multi-bounce research workflow to keep each AI-worker segment cognitively bounded and reproducible.

The repository, not accumulated chat context, is the canonical handoff surface.

## Core principle

> **Finish a bounded research segment, write the state to GitHub, stop, and restart from canonical repository state.**

A bounce should be short enough that one worker can hold the active question, evidence, and decision criteria without carrying the entire project history.

The overall project may be long-running; individual bounces should not be.

## Bounce lifecycle

```text
REHYDRATE
  ↓
FRAME
  ↓
PSEUDO-COUNCIL
  ↓
EXECUTE
  ↓
OBSERVE / VALIDATE
  ↓
COMMIT
  ↓
HANDOFF CAPSULE
  ↓
STOP
```

### 1. REHYDRATE

At the start of a bounce, read only the minimum canonical state needed for the current question.

Default read set:

- `README.md`;
- `docs/NORTH_STAR.md`;
- `docs/RESEARCH_CHARTER.md`;
- the current experiment spec;
- the latest relevant finding;
- the latest handoff capsule.

Do **not** reload the entire repository or prior conversation history unless the current question genuinely requires it.

### 2. FRAME

Write one bounded objective.

A good bounce objective has:

- one research question;
- one authority boundary;
- one expected artifact or decision;
- an explicit stop condition.

Examples:

```text
Good:
Can mincore-observed hot-set residency predict retouch latency at 164 MiB?

Too broad:
Figure out the best memory manager.
```

### 3. PSEUDO-COUNCIL

For non-trivial decisions, run a lightweight pseudo-Council before execution.

Typical roles may include:

- kernel / VM engineer;
- application / runtime engineer;
- performance measurement reviewer;
- statistician;
- falsification / Red-Team reviewer;
- reproducibility reviewer.

The Council should converge on:

- the narrow question;
- what would falsify the hypothesis;
- the minimum experiment or calculation;
- what claims are authorized if it passes;
- what claims remain unauthorized.

Pseudo-Council is optional for purely mechanical tasks, but preferred for research-design transitions.

### 4. EXECUTE

Perform one bounded experiment, calculation, or repository change.

Do not silently expand scope mid-bounce.

If a new research question appears, record it for the next bounce instead of recursively opening a second project inside the first.

### 5. OBSERVE / VALIDATE

Separate:

```text
execution success
≠
scientific support
≠
mechanism attribution
≠
architecture decision
```

Record negative and null results.

### 6. COMMIT

Before ending a bounce, persist durable state to GitHub.

Depending on the bounce, this may include:

- experiment spec;
- source code;
- workflow;
- structured evidence;
- finding;
- design decision;
- updated README status.

The commit is the durable checkpoint.

### 7. HANDOFF CAPSULE

Every substantive bounce should end with a compact handoff capsule under `handoffs/`.

The capsule should contain only what the next fresh worker needs:

- bounce ID;
- objective;
- canonical inputs;
- actions completed;
- evidence / results;
- frozen decisions;
- unresolved questions;
- explicit next recommended question;
- authority boundary;
- relevant commit SHA / workflow run IDs.

It should not contain a narrative replay of the whole project.

### 8. STOP

After the handoff is committed, stop the bounce.

Do not continue merely because context remains available.

The next bounce should rehydrate from repository state.

## Context discipline

The worker should treat prior conversational context as non-authoritative unless it has been promoted into the repository.

When repository state and remembered conversational state disagree:

> **Repository state wins.**

This reduces stale-context drift and makes worker replacement possible.

## Bounce size

A bounce should usually contain one of:

- one experiment design;
- one experiment execution + immediate validation;
- one focused analysis;
- one finding / freeze decision;
- one bounded implementation supporting a single research question.

Avoid combining all five unless the work is trivial.

## Multi-bounce and GitHub Actions

Long compute may continue inside GitHub Actions, but the human/AI reasoning bounce should remain bounded.

A valid pattern is:

```text
Bounce N:
design + launch workflow
  ↓
commit launch state
  ↓
stop

Bounce N+1:
read workflow result
  ↓
analyze
  ↓
commit finding
  ↓
stop
```

This is preferred to holding a large reasoning context while waiting for computation.

## Multi-bounce and Monte Carlo

Monte Carlo may be used in a dedicated bounce for:

- experiment-design selection;
- uncertainty estimation;
- rare-event search;
- adversarial search;
- stop-rule analysis.

Its output should become a compact design/finding artifact before the next bounce.

## Multi-bounce and authority

A bounce may produce:

- **Observation**
- **Finding**
- **Design Decision**
- **Implementation Candidate**

These must not be silently conflated.

A handoff capsule must state which category was produced.

## Principle

> **The project carries memory in Git; the worker carries only the current question.**


## Micro-bounce timeout discipline

Operational experience showed that even a scientifically reasonable bounce can be lost if the chat/tool session ends before its final commit.

Therefore the default unit is now a **micro-bounce**.

A micro-bounce should normally produce at most one durable transition:

- freeze one design;
- implement one bounded unit;
- launch one workflow;
- read one workflow result;
- record one finding;
- perform one maintenance migration step.

### Commit-before-wait rule

Before any operation that may wait on remote compute, large logs, or many repository mutations:

1. commit the durable state already completed;
2. write a handoff capsule;
3. only then launch or wait.

A worker must never hold the only copy of substantive reasoning in chat while waiting for GitHub Actions.

### Early-checkpoint rule

If a bounce has already produced a useful design decision, implementation, or interpretation, checkpoint it immediately even if more work appears possible.

The next step belongs to the next bounce.

### Heartbeat rule

For long multi-step work, prefer:

```text
small artifact
  ↓
commit
  ↓
handoff
  ↓
fresh rehydrate
```

over:

```text
many local steps
  ↓
one large final commit
```

### Failure semantics

If a chat/tool session ends before a GitHub checkpoint:

> **That uncommitted work is non-canonical and must be treated as not completed.**

This rule intentionally favors duplicated reasoning over lost provenance.

### Default size

Unless a task is trivially mechanical, one bounce should target roughly one of:

- one document/spec decision;
- one implementation slice;
- one workflow launch;
- one result readback;
- one finding;
- one maintenance batch.

Do not combine design + implementation + launch + finding in one bounce merely because context remains.
