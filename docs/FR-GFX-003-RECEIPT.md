# FR-GFX-003 — Signal Ablation Receipt

Status: **PASS / SYNTHETIC SIGNAL ABLATION VALIDATED**

## Qualification

- workflow run: 37106794533
- job: 111156793731
- execution head: 9032b81874715a528e1eb7c42dff3dc024af23e1
- targeted tests: 7/7 PASS
- artifact ID: 11268440396
- artifact ZIP SHA256: 1d2d8b84d77f9c5e30e5ab88a36d0091f9a8a23ba32612b39c5507e00fdb1a3c
- spec SHA256: 644870d432108778787700b5914c5baf906cb348369ed14547c5c4dae0f52436
- result SHA256: 2415570eaee65f43ca9470f8500e34507d0b3e51e2c0e8a1c5400f310db8adc5

## Frozen ablation

| signals | abstract cost | action accuracy | GPU false-downscale |
|---|---:|---:|---:|
| FRAME | 1.0 | 71.1975% | 32.5228% |
| FRAME_MEM | 1.2 | 88.3850% | 10.3636% |
| FRAME_GPU | 1.8 | 69.6960% | 2.3371% |
| FRAME_CPU | 1.2 | 79.2358% | 22.1593% |
| FRAME_GPU_MEM | 2.0 | 86.8835% | 0% |
| FULL | 2.2 | 94.9219% | 0% |

Under the frozen safety rule:

- accuracy >= 85%
- GPU false-downscale <= 1%

the minimum-cost set is:

`FRAME_GPU_MEM`.

Under a 90% accuracy floor, FULL is required.

## Main result

Observation itself should be tiered:

`cheap observation -> ambiguity -> expensive observation escalation`.

The acquisition-cost units are synthetic and do not claim measured live
instrumentation overhead.

## Claim ceiling

**SYNTHETIC_SIGNAL_ABLATION_ONLY**
