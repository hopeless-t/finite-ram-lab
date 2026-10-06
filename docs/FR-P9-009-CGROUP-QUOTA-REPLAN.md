# FR-P9-009 — Kernel-Enforced Cgroup Quota Replan

## Why this exists

FR-P9-008 proved the admission logic only against a synthetic PSS cap transition, even though its candidate surface came from hosted measurements. FR-P9-009 removes that remaining gap: the resource boundary itself is enforced by the Linux kernel through a disposable cgroup v2 `memory.max` domain.

The experiment deliberately freezes residency to `KEEP_WARM` so only the concurrency/resource boundary is under attack.

## Failure-domain design

The orchestration/monitor process remains outside the constrained cgroup. Only worker processes are moved into the disposable memory domain before the Python interpreter is exec'd.

```text
parent monitor (unconstrained)
        |
        +-- cgroup v2 memory domain
              +-- worker 0
              +-- worker 1
              +-- worker 2
              +-- worker 3
```

The cgroup sets:

- `memory.max`
- `memory.swap.max = 0` when available
- `memory.oom.group = 1` when available

This lets the experiment observe kernel OOM evidence without endangering the runner process itself.

## Fixture

Each worker keeps two memory surfaces live:

1. a shared 8 MiB immutable mapped capability;
2. a private 16 MiB touched workspace.

The private workspace intentionally widens the physical N2/N4 separation so the experiment does not depend on a fragile few-MiB threshold.

The deterministic workload is 12 jobs with four SHA256 rounds per job. Job results depend on job ID and the immutable capability, not worker identity, so a concurrency replan must preserve the complete job digest map.

## Quota derivation

No fixed tight quota is preregistered.

First, N2 and N4 each run twice under a high 256 MiB quota. Their kernel `memory.peak` values define two envelopes:

```text
N2_required = max(N2 calibration peaks)
N4_floor    = min(N4 calibration peaks)
gap         = N4_floor - N2_required
```

The experiment refuses to continue unless `gap >= 12 MiB`.

The enforced tight quota is then derived strictly between those envelopes:

```text
headroom = max(4 MiB, gap / 4)
tight_quota = N2_required + headroom
```

Therefore the prediction is frozen *before* tight-quota execution:

- N4: infeasible
- N2: feasible

## Physical falsifier

Under exactly the derived `memory.max`:

1. run N4 and require an isolated kernel OOM kill;
2. run N2 and require clean completion with zero OOM kill;
3. require N2's complete job digest map to equal the high-quota N4/N2 baseline map.

This tests the chain:

```text
physical calibration
      -> resource certificate
      -> stale N4 feasibility prediction = false
      -> kernel enforcement
      -> isolated OOM evidence
      -> replan N2
      -> semantic-equivalent completion
```

## Boundaries

This is still a hashing/capability proxy on GitHub-hosted Ubuntu. It does **not** establish a universal memory threshold, application throughput claim, Strata optimum, game-engine worker count, or AI-worker deployment recommendation.

`scalar_gain = null`.

Resource feasibility does not grant execution authority, and kernel OOM evidence does not grant retry permission.

## Claim ceiling

`HOSTED_GITHUB_LINUX_CGROUP_V2_QUOTA_AND_HASHING_PROXY_ONLY_NO_UNIVERSAL_MEMORY_THRESHOLD_OR_APPLICATION_PERFORMANCE_CLAIM`

## Next falsifier

Make residency policy physical as well: under one fixed kernel quota, test whether `FAULT_IN` can rescue a concurrency class that `KEEP_WARM` cannot admit, while preserving semantic output and accounting for resume/fault cost.
