# FR-P9-011 — Repeated phase transitions as a typed residency horizon

## Question

FR-P9-010 showed that the same four-worker semantic workload can survive a kernel memory quota when phase-A state is released before phase-B capability materialization, even though KEEP_WARM dies from lifetime overlap. FR-P9-011 asks what happens when that phase boundary repeats.

The hypothesis is deliberately two-sided:

- `FAULT_IN` should preserve a lower kernel memory peak by preventing workspace/capability overlap;
- `KEEP_WARM` should avoid repeated capability materialization cost.

If both are true, residency policy is not a universal winner but a **horizon-dependent typed tradeoff**.

## Frozen hosted proxy

- GitHub-hosted Ubuntu 24.04
- Linux cgroup v2 memory controller
- 4 workers
- deterministic 8 MiB private capability
- private 16 MiB phase-A workspace per worker
- 12 deterministic jobs per transition
- 4 SHA256 rounds per job
- transition horizons `1,2,4,8`
- 2 repetitions per mode/horizon, with mode order reversed on the second repetition
- high quota 256 MiB so this experiment measures the frontier rather than forcing OOM

Each transition executes the same semantic shape in both modes:

1. materialize/touch phase-A workspace and emit a deterministic signature;
2. end the workspace lifetime;
3. process the same phase-B capability and deterministic jobs.

Physical policy differs only in capability lifetime:

- `KEEP_WARM`: capability is materialized once per worker before READY and retained across all transitions;
- `FAULT_IN`: capability is materialized after each phase-A release and unmapped again after each transition.

## Typed objectives

No scalar winner is preregistered. For each transition horizon we minimize separately:

- kernel `memory.peak`;
- total measured capability materialization nanoseconds.

Batch wall time is recorded as a diagnostic third dimension but is not used to force a winner.

The per-horizon Pareto frontier is accepted only if the measured surface actually shows the expected conflict: FAULT_IN has lower peak memory while KEEP_WARM has lower materialization time.

## Fail-closed semantics gate

Within each horizon, all repetitions and both residency modes must preserve:

- every deterministic job digest;
- every `(worker, transition, workspace_checksum)` signature;
- zero kernel OOM under the high quota.

A semantic mismatch invalidates the frontier even if the resource measurements look attractive.

## Interpretation boundary

A PASS establishes only that this hosted hashing proxy exhibits a repeated-transition memory/latency tradeoff. It does not establish a universal residency policy, an application-level speedup, or an external price between bytes and latency.

Decision candidate:

`TREAT_RESIDENCY_LIFETIME_AS_HORIZON_DEPENDENT;FAULT_IN_CAN_BUY_LOWER_PEAK_MEMORY_AT_THE_COST_OF_REPEATED_MATERIALIZATION;KEEP_THE_RESULT_TYPED_UNTIL_AN_EXTERNAL_MEMORY_OR_LATENCY_PRICE_EXISTS`

Next falsifier: introduce an explicit family of memory prices / latency SLOs and compile the typed frontier into policy regions without claiming a universal scalar winner.

Claim ceiling:
`HOSTED_GITHUB_LINUX_CGROUP_V2_REPEATED_PHASE_AND_HASHING_PROXY_ONLY_NO_UNIVERSAL_RESIDENCY_POLICY_OR_APPLICATION_PERFORMANCE_CLAIM`
