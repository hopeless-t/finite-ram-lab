# FR-SOOM-002A — Memory-Pressure Controller Taxonomy

Status: **SOURCE-GROUNDED DESIGN INVENTORY**

Verified: 2026-10-02

## Question

Which existing open-source memory-pressure controllers are closest to the
Semantic OOM / User-Task Survival direction, and which architectural pieces can
be reused without copying their policy assumptions?

The answer is not one single competitor.

The ecosystem separates into four control layers:

```text
pressure sensing
    ->
resource shaping / cooperative shrink
    ->
victim selection
    ->
last-resort termination
```

Finite RAM Lab currently spans all four conceptually, but should keep them
separate in implementation and evidence.

## Baseline matrix

| system | primary signal | control granularity | main action | semantic / importance input | relation to FR-SOOM |
|---|---|---|---|---|---|
| earlyoom | MemAvailable + free swap | process | SIGTERM / SIGKILL | oom_score plus static prefer/avoid/ignore regex | simple emergency-kill baseline |
| nohang | memory/swap + PSI and additional configurable signals | process / cgroup matching | signals or configurable commands | configurable badness by names, cgroups, paths, environment, cmdline, uid | richer desktop baseline |
| Meta oomd | PSI + cgroup v2 + plugin detectors | cgroup/workload | plugin action chain, commonly kill | workload-specific protection rules via configuration/plugins | strongest policy-engine donor |
| systemd-oomd | cgroup v2 + PSI + memory/swap state | cgroup | kill cgroup | ManagedOOM policy/preferences and cgroup hierarchy | production cgroup baseline |
| systemd pressure protocol | per-service PSI | service/application | application releases caches, trims workers, GC, or exits when idle | application knows what is redundant | strongest cooperative-shrink donor |
| low-memory-monitor | Linux memory pressure proxied through D-Bus | desktop application | warning signal only | application decides what to discard | cooperative notification baseline |
| Android lmkd | PSI, swap/resource use, thrashing and process importance | Android process | kill eligible process | oom_adj / process importance classes | deployed coarse semantic victim selection |
| Senpai | PSI + cgroup v2 memory.high feedback | container/workload | dynamically pressure working set | workload performance under pressure | closest working-set sizing relative |
| Intel Memory Usage Analyzer | cgroup statistics, page-fault rate, PSI | workload/cgroup | static/dynamic memory-pressure/reclaimer experiments | pluggable reclaimer, benchmark context | experiment harness relative |
| Linux cgroup v2 primitives | memory.pressure / PSI and memory accounting | cgroup | memory.low/min/high/max/reclaim | hierarchy and protection values | substrate, not a policy daemon |

## Key source-grounded observations

### 1. Meta oomd is a policy engine, not merely a killer

Meta oomd uses PSI and cgroup v2 and explicitly separates detector plugins from
action plugins.

Its configuration permits workload-specific protection rules and custom actions.

This makes it architecturally interesting for FR-SOOM even if its default
corrective action is usually termination.

Potential transfer:

```text
DETECTOR
  -> POLICY / CLASSIFIER
  -> ACTION CHAIN
```

Do not transfer:

- datacenter assumptions;
- cgroup-only semantic identity;
- any literal victim threshold.

Source:

https://github.com/facebookincubator/oomd

### 2. systemd already has the cooperative half of the desired ladder

systemd's Resource Pressure Handling protocol allows a service to receive PSI
pressure notifications and proactively release resources.

The official guidance explicitly includes:

- allocator-cache trimming;
- application cache release;
- terminating idle worker threads/processes;
- garbage collection;
- exiting if idle and automatically restartable.

This is extremely close to the FR-SOOM direction:

```text
pressure
  -> ask the application to shed semantic-COLD state
  -> only later consider termination
```

Source:

https://systemd.io/MEMORY_PRESSURE/

### 3. Desktop semantics already exist in coarse form

systemd desktop integration distinguishes:

- session.slice — graphical-session essentials;
- app.slice — normal user applications;
- background.slice — low-priority background work.

The stated purpose includes preferentially killing background tasks or otherwise
assigning resource priorities so the session remains responsive.

This is not fine-grained current-task semantics, but it proves that coarse
purpose labels already belong in Linux userspace resource policy.

Source:

https://systemd.io/DESKTOP_ENVIRONMENTS/

### 4. Low Memory Monitor is a semantic callback channel, not a controller

org.freedesktop.LowMemoryMonitor emits D-Bus `LowMemoryWarning` levels.

Applications can respond by freeing caches and unnecessary allocated state, and
at higher urgency may choose to quit.

This supplies a possible compatibility bridge for applications that do not
implement the newer systemd pressure protocol directly.

Source:

https://hadess.pages.freedesktop.org/low-memory-monitor/

### 5. Android lmkd demonstrates coarse semantic victim selection in production

Android userspace lmkd uses PSI on modern Android versions and selects from
processes according to importance/oom adjustment classes, while also considering
memory pressure, swap, and thrashing-related state.

The important conceptual transfer is:

```text
process importance can be an explicit input to memory-pressure policy
```

The Android importance model is not directly portable to a Linux desktop, but
the architectural precedent is relevant.

Source:

https://source.android.com/docs/core/perf/lmkd

### 6. Senpai is unusually close to the Finite RAM application lane

Senpai does not primarily solve emergency OOM killing.

It uses PSI plus cgroup v2 `memory.high` to apply controlled pressure and
estimate the working-set memory requirement of a running container.

That maps closely to the existing Finite RAM principle:

`allocated / resident bytes != required working-set bytes`.

Source:

https://github.com/facebookincubator/senpai

### 7. Intel Memory Usage Analyzer is useful as an experiment-harness relative

Intel's Memory Usage Analyzer can run workloads in baseline and pressured modes,
including a dynamic reclaimer using page-fault rate, and exposes a plugin
interface for other reclaimers such as Senpai.

This is especially relevant to methodology rather than replacement policy.

Source:

https://github.com/intel/memory-usage-analyzer

## Architectural synthesis

The existing ecosystem suggests that a Semantic OOM replacement should not be
designed as one monolithic killer.

A better split is:

```text
1. Pressure Observer
   PSI + MemAvailable + swap + refault/thrash signals

2. Semantic Registry
   current-task / background / restartable / unsaved / reconstruction-cost
   plus explicit application-provided reclaim capabilities

3. Cooperative Action Planner
   cache trim
   idle-worker release
   GC
   application-specific shrink
   background pause / defer
   graceful restartable exit

4. Emergency Victim Planner
   only when required relief is not obtained quickly enough

5. Hard Fallback
   kernel OOM remains the final safety net
```

The core policy distinction becomes:

`what may be reclaimed != what may be terminated`.

## New research hypothesis

A process-level semantic score is still too coarse.

For a browser, for example:

```text
same process tree
  ├─ active unsaved task state       HOT / high-loss
  ├─ foreground renderer             HOT
  ├─ background renderer             WARM
  ├─ image / network / JS caches     COLD / reconstructable
  └─ idle worker                     COLD / removable
```

Therefore the strongest replacement architecture probably needs **two semantic
levels**:

1. cross-process / cross-cgroup importance;
2. intra-application reclaimability.

That leads to a stronger objective than victim ranking alone:

`minimize semantic loss per unit pressure relief under a response-time bound`.

## Relation to FR-SOOM-001 / 002

FR-SOOM-001 proved a synthetic victim-ranking counterexample.

FR-SOOM-002 qualified a read-only comparison receipt.

FR-SOOM-002A adds the missing ecosystem decomposition and changes the next design
question from:

> Which process should we kill?

to:

> Which reversible or reconstructable intervention should be attempted before
> termination, and how long can we wait before hang risk dominates?

## Next synthetic experiment

Until target-host shadow binding exists, the safe next experiment is a
**deadline-constrained action ladder**.

For each hypothetical pressure episode, freeze:

- required relief;
- intervention latency;
- reversible relief;
- semantic loss;
- reconstruction cost;
- current-task damage.

Then compute the Pareto frontier:

`pressure relief x response latency x semantic loss`.

This will determine when cooperative shrink is still timely enough and when the
controller must escalate toward termination.

## Claim ceiling

**SOURCE_GROUNDED_CONTROLLER_TAXONOMY_ONLY**

This document does not rank the projects overall and does not claim any one
controller is sufficient for the user's host.
