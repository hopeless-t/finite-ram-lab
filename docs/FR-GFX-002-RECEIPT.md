# FR-GFX-002 — Read-only Observation Plane Receipt

Status: **PASS / READ-ONLY SCHEMA + SYNTHETIC IDENTIFIABILITY VALIDATED**

## Qualification

- workflow run: 37106666614
- job: 111156429719
- execution head: c158faf07fb0794690daa3665d62a6e7213709f6
- targeted tests: 7/7 PASS
- artifact ID: 11267523308
- artifact ZIP SHA256: 840f5e0ab85f667af2664bfcc5786cca52a07e4d87f3ef52a3586a9cd0ee8a99
- spec SHA256: 20717d9d15c75ba2c0f2382fca6c05b54a68e203a2d8c7eb682764ce7dc6af15
- result SHA256: 55304b595cd89332459ee139016f5ed85ca4542151d7191e90ea7414aac1569d

## Frozen result

16,384 deterministic synthetic observations.

At matched GPU-bound recall 86.1534%:

- FPS-only GPU-downscale false-positive rate: 30.6028%
- multi-signal GPU-downscale false-positive rate: 0%
- FPS-only action-class accuracy: 69.6960%
- multi-signal action-class accuracy: 94.9219%

The supported invariant is:

`low FPS != GPU-bound`.

## Read-only contract

The lane changes no:

- sysfs values;
- GPU clocks;
- game settings;
- driver settings;
- process state.

It only normalizes observation streams.

## Claim ceiling

**READ_ONLY_SCHEMA_AND_SYNTHETIC_IDENTIFIABILITY_ONLY**
