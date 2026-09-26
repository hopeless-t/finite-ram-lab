# ENV-002 Initial Finding

> **Status:** INITIAL FINDING  
> **Run:** 36213825556  
> **Source commit:** `04af9e905fd537ba6e891bdd3adecfc5d7c53f2d`

## Observation

A transient systemd unit on the GitHub-hosted `ubuntu-24.04` runner successfully enforced an isolated cgroup v2 memory budget.

Declared limits:

- `memory.high = 201326592` bytes (192 MiB);
- `memory.max = 268435456` bytes (256 MiB).

A bounded 64 MiB touched allocation ran inside:

```text
/system.slice/finite-ram-env002-36213825556-1.service
```

Observed:

- `memory.current` readable before and after;
- `memory.high` matched the declared value;
- `memory.max` matched the declared value;
- memory usage increased after the touched allocation;
- no OOM event occurred;
- cgroup-local `memory.stat`, `memory.pressure`, and swap counters were readable.

All declared ENV-002 checks passed.

## Finding

The current GitHub-hosted runner can support **isolated, bounded memory experiments** without intentionally pressuring the whole runner.

## Research impact

OBS-001 is no longer blocked on the basic control surface.

The next experiment may place a controlled workload inside a transient cgroup and record application phase transitions together with cgroup memory telemetry on a shared monotonic timeline.
