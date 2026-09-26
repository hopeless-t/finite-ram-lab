# ENV-001 Initial Finding

> **Status:** INITIAL FINDING  
> **Run:** 36213664247  
> **Source commit:** `b5dbb619723592d81dc1cc4a25c7b49072e7befc`

## Observation

The GitHub-hosted `ubuntu-24.04` runner exposed enough Linux memory telemetry to support the next observation phase.

Observed environment:

- kernel: `6.17.0-1022-azure`;
- visible CPU count: 4;
- visible physical memory: about 15.6 GiB;
- configured swap: about 3.0 GiB;
- cgroup v2: present;
- process cgroup: `/system.slice/hosted-compute-agent.service`.

At the process cgroup, the following were readable:

- `memory.current`;
- `memory.peak`;
- `memory.high`;
- `memory.max`;
- `memory.events`;
- `memory.events.local`;
- `memory.stat`;
- `memory.pressure`;
- `memory.swap.current`;
- `memory.swap.max`.

System-wide PSI and selected `/proc/vmstat` counters were also readable.

## Important boundary

This result establishes **observability**, not controllability.

The current cgroup reported `memory.high=max` and `memory.max=max`, so no memory limit was imposed by the observed parent cgroup.

A read attempt on `memory.reclaim` returned an error. It should not be treated as an observation field; later work must distinguish telemetry interfaces from control interfaces.

## Finding

The hosted runner provides a viable telemetry surface for OBS-001.

## Next decision

Before creating memory-pressure experiments, test whether an isolated child workload can be placed under a reproducible memory limit without modifying the whole runner.

That question becomes ENV-002.
