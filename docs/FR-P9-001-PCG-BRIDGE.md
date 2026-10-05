# FR-P9-001 PCG bridge

This note records the transfer shape only. It is not a catfood-pcg-lab result.

## Shared abstraction

Finite RAM and PCG both operate on a much larger addressable/canonical universe than the set that should be resident for one bounded unit of work.

```text
canonical world / semantic truth
        |
        +-- current frame projection
        +-- generation projection
        +-- verification projection
        +-- recovery projection
```

Candidate PCG mappings:

| Finite RAM / semantic residency | PCG realization |
| --- | --- |
| canonical atom | world rule, recipe, chunk, asset, provenance record |
| WorkUnit | frame, chunk generation, collision/nav validation, save/recovery step |
| decision plane | content/placement choice needed now |
| verification plane | topology, collision, budget, determinism validator |
| recovery plane | seed, recipe, checkpoint, regeneration manifest |
| capability plane | generator, decompressor, renderer/validator capability |
| compiled projection | current bounded world/runtime slice |
| cold canonical state | distant cells, source variants, editor history, archive |

## Transfer gate

Do not claim a PCG performance gain from FR-P9-001. The first valid transfer requires a catfood-pcg-lab experiment comparing at least:

1. fixed preload;
2. simple distance-only streaming;
3. semantic/utility compiled projection plus physical placement.

Frame-time tail, visible pop-in, load latency, regeneration cost, verifier correctness and resident bytes must remain separate metrics until an explicit utility/rent is supplied.
