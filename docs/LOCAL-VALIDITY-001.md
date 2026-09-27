# LOCAL-VALIDITY-001 — Personal Linux External-Validity Protocol

> **Status:** FROZEN DESIGN / NOT AUTHORIZED FOR EXECUTION
> **Parent evidence:** STRATA-002-PILOT-v1 + STRATA-002-CONFIRMATORY-MC-v1

## Why local validation is now higher value

Hosted STRATA-002 showed a strong memory-pressure mechanism:

- sliding DONTNEED reduced post-scan resident footprint by ~52% in the tested workload;
- COLD file residency fell from ~86.5% to 0%;
- MemoryHigh events were suppressed in 8/8 blocks;
- O_DIRECT and DONTNEED had similar pressure footprints.

However, confirmatory design Monte Carlo showed hosted timing noise is the limiting uncertainty.

No candidate through 72 hosted blocks reached the frozen 80% joint assurance target.

Therefore the next information-rich step is the actual personal Linux target environment rather than blindly extending hosted runner count.

## Authority split

### Phase L0 — read-only environment observation

Requires an explicit finite-ram-specific MVCA read-only gate/lease and a bounded tool surface.

Allowed observations only:

- OS/kernel release;
- page size;
- filesystem/mount type for candidate test location;
- total/available RAM;
- swap/zram presence and sizes;
- baseline memory PSI where available;
- baseline vmstat/cgroup counters where available;
- storage device/filesystem identity sufficient to interpret timing.

No file scan.
No cache advice.
No process spawning unless the gate explicitly permits it.
No persistent mutation.

### Phase L1 — bounded synthetic cache experiment

Requires a separate explicit execution gate because even though file contents are unchanged, the experiment intentionally changes runtime cache state.

The gate must bind:

- exact workload binary/script digest;
- exact temporary directory;
- maximum temporary file size;
- maximum process memory;
- maximum runtime;
- no network;
- no arbitrary command forwarding;
- one-shot execution count;
- retry=0 after unknown delivery.

### Phase L2 — real workload dogfood

Not authorized by this protocol.

Only considered after L1 reproduces or falsifies the hosted mechanism.

## L1 scientific design

### Arms

1. ordinary buffered stream;
2. buffered + sliding POSIX_FADV_DONTNEED;
3. optional O_DIRECT reference only if alignment/filesystem capability is explicitly verified.

NOREUSE is not prioritized because STRATA-002 did not show immediate pressure reduction.

### Dataset

Use a generated temporary file, not a personal/user document.

The file must be:

- deterministic;
- disposable;
- read-only during trials;
- deleted only under a separately authorized cleanup action or retained in an explicitly approved temp location.

### Sizing

Do not hard-code hosted MiB values.

Derive a bounded local design from observed available RAM, with conservative caps.

Candidate initial rule:

- HOT anonymous region: min(512 MiB, 5% of physical RAM);
- COLD file: min(1024 MiB, 10% of physical RAM);
- scratch buffer: 4 MiB;
- experimental MemoryHigh: HOT + COLD + small bounded overhead margin, only if an isolated cgroup/scope can be created safely.

Exact values must be frozen after L0 and before L1.

### Replication

Start with 8 paired local blocks.

Reason:

- the hosted mechanism was already 8/8 consistent for pressure;
- local hardware removes between-runner hardware heterogeneity;
- the first objective is external validity, not final production certification.

If local timing variance remains high, run a new sizing Council before adding blocks.

## Metrics

Use the same frozen bundle so hosted and local results are directly comparable.

### Capacity / pressure

- Resident Footprint Reduction (RFR)
- Recovered Memory Headroom (RMH / NRH)
- Cold Cache Retention Fraction (CCRF)
- Pressure Event Suppression (PES)
- Cold-Stream Amplification Factor (CSAF), if O_DIRECT reference exists

### Cost / bandwidth proxy

- Scan-Time Cost Ratio (SCR)
- raw read throughput MiB/s
- wall-clock scan time

### Host safety

- swap in/out deltas;
- zram usage delta where observable;
- memory PSI;
- OOM/kill events;
- system responsiveness proxy only if it can be measured without intrusive instrumentation.

## LLM-specific progression

Do not begin with model weights.

First prove the synthetic one-shot STREAM_COLD mechanism locally.

Then choose one real LLM-related candidate only if its semantics are clear.

Eligible examples:

- disposable model-conversion staging file;
- one-pass shard verification;
- one-pass model/download checksum scan;
- dataset indexing pass.

Do not DONTNEED:

- active mmap-backed model weights;
- active KV cache;
- active inference workspace;
- any region whose reuse semantics are uncertain.

## Capacity vs bandwidth reporting

The local result must report memory and throughput separately.

A memory optimization does not pass practical review merely because it saves RAM.

Minimum practical report:

- RFR;
- RMH;
- CCRF;
- PES;
- SCR;
- MiB/s.

When moving to actual inference, add:

- model load time;
- time to first token;
- steady-state tokens/s;
- context length;
- KV-cache size/format.

## Hosted/local comparison

The local report should compare direction, not demand exact magnitude equality.

Questions:

1. Does DONTNEED still materially reduce COLD cache retention?
2. Does it recover meaningful headroom?
3. Does it suppress pressure/reclaim signals?
4. Is its timing cost stable on fixed hardware?
5. Does local filesystem/kernel behavior match hosted assumptions?

## Stop conditions

Immediately stop and classify HOLD if:

- the execution gate is absent or expired;
- required tool surface is broader than the gate;
- temporary file bounds cannot be guaranteed;
- isolated process/cgroup limits cannot be established where required;
- swap/zram or memory pressure approaches a pre-frozen safety threshold;
- delivery becomes UNKNOWN;
- any unexpected mutation occurs.

No blind retry.

## MVCA relation

Transport reachability is not authority.

The protocol requires:

`Web ChatGPT → Secure MCP Tunnel → MVCA gate/one-shot lease → bounded local tool`

The existing E2E proof is a transport/admission capability proof only.

## Decision

Freeze LOCAL-VALIDITY-001 now.

Wait for an explicit finite-ram-specific MVCA gate before any local execution.
