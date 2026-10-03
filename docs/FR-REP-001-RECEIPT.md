# FR-REP-001 — Representation × Placement Qualification Receipt

Status: **PASS / SYNTHETIC REPRESENTATION-PLACEMENT GRAPH VALIDATED**

## Frozen qualification

- workflow run: 37096572599
- job: 111127613717
- execution head: 2b7c173a0b627345bf4afec024acd8939f113165
- targeted tests: 7/7 PASS
- artifact ID: 11264198053
- artifact ZIP SHA256: c4cc1beb79551e3ca063dfb223a9867dcd0a448c7d2c699c6b89c9afbcce287a
- spec SHA256: 3f1d1bce83f9e9db443be4bc7a9b146d3217f770b2a55449e43e856077cf1f1e
- result SHA256: 139eb6fb8cfcc8d7ab53995f15c0e6b7e010a012f1f8e9828f7f51d5b693a8cc

## Frozen selections

| state | representation | placement |
|---|---|---|
| HOT_WEIGHT_SHARD | AWQ4 | RAM |
| WARM_EXPERT_SHARD | AWQ4 | SSD |
| COLD_MODEL_SHARD | AWQ4 | CLOUD_OBJECT |
| BITNET_NATIVE_SHARD | BITNET_B1_58 | SSD |

## Taxonomy invariants

- AWQ / GPTQ are modeled as weight-quantization methods.
- NF4 is modeled as a numeric representation.
- GGUF is modeled as a container and receives no compression credit by itself.
- BitNet b1.58 is modeled as a native model encoding / architecture class.
- Cloud object storage is modeled as a placement tier.

## Qualification repair

The first qualification attempt treated all volatile resident bytes as fungible.

That made AWQ4/RAM and AWQ4/VRAM equal at 128 MiB and selected VRAM only because
its synthetic latency was lower.

The repair did not change any representation size, quality proxy, latency,
bandwidth, deadline, cloud policy, or expected semantic compatibility.

Instead the objective was corrected to type residency by resource class:

1. accelerator-resident bytes;
2. host-RAM-resident bytes;
3. local-storage bytes;
4. network-fetch bytes;
5. quality proxy;
6. latency.

This freezes the new invariant:

`residency bytes are tier-typed, not fungible`.

## Cloud counterfactual

Forced AWQ4 + CLOUD_OBJECT remains:

- HOT: deadline FAIL;
- WARM: deadline FAIL;
- COLD: deadline PASS.

Therefore cloud is qualified only as a cold placement class in this synthetic
fixture.

## BitNet compatibility boundary

The planner rejects BITNET_B1_58 for the conventional HOT_WEIGHT_SHARD.

BitNet-native compactness is not modeled as an emergency runtime transform for
arbitrary conventional checkpoints.

## Claim ceiling

**SYNTHETIC_REPRESENTATION_PLACEMENT_GRAPH_ONLY**

No model was converted.
No cloud object was transferred.
No live memory controller was changed.
