# FR-P9-015 — Single-CPU resource-typed slack contention

## Question

FR-P9-014 showed that 40 ms of post-release sleep slack could hide reconstruction stall without restoring KEEP_WARM peak memory. That does **not** imply every 40 ms interval is equally useful.

FR-P9-015 asks whether slack must carry a resource identity.

## Frozen comparison

All child runs are pinned to exactly one CPU from their allowed affinity mask.

Two FAULT_IN lanes have the same nominal 40 ms post-release interval:

- `SLEEP`: the main thread yields CPU while reconstruction proceeds.
- `CPU_BUSY`: the main thread performs deterministic integer work while the reconstruction thread competes for the same pinned CPU/process scheduling domain.

Both reconstruct the same 16 MiB logical capability from the same gzip cold representation, execute the same four transitions, use the same 24 MiB phase-A workspace, and verify the same semantic signature.

A KEEP_WARM lane is rerun on the same host as the peak-memory reference.

Lane order is reversed on alternate repetitions.

## Preregistered falsifier

PASS requires all of the following together:

1. identical semantic signatures and no kernel OOM;
2. exact single-CPU affinity on every run;
3. FAULT_IN reconstruction begins only after phase-A workspace release;
4. both FAULT_IN lanes retain >=8 MiB peak saving vs KEEP_WARM;
5. `SLEEP` exposes <=5 ms total stall;
6. `CPU_BUSY` exposes >=5 ms total stall and >=5 ms more than `SLEEP`;
7. `CPU_BUSY` increases measured reconstruction elapsed time over `SLEEP`.

If these gates fail, the resource-typed-slack hypothesis is **not** rescued by changing thresholds after measurement. The failure becomes the next input.

## Candidate model

Instead of scalar slack duration `S`, compile:

```text
TypedSlack = (
  resource_kind,
  duration,
  contention_domain,
  phase_epoch
)
```

For this probe, `resource_kind` distinguishes CPU-yield from CPU-consuming work and `contention_domain=PINNED_CPU` is intentionally narrow.

## Evidence boundary

This is a GitHub-hosted Linux physical proxy using cgroup-v2 memory accounting, one-CPU affinity, Python threads, gzip reconstruction and deterministic strided semantic work. It is not a universal OS scheduler result or application benchmark.

The experiment does not grant execution authority or retry permission and does not synthesize a scalar gain.
