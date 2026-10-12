# Fast Reinstall Loop — Convergence v1

Date: 2026-10-12
Status: CONVERGED FOR CURRENT PURE-PYTHON PROJECTION LANE

## Path to convergence

1. Source reinstall: 1638.96 ms median; runtime ~3.70 MB.
2. Wheel install: 836.57 ms.
3. Direct wheel extraction: 17.07–18.17 ms; runtime ~1.48 MB.
4. Direct wheel zipimport: 1.14 ms; materialized runtime **0 bytes**.
5. Artifact epoch identity: 0.003665 ms median versus 0.94296 ms full SHA-256.
6. Warm worker: 12.16–12.28 ms request latency versus ~50.8 ms cold process.
7. In-process useful-work lower bound: 11.39 ms; warm-worker overhead only ~7.9%.
8. Fork-template: 14.29 ms while destroying request-local mutable state after every request.
9. Full eviction/reprime: 43.50 ms warm and 45.61 ms fork-template versus 49.52 ms direct cold execution in the 60-block confirmatory run.

## Frozen invariants

- semantic output parity maintained in all paired/triplet runtime experiments;
- canonical source-tree build residue eliminated by isolated artifact construction;
- direct zipimport requires zero per-runtime package-tree materialization;
- local artifact mutation with same size and restored mtime was detected by the epoch identity tuple through ctime change;
- full SHA-256 remains the trust root outside the bounded local immutable-artifact epoch;
- fork-template resets deliberate mutable request state on every execution;
- resident process images are optional and can be evicted without losing capability.

## Convergence criterion

This lane stops because all three conditions now hold:

1. **Projection cost is negligible:** artifact activation verification is measured in single-digit microseconds and runtime materialization is zero.
2. **Warm execution is near the useful-compute floor:** persistent-worker latency is within 10% of the already-running in-process lower bound.
3. **Resident memory is not required for correctness or acceptable cold recovery:** a fully evicted state reprimes within the frozen 10% cold-path gate.

Further optimization of reinstall/projection would improve total user-visible latency by materially less than optimizing the workload itself. The next performance frontier is therefore algorithm/runtime execution, not reinstall.

## Converged controller shape

```text
verified artifact epoch
        |
        +-- identity unchanged --> cheap activation check
        |                         |
        |                         +-- RAM abundant + state reuse OK --> warm worker
        |                         |
        |                         +-- RAM abundant + reset required --> fork template
        |                         |
        |                         `-- RAM pressure --> no resident worker
        |                                             |
        |                                             `-- next request --> reprime
        |
        `-- identity changed --> full hash / re-establish artifact epoch
```

The runtime is therefore a cache, not an asset.

**Keep meaning and trust evidence. Recreate or evict everything else.**
