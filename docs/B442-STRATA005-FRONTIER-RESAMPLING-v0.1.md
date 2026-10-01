# B442 — STRATA-005 Frontier Resampling v0.1

Status: **historical block-level resampling**. No new physical experiment ran.

## 1. Why B442 exists

B440 found a descriptive timing-only frontier loss in STRATA-005.

B441 then froze an Objective Evidence Gate and classified that result as PROJECTION_FRAGILE.

B442 asks a different question:

> Even if we temporarily admit the descriptive timing coordinate, is the observed frontier relation stable to the original experiment's four independent blocks?

The answer is no.

## 2. Source recovery

All eight STRATA-005 block artifacts were re-downloaded from workflow run 36431449193.

They contain the original trial JSON/JSONL records for:

- MemoryHigh 144 MiB, blocks 0..3
- MemoryHigh 176 MiB, blocks 0..3

Each block contains one trial for each arm.

B442 freezes the selected trial-level values needed for frontier replay:

- peak RAM
- MemoryHigh events
- pgscan
- scan elapsed

The raw source artifact IDs and SHA-256 digests are preserved in the input artifact.

## 3. Why exact bootstrap is possible

There are only four blocks at each capacity.

A nonparametric block bootstrap sample has:

4^4 = 256

possible ordered resamples per capacity.

For independent resampling of the two capacities there are:

256 * 256 = 65,536

possible resample pairs.

Therefore B442 does not need Monte Carlo.

The finite bootstrap distribution can be enumerated exactly.

## 4. Primary pressure projection

Objectives:

- peak_ram_bytes
- memory_high_events
- pgscan

Across all exact block resamples:

- dontneed_80m is never on the 144-MiB primary frontier
- dontneed_80m is never on the 176-MiB primary frontier
- probability of losing dontneed_80m from the primary frontier = 0
- probability of any primary frontier loss = 0

This is fully consistent with B441's evidence-gated conclusion.

## 5. Extended timing projection

Objectives:

- peak_ram_bytes
- memory_high_events
- pgscan
- scan_elapsed_ns

Exact frontier membership probabilities:

### DONTNEED 48 MiB

- H=144 membership = 1.0
- H=176 membership = 1.0
- loss probability = 0

### DONTNEED 64 MiB

- H=144 membership = 1.0
- H=176 membership = 0.6875
- loss probability = 0.3125

### DONTNEED 80 MiB

- H=144 membership = 0.6875
- H=176 membership = 0.3125
- independent loss probability = 0.47265625

### DONTNEED 96 MiB

- H=144 membership = 0.3125
- H=176 membership = 0
- loss probability = 0.3125

Thus the median-derived DONTNEED-80 disappearance is not a high-confidence block-stable event.

## 6. Any-loss probability

Under the timing projection, some frontier arm is lost in:

0.9327545166015625

of the exact independent resample pairs.

This does **not** mean there is strong evidence that capacity destroys Pareto strategies.

The opposite interpretation is more appropriate:

> the frontier itself is highly unstable when noisy scan timing is admitted as an objective.

The identity of the lost timing-supported arm varies across resamples.

## 7. Leave-one-block-out versus bootstrap

An interesting contrast appears.

Leave-one-block-out medians are stable.

For every omitted block:

H=144 timing frontier:
- dontneed_48m
- dontneed_64m
- dontneed_80m

H=176 timing frontier:
- dontneed_48m
- dontneed_64m

So a simple jackknife-style deletion would make the transition look robust.

But exact bootstrap resampling shows only 47.265625% probability for the specific DONTNEED-80 loss.

Why?

With four blocks, resampling with replacement can give substantial weight to the large timing outliers present in individual runner blocks.

Therefore:

> leave-one-out stability is not sufficient evidence of frontier stability for this small, heavy-tailed timing sample.

## 8. Timing outliers are directly visible

Examples from the raw blocks include scan times far above the other blocks.

At H=176:

- DONTNEED 64 block 0: ~2.164 s
- other DONTNEED 64 blocks: ~28.8–37.4 ms

At H=144:

- DONTNEED 48 block 0: ~1.380 s
- other DONTNEED 48 blocks: ~34.4–84.6 ms

This is entirely consistent with the original study's decision to mark hosted timing as descriptive.

B442 does not reinterpret those outliers causally.

## 9. New evidence rule

B441 addressed **authority of an objective**.

B442 adds **stability of the frontier relation**.

A dynamic frontier transition should be promoted only when:

1. it exists in the PRIMARY projection; and
2. it is sufficiently stable under the experiment's appropriate resampling unit.

A DESCRIPTIVE-only transition that is also resampling-unstable is strictly exploratory.

## 10. Implementation

Frozen branch:

- research/frontier-resampling-b442

Files:

- src/finite_ram_lab/frontier_resampling.py
- tests/test_frontier_resampling.py
- analysis/inputs/B442-STRATA005-BLOCK-FRONTIER-RESAMPLING-v0.1.json
- docs/B442-STRATA005-FRONTIER-RESAMPLING-v0.1.md

The analysis code supports:

- block-median frontier construction
- leave-one-block-out frontier checks
- random bootstrap when exact enumeration is too large
- exact finite bootstrap membership enumeration
- exact independent target-loss probability

## 11. New principle H442 — Frontier Stability Gate

> A frontier transition is not stronger than the stability of the frontier membership relation that generates it.

In particular:

- stable median point estimates do not guarantee stable Pareto membership;
- noisy secondary objectives can cause large topology changes in the frontier;
- resampling should operate at the independent experimental block/unit, not individual telemetry rows.

## 12. Where the research now stands

The first historical dynamic replay did not produce a robust B438 violation.

That is useful.

The chain is now:

B438 static theorem
-> B439 comparator
-> B440 real historical replay
-> B441 objective evidence gate
-> B442 block-stability gate

The next physical dynamic experiment can now be designed with the failure modes already known:

- primary objective roles frozen before launch
- stable plan identity
- independent-block replication
- enough timing replication if latency is intended as PRIMARY
- raw receipts preserved for frontier resampling
- no promotion from median-only topology

## 13. Next candidate B443

Design a **Dynamic Frontier Qualification Contract** before any new physical run.

The contract should freeze:

- capacity axis
- plan identities
- PRIMARY objectives
- descriptive objectives
- independent resampling unit
- minimum replication
- missing-data rules
- frontier-stability criterion
- claim ceiling

Only after that contract passes should B425 or a GPU/application capacity sweep be resumed.
