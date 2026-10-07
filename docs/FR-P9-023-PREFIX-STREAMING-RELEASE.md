# FR-P9-023 — Physical prefix-release streaming pipeline

## Why this follows P9-022

P9-022 uses a conservative sequential rule: downstream CPU service only counts after the entire upstream transfer stage releases the runtime representation. That is correct for an indivisible object but too conservative when prefixes/chunks are independently processable.

FR-P9-023 physically tests whether **release granularity is itself part of the semantic materialization contract**.

## Prior-art boundary

Streaming, pipelining, chunked scheduling, prefetch and service-curve composition are established systems and Network Calculus ideas. This experiment does not claim to invent pipeline overlap.

The Part9-specific question is narrower: may the Semantic Residency Compiler treat a partial runtime projection as semantically released early enough to begin downstream materialization work?

## Frozen physical proxy

Same total work in both modes:

- source: 4 MiB
- chunk size: 1 MiB
- four transfer service gates: 25 ms each
- four CPU service gates + SHA-256 chunk work: 20 ms each
- deadline: 150 ms
- three repetitions, reversed order on the middle repetition

### FULL_BARRIER

Transfer all four chunks first, retain the full object, then perform four CPU quanta.

### PREFIX_STREAMING

After each chunk becomes available, enqueue it to a CPU worker immediately. Transfer of the next chunk proceeds while CPU work on the previous released prefix is underway.

Both modes must produce the same ordered chunk digest signature.

## Expected shape

Ignoring small Python overhead:

```text
FULL_BARRIER    ~ 4*25 + 4*20 = 180 ms
PREFIX_STREAM   ~ pipeline max(transfer,cpu) = about 120 ms
```

The 150 ms deadline is intentionally between those regions.

The experiment also records a **logical buffered-byte peak**. It is not RSS and must not be reported as physical memory consumption. The purpose is only to test whether downstream work requires the complete 4 MiB object to be buffered before progress.

## Boundary

Results support only this userspace paced, chunk-independent proxy. They do not prove that arbitrary compressed formats, model weights, game assets, KV blocks or verification chains are safely prefix-decodable.

That semantic property is the next gate.

```text
prefix available != prefix semantically valid
prefix semantically valid != authority to consume it
```

Claim ceiling:
`HOSTED_GITHUB_USERSPACE_PACED_CHUNK_PIPELINE_PROXY_ONLY_NO_STORAGE_BANDWIDTH_CPU_SCHEDULER_OR_UNIVERSAL_STREAMING_CLAIM`
