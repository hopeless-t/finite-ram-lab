# FR-SOOM-002 — Read-Only Shadow Ranking Qualification Receipt

Status: **PASS / OBSERVATION-ONLY SHADOW ADAPTER VALIDATED**

## Frozen qualification

- workflow run: 37006736064
- job: 110836665651
- execution head: f1783430b6f778697c047fa718fa308157f2f001
- targeted tests: 5/5 PASS
- artifact ID: 11225219747
- artifact ZIP SHA256: bb66fba66c09eb88b2ea0c8ed75deb1997dd4d1d8dcb9c98dcfca9da3447010b
- spec SHA256: 3079467af44d6c5341c69992a32c843831aa00939c18774f875c0870d0d00138
- result SHA256: ba3dc01627a330a45e25781898e31d52e2fbd8be0e7216c6f5312ffe3518b89d

## Safety result

The frozen receipt asserts:

- observation_only = true
- signals_sent = 0
- control_changes = 0
- authority_effect = NONE

This is the core qualification result.

The adapter can compare hypothetical victims without becoming a memory-control
mechanism.

## Frozen ranking disagreement

At a 2048 MiB relief target:

### Oom-score-like shadow

Victim:

- chrome-active

Expected relief:

- 3200 MiB

Current-task survival:

- false

Synthetic semantic loss:

- 280

### Semantic shadow

Victims:

- batch-compressor
- background-indexer

Expected relief:

- 2300 MiB

Current-task survival:

- true

Synthetic semantic loss:

- 18

### Delta

Semantic-loss improvement:

- 262 points

Both hypothetical selections satisfy the same relief target.

Therefore the shadow receipt preserves the key comparison needed for future live
observation:

`same relief class + different victim semantics`.

## What is and is not qualified

Qualified:

- snapshot schema;
- deterministic policy comparison;
- ranking-disagreement flag;
- semantic-loss delta;
- current-task-survival delta;
- explicit no-control receipt.

Not qualified:

- live /proc collection;
- live pressure timing;
- real earlyoom configuration replay;
- nohang badness replay;
- signal delivery;
- service replacement;
- recovery latency.

## Live gate readback

Before attempting a target-host shadow run, MVCA/LDC was read back.

Canonical state was CURRENT.

The available LDC configuration path returned:

`DOMAIN_DENIED / operator_tool_mismatch`.

Authority grant remained NONE.

Per the frozen contract:

`UNKNOWN or DOMAIN_DENIED -> DO_NOT_RETRY`.

No local snapshot collection was attempted after that denial.

## Replacement implication

At this point the project has two pieces of evidence:

1. FR-SOOM-001 — a synthetic victim-selection counterexample exists;
2. FR-SOOM-002 — the comparison can be represented in a side-effect-free shadow
   receipt.

The missing evidence is now concrete:

> Do the real target-host process ecology and real pressure episodes produce the
> same kind of ranking disagreement?

Until that is observed, replacement remains a research hypothesis rather than a
deployment decision.

## Claim ceiling

**READ_ONLY_SHADOW_RANKING_ONLY**

## Next

Wait for a matching MVCA/LDC operator binding for a bounded read-only snapshot.

When available, the first live run should:

- capture exactly one process/pressure snapshot;
- write exactly one shadow receipt;
- send zero signals;
- make zero control changes;
- avoid automatic retry on unknown delivery;
- bind the receipt to host fingerprint and exact code commit.
