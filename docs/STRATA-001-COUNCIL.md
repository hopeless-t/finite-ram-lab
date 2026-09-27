# STRATA-001 Council — Cold-file Page-Cache Bypass Preservation

> **Status:** COUNCIL CONVERGED / EXPERIMENT AUTHORIZED FOR DESIGN
> **Inspiration:** https://github.com/Niko1221/Strata
> **Observed upstream commit:** `8117643ccc68e3d08f80d38e064333742d4474bb`

## Why Strata matters here

Strata explicitly treats GPU VRAM, host RAM, and SSD as different residency tiers.

For its large lookup table, Strata's Linux implementation deliberately uses direct I/O so that the SSD-resident data does not consume host RAM through the OS page cache.

Finite RAM Lab studies a broader question:

> when physical memory is scarce, can application knowledge prevent semantically valuable memory from being displaced by data whose reuse value is low?

STRATA-001 translates one concrete Strata design choice into an independent Linux memory experiment.

## Provenance and respect for upstream

This study is **inspired by Strata's architecture and documented design rationale**.

Initial sources inspected:

- `README.md`;
- `docs/DETAILS.md`;
- `include/strata/platform/direct_file.hpp`;
- `src/platform/direct_file.cpp`;
- `include/strata/core/pinned.hpp`;
- `src/plan/plan_main.cpp`.

No Strata source code is copied into finite-ram-lab for STRATA-001.

The experiment is an independent implementation and asks a broader OS-memory question.

At the observed upstream revision there was no root `LICENSE` file returned by the GitHub contents API. Therefore any future source-code reuse must first perform an explicit license review. Conceptual inspiration and attribution do not authorize code copying.

## Candidate ideas considered

### A — copy adaptive expert-cache policy

Rejected as first study.

Strata's MoE router exposes a domain-specific near-future-use signal. That is scientifically interesting but not a generic application-memory signal.

### B — reproduce full VRAM/RAM/SSD tiering

Rejected as first study.

Too many mechanisms move at once and would obscure causal interpretation.

### C — isolate page-cache bypass

**Adopted.**

It is small, independently testable, Linux-native, and directly connects to finite-ram-lab's existing anonymous-residency measurements.

## Frozen scientific question

Under the same cgroup memory pressure and the same sequential read-only file access pattern, does bypassing the Linux page cache for a semantically COLD file reduce displacement and reuse cost of a semantically HOT anonymous region?

## Candidate arms

1. `MMAP`
   - file-backed mapping;
   - sequentially touch every page.

2. `BUFFERED_PREAD`
   - ordinary buffered reads into a fixed reusable userspace buffer.

3. `DIRECT_PREAD`
   - `O_DIRECT`;
   - aligned reads into a fixed reusable aligned buffer;
   - no intentional page-cache population.

All arms read the same byte ranges in the same order.

## Primary causal contrast

`DIRECT_PREAD vs BUFFERED_PREAD`

Primary reason:

The userspace access form is nearly identical while page-cache participation changes.

`MMAP` is an important secondary arm because it is the natural file-backed residency mechanism and Strata explicitly retained mmap as an A/B comparison path.

## Primary outcomes

Immediately after the COLD-file scan and before HOT reuse:

- HOT anonymous resident fraction;
- cgroup `memory.stat anon`;
- cgroup `memory.stat file`.

During HOT reuse:

- HOT retouch latency;
- major faults;
- swap-ins / anonymous refaults where observable.

End-to-end:

- file-scan elapsed time;
- total work interval;
- bytes read from process I/O accounting;
- OOM / cgroup memory events.

## Critical confounds and controls

### Warm page cache

A trial is invalid if the file is materially cached before the scan.

The workload must create or prepare the dataset through a path that does not intentionally warm the buffered page cache, and must measure pre-scan file residency where feasible.

### Userspace buffer memory

BUFFERED_PREAD and DIRECT_PREAD use the same fixed-size reusable buffer.

The buffer must not scale with dataset size.

### Alignment

DIRECT_PREAD must fail closed if filesystem/device alignment requirements are not met.

No silent fallback to buffered I/O is allowed.

### Filesystem support

If the runner filesystem rejects `O_DIRECT`, classify the environment as `CAPABILITY_HOLD`, not as evidence against the hypothesis.

Record filesystem type and relevant mount context.

### Semantic asymmetry

The anonymous region is HOT because it is deliberately reused after the scan.

The file dataset is COLD because the workload intentionally does not reuse it during the measured interval.

This is an experimental semantic contract, not a claim about arbitrary real applications.

## Experiment order

1. capability probe;
2. design calibration / small pilot;
3. Monte Carlo sizing from pilot variance;
4. frozen confirmatory experiment.

Do **not** jump directly to a large hosted-runner campaign.

## Success interpretation

A result supports the mechanism only if page-cache bypass:

- reduces file-backed cgroup residency as intended;
- preserves more HOT anonymous residency or reduces its reuse cost;
- and does not merely move the cost into an unacceptable end-to-end I/O penalty.

## Negative result

A negative result is useful.

It may show that Linux reclaim already protects the anonymous working set sufficiently under the tested regime, or that direct-I/O cost dominates any residency advantage.

## Broader connection

Strata uses explicit tiering because it knows which model data belongs in VRAM, RAM, or SSD.

Finite RAM Lab asks whether similarly explicit placement information can be useful beyond LLM inference without giving applications unsafe authority over global memory management.

## Authority boundary

STRATA-001 authorizes only an independent bounded experiment design.

It does not authorize kernel changes, deployment, system-wide cache bypass, or copying Strata source code.
