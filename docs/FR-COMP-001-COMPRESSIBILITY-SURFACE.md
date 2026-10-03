# FR-COMP-001 — Compressibility and Codec Surface

Status: **HOSTED LINUX USERSPACE PHYSICAL EXPERIMENT**

Parent: **FR-IO-001**

## Question

How much RAM is a "compressed RAM" byte worth?

There is no single answer.

The ratio depends on the state being compressed, while CPU and decode cost
depend on both state and codec.

## Kernel-relative motivation

Linux zram supports multiple compression algorithms.

Current kernel documentation also describes multi-compressor recompression:
cold or poorly-compressed pages can be recompressed with a slower but more
effective secondary algorithm.

That design already implies:

[
oxed{
	ext{compression ratio}
leftrightarrow
	ext{compression/decompression cost}
}
]

zswap similarly describes itself as trading CPU cycles for potentially reduced
swap I/O.

FR-COMP-001 does not modify zram or zswap.

It tests the more basic invariant in userspace.

## Payload classes

Each fresh process compresses a deterministic 4 MiB payload.

### ZERO

All bytes are zero.

Extreme redundant-page relative.

### REPEATED_BLOCK

One pseudo-random 4 KiB block repeated through the payload.

This has high local entropy but extreme long-range repetition.

### SPARSE_OUTLIER

Every 64-byte region contains eight random bytes and 56 zeros.

This is a simple relative for sparse/outlier-heavy state.

### LOW_ENTROPY_4BIT

Every byte is drawn from only 16 possible values.

It approximates a low-entropy representation without pretending to be a real
packed 4-bit tensor.

### RANDOM

Uniform deterministic pseudo-random bytes.

This is the incompressible control.

## Codecs

Physical userspace proxies:

- zlib level 1;
- zlib level 9;
- bzip2 level 1;
- LZMA preset 0.

These are **not** claimed to reproduce zram codec performance.

Their purpose is to expose a real ratio/CPU/decode/workspace surface.

## Measurements

Three fresh-process repetitions per payload × codec.

Record:

- compressed bytes;
- compression ratio;
- compression CPU/wall time;
- decompression CPU/wall time;
- peak RSS;
- exact SHA-256 roundtrip.

The timing values are retained as evidence but are not universal thresholds.

## Qualification

The experiment requires:

- every roundtrip exact;
- ZERO ratio <1% for every codec;
- REPEATED_BLOCK best-codec ratio <1%;
- REPEATED_BLOCK codec spread >5 percentage points;
- LOW_ENTROPY_4BIT in a broad 35–80% ratio envelope;
- RANDOM ratio >98% even for the best codec.

The important test is that the same nominal input bytes have radically
different compressed capacity **and** that the same state can interact very
differently with different codec structures.

## Prequalification failure that changed the model

The first qualification attempt required every codec to compress the repeated
4 KiB pseudo-random block below 5%.

That assumption failed.

Observed mean ratios in the pilot were approximately:

- zlib level 1: 0.97%;
- zlib level 9: 0.69%;
- LZMA preset 0: 0.12%;
- bzip2 level 1: **8.18%**.

The experiment therefore did **not** simply relax the threshold.

Instead it changed the hypothesis:

[
\boxed{
\text{compressibility}
=
f(\text{state},\text{codec})
}
]

The canonical qualification now requires a strong best-codec result and a
large codec-interaction spread for the repeated-block fixture.

## New Finite RAM equation

The compressed tier should not be modeled as:

[
M_{compressed}=rac{M}{2}.
]

Instead:

[
M_{compressed}
=
sum_i
M_i,r(s_i,c_i)
+
W(c_i)
]

where:

- (s_i) = state class;
- (c_i) = codec;
- (r) = observed compressed ratio;
- (W) = codec metadata/workspace tax.

And controller cost must include:

[
C_i =
T_{compress}
+
N_{restore}T_{decompress}
+
tail
+
CPU pressure.
]

## Consequence

Hot state can rationally choose:

- faster codec;
- weaker ratio;
- perhaps no compression.

Cold state can rationally choose:

- stronger codec;
- slower compression;
- lower resident bytes.

That is exactly the same **bounded escalation** architecture seen elsewhere in
Finite RAM Lab.

## Next

### FR-COMP-002

Replay real state samples:

- model shards;
- quantized weights;
- KV-like buffers;
- logs/text;
- already-compressed media;
- encrypted/random state.

### FR-ATOM-002

At this point the lab has direct experiments for:

- Q — representation;
- D — duplication;
- F — fragmentation;
- G — rematerialization;
- P — page-cache residency;
- Z — generic compression.

The next synthesis should choose **which atom to attack** for each failure
domain.

## Claim ceiling

**HOSTED_LINUX_USERSPACE_CODEC_SURFACE_ONLY**
