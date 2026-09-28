# REC-002 Recorder Overhead Result

> **Status:** PASS / HOSTED WORKLOAD SCREEN
> **Run:** `36427808785`
> **Source commit:** `15530bfa7e619e44e97302109422f7331d131dc5`
> **Aggregate artifact:** `REC-002-OVERHEAD-36427808785`
> **Artifact digest:** `sha256:1d2f74da69a221559938c6c90a6c08a34852daa0f7000e58769bac87e4a9d6e3`

## Validity

- 8 paired runner blocks
- recorder_off + recorder_on in every block
- 16 / 16 trials accepted
- boundary workload: MemoryHigh=160 MiB, DONTNEED=80 MiB
- recorder_on emitted 26 synchronous JSONL records per trial
- SQLite ingestion remained outside the measured interval

## Aggregate observation

Median recorder_off:

- MemoryHigh events: 0
- max scan memory: 166,285,312 bytes
- post-scan memory: 80,330,752 bytes
- scan elapsed: 44,499,014 ns
- JSONL bytes: 0

Median recorder_on:

- MemoryHigh events: 0
- max scan memory: 166,313,984 bytes
- post-scan memory: 80,330,752 bytes
- scan elapsed: 46,406,860 ns
- JSONL bytes: 6,607

Paired medians (on - off):

- MemoryHigh event delta: 0
- max scan memory delta: -2,048 bytes
- scan elapsed delta: +724,882.5 ns
- scan elapsed ratio on/off: 1.0178166593

All 8 paired blocks had MemoryHigh event delta = 0.

## Interpretation

REC-001 recording did **not** move the observed hosted boundary workload into a different MemoryHigh-event regime.

The paired timing result is noisy. Two blocks had recorder_on substantially faster than recorder_off, while most other blocks showed small positive timing deltas. Therefore this study does not support a precise universal timing-overhead claim.

For this GitHub-hosted workload and this recording density, REC-001 is accepted for STRATA-005 evidence collection.

This is not a claim of universal measurement transparency across platforms, workloads, filesystems, or higher recording densities.

## Research decision

Return to STRATA-005.

Recorder hardening remains sidecar work: a real counterexample triggers atomic repair and a regression, but Recorder robustness work no longer blocks the research mainline.
