# FR-P9-003 — Phase-separated capability residency frontier

Status: **HOSTED PROXY + TYPED COST FRONTIER / PART 9**

Parent: **FR-P9-002**

## Why this experiment exists

FR-P9-002 established that a semantic projection can remain correct while its
physical placement becomes stale after runtime materialization. Re-observation
and replanning are therefore necessary when planner-relevant resource facts
change.

The next temptation is to turn capability residency into a simple state machine:

```text
HOT -> WARM -> COLD -> OFF
```

and then search for one universal timeout.

That is likely too coarse.

A capability kept WARM pays resident byte-time while idle. A capability made
COLD pays transfer and resume work when needed again. Neither cost has the same
unit, and neither is automatically more important.

## Research question

> Does a universal warm/cold threshold exist across phase gaps, or are
> `KEEP_WARM` and `FAULT_IN` typed Pareto alternatives until an external price or
> hard resource constraint is supplied?

## Two policies

### KEEP_WARM

The capability payload remains resident across the phase gap.

Typed cost:

```text
resident_byte_seconds = B * gap
requested_transfer_bytes = 0
resume_latency = resident verification/access latency
```

### FAULT_IN

The capability is not resident during the phase gap and is read again when the
next phase needs it.

Typed cost:

```text
resident_byte_seconds = 0
requested_transfer_bytes = B
resume_latency = file read + verification latency
```

The `requested_transfer_bytes` field is the logical number of file bytes read by
the proxy. It is **not** a claim about physical NVMe bus traffic, page-cache miss
bytes, or device-level I/O.

## Hosted proxy

The GitHub-hosted Linux probe uses:

- Ubuntu 24.04
- 8 MiB deterministic capability payload
- six repetitions
- alternating arm order
- SHA256 equality as the semantic verification gate
- best-effort `POSIX_FADV_DONTNEED` before file reads when supported

The warm arm hashes already resident bytes.

The fault-in arm requests the same file bytes and hashes the resulting payload.

This is deliberately a narrow proxy. `POSIX_FADV_DONTNEED` is an advisory
interface, so the result cannot be interpreted as a universal SSD latency or a
guaranteed physical cache miss.

## Typed Pareto rule

For the frozen vector:

```text
C = (
  resident_byte_seconds,
  requested_transfer_bytes,
  resume_latency_ns
)
```

policy A dominates B only when A is no worse in every dimension and strictly
better in at least one.

For every positive phase gap:

- KEEP_WARM necessarily pays more gap resident byte-time;
- FAULT_IN necessarily requests more transfer bytes.

Therefore neither policy can dominate the other on the typed vector solely from
those two dimensions, regardless of which latency median wins on one hosted run.

This means the lab must not invent a universal `warm_timeout_ms` from the proxy.

## Scalarization only with explicit external prices

If a caller supplies an explicit price vector:

- `p_resident`: cost per byte-second of residency
- `p_transfer`: cost per requested transfer byte
- `p_latency`: cost per nanosecond of resume latency

then the two policies can be scalarized for that caller.

The crossover phase gap is:

```text
gap* =
  [p_transfer * B + p_latency * (L_fault - L_warm)]
  / (p_resident * B)
```

when `p_resident > 0`.

The lab does not infer those prices. Without them:

```text
scalar_gain = null
```

This preserves the result from the earlier physical rent work: heterogeneous
resource costs should remain typed until a real external price or hard constraint
makes scalarization meaningful.

## Part 9 interpretation

The new decomposition is:

```text
SemanticTemperature
  HOT / WARM / COLD / DORMANT

PhysicalResidency
  RAM / peer / storage / absent

PhaseLifetime
  current phase / next phase / delayed reuse

CostVector
  byte-time / transfer / latency / verification / recovery risk
```

`SemanticTemperature` does not directly select `PhysicalResidency`.

A semantically WARM capability can still live on storage if latency constraints
allow it. A semantically COLD object can still remain physically resident if
external memory rent is effectively zero and fault-in cost is high.

## Qualification gates

The hosted probe passes only when:

- all warm digests equal the frozen source digest;
- all fault-in digests equal the same digest;
- KEEP_WARM requests zero transfer bytes;
- FAULT_IN pays zero gap resident byte-seconds;
- both policies remain non-dominated on every frozen positive phase gap;
- no scalar price vector is inferred;
- authority effect remains NONE.

## Authority boundary

Residency optimization does not grant execution authority.

A capability being warm, resident, or immediately callable is not permission to
invoke it.

`authority_effect = NONE`

## Claim ceiling

`HOSTED_GITHUB_LINUX_FILE_READ_PROXY_AND_TYPED_COST_FRONTIER_ONLY_NO_UNIVERSAL_STORAGE_OR_HOST_THRESHOLD_CLAIM`

## Next falsifier

FR-P9-004 should add repeated phase transitions and shared capability reuse.

The next candidate equation is not merely a warm/cold timeout. It is a
parallelism/reuse tax:

```text
NetParallelGain
  = QueueReduction
  + UsefulConcurrency
  - ResidencyTax
  - Contention
  - Coordination
  - VerificationOverhead
```

The test should ask whether adding workers or slots increases useful progress
while silently multiplying resident capability/context state, and whether shared
immutable state can remove part of that tax.
