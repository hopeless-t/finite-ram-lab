# FR-COMP-001 — Compressibility Surface Receipt

Status: **PASS / HOSTED USERSPACE CODEC SURFACE VALIDATED**

## Qualification

- workflow run: 37120956744
- job: 111196802416
- execution head: 957bec07ea682e396aec9ebe23116e9e627a805a
- artifact ID: 11272883908
- artifact ZIP SHA256: 801f6cec5aa06830aa6f8cdd81762a233da0b6a50954626053385204a18e9f59
- spec SHA256: 12bed33c0229dc6a64c5f63a4b0a17b585a1c1720f678ddb6f39c0a891d0acbc
- result SHA256: ba4931d908a0f55cd5e03602d7b8ea82b5e2676330b07bb4eebeaf3e9bc86c3b

## Prequalification failure

Initial run 37120807723 rejected the assumption that every codec would compress
the repeated pseudo-random 4 KiB block below 5%.

The counterexample was bzip2 at about 8.18%.

No threshold was simply relaxed.

The hypothesis was updated to:

`compressibility = f(state, codec)`.

The canonical gate requires both a strong best-codec result and a large
state-by-codec spread.

## Frozen physical surface

Mean compression ratios:

| payload | best ratio | worst ratio | best-ratio codec |
|---|---:|---:|---|
| ZERO | 0.00114% | 0.43657% | BZ2_1 |
| REPEATED_BLOCK | 0.11686% | 8.18442% | LZMA_0 |
| SPARSE_OUTLIER | 13.31523% | 15.37246% | LZMA_0 |
| LOW_ENTROPY_4BIT | 50.93600% | 58.42045% | BZ2_1 |
| RANDOM | 100.00648% | 100.80518% | LZMA_0 |

Repeated-block codec spread:

`8.06756 percentage points`.

Random state remains incompressible and can grow after codec framing/metadata.

## Example ratio/CPU trade

LOW_ENTROPY_4BIT:

- BZ2_1: ratio 50.9360%, mean compress CPU ~212.97 ms
- ZLIB_1: ratio 58.4205%, mean compress CPU ~35.52 ms
- ZLIB_9: ratio 56.9525%, mean compress CPU ~109.92 ms
- LZMA_0: ratio 57.1902%, mean compress CPU ~249.59 ms

This is runner-specific timing evidence, not a universal codec ranking.

## Main invariants

- compressed capacity is state-dependent
- codec choice changes both capacity and CPU/decode cost
- incompressible state should be eligible for NO_COMPRESSION
- cold/hot state may rationally choose different codecs
- generic compressed RAM cannot be modeled as a fixed 2x multiplier

## Claim ceiling

**HOSTED_LINUX_USERSPACE_CODEC_SURFACE_ONLY**
