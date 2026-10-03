# FR-GFX-001 — Happy iGPU / UMA Governor Receipt

Status: **PASS / SYNTHETIC UMA iGPU GOVERNOR VALIDATED**

## Qualification

- workflow run: 37106120171
- job: 111154872539
- execution head: ff3bf16297b7c2e5e51436be353239c8c09bcf77
- targeted tests: 6/6 PASS
- artifact ID: 11267529099
- artifact ZIP SHA256: 45aae1d9fcfef2f01af29a153e318fecc57a98052e317f57bab62fc83e44c67d
- spec SHA256: 1facc6d3b8fa95d3a3c69e93c16b07e1219fbce9ce71a895c0ed4b6228c1b49d
- result SHA256: 765544aa8e436a9ea17bfafa971a8b182bee64844308546a7688d70c82de1e89

## Frozen 5000-frame synthetic result

| policy | deadline misses | memory violations | control evaluations |
|---|---:|---:|---:|
| NATIVE_STATIC | 706 | 185 | 5000 |
| UPSCALE_STATIC | 224 | 0 | 5000 |
| EXPERT_FULL_SCAN | 41 | 0 | 60000 |
| LOCAL_ONLY | 69 | 0 | 6970 |
| BOUNDED_PROBE_4 | 53 | 0 | 7379 |

## Derived result

Relative to LOCAL_ONLY, BOUNDED_PROBE_4:

- reduces deadline misses by 23.1884%;
- increases control evaluation work by 5.8680%;
- increases minimum UMA headroom by about 92.55 MiB;
- slightly reduces the mean synthetic quality proxy.

Relative to EXPERT_FULL_SCAN, BOUNDED_PROBE_4:

- uses about 87.70% fewer control evaluations;
- has a worse frame-time tail and lower quality.

Therefore the result is a Pareto trade, not a universal win.

## Interpretation

The useful transfer from KSLA is:

`local expertise + rare externally-verified nonlocal probes`.

The global probes are only injected when the best local adjustment remains
deadline/headroom risky.

This provides a graphics analogue of bounded idiocy: cheap nonlocal proposals
cover local-controller blind spots without paying for global exhaustive search
every frame.

## Source grounding

- Linux DRM memory management explicitly covers UMA and dedicated-VRAM devices.
- Vulkan sparse residency permits partially resident resources when supported.
- FidelityFX / dynamic-resolution style systems motivate explicit tradeoffs
  between render resolution, working set, and visual quality.

## Boundary

All frame-time, memory, quality, scene, and bandwidth values are synthetic
controls.

No live game or GPU was benchmarked.

No driver setting was changed.

## Claim ceiling

**SYNTHETIC_UMA_IGPU_GOVERNOR_ONLY**
