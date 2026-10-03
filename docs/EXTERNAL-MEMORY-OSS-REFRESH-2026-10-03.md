# External Memory-Control / Tiering Intake — 2026-10-03

Status: **SOURCE-GROUNDED REFRESH / NO ADOPTION DECISION**

Purpose: refresh the external projects that currently inform the Finite RAM Lab
Semantic OOM, tiered-residency, and physical-pressure methodology.

This intake does not import source code and does not transfer external numeric
thresholds to the user's machine.

## Executive result

The external landscape has split into three groups.

### Materially changed since the last Finite RAM intake

1. **Niko1221/Strata**
2. **Intel memory-usage-analyzer**

Both have acquired changes that directly affect current Finite RAM hypotheses.

### Current Finite RAM pins are still current

1. **strands-labs/strands-decider**
2. **maanHimself/OpenDLSS-NR**

The commits frozen by FR-DECIDER-001 and FR-DLSSNR-001 are the current repository
heads observed in this refresh.

### Architecturally useful but recently stable

- earlyoom
- nohang
- Meta oomd
- Senpai
- systemd pressure / oomd control surfaces

No newly observed change in these projects requires revising the current
Semantic OOM architecture.

---

# 1. Strata refresh

Repository:

`Niko1221/Strata`

Previous explicit Finite RAM external intake:

`3ce2523c2823687de5372be3af58534f56cbf286`

Observed date:

2026-09-30 JST

Current observed head:

`99f3dbd0b21d1401b3769e0c0d963913607f380b`

Current head time:

2026-10-03T00:21:36Z

Git comparison from the previous intake reports:

`423 commits ahead`

This is large enough that the previous Strata intake must be treated as stale
for implementation details.

## 1.1 Cross-tier desktop-pressure incident

Relevant commit:

`b48aad2a9d96eceb749b4f06ffd6607f9b00be7f`

The Strata change documents two AMD Linux desktop reports where a small default
VRAM reserve allowed the expert cache to fill the GPU. When the desktop later
needed VRAM, amdgpu moved GPU memory into system RAM/GTT. The combined pressure
could kill or destabilize desktop components.

The upstream change is a recommendation, not a new engine policy:

- recommend approximately 3072 MiB VRAM reserve on an AMD Linux desktop;
- explain the observed symptom;
- preserve user override.

## Finite RAM interpretation

This is a highly relevant real-world **cross-tier pressure coupling** specimen:

```text
VRAM optimization
   -> GPU memory spill / GTT pressure
   -> system-RAM pressure
   -> foreground desktop damage
```

It reinforces a Semantic OOM invariant:

`local tier success != whole-system task survival`.

A future governor cannot optimize RAM, VRAM, swap, or SSD in isolation.

External numbers such as 3072 MiB are **not transferable thresholds**.

## 1.2 File-cache bypass became a real resident-budget mechanism

Relevant commit:

`25416f3d335807f22531c56af118cc1f932a7761`

Strata added a Windows file-tier path that reads expert data unbuffered when the
GGUF file cache cannot coexist with the configured resident RAM budget.

The stated problem is directly analogous to STRATA-001:

```text
mapped cold file data
   -> OS cache residency
   -> consumes RAM intended for semantic HOT state
```

The treatment:

- unbuffered reads for the cold expert path;
- batched / merged reads;
- avoid prefetching mapped expert pages through the cache when using the
  unbuffered path.

## Finite RAM interpretation

This is independent implementation evidence that **page/file-cache residency
can become a competing resource against an explicit resident budget**.

It strengthens the motivation for STRATA-001/002 but does not prove the same
effect on Linux or on the user's host.

## 1.3 Residency is now more explicitly controlled

Current Strata source also exposes explicit resident-memory locking:

- Windows minimum-working-set adjustment + VirtualLock;
- Linux mlock;
- partial success is surfaced rather than hidden.

Current documentation additionally describes:

- RAM-pinned experts;
- GPU expert-cache residency;
- KV streaming between RAM and VRAM;
- optional 4-bit KV;
- SSD-backed auxiliary data;
- adaptive expert tiering.

This makes Strata an increasingly useful **multi-tier residency adversary** for
Finite RAM Lab.

## 1.4 New failure surfaces are equally important

Recent Strata reports also expose:

- expert-cache / per-layer residency correctness failures;
- long-prompt faults;
- multi-GPU reserve / post-cache allocation failures;
- architecture-specific performance regressions.

Therefore the correct intake is not:

`Strata proves tiering works`.

It is:

`tiering creates useful control surfaces and new correlated failure domains`.

This aligns with FR-SOOM-002C through 002G:

- mean-fast != tail-safe;
- matched marginal failure != matched risk shape;
- failure-domain dependence must be inferred;
- current-task survival must remain an explicit endpoint.

---

# 2. Intel Memory Usage Analyzer refresh

Repository:

`intel/memory-usage-analyzer`

Current observed head:

`d571f54be6b5c4c10ae7db8a403e1ef03dcb0f03`

Observed time:

2026-10-02T20:27:55Z

The current change substantially expands the Redis pressure methodology,
including a VM-based benchmark.

## 2.1 Methodological feature: remove the page-cache escape hatch

The new Redis VM benchmark deliberately separates:

- server VMs under the pressured host cgroup;
- client/load-generator VMs outside that pressure;
- server guest memory appearing as anonymous host memory.

The documented motivation is that a native workload may let the kernel evict
file-backed page cache before strongly exercising anonymous-memory compression.

Running Redis inside a VM removes that particular page-cache escape path from the
host's perspective.

## Finite RAM interpretation

This is a powerful experimental-design lesson:

`pressure mechanism must be isolated before interpreting a knee`.

A future Finite RAM physical benchmark should distinguish at least:

- file-cache relief;
- anonymous reclaim;
- compression;
- swap;
- application-local shrink;
- process termination.

Otherwise a treatment may look good only because the kernel escaped through a
different memory class.

## 2.2 Pressure-knee methodology

The new harness also provides examples of:

- baseline peak estimation;
- memory.max sweeps;
- zswap / zram compressor comparison;
- aggregate throughput;
- p99 latency;
- VM-count sweeps under a fixed physical-memory budget;
- explicit KPI crossing-point analysis;
- separate unconstrained load generators.

These ideas transfer well to Finite RAM methodology.

The literal host sizes, compressor settings, and thresholds do not.

---

# 3. Stable / slow-moving controller baselines

## earlyoom

Current observed head:

`48348938a8ffc1f74004d8492132ca2d99283e6b`

Observed latest change:

README kill-log example update.

No newly observed algorithm change invalidates the current FR-SOOM earlyoom
baseline.

## nohang

Current observed head:

`50fad9429ff03e759f8a9405c383339683dbe7f4`

Latest observed change is documentation-only.

No newly observed policy change requires revising the current taxonomy.

## Meta oomd

Current observed head:

`ad7e64d67a95c8d237aaa6db03a02c1ecf036792`

The latest observed change is watchdog stack normalization, not a core victim or
pressure-policy redesign.

The detector/action-plugin architecture remains useful as a controller design
relative.

## Senpai

Observed head:

`c51e8e21de5c459406a015c1860d5f6c5ff6a426`

The repository remains effectively static from the original 2019 import.

Senpai remains a conceptual working-set relative, not an actively evolving
baseline.

## systemd

Recent relevant searched changes concern implementation correctness and tests,
not a newly observed redesign of the pressure / ManagedOOM control semantics.

The current Finite RAM separation remains valid:

```text
PSI / pressure observation
!=
semantic failure-domain inference
!=
action policy
```

---

# 4. Current external pins used by new PRs

## FR-DECIDER-001 / PR #70

Pinned:

`strands-labs/strands-decider @ 890947e7ccd44c3de4115e26a7f46cc5c3147b44`

The pin matches the current observed repository head in this refresh.

Notably, that head includes an MLX backend and device-parity work, which makes
resource/performance measurements across device backends especially relevant to
the planned sub-1B experiment.

## FR-DLSSNR-001 / PR #68

Pinned:

`maanHimself/OpenDLSS-NR @ 9d08f4184bbcb9d858e2fb7a7834ec0837a9d2f1`

The pin matches the current observed repository head.

The source-contract PR is therefore not already stale.

## FR-BONSAI-001 / PR #66

Current observed Bonsai-demo head:

`bfaea577522626b883f755236878e4583f3d6e68`

The current public documentation still describes Bonsai 2 27B as a fork-bound
runtime surface with PTQ1_0 / PQ2_0 formats.

FR-BONSAI-001 correctly treats runtime capability as a prerequisite rather than
assuming block-level residency controls exist.

However, the current FR-BONSAI-001 experiment contract should freeze an exact
upstream commit before any physical implementation work begins.

---

# 5. New research consequence: cross-tier pressure coupling

The strongest new cross-project hypothesis from this refresh is:

> A memory controller that optimizes one tier without reserving semantic
> headroom in adjacent tiers can increase whole-system task-loss risk.

Candidate state vector:

```text
RAM pressure
VRAM free / reserve
GPU shared-memory / GTT pressure
swap / zram state
SSD migration bandwidth
application semantic value
foreground task state
```

Candidate invariant:

`tier-local relief != global semantic relief`.

This should become a dedicated synthetic lane before physical control.

The immediate target is to compare:

1. TIER_LOCAL_GREEDY
   - maximize model/expert residency in VRAM/RAM;

2. CROSS_TIER_HEADROOM
   - preserve an explicit system/foreground headroom constraint;

3. EMERGENCY_REACTIVE
   - wait for pressure and sacrifice after spill has occurred.

Primary endpoints:

- foreground/current-task loss;
- model resident capacity;
- total useful work;
- cross-tier spill volume;
- deadline relief success;
- p95/p99 semantic loss.

---

# Transfer rule

Keep the existing rule:

```text
transfer invariants aggressively
transfer thresholds conservatively
re-prove target behavior locally
```

This refresh provides source-grounded hypotheses and methodology.

It does not authorize live memory control.
