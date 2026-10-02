# FR-SOOM-001 — Semantic OOM / User-Task Survival

Status: **SYNTHETIC HYPOTHESIS QUALIFICATION**

## Hypothesis

A memory-pressure controller can successfully preserve system availability while
still failing the user's task.

Therefore:

`system survival != task survival != semantic survival`.

The motivating desktop failure is straightforward:

- memory pressure rises;
- a large/high-oom-score foreground browser becomes an attractive victim;
- killing it relieves pressure;
- the operating system remains responsive;
- the user's active work is nevertheless destroyed.

That outcome is operationally successful at the system layer and semantically
unsuccessful at the user-task layer.

## Why this belongs in Finite RAM Lab

The existing project already separates:

`information obligation != simultaneously resident representation`

and the semantic-working-set lane established:

`one-step success != trajectory survival != endpoint success`.

Semantic OOM extends the same distinction to emergency memory control:

`memory relief != acceptable user outcome`.

## Public baseline context

The current earlyoom README documents a default victim-selection dimension based
on highest `/proc/*/oom_score`, with configurable prefer/avoid/ignore controls.

nohang exposes a richer control surface including PSI thresholds and configurable
badness adjustments.

Those are useful baselines, but neither mechanism automatically knows which
process is carrying the user's current semantic trajectory.

FR-SOOM-001 therefore does **not** attempt to reimplement either daemon.

It creates a frozen synthetic counterexample to test whether adding explicit
task-value information can change victim selection while meeting the same
memory-relief target.

## Frozen synthetic process ecology

The fixture contains:

- desktop shell — hard protected;
- active Chrome — large, high oom_score, active-task carrier, unsaved state;
- terminal session — smaller active-task carrier with unsaved state;
- model worker — moderate background value;
- batch compressor — low-value/restartable;
- background indexer — very low-value/restartable.

The low-value non-current-task processes contain 3.5 GiB total resident memory.

That creates an intentional boundary:

- up to 3 GiB of relief can be achieved without sacrificing current-task state;
- at 4 GiB and above, even the semantic policy must sacrifice part of the active
  task.

This prevents the experiment from defining an unrealistically invincible
foreground application.

## Frozen policies

### EARLYOOM_LIKE_OOM_SCORE

Static-snapshot approximation only:

- rank eligible processes by descending `oom_score`;
- select victims until the requested relief is reached.

This is **not** an implementation or benchmark of earlyoom.

### RSS_FIRST

Rank by largest resident memory first.

This asks whether simply maximizing bytes-per-kill solves the semantic problem.

### SEMANTIC_MIN_LOSS

Exact subset search over the small frozen corpus.

Objective order:

1. minimize the number of current-task processes killed;
2. minimize semantic loss;
3. minimize excess memory relief;
4. deterministic name tie-break.

Frozen semantic loss:

`task_value + reconstruction_cost + 100 * unsaved_state`.

The numbers are synthetic utilities. They are not inferred user preferences.

## Pressure sweep

Required memory relief:

`1024, 2048, 3072, 4096, 5120 MiB`.

Every policy must satisfy the same relief target.

## Primary endpoints

- relief satisfied;
- selected victims;
- total semantic loss;
- current-task survival;
- excess memory relief;
- victim count.

## Frozen falsifiers

The experiment fails if:

- any policy cannot satisfy the pressure target;
- the oom-score baseline does not select active Chrome for the 1 GiB case;
- the semantic policy does not reduce semantic loss at every frozen deficit;
- the semantic policy cannot preserve the current task through 3 GiB;
- the semantic policy still claims to preserve the current task at 4 GiB.

That last condition is important: semantic priority is not magical extra RAM.

## Replacement ladder

This branch explicitly does **not** replace earlyoom.

A possible replacement path is:

### FR-SOOM-001 — synthetic counterexample

No live process access. No signals. No daemon.

### FR-SOOM-002 — read-only shadow mode

On the target host:

- read memory-pressure telemetry;
- read candidate process metadata;
- compute earlyoom-like, nohang-like, and semantic rankings;
- emit a comparison receipt;
- send **no signal**;
- make **no control change**.

The key question is whether real pressure episodes contain meaningful ranking
disagreements.

### FR-SOOM-003 — bounded intervention

Only after shadow evidence:

- allow a narrow corrective-action surface;
- prefer cooperative reclaim / pause / terminate of low-value work;
- preserve hard safety fallback;
- bind every action to a receipt;
- fail closed on unknown delivery.

### Replacement decision

Actual earlyoom replacement is justified only if a target-host experiment shows
that the semantic controller:

- prevents or reduces hang risk;
- preserves more user-task trajectories;
- does not materially worsen recovery latency;
- does not create unacceptable failure tails.

## Design direction

The eventual controller should not jump directly from pressure to kill.

Candidate ladder:

```text
pressure detected
    |
    v
reclaimable / discardable representation?
    |
    v
cooperative application shrink?
    |
    v
pause / throttle low-value work?
    |
    v
terminate restartable low-value work?
    |
    v
last-resort active-task sacrifice
```

This makes victim killing one intervention class rather than the entire policy.

## Claim ceiling

**SYNTHETIC_VICTIM_SELECTION_COUNTEREXAMPLE_ONLY**

No claim is made about the user's live earlyoom configuration or actual Chrome
victim behavior.

## Next

FR-SOOM-002 should build the observation-only shadow adapter and a structured
receipt schema suitable for MVCA/LDC execution when an appropriate local
binding exists.
