# AI Worker Calculation Toolbox

> **Status:** READY v0.1

Finite RAM Lab exposes reusable research calculations through one command:

```bash
pip install -e ".[analysis]"
frl catalog
```

An AI worker should prefer these tools over re-deriving the calculation from scratch.

## Worker contract

The normal workflow is:

```text
discover
  ↓
create a small JSON spec
  ↓
run the named calculator
  ↓
store structured JSON evidence
  ↓
interpret separately
```

Commands:

```bash
frl doctor
frl catalog --json
frl template changepoint
frl run-spec path/to/spec.json --out evidence/result.json
```

Input paths in a calculation spec are resolved relative to the spec file.

## Ready-made calculations

| Tool | Research question |
| --- | --- |
| `changepoint` | Where does a pressure/performance regime change? |
| `exact_oracle` | What is the exact bounded offline residency optimum for a small trace? |
| `info_gain` | How many bits of uncertainty does an added application signal remove? |
| `system_id` | What input→output delay and first-order dynamic best fit the timeline? |
| `tail_fit` | What does the extreme latency/stall tail look like? |
| `qmc_design` | Which Sobol/LHS parameter points should a controlled experiment run? |
| `prcc` | Which sampled parameters most strongly control the measured output? |

## Example — changepoint

```json
{
  "task_id": "CHAR-CP-001",
  "tool": "changepoint",
  "input": "../evidence/pressure-sweep.csv",
  "params": {
    "x": "memory_high_mib",
    "y": "p99_latency_ms",
    "min_segment": 4
  }
}
```

## Example — exact oracle

The input JSON contains the access trace:

```json
{
  "trace": ["A", "B", "C", "A", "D", "A", "B"]
}
```

The calculation spec can then request:

```json
{
  "task_id": "ORACLE-001",
  "tool": "exact_oracle",
  "input": "../data/trace.json",
  "params": {
    "capacity": 3,
    "page_sizes": {},
    "page_miss_costs": {}
  }
}
```

The solver uses SciPy/HiGHS MILP and returns the exact optimum for the declared bounded model.

## Example — information value

```json
{
  "task_id": "INFO-001",
  "tool": "info_gain",
  "input": "../evidence/events.csv",
  "params": {
    "target": "next_region",
    "observed": ["recent_access_class", "pressure_class"],
    "added": ["application_phase"]
  }
}
```

The result reports:

```text
H(target | observed)
H(target | observed, added)
difference in bits
fraction of remaining uncertainty removed
```

This is a direct bridge to the Application/OS Information Gap hypothesis.

## Example — system identification

```json
{
  "task_id": "SYSID-001",
  "tool": "system_id",
  "input": "../evidence/timeline.csv",
  "params": {
    "input": "working_demand_mib",
    "output": "latency_ms",
    "max_delay": 20
  }
}
```

The current model is a deliberately small ARX(1,1) model. It chooses the integer input delay with the lowest BIC.

A more complex model should only be added when the simple model demonstrably fails.

## Example — extreme tail

```json
{
  "task_id": "TAIL-001",
  "tool": "tail_fit",
  "input": "../evidence/repeated-runs.csv",
  "params": {
    "value": "stall_ms",
    "threshold_quantile": 0.95,
    "tail_probabilities": [0.01, 0.001]
  }
}
```

The tool fits a Generalized Pareto Distribution to threshold exceedances.

## Example — quasi-Monte Carlo design

```json
{
  "task_id": "DESIGN-001",
  "tool": "qmc_design",
  "params": {
    "method": "sobol",
    "n": 256,
    "seed": 20260926,
    "parameters": [
      {"name": "memory_high_mib", "min": 96, "max": 512},
      {"name": "hotset_mib", "min": 32, "max": 256},
      {"name": "scan_mib", "min": 0, "max": 512}
    ]
  }
}
```

This produces a deterministic low-discrepancy design that can be fed into later GitHub Actions experiments.

## Example — parameter influence

After a Sobol/LHS design has been executed and the resulting table has an outcome column:

```json
{
  "task_id": "PRCC-001",
  "tool": "prcc",
  "input": "../evidence/design-results.csv",
  "params": {
    "inputs": ["memory_high_mib", "hotset_mib", "scan_mib"],
    "output": "p99_latency_ms"
  }
}
```

PRCC is a screening tool. A high coefficient suggests a parameter is influential after rank-linear adjustment for the other declared inputs; it is not proof of causality.

## GitHub Actions

`.github/workflows/research-calc.yml` runs the same spec-driven interface on a hosted runner.

The workflow accepts a repository-relative `spec_path`, runs:

```bash
frl doctor
frl run-spec "$SPEC_PATH" --out evidence/calculations/result.json
```

and uploads the result as an artifact.

This lets an AI worker prepare a spec without writing a new analysis program.

## Authority boundary

The toolbox automates calculations, not scientific conclusions.

```text
calculation result ≠ interpretation
interpretation ≠ finding
finding ≠ architecture decision
```

Every new calculator should have:

- a narrow question;
- deterministic or explicitly seeded behavior;
- known-answer tests;
- a documented model boundary;
- structured output.
