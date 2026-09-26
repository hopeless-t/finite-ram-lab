# Execution Model

> **Status:** FROZEN  
> **Decision:** GitHub-hosted Actions runners are the primary experimental substrate for the current research phase.  
> **Scope:** This decision governs where Finite RAM Lab executes validation, simulation, and early memory-pressure experiments.

## 1. Primary execution environment

Finite RAM Lab shall treat **GitHub-hosted Ubuntu runners** as the primary execution environment for the current phase.

Local and self-hosted runners are not required for the research plan.

The local workstation may be used opportunistically, but no core experiment, validation rule, or research conclusion may depend on local availability.

## 2. Why this is the default

The project values:

- reproducible execution from a public commit;
- clean ephemeral environments;
- parallel execution;
- deterministic Monte Carlo sharding;
- reviewable workflow definitions;
- machine-readable artifacts;
- low dependence on the researcher's actively used workstation.

This makes GitHub Actions the preferred coordination surface for early research.

## 3. Authority boundary

GitHub-hosted results may be authoritative for:

- deterministic software validation;
- experiment-spec validation;
- controlled synthetic workloads;
- relative comparisons inside a declared runner environment;
- seeded Monte Carlo and sensitivity analysis;
- failure injection and Red Team cases;
- observation-contract validation;
- structured evidence generation;
- documentation and artifact consistency.

GitHub-hosted results are **not**, by themselves, authoritative evidence for:

- a specific physical DRAM device;
- bare-metal memory-controller behavior;
- a particular personal computer's interactive responsiveness;
- hardware-specific NUMA behavior;
- physical SSD or swap-device latency;
- platform-specific thermal or power behavior.

The repository must describe results at the level actually supported by the execution environment.

## 4. Hosted-runner reproducibility contract

Each experimental run should record, when available:

- source commit;
- workflow and job identity;
- runner OS image / image version;
- kernel version;
- architecture;
- visible CPU count;
- visible memory capacity;
- cgroup version and relevant limits;
- swap configuration;
- experiment parameters;
- random seed;
- software/runtime versions.

The project should prefer an explicit Ubuntu runner version over a moving `ubuntu-latest` label for canonical experiments.

A change in runner image, kernel, or relevant resource controls is an experimental-environment change and must not be silently merged with earlier measurements.

## 5. Observation before intervention

The hosted environment must first be characterized before it is used to support memory-management claims.

The project shall not assume that all Linux memory features required by later experiments are available or controllable on GitHub-hosted runners.

Capabilities such as pressure metrics, cgroup controls, swap behavior, kernel interfaces, and access-monitoring facilities must be probed and recorded before becoming experimental dependencies.

## 6. Monte Carlo policy

Monte Carlo is a first-class GitHub Actions workload.

Monte Carlo jobs should be:

- seeded;
- reproducible;
- shardable across a job matrix;
- bounded in runtime and memory;
- aggregated into machine-readable summaries;
- accompanied by raw or sufficiently detailed intermediate evidence.

Monte Carlo may be used to explore:

- access-pattern distributions;
- reuse-distance distributions;
- policy sensitivity;
- threshold sensitivity;
- information freshness;
- state-transition delay;
- noisy or incorrect application hints;
- failure boundaries.

Monte Carlo results are **decision support and synthetic evidence**.

They do not substitute for measured behavior from a declared execution environment.

## 7. Parallelism

Parallelism should be used to explore independent parameter regions, not to hide nondeterminism.

The same seed and parameter set should reproduce the same logical result regardless of matrix scheduling order.

Aggregation must be order-independent.

## 8. No self-hosted dependency

The research roadmap must remain executable without a self-hosted runner.

If a future question genuinely requires bare-metal or hardware-specific evidence, that requirement must be introduced as a new explicit research dependency rather than assumed from the start.

## 9. Current consequence

Before OBS-001 relies on GitHub-hosted memory telemetry, the project should characterize the runner itself.

The next execution-oriented milestone should therefore answer:

> Which memory-pressure, reclaim, fault, cgroup, swap, and timing signals are actually observable and reproducible on the selected GitHub-hosted Ubuntu runner?

That characterization is an environment contract, not yet an optimization experiment.
