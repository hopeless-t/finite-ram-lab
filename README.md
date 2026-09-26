# Finite RAM Lab

A small, reproducible systems research lab for understanding how finite physical RAM aligns with actual application memory demand.

> **Core question:**  
> When physical RAM is limited, what should remain in memory, what should be reclaimed, and when?

[![CI](https://github.com/hopeless-t/finite-ram-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/hopeless-t/finite-ram-lab/actions/workflows/ci.yml)
[![ENV-001](https://github.com/hopeless-t/finite-ram-lab/actions/workflows/env-001.yml/badge.svg)](https://github.com/hopeless-t/finite-ram-lab/actions/workflows/env-001.yml)
[![ENV-002](https://github.com/hopeless-t/finite-ram-lab/actions/workflows/env-002.yml/badge.svg)](https://github.com/hopeless-t/finite-ram-lab/actions/workflows/env-002.yml)
[![OBS-001](https://github.com/hopeless-t/finite-ram-lab/actions/workflows/obs-001.yml/badge.svg)](https://github.com/hopeless-t/finite-ram-lab/actions/workflows/obs-001.yml)
[![CHAR-001](https://github.com/hopeless-t/finite-ram-lab/actions/workflows/char-001.yml/badge.svg)](https://github.com/hopeless-t/finite-ram-lab/actions/workflows/char-001.yml)
[![MC-001](https://github.com/hopeless-t/finite-ram-lab/actions/workflows/monte-carlo.yml/badge.svg)](https://github.com/hopeless-t/finite-ram-lab/actions/workflows/monte-carlo.yml)

## Status

**Systems research / experimental software — early development**

Current principle:

> **Observation before coordination.**

The project currently uses GitHub-hosted Linux runners as its primary experimental substrate. It begins by characterizing what can actually be observed there before making memory-management claims.

Current evidence:

- **ENV-001 — PASS:** hosted-runner memory telemetry is observable;
- **ENV-002 — PASS:** isolated cgroup memory budgets are enforceable;
- **OBS-001 — PASS:** application phases and OS memory state can be captured on one monotonic timeline;
- **MC-001 — 16,000 trials:** seeded synthetic replacement study completed successfully;
- **CHAR-001 — PASS / 96 trials:** a sharp hosted-runner memcg-pressure regime transition was observed;
- **VAL-001 — PASS / 108 trials:** the transition reproduced across six independent runner blocks and localized to the sampled 162–166 MiB region;
- **OBS-002 — PASS / 48 trials:** semantic-region residency loss strongly tracked subsequent retouch cost in the transition zone;
- **HYP-001 — negative:** simple recency ordering did not reliably control later semantic-region cost;
- **EXP-002 — primary benefit not supported / Red-Team harm confirmed:** CORRECT_PAGEOUT did not establish central-tendency benefit over NO_HINT, while WRONG_PAGEOUT was strongly harmful;
- **VAL-003 — confirmatory tail benefit not supported / 800 independent new trials:** >=500 ms stalls occurred in 6/400 CORRECT_PAGEOUT trials versus 7/400 NO_HINT trials; the pre-registered one-sided runner-block randomization test did not support a tail-risk reduction;
- **OBS-003 — PASS / 320 NO_HINT trials:** natural HOT-residency misalignment was pressure-dependent: about 59% at 160 MiB, 58% at 162 MiB, 11% at 164 MiB, 6% at 166 MiB, and 2% at 168 MiB. Misaligned trials were much slower, and an exploratory mapping/order asymmetry at 160–162 MiB motivates direct confirmation.

The current evidence supports a real residency-sensitive performance regime and measurable natural residency-selection headroom under stronger pressure, but does **not** support the tested semantic PAGEOUT operation as a beneficial coordination mechanism.

**Next research stage:** HYP-002 — test whether randomized past recency/order determines natural residency selection independently of future semantic HOT identity at 160–162 MiB.

No generalized memory-coordination plane or kernel change is authorized by the current evidence.

## Why this project exists

Applications and operating systems observe different parts of the memory problem.

Applications can know the meaning, lifecycle, rebuild cost, phase, and near-future importance of their own data.

The operating system can observe global physical-memory pressure, competition between processes, residency, reclaim activity, faults, refaults, swap behavior, and system-wide resource constraints.

Finite RAM Lab asks whether a measurable gap exists between:

```text
actual application demand
          ↕
OS-estimated demand
          ↕
physical-memory residency
```

and whether closing any observed gap can move the practical memory limit without unacceptable performance loss.

The project does **not** assume that existing Linux memory management is inefficient.

## Research architecture

```mermaid
flowchart LR
    A["Application side<br/>demand / phase / intent"] --> AT["Application telemetry"]
    K["OS / Kernel side<br/>supply / pressure / reclaim"] --> KT["OS telemetry"]

    AT --> O["Memory Observation Plane"]
    KT --> O

    O --> T["Synchronized timeline"]
    T --> C["Bottleneck characterization"]
    C --> D{"Reproducible gap?"}

    D -->|"No"| N["Record negative result"]
    D -->|"Yes"| H["Mechanism-specific hypothesis"]
    H --> E["Controlled intervention"]
    E --> V["Comparison / validation"]
```

Observation is intentionally separated from intervention.

## Research order

```text
Observe
  ↓
Characterize
  ↓
Reproduce
  ↓
Form hypothesis
  ↓
Intervene
  ↓
Compare
```

A future mechanism may be an application hint library, a userspace coordination agent, a hybrid design, a minimal kernel extension, or no new mechanism at all.

The implementation is an experimental result, not a premise.

## AI Worker calculation toolbox

The repository includes a spec-driven calculation interface so an AI worker does not need to re-derive standard analysis code for every experiment.

```bash
pip install -e ".[analysis]"
frl doctor
frl catalog
frl template changepoint
frl run-spec path/to/spec.json --out evidence/result.json
```

Ready-made tools currently cover:

- changepoint / knee detection;
- exact offline residency optimization with SciPy/HiGHS MILP;
- conditional information gain;
- small ARX system identification;
- generalized Pareto tail fitting;
- Sobol / Latin-hypercube experiment design;
- PRCC parameter screening.

The same interface can run on GitHub-hosted Actions through `.github/workflows/research-calc.yml`.

See [AI Worker Calculation Toolbox](docs/AI_WORKER_TOOLBOX.md).

## Evidence rules

- observation is not explanation;
- correlation is not causation;
- a refault is not automatically a bad eviction;
- high memory utilization is not automatically inefficient;
- free memory is not itself an optimization objective;
- a successful program execution is not automatically a successful experiment;
- a benchmark improvement is not sufficient evidence of a general memory-management improvement;
- GitHub-hosted measurements describe the declared hosted environment, not arbitrary bare-metal PCs.

Canonical evidence must be structured and carry provenance.

Plots and rendered diagrams are explanatory artifacts unless an experiment contract explicitly says otherwise.

## Research roadmap

```mermaid
flowchart LR
    ENV["ENV-001<br/>Hosted-runner observability"]
    OBS["OBS-001<br/>Dual-sided observation contract"]
    CHAR["CHAR-001<br/>Bottleneck classification"]
    VAL["VAL-001<br/>Failure-mode reproduction"]
    HYP["HYP-001<br/>Targeted hypothesis"]
    EXP["EXP-001<br/>Intervention"]
    BENCH["BENCH-001<br/>Baseline comparison"]
    FIND["Finding<br/>positive or negative"]

    ENV --> OBS --> CHAR --> VAL --> HYP --> EXP --> BENCH --> FIND

    MC["MC-001<br/>Monte Carlo decision support"]
    MC -. informs .-> CHAR
    MC -. informs .-> HYP
```

Later nodes describe research stages, not predetermined mechanisms.

## Repository structure

```text
finite-ram-lab/
├── README.md
├── pyproject.toml
├── specs/
│   ├── ENV-001.json
│   ├── ENV-002.json
│   ├── OBS-001.json
│   ├── CHAR-001.json
│   ├── MC-001.json
│   └── MC-QUALITY-001.json
├── src/finite_ram_lab/
│   ├── env_probe.py
│   ├── limit_probe.py
│   ├── obs_workload.py
│   ├── char_sweep.py
│   ├── calculators.py
│   ├── cli.py
│   ├── sim.py
│   ├── mc.py
│   └── aggregate_mc.py
├── tests/
├── docs/
│   ├── RESEARCH_CHARTER.md
│   ├── REPOSITORY_SPEC.md
│   ├── EVIDENCE_MODEL.md
│   ├── ENV-001.md
│   ├── ENV-002.md
│   ├── OBS-001.md
│   ├── CHAR-001.md
│   ├── AI_WORKER_TOOLBOX.md
│   ├── MONTE_CARLO.md
│   ├── EXECUTION_MODEL.md
│   └── NORTH_STAR.md
└── .github/workflows/
    ├── ci.yml
    ├── env-001.yml
    ├── env-002.yml
    ├── obs-001.yml
    ├── char-001.yml
    ├── research-calc.yml
    ├── deep-monte-carlo.yml
    └── monte-carlo.yml
```

The repository grows only when a real experiment or validation need earns a new component.

## Frozen principles

See:

- [Research Charter](docs/RESEARCH_CHARTER.md)
- [Repository Specification](docs/REPOSITORY_SPEC.md)
- [Evidence Model](docs/EVIDENCE_MODEL.md)
- [Execution Model](docs/EXECUTION_MODEL.md)
- [North Star](docs/NORTH_STAR.md)

## Project principle

> **Observe before optimizing.**

And, for future architecture:

> **Do not choose the control plane before measuring the coordination gap.**
