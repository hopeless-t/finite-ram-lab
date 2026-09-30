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

**Systems research / experimental software — Chapter II active**

Current principle:

> **Prove the state before interpreting the outcome.**

Finite RAM Lab has moved from broad finite-memory characterization into a narrower Linux memcg state-transition study.

### Chapter I — what was established

The current memcg lane has strong evidence for:

- a source-grounded 64-page memcg charge batch;
- a resettable Q64 stock phase;
- controlled PTE preconditioning that removes measured page-table growth from the target sequence;
- a shared per-CPU LRU release path that can contaminate `memory.current` without consuming the target residual stock;
- a direct charge-side observer that sees Q64 even when net `memory.current` is masked by a simultaneous release;
- historical controlled-spawn endpoint 49/72 and primer-qualified terminal pattern 55/55, both kept frozen under their original semantics.

The major semantic correction is that historical SUCCESS/FAIL was too coarse. A first-touch miss, an observer contamination event, an invalidated stock epoch, and a genuine target contradiction are not the same thing.

### Chapter II — current frontier

The largest Chapter-II correction is methodological:

> **Historical SUCCESS/FAIL was too coarse. The research now asks which named state transition occurred before it asks whether the run "failed."**

The active state model distinguishes natural pre-VERIFY state from verified transactional state:

```text
natural pre-VERIFY ecology
  ├─ PREVERIFY_S64 / MAX_STOCK_BOUNDARY
  ├─ STARTUP_STOCK_SEED
  └─ SMALL_RESIDUAL_REFILL
          |
          v
       NORMALIZE
          |
     measured direct Q64
          |
          v
     VERIFIED R0 = 63
          |
          ├─ source-grounded RELEASE_ONLY
          ├─ TARGET_STOCK_EVICTION
          ├─ explicit invalidators
          └─ TARGET
                 |
            SUCCESS / true TARGET_FAIL
```

After a measured one-page direct-Q64 primer, the verified residual invariant remains:

```text
R0 = 63
T0 = 64
```

But natural pre-VERIFY stock is broader. Source and physical evidence support:

```text
0 <= S0 <= 64
T = S0 + 1
```

with the following named mechanisms/states:

- **PREVERIFY_S64 / MAX_STOCK_BOUNDARY** — the natural stock can legally begin at 64 before the experiment establishes its own primer;
- **STARTUP_STOCK_SEED** — transient service / worker startup can leave large inherited stock on the future stock CPU; a cpuset intervention strongly suppresses the large high-T phenotype;
- **SMALL_RESIDUAL_REFILL — ESTABLISHED** — two zero-miss physical specimens captured `systemd` PID 1 returning exactly one page to the later measured owner memcg on the future stock CPU, followed by `S0=1` and first measured Q64 at `T=2`;
- **TARGET_STOCK_EVICTION** — verified residual stock can be asynchronously drained, moving the next Q64 boundary earlier;
- **RELEASE_ONLY** — a positively source-grounded shared-LRU release can change accounting while preserving the target residual.

Known explicit invalidators still include unexpected refill, relevant stock-CPU drain, PTE growth, CPU mismatch, worker error, and incomplete observer coverage.

Across the completed B405 generations, no complete verified target path has produced a genuine `TARGET_FAIL`. That is a current evidence statement, not a reliability guarantee.

### Current experiment sequence

The physical program is now:

1. **B404 transactional smoke — COMPLETE / PASS** — 12/12 normal protocol successes plus a forced invalidation/re-prime sentinel;
2. **B405 causal matrix — mechanism decomposition complete enough to move the frontier** — CLEAN / RELEASE_ONLY / UNEXPECTED_REFILL / PTE_GROWTH plus observer-coverage work exposed named invalidators instead of an undifferentiated FAIL bucket;
3. **normalize ecology — COMPLETE for the major known states** — R9 confirmed the source-derived `T <= 65` bound in 32/32 identities, and the frozen R8 specimen established `PREVERIFY_S64`;
4. **STARTUP_STOCK_SEED — ESTABLISHED and causally challenged** — startup Q64/refill63 explains the large inherited-stock cluster, and `AllowedCPUs=prep` suppresses that large phenotype;
5. **SMALL_RESIDUAL_REFILL — ESTABLISHED** — R13-B1 captured two independent zero-miss `refill_stock(...,1) -> S0=1 -> T=2` specimens;
6. **current next step: refill1 provenance** — identify the exact caller path behind the systemd PID1 refill1 receipts;
7. **then return to age-decoupling** — use the already-frozen FAST/HOLD design to study verified-state wall-clock hazards rather than continuing to expand the pre-VERIFY taxonomy indefinitely.

The project deliberately separates mechanism existence, provenance, prevalence, and transactional reliability. Establishing one does not imply the others.

See:

- [OBS-011 — SMALL_RESIDUAL_REFILL established](docs/OBS-011-SMALL-RESIDUAL-REFILL-ESTABLISHED.md)
- [OBS-010 — R13-A refill1 candidate and scope correction](docs/OBS-010-R13A-SMALL-RESIDUAL-REFILL-RESULT.md)
- [MATH-024 — Pre-VERIFY stock bound and 65-touch theorem](docs/MATH-024-PREVERIFY-STOCK-BOUND-65-TOUCH-THEOREM.md)
- [B404 R2 — Transactional physical smoke PASS](docs/B404-R2-TRANSACTIONAL-SPAWN-PHYSICAL-PASS.md)
- [MATH-023 — Monte Carlo age-decoupling design](docs/MATH-023-AGE-DECOUPLING-DESIGN-MONTE-CARLO.md)
- [Current handoff](handoffs/CURRENT.md)

Historical project stages and negative results remain part of the evidence record; this README now tracks the active frontier rather than repeating the full experiment ledger.

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


## Inspired research

### STRATA-001 — page-cache bypass and semantic HOT-memory preservation

STRATA-001 was inspired by [Niko1221/Strata](https://github.com/Niko1221/Strata), whose explicit VRAM/RAM/SSD tiering and Linux direct-I/O path motivated a narrower Finite RAM Lab question: whether keeping intentionally COLD file data out of page-cache pressure can preserve intentionally HOT anonymous memory under a finite memory budget.

See [the Strata inspiration note](docs/STRATA-INSPIRATION.md) and [STRATA-001 Council](docs/STRATA-001-COUNCIL.md).

The initial study is an independent implementation; no Strata source code is copied into Finite RAM Lab.
