# Evidence Model

> **Status:** FROZEN v0.1

## Principle

```text
Intent
  ↓
Execution
  ↓
Observation
  ↓
Checks
  ↓
Evidence
```

Interpretation happens after evidence exists.

## Evidence classes

### Measurement

Directly recorded from the declared execution environment.

Examples:

- `/proc/vmstat` counters;
- PSI text;
- cgroup values;
- process timing;
- synthetic fault counts.

### Derived metric

Computed deterministically from measurements.

Examples:

- miss rate;
- LRU-versus-oracle gap;
- percentile;
- normalized performance ratio.

### Interpretation

A proposed explanation of measurements.

Interpretation is not canonical evidence.

### Finding

An interpretation accepted after its declared validation/reproduction requirements are met.

### Decision

A choice about what to test or build next.

Finding and Decision must not be silently merged.

## Provenance minimum

When available, structured evidence should record:

- source commit;
- workflow;
- run ID;
- job identity;
- timestamp;
- runner OS/image metadata;
- kernel;
- architecture;
- visible CPU count;
- visible physical-memory capacity;
- cgroup mode and limits;
- swap state;
- software/runtime version;
- experiment ID;
- spec identity;
- random seed and trial count for stochastic studies.

## Hosted-runner boundary

GitHub-hosted measurements are authoritative only for the declared hosted environment and the logical/synthetic experiment being executed.

They do not establish bare-metal performance for an unrelated machine.

## Visualization

Figures, Mermaid diagrams, and plots reduce comprehension cost.

They are non-authoritative unless a specific contract explicitly promotes a rendered artifact into an acceptance criterion.

Structured numeric evidence remains the default authority.
