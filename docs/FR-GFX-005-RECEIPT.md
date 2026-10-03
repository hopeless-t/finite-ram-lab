# FR-GFX-005 — Observer Perturbation A-B-A Receipt

Status: **PASS / SYNTHETIC A-B-A PERTURBATION PROTOCOL VALIDATED**

## Qualification

- workflow run: 37109160215
- job: 111163547982
- execution head: 05d2cf1e2ebf36cf9e5dbae7c671cec2c4e77eab
- targeted tests: 6/6 PASS
- artifact ID: 11269390956
- artifact ZIP SHA256: a5f1e6ac96f3d2d90fdf608f7f53ff9cb3c7d9ca8cccaad0e58fdfc66e3df571
- spec SHA256: 11cddade9a7311b6e8f8d915a61f39ac057e4cc6c759992928034cd941b1de83
- result SHA256: 75445535ec6d8e2ccf6f014b25ee6611a00f17d2c2a26208acf3e13fa9ebf380

## Frozen result

Under the synthetic NULL observer:

- one naive A-B block exceeds the 1 ms fixture margin in 53.8940% of episodes;
- one drift-corrected A-B-A block exceeds it in 23.5352%;
- eight matched A-B-A blocks reduce the frozen false >1 ms call to 0%.

With eight matched blocks:

- LIGHT observer equivalence pass: 93.2617%;
- HEAVY observer equivalence pass: 0%.

The 1 ms margin is fixture-only.

## Main invariant

`read-only != zero perturbation`

and:

`observer qualification requires repeated matched blocks, not one before/after run`.

## Claim ceiling

**SYNTHETIC_OBSERVER_PERTURBATION_PROTOCOL_ONLY**
