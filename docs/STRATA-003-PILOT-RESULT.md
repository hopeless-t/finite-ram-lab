# STRATA-003-PILOT-v1 Result

> **Status:** PASS / PILOT RESPONSE SURFACE
> **Run:** `36361919521`
> **Aggregate artifact:** `STRATA-003-PILOT-36361919521`
> **Artifact id:** `10945883333`
> **Artifact digest:** `sha256:4038653b2c76103c305c785057efee4dc05abc5ae86a25a6aad0197a4c1eba6b`

## Validity

All frozen checks passed:

- 8 runner blocks;
- 56 trials;
- all arms once per block;
- all trials valid;
- file cold before every scan;
- all DONTNEED calls successful;
- release ranges page aligned;
- O_DIRECT no fallback;
- content integrity preserved;
- no OOM.

Launch-commit ordinary CI `36361919522` also passed.

## Response surface

| Arm | Advice calls / 96 MiB | high events | max scan memory MiB | post-scan memory MiB | post file residency |
| --- | ---: | ---: | ---: | ---: | ---: |
| buffered | 0 | 6 | 159.50 | 158.22 | 0.8542 |
| DONTNEED 4 MiB | 24 | 0 | 81.86 | 75.86 | 0.0000 |
| DONTNEED 8 MiB | 12 | 0 | 85.98 | 76.11 | 0.0000 |
| DONTNEED 16 MiB | 6 | 0 | 93.83 | 75.86 | 0.0000 |
| DONTNEED 32 MiB | 3 | 0 | 109.86 | 75.86 | 0.0000 |
| DONTNEED 96 MiB | 1 | 6 | 159.91 | 76.02 | 0.0000 |
| direct | 0 | 0 | 75.86 | 75.86 | 0.0000 |

## Key finding

The final footprint alone is insufficient.

The 96 MiB / end-of-stream arm looks excellent **after** cleanup:

- post-scan memory: ~76 MiB;
- file residency: 0.

But during the scan it behaves like ordinary buffered I/O:

- max scan memory: ~159.91 MiB;
- median high events: 6;
- transient-footprint reduction: approximately 0.

Therefore:

> final cleanup that arrives after the full stream does not prevent transient memory pressure.

## Cadence knee

All tested release intervals through 32 MiB fully suppressed observed MemoryHigh events in 8/8 blocks.

The tested 96 MiB end-of-stream interval did not.

Thus the current evidence brackets the pressure-avoidance knee somewhere in:

`32 MiB < knee <= 96 MiB`

Do not freeze 32 MiB as an OSS default yet.

## Advice density

Per GiB streamed:

- 4 MiB cadence: 256 calls/GiB;
- 8 MiB: 128 calls/GiB;
- 16 MiB: 64 calls/GiB;
- 32 MiB: 32 calls/GiB;
- 96 MiB: ~10.67 calls/GiB.

The 32 MiB arm reduced advice-call density by 8x relative to the original 4 MiB pilot while preserving complete high-event suppression in this workload.

## Transient footprint reduction vs buffered

Median:

- 4 MiB: ~48.7%
- 8 MiB: ~46.1%
- 16 MiB: ~41.1%
- 32 MiB: ~31.1%
- 96 MiB: ~0%

This exposes a gradual tradeoff before the pressure-event cliff.

## Timing

Hosted timing remains noisy and should not be used to select a default cadence from this pilot.

The important robust signal is pressure/capacity behavior.

## Next research question

Refine the interval between 32 and 96 MiB.

Candidate targeted cadences should minimize new trials while locating the pressure-event cliff, for example 48 and 64 MiB, with 32/96 anchors.

## Authority boundary

Pilot only. No OSS default cadence is authorized.
