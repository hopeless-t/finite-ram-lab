# Bounce Handoff

> **Bounce ID:** B001  
> **Status:** COMPLETE / PAUSED BY HUMAN

## Objective

Establish whether the CHAR/VAL pressure transition can be connected to semantic-region residency loss without yet introducing a control mechanism.

## Canonical inputs

- `findings/CHAR-001-initial.md`
- `findings/VAL-001-initial.md`
- `docs/OBS-002-DESIGN.md`
- `specs/OBS-002.json`
- latest repository HEAD at pause time: `a7611d9e01160676690e593ac52205a0f7c3f795`

## Completed

- CHAR-001 reproduced a sharp memcg-pressure performance regime.
- VAL-001 reproduced/refined that regime across independent hosted-runner blocks.
- VAL-001 design was selected using Monte Carlo before running the validation.
- OBS-002 design used a sample-size Monte Carlo before allocating hosted-runner trials.
- OBS-002 introduced region-resolved anonymous-mmap residency observation using `mincore(2)`.
- OBS-002 completed successfully across eight runner blocks.

## Evidence / result

OBS-002 run: `36220164283`

Execution:

- 8 independent runner blocks;
- 48 total trials;
- 32 transition-zone trials at 164 MiB;
- all execution checks passed.

Level summaries:

- 160 MiB: median hot-set resident fraction after burst ≈ 0.9601; median retouch latency ≈ 586.4 ms.
- 164 MiB: median hot-set resident fraction after burst ≈ 0.9915; median retouch latency ≈ 13.84 ms.
- 168 MiB: median hot-set resident fraction after burst = 1.0; median retouch latency ≈ 3.96 ms.

At 164 MiB:

- hot-set resident fraction after burst vs retouch latency:
  - Spearman rho ≈ -0.8612;
  - blocked permutation test: 100,000 permutations;
  - two-sided p ≈ 3.0e-5;
  - cluster-bootstrap rho 95% interval ≈ [-0.9267, -0.7400].

Supporting relationship:

- missing hot-set pages after burst vs retouch swap-ins:
  - Spearman rho ≈ 0.8999;
  - blocked permutation p ≈ 3.0e-5.

## Frozen decisions

- Region-resolved observation is now justified as part of the measurement model.
- No control-plane intervention is authorized yet.
- No `madvise`, hinting, mlock, coordinator, or kernel change should be introduced before causal validation.

## Unresolved

The current evidence shows a strong association between loss of hot-set residency after the burst and retouch cost.

It does not yet establish whether hot-set residency loss is the causal bottleneck, a mediator of another mechanism, or a correlated consequence of memcg pressure.

## Next recommended bounce

> Design the smallest causal validation experiment that can distinguish “hot-set eviction causes retouch latency” from competing explanations, while preserving observation/intervention separation.

Run a fresh pseudo-Council before choosing the intervention.

## Authority boundary

This checkpoint does **not** establish:

- that Linux has a memory-management defect;
- that application hints would improve performance;
- that a userspace Memory Coordination Plane is necessary;
- that the same numeric thresholds apply to bare-metal physical-RAM exhaustion.

## References

- VAL-001 successful workflow: `36219464738`
- OBS-002 successful workflow: `36220164283`
- pause HEAD: `a7611d9e01160676690e593ac52205a0f7c3f795`
