# FR-GFX-004 — Adaptive Observation Cadence Receipt

Status: **PASS / SYNTHETIC ADAPTIVE OBSERVATION CADENCE VALIDATED**

## Qualification

- workflow run: 37106967303
- job: 111157279563
- execution head: 7de4be579a30c3b135f5d849c8ee9ba26f22ca95
- targeted tests: 7/7 PASS
- artifact ID: 11268226342
- artifact ZIP SHA256: e50829b484193814086ded8c96465f7b41b6bfd2888907085434ce682373e2d6
- spec SHA256: 1e25293c8e5033b8869337aa9abda72f7f6fd32ecfb77896f117cd2377aad915
- result SHA256: 1dc10d0566a3fe008840966d7a379fee687fd697de34eafe48e39498a96d36bf

## Frozen cadence result

Fixed periodic sampling:

- 50 ms: 100% detection / 20 samples/s
- 100 ms: 87.5% / 10 samples/s
- 250 ms: 59% / 4 samples/s
- 500 ms: 37% / 2 samples/s
- 1000 ms: 26% / 1 sample/s

Adaptive policy:

- base cadence: 500 ms
- cheap trigger recall: 90%
- burst cadence: 50 ms
- burst window: 500 ms
- harmful-event rate: 0.2/s
- detection: 93.7%
- expensive sample rate: 3.8/s
- sample reduction vs always-50ms: 81%

## Derived gates

To achieve a 90% synthetic detection SLO with the frozen 500 ms base sampler,
cheap-trigger recall must be at least:

`84.126984%`.

The adaptive sampler reaches the same sample rate as always-50ms monitoring only
at a frozen harmful-event rate of:

`2.0 events/s`.

## Interpretation

Observation itself should use bounded escalation:

`cheap continuous observer -> anomaly -> expensive telemetry burst`.

This is a synthetic cadence model only. It does not measure live MangoHud,
intel_gpu_top, procfs, or DXVK overhead.

## Next gate

FR-GFX-005 must measure observer perturbation with A-B-A read-only runs before
any live graphics control is allowed.

## Claim ceiling

**SYNTHETIC_OBSERVATION_CADENCE_MODEL_ONLY**
