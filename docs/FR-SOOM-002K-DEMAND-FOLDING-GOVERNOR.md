# FR-SOOM-002K — Steal-inspired Demand-Folding Governor

Status: **SOURCE-GROUNDED DESIGN TRANSFER + SYNTHETIC SHADOW CONTROL**

Verified: 2026-10-03

Parent: **FR-SOOM-002J**

## Question

Can Finite RAM Lab add a reversible control step before representation loss,
SSD spill, background exit, or process death?

The Steal Governor provides a useful systems precedent:

> When contention makes additional nominal parallelism reduce effective
> progress, reduce the preferred execution set instead of continuing to schedule
> all available virtual CPUs.

FR-SOOM-002K transfers that control structure into memory-pressure research.

The proposed memory-side action is **demand folding**:

~~~text
pressure rises
    ->
reduce active work demand
    ->
observe forward progress
    ->
only then spend semantic state / SSD bandwidth / process lifetime
~~~

This experiment does not copy the kernel patch and does not claim that steal
time and memory pressure are the same physical quantity.

## Source-grounded Linux mechanism

The Linux v14 series has four distinct layers that matter to this transfer.

### 1. Observable: steal ratio

The driver periodically aggregates steal time and normalizes it by elapsed time
and active CPUs.

Steal time is not ordinary CPU utilization. It represents execution time that a
guest expected to receive but lost to hypervisor scheduling.

That distinction is essential.

The useful abstraction is:

~~~text
nominal resource entitlement
        !=
effective service delivered
~~~

A memory analogue should therefore not be "RAM utilization is high".

Candidate signals must instead describe lost forward progress or costly
resource contention, for example PSI stall, reclaim latency, refaults, swap-in
latency, queue delay, and task-level progress.

Source:

- https://lists.openwall.net/linux-kernel/2026/09/28/358

### 2. Actuator: preferred CPUs, not CPU hot-unplug

The governor changes a preferred CPU mask.

The invariant is:

~~~text
preferred subset active subset online subset present subset possible
~~~

Tasks are steered toward the preferred subset where possible. CPUs are not
literally removed from the machine.

This is the deepest transfer into FR-SOOM.

The memory-side first response should also be a **soft reduction of active
demand**, not immediate destruction of resident semantic state.

Examples:

- worker concurrency;
- in-flight request count;
- batch width;
- prefetch depth;
- speculative work;
- background parallelism;
- model/expert parallel lanes.

### 3. Policy loop: hysteresis plus bounded steps

The v14 defaults are:

- interval: 1000 ms;
- low threshold: 2%;
- high threshold: 5%;
- above high: remove one preferred core;
- at or below low: restore one preferred core;
- between them: do nothing.

The thresholds are separated by a deadband.

This is not cosmetic. It prevents a noisy signal near one threshold from
repeatedly changing scheduler state.

The step is also deliberately bounded.

The governor does not jump directly from all cores to one core after a single
sample.

Source:

- https://lists.openwall.net/linux-kernel/2026/09/28/351
- https://lists.openwall.net/linux-kernel/2026/09/28/358

### 4. Safety invariants and topology

The driver always retains at least one core in the preferred set and protects a
housekeeping core. It acts on sibling CPUs as a core unit because SMT and
hypervisor core scheduling matter.

If preferred-CPU invariants are broken, the driver restores preferred CPUs to
the active set and stops its work loop.

The current policy also intentionally avoids NUMA splicing and expects a
reasonably uniform topology.

This implies two memory-side rules.

First, demand folding needs a progress floor:

~~~text
at least one foreground work unit survives
~~~

Second, the fold unit must respect the application topology. A "worker" may be
the wrong granularity if workers share a model shard, NUMA domain, GPU queue,
database lock domain, or cgroup.

## Why fewer resources can produce more progress

The important quantity is not resource use. It is **useful forward progress**.

Let:

- n = active work units;
- F(n) = useful forward progress;
- C(n) = contention / stall cost;
- L(n) = semantic loss;
- H(n) = control churn.

A conceptual objective is:

~~~text
maximize J(n) =
    F(n)
    - lambda_stall * C(n)
    - lambda_semantic * L(n)
    - lambda_churn * H(n)
    - lambda_deadline * deadline_violations(n)
~~~

For demand folding, L(n) is initially zero because no semantic region is
destroyed.

The ideal marginal decision would be:

~~~text
fold from n to n-1
when

F(n) - F(n-1)
    <
marginal contention tax of the nth work unit
~~~

But the controller cannot directly observe that counterfactual online.

Therefore pressure is only a proxy.

This produces a central FR-SOOM-002K rule:

> A pressure signal may authorize an experiment, but only measured
> forward-progress improvement can qualify the policy.

Pressure relief by itself is not success.

## Atomic transfer map

| Steal Governor atom | Memory-side transfer | What must not be copied blindly |
|---|---|---|
| aggregate steal ratio | stall/thrash/progress observable vector | steal thresholds |
| preferred CPU mask | preferred active work set | CPU topology assumptions |
| one-core decrease | one bounded fold step | literal one-worker step for every app |
| one-core increase | gradual unfold | instant return to max demand |
| 2% / 5% deadband | separated fold/unfold thresholds | numeric values |
| protected core | minimum foreground progress floor | kernel housekeeping meaning |
| core siblings | semantic/topological work unit | SMT semantics |
| no cross-VM messages | independent cooperative self-folding | assumption every participant cooperates |
| restore on disable | bounded restore to declared max | unsafe restore during unresolved memory emergency |
| accurate steal telemetry required | calibrated pressure/progress observability required | treating PSI as perfect truth |
| workload-dependent benefit | qualify only on coupled/thrashing workloads | universal performance claim |
| FAIR-only current scope | begin with opt-in application-local controller | system-wide/RT control |

## New FR-SOOM action ladder

FR-SOOM-002J currently chooses among RAM representations, SSD residency, drop,
background exit, and active-task sacrifice.

FR-SOOM-002K inserts a cheaper action before all of them:

~~~text
0 OBSERVE
1 DEMAND_FOLD
2 REPRESENTATION_DOWNSHIFT
3 SSD_TIER_OR_DROP
4 BACKGROUND_EXIT
5 ACTIVE_TASK_KILL
6 KERNEL_OOM_FALLBACK
~~~

This is the important architectural change.

The earlyoom-successor direction becomes:

~~~text
do not ask "what should die?" first

ask:
1. can demand be folded?
2. can cold state be represented more cheaply?
3. can cold state move tiers?
4. can background work exit?
5. only then, what must die?
~~~

## Candidate observable vector

No single memory scalar is qualified yet.

The first physical observer should capture a vector:

- memory PSI some/full;
- cgroup memory.events high/max/oom;
- major-fault rate and latency;
- workingset refault activity;
- pgscan / pgsteal and reclaim latency;
- swap-in latency;
- zram compression throughput and latency;
- SSD queue latency and migration bandwidth;
- task-specific useful forward progress.

The last signal is mandatory.

A system can reduce PSI by doing less useful work. That is not automatically an
improvement.

## Synthetic shadow model

The repository includes a deliberately synthetic model in
src/finite_ram_lab/semantic_demand_folding.py.

It has three policy arms.

### FULL

Concurrency is permanently held at eight work units.

This models the naive assumption:

~~~text
available concurrency = desirable concurrency
~~~

### HYSTERESIS

The synthetic pressure signal uses:

- high threshold: 0.50;
- low threshold: 0.20;
- step: one work unit;
- minimum: one;
- maximum: eight.

These values are synthetic and intentionally unrelated to the kernel's 2% and
5% defaults.

### SINGLE_THRESHOLD

A one-threshold controller uses 0.35 for both directions.

It exists only to expose control chatter.

## Frozen synthetic result

The deterministic trace moves through low pressure, rising pressure, a high
plateau, and recovery.

Current frozen output:

| arm | total useful progress | max pressure | samples pressure > 0.60 | control transitions |
|---|---:|---:|---:|---:|
| FULL | 349.3866 | 0.7825 | 30 | 0 |
| HYSTERESIS | 407.7842 | 0.6370 | 1 | 8 |
| SINGLE_THRESHOLD | 407.6115 | 0.4915 | 0 | 50 |
| per-step oracle | 447.4468 | n/a | n/a | n/a |

Within this fixture:

- hysteresis useful progress / FULL = 1.1671;
- hysteresis captures 0.9114 of the per-step oracle progress;
- severe-pressure samples fall from 30 to 1;
- control transitions fall from 50 in the single-threshold reference to 8.

This is a controller-architecture demonstration only.

It is not a claim about the user's PC, Linux memory management, PSI thresholds,
or any real application.

## Why the single-threshold arm matters

The single-threshold controller achieves almost the same synthetic useful
progress while changing the actuator 50 times.

This isolates a second objective:

~~~text
good control != only good final throughput
~~~

Policy quality also includes:

- actuator churn;
- cache disruption caused by repeated fold/unfold;
- warmup cost;
- control-plane overhead;
- user-visible latency variance;
- unnecessary semantic-plan switching.

This directly connects FR-SOOM-002K to the hysteresis lesson already observed
in FR-SOOM-002H regime-drift control.

## Failure modes to hunt

### False positive pressure

A noisy or miscalibrated pressure signal may fold healthy work and reduce
throughput.

Required test:

- inject false-high episodes;
- record unnecessary fold duration;
- measure recovery lag.

### False low pressure

A stale or diluted signal may unfold too early and cross the pressure knee
again.

Required test:

- inject false-low episodes;
- measure repeated knee crossings and tail stall.

### Uncontrollable external pressure

Some pressure remains high even after the application reaches its minimum work
set.

The controller must not continue interpreting "pressure high" as proof that
further application sacrifice is useful.

At the progress floor it must escalate to a different action class or remain in
shadow mode.

### Slow actuator

Reducing worker count may not release memory immediately.

Queues, allocator caches, asynchronous deallocation, GPU work, page-cache
writeback, or pending IO may create a delayed response.

The control loop therefore needs actuator-response identification, not merely a
threshold.

An ARX/state-space lane is a natural later experiment.

### Topology mismatch

Folding one nominal worker can remove the wrong capacity if the application has
heterogeneous workers, model shards, NUMA affinity, lock owners, or dedicated
IO threads.

The safe unit is semantic/topological, not necessarily one PID or thread.

### Cooperative unfairness

Steal Governor is most effective when guests cooperate independently.

A similar problem appears for multiple applications under RAM pressure.

An opt-in application that self-folds could concede resources to a
non-cooperating application.

Future system-level work therefore needs fairness and admission semantics.

This is not solved in FR-SOOM-002K.

## Physical qualification sequence

No live controller should be enabled from this PR.

The next sequence is:

1. collect read-only host traces;
2. define a task-specific useful-progress metric;
3. sweep concurrency under frozen workload pressure;
4. identify a pressure/concurrency knee;
5. estimate signal -> actuator -> pressure response delay;
6. replay the trace through the governor in shadow mode;
7. compare FULL / STATIC / HYSTERESIS / oracle offline;
8. inject false-high, false-low, delayed-response, and phase-change rare events;
9. only then authorize application-local opt-in folding;
10. pair reference/treatment on the same host;
11. couple FR-SOOM-002K folding to FR-SOOM-002J residency actions only after
    folding is independently qualified.

## Proposed physical metrics

Primary:

- useful work per second;
- p95/p99 task latency;
- memory PSI some/full time;
- reclaim stall time;
- major/refault latency;
- time above the previously measured pressure knee.

Controller:

- number of fold operations;
- number of unfold operations;
- time spent at each concurrency;
- fold -> measurable relief delay;
- false-fold duration;
- re-crossings of the knee;
- policy switching/chatter.

Semantic escalation:

- number of representation downshifts avoided;
- SSD bytes avoided;
- background exits avoided;
- active-task kills avoided;
- kernel OOM events.

The strongest success case would be:

~~~text
same or higher useful progress
+
lower tail stall
+
fewer destructive semantic actions
~~~

not simply lower RAM use.

## Relation to STRATA / KV / SSD work

FR-SOOM-002J asks where semantic state should live under pressure.

FR-SOOM-002K asks whether the system can first reduce how aggressively it is
creating and touching state.

The combined controller becomes:

~~~text
pressure
  |
  +-- fold concurrency / inflight / prefetch
  |
  +-- compress or quantize
  |
  +-- move cold state to SSD
  |
  +-- drop rebuildable state
  |
  +-- stop background work
  |
  +-- terminate only when deadlines require it
~~~

This creates two independent control axes:

~~~text
demand rate
x
residency representation
~~~

That is stronger than treating SSD spill, compression, or killing as the only
available responses.

## Relation to the earlyoom-successor program

earlyoom acts near the destructive end of the ladder.

FR-SOOM now has a richer decomposition:

~~~text
Pressure Observer
  ->
Demand-Folding Governor
  ->
Semantic Residency Planner
  ->
Emergency Victim Planner
  ->
Kernel OOM fallback
~~~

The Steal Governor contribution is specifically the second plane.

It suggests that the controller should attempt to change **how much work is
actively competing for the constrained resource** before deciding that useful
state itself must be destroyed.

## Evidence boundary

This PR proves only that:

1. the Linux Steal Governor control structure can be decomposed into reusable
   systems principles;
2. those principles map coherently onto a pre-destructive memory action;
3. a deterministic synthetic fixture exhibits the intended feedback behavior;
4. hysteresis reduces synthetic actuator chatter relative to a one-threshold
   reference.

It does not prove:

- a valid memory-pressure scalar;
- a host threshold;
- a host sampling period;
- a correct fold unit;
- a real-machine performance improvement;
- an SSD policy;
- an OOM replacement;
- a kernel design.

## Claim ceiling

**SOURCE_GROUNDED_STEAL_GOVERNOR_TRANSFER_PLUS_SYNTHETIC_DEMAND_FOLDING_SHADOW_ONLY**

## Sources

Primary Linux material:

- https://gihyo.jp/article/2026/10/daily-linux-261001
- https://lists.openwall.net/linux-kernel/2026/09/28/341
- https://lists.openwall.net/linux-kernel/2026/09/28/343
- https://lists.openwall.net/linux-kernel/2026/09/28/351
- https://lists.openwall.net/linux-kernel/2026/09/28/358
