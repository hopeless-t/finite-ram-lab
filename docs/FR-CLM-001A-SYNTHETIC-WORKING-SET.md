# FR-CLM-001A — Synthetic Semantic Working-Set Harness Validation

Status: **SYNTHETIC HARNESS VALIDATION**

## Goal

Before comparing real CLM/Pi/KITten context managers, validate that Finite RAM Lab can
measure semantic working-set pressure without confusing token reduction with correctness.

This experiment does **not** run a language model.

## Synthetic task model

Each case contains an ordered history of key/value events plus a final set of query keys.

The reference answer is the latest full-history value for every queried key.

The corpus contains four deterministic cases:

- an important early fact followed by distractors;
- a two-key case with a superseded value;
- two required facts separated across history;
- a late required fact.

The resident budget is measured in event units for this harness.

## Arms

### FULL

All history remains resident.

This is the semantic reference.

### APPEND_TRUNCATE

Keep only the newest B events.

This models ordinary recency-only pressure handling.

### KEY_AWARE

Given the declared query keys:

1. keep the newest event for each queried key;
2. fill any remaining budget with recent events.

This is a deterministic research heuristic.
It is not a CLM model and it uses explicit task information.

## Sweep

Budgets:

`1, 2, 4, 6, 8`

Primary endpoint:

`exact_rate`

Secondary endpoints:

- mean resident count;
- mean interference events;
- first-failure biopsy.

## Frozen expected result

The corpus is deliberately constructed so that:

- FULL = exact;
- APPEND_TRUNCATE first reaches 100% at budget 8;
- KEY_AWARE first reaches 100% at budget 2.

At budget 2:

- APPEND_TRUNCATE exact rate = 0.25;
- KEY_AWARE exact rate = 1.0.

The point is not that KEY_AWARE is generally superior.
The point is to validate that the harness can distinguish:

```text
resident size reduction
from
semantic omission
from
irrelevant resident interference
```

## Failure-state biopsy

Every failing case records:

- case id;
- resident indices;
- missing required keys;
- stale required keys;
- resident event count;
- interference event count.

The first synthetic failure of APPEND_TRUNCATE at budget 2 contains the missing early
`goal` key explicitly.

## Relation to B461-B501

Physical Finite RAM established:

`information obligation != simultaneously resident representation`.

FR-CLM-001A validates the analogous measurement shape:

`semantic obligation != simultaneously resident context representation`.

Unlike the exact CRT line, semantic context selection is allowed to fail if necessary
information is omitted. Therefore correctness must remain a first-class endpoint.

## What this enables next

If FR-CLM-001A passes:

- FR-CLM-001B can add stochastic/rare omission cases;
- FR-CLM-002 can perform a larger pressure sweep and change-point search;
- later real-model work can replace deterministic success with task/model outcomes while
  preserving the same receipt structure.

## Claim ceiling

**SYNTHETIC_SEMANTIC_WORKING_SET_HARNESS_ONLY**

No real CLM, Pi, KITten, or provider performance result is claimed.
