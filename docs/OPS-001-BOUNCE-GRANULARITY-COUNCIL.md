# OPS-001 — Bounce Granularity Council

> **Status:** CONVERGED / OPERATING DECISION
> **Scope:** research operations only

## Trigger

The human observed a repeated failure mode:

- the assistant appeared to remain "working" for tens of minutes;
- when interrupted, the assistant said it had still been working;
- GitHub showed no corresponding recent checkpoint.

Repository inspection confirms the relevant operational fact:

- latest canonical research handoff before this Council: `B083-EXP003-COUNCIL.md`;
- commit time: 2026-09-26 14:49:47 UTC (23:49:47 JST);
- at review time there were no active GitHub Actions runs;
- therefore no durable project work existed after B083, regardless of any uncommitted chat-side activity.

The Council does not claim the exact cause of the silent interval. It treats **lack of GitHub progress** as the failure signal.

## Council roles

### Reliability reviewer

The existing micro-bounce definition still allowed too much uncommitted work between checkpoints.

Recommendation: one durable transition per bounce.

### Provenance reviewer

Separate "artifact commit" and later "handoff commit" leaves an avoidable gap.

Recommendation: artifact + handoff in one atomic Git commit whenever possible.

### Tool-latency reviewer

Wall-clock duration is difficult to control reliably across remote tools.

Recommendation: enforce a tool-call budget instead.

Default: six external calls between durable commits.

### Research-method reviewer

Shorter operational bounces do not require smaller scientific questions.

A long experiment may still exist, but its design, implementation, launch, readback, and finding must be different bounces.

### Human-burden reviewer

Do not require human approval after each bounce.

Continue the relay automatically, but use GitHub as the baton.

### Rehydration reviewer

Searching for the newest handoff is unnecessary recurring work and previously contributed to stale-state risk.

Recommendation: maintain a fixed `handoffs/CURRENT.md` pointer.

## Converged operating model

```text
READ CURRENT
   ↓
one narrow action
   ↓
ATOMIC COMMIT
  artifact + B### + CURRENT
   ↓
fresh rehydrate
```

Default maximum uncommitted span:

```text
<= 6 external calls
```

Remote compute:

```text
launch + checkpoint
        ↓
STOP THAT BOUNCE

fresh bounce
        ↓
one result readback
        ↓
checkpoint
```

## Decision

The previous micro-bounce protocol was directionally correct but still too coarse for the observed environment.

The new default is **atomic micro-bounce**.

The project optimizes for:

> duplicated reasoning over lost provenance.

## Authority boundary

This changes only execution discipline. No scientific finding, experiment design, or EXP-003 authority changes.
