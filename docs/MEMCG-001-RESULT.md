# MEMCG-001 Page-Charge Quantization Result v1

> **Status:** PASS / SUPPORT_H64
> **Run:** `36449072026`
> **Launch commit:** `68f9e1f9f170ff4181255b6669ebcb94221b70a5`
> **Aggregate artifact id:** `10982376614`
> **Aggregate digest:** `sha256:507c826852d31d778e551827f5785ba7a8483981b3ffb3d60da4f4e2c33d84a9`

## Validity

- 8 / 8 trials PASS
- 4 touch blocks
- 4 no-touch control blocks
- C worker
- fresh transient cgroup per trial
- worker CPU pinned
- base page size exactly 4096 bytes
- 256 one-page sampling steps
- no local-PC execution

Environment on all four blocks:

- Ubuntu 26.04.1 LTS
- kernel `7.0.0-1012-azure`
- systemd `259 (259.5-0ubuntu3.4)`
- cgroup v2
- 4 online CPUs
- runner image `20260920.143.1`
- X64

## Preregistered decision

Aggregate decision:

`SUPPORT_H64`

- touch blocks satisfying H64: **4 / 4**
- controls satisfying H64: **0 / 4**
- dominant touch best quantum from the original analyzer: **64 pages**

## Exact non-zero memory.current first differences

### block 0 touch

- +64 pages at 34
- +64 at 98
- +64 at 162
- +64 at 226

Spacing:

`64,64,64`

### block 1 touch

Identical:

`34,98,162,226`

all +64 pages.

### block 2 touch

- +64 at 35
- +64 at 99
- +64 at 163
- **-65 at 173**
- +64 at 186
- +64 at 250

Before the negative discontinuity:

`35,99,163`

is an exact 64-page lattice.

After the discontinuity:

`186,250`

is another exact 64-page lattice with a different phase.

Thus block 2 is better described as a **phase reset / regime change** than as loss of the 64-page quantum.

### block 3 touch

`37,101,165,229`

all +64 pages with exact 64-page spacing.

### controls

All four no-touch controls had no non-zero `memory.current` first differences.

## Strongest current interpretation

The hosted signal supports two distinct properties:

1. **quantum magnitude:** observed positive accounting jumps are exactly 64 base pages = 256 KiB;
2. **within-regime spacing:** positive jumps recur every 64 touched pages.

The phase is not universal across fresh trials.

Observed first phases:

- block0: 34
- block1: 34
- block2: 35
- block3: 37

Block2 additionally shows that phase can change after a negative accounting discontinuity while the 64-page spacing survives within the new regime.

This is consistent with a hidden accounting-stock state rather than a globally fixed periodic clock.

## Upstream mechanism consistency

The inspected upstream Linux source snapshot:

`torvalds/linux@72d3fcf802c45d00b300f25b848a93c3a2bd7c7e`

defines:

`MEMCG_CHARGE_BATCH = 64U`

and the cgroup selftests describe memory-cgroup charging as using per-CPU batches 64 pages large.

The source also exposes per-CPU charge caches and `drain_all_stock()`, making a resettable per-CPU stock mechanism qualitatively compatible with the observed phase behavior.

This is mechanism consistency, not proof of the exact cause of block2's -65 event.

## What this does NOT show

- It does not establish a DRAM-cell hardware quantization law.
- It does not prove every Linux kernel/substrate exposes identical behavior.
- It does not identify the exact trigger of the block2 negative discontinuity.
- It does not authorize a memory controller/default.

The result is specifically about observed cgroup-v2 `memory.current` accounting on this hosted Linux substrate.

## Next mathematical problem

The original lattice scorer has a divisor-alias issue: a +64 jump is also divisible by 1/2/4/8/16/32. Block2's phase reset caused its per-trial best-Q score to prefer 8 even though the physical jump magnitude and within-regime spacing remained 64.

Therefore the next step is explicit **model competition**, not another ad-hoc score.

Candidate models:

- page-linear;
- stationary Q staircase;
- reset-aware Q staircase;
- arbitrary jump locations;
- no-touch/null.

Compare them using:

- full-sequence prediction error;
- Minimum Description Length;
- leave-one-block-out prediction;
- reset-conditioned prediction;
- optional spectral evidence as a secondary diagnostic.

## Compact evidence

Machine-readable jump evidence:

`evidence/MEMCG-001/event-sequence-v1.json`

Raw workflow artifacts remain canonical for full samples.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
