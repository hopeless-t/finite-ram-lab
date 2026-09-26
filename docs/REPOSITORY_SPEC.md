# Repository Specification

> **Status:** FROZEN v0.1

This document defines the research lanes, authority boundaries, and minimum repository shape.

## Research lanes

| Prefix | Purpose |
| --- | --- |
| `ENV-xxx` | execution-environment characterization |
| `OBS-xxx` | observation contracts and measurement experiments |
| `MC-xxx` | Monte Carlo / synthetic decision-support studies |
| `CHAR-xxx` | bottleneck characterization |
| `VAL-xxx` | methodological or failure-mode validation |
| `HYP-xxx` | explicit mechanism-specific hypothesis |
| `EXP-xxx` | intervention experiment |
| `BENCH-xxx` | controlled performance comparison |

A lane name describes authority, not importance.

## Lifecycle

```text
Question
  ↓
Spec / Contract
  ↓
Validation
  ↓
Execution
  ↓
Observation
  ↓
Checks
  ↓
Evidence
  ↓
Interpretation
  ↓
Finding or next question
```

A workflow completing successfully is not automatically a scientific PASS.

## State vocabulary

Executable contracts may use:

```text
PASS
FAIL
INVALID
ERROR
```

- **PASS** — execution completed and every declared acceptance check passed;
- **FAIL** — execution completed but at least one acceptance check failed;
- **INVALID** — input/specification was invalid and scientific execution did not begin;
- **ERROR** — infrastructure/runtime failure prevented valid evaluation.

Capability probes may additionally classify individual signals as:

```text
SUPPORTED
UNAVAILABLE
ERROR
```

The overall ENV experiment can still PASS when a capability is explicitly UNAVAILABLE; ENV-001 measures availability rather than demanding it.

## Directory authority

### `specs/`

Machine-readable experimental intent.

### `src/finite_ram_lab/`

Deterministic or bounded research code.

Core simulation logic should avoid filesystem/network/Git dependencies.

### `tests/`

Known-answer tests, invalid-input tests, determinism tests, and intentional failure cases.

### `docs/`

Human-readable research contracts and boundaries.

### GitHub Actions

Primary execution substrate for the current phase.

Workflow definitions are part of the experiment contract.

### Artifacts

GitHub Actions artifacts may carry raw/structured run evidence.

They are not automatically canonical cross-platform evidence.

## Change discipline

A frozen research contract may be revised, but the revision must be explicit.

Do not silently change:

- acceptance criteria;
- Monte Carlo distributions;
- runner labels;
- seeds;
- measurement definitions;
- evidence schema.

A changed contract creates a changed experimental condition.

## Minimal current repository

The repository intentionally starts with:

- frozen research documents;
- ENV-001 capability probe;
- MC-001 synthetic Monte Carlo baseline;
- tests;
- CI;
- OBS-001 contract.

No production coordinator, memory daemon, or kernel patch is authorized yet.
