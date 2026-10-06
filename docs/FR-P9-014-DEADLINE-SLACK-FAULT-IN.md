# FR-P9-014 — Post-release deadline slack for just-in-time residency

## Question

P9-013 showed that repeated reconstruction buys lower peak residency but pays reconstruction time. P9-014 asks whether some of that time can become **non-exposed latency** when reconstruction is scheduled inside already-available independent slack.

This experiment never treats hidden latency as free work. It keeps three quantities separate:

- total reconstruction time `R`;
- available post-release slack `S`;
- exposed stall after slack ends.

The idealized lower bound is:

`L_exposed = max(0, R - S)`

The hosted experiment measures exposed stall directly from timestamps rather than assuming the formula is exact under scheduling noise.

## Critical lifetime invariant

Reconstruction may start **only after phase-A workspace state has been closed**.

```text
phase-A workspace live
        |
        v
workspace release
        |
        +------ background FAULT_IN reconstruction ------+
        |                                                |
        +------ independent schedulable slack -----------+
                                                         |
phase-B needs capability ------------------------------> join if needed
```

Starting reconstruction while phase-A remains resident would recreate the overlap that P9-010/P9-013 were designed to remove, so that schedule is outside the qualified policy.

## Frozen hosted proxy

- GitHub-hosted Ubuntu 24.04 / cgroup v2
- P9-013 compressed capability shape: 16 MiB logical runtime state reconstructed from gzip
- phase-A private workspace: 24 MiB
- four transitions per run
- deterministic strided arithmetic semantics
- FAULT_IN slack lanes: `0,10,20,40,80 ms` per transition
- three repetitions
- lane order reversed on alternating repetitions
- KEEP_WARM baseline reconstructs once before READY
- high quota: 128 MiB

Slack uses `sleep` deliberately. It is a scheduling proxy for independent work and avoids adding CPU contention to this first test. A later falsifier replaces it with bounded deterministic CPU work.

## Measurements

For every run:

- kernel `memory.peak`;
- total physical reconstruction nanoseconds;
- aggregate exposed stall after each slack window;
- run wall time as diagnostic only;
- semantic signature;
- reconstruction-start minus workspace-close timestamp;
- kernel OOM events.

## Preregistered PASS gate

PASS requires all of:

1. all runs complete with identical semantics and zero OOM;
2. every FAULT_IN reconstruction begins after workspace release;
3. every slack lane retains at least 8 MiB lower peak than KEEP_WARM;
4. exposed stall is nonincreasing with slack;
5. zero-slack aggregate exposed stall is at least 40 ms across four transitions;
6. 80 ms/transition slack reduces aggregate exposed stall to at most 2 ms;
7. the largest slack lane still retains the peak-memory advantage;
8. no authority or retry permission is created.

Thresholds are frozen before hosted observation.

## Interpretation boundary

A PASS would show only that, on this hosted sleep-slack proxy, reconstruction can be scheduled after phase-state release so that some/all reconstruction time is no longer exposed at the phase-B join while the lower peak-residency shape remains intact.

It would **not** mean reconstruction became free, total wall time universally improved, CPU-heavy overlap behaves the same way, or application deadlines are universally satisfied.

Decision candidate:

`POST_RELEASE_SLACK_CAN_HIDE_FAULT_IN_RECONSTRUCTION_STALL_WITHOUT_RECREATING_KEEP_WARM_PEAK_ON_THIS_HOSTED_PROXY_IF_QUALIFIED`

Next falsifier: replace sleep slack with bounded deterministic independent CPU work and measure contention effects while preserving the same post-release ordering.

Claim ceiling:
`HOSTED_GITHUB_LINUX_CGROUP_V2_POST_RELEASE_SLEEP_SLACK_AND_COMPRESSED_RECONSTRUCTION_PROXY_ONLY_NO_UNIVERSAL_LATENCY_HIDING_OR_APPLICATION_PERFORMANCE_CLAIM`
