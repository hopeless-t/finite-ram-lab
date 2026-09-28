# EVIDENCE-001 SQL Corpus Result v1

> **Status:** PASS / QUERYABLE EVIDENCE SURFACE OPERATIONAL
> **Run:** `36447185071`
> **Launch commit:** `25285b8a82472bf9846d508b87efb61dc19315ab`
> **Artifact:** `EVIDENCE-001-SQL-CORPUS-36447185071`
> **Artifact id:** `10981205287`
> **Artifact digest:** `sha256:9e6a4d90afbb753741a65406b215d1fe0d121af337f0d422bfa790b456662707`

## Validity

The repaired hosted corpus build completed successfully.

Outputs:

- `corpus.sqlite`
- `query-results.json`
- `query-results.md`

Seeded canonical studies:

- STRATA-004..009
- REC-003..004

The corpus is derived evidence. Canonical result documents and raw artifacts remain authoritative.

## SQL rediscovery

The corpus recovered the accepted relations without hard-coding the final verdicts into the output.

### Pressure axis

Fixed raw-knee interval intersection:

- max lower-exclusive bound: 96 MiB
- min upper-inclusive bound: 80 MiB
- intersection empty: true

Thus one universal raw-MiB knee cannot satisfy the tested pressure settings.

### Live-set transform

For the H=160 / cold=96 live-set series:

`144 MiB < K+hot <= 152 MiB`

is the common transformed interval across 3 rows.

### Cold-capacity axis

Across cold capacities:

- 96 MiB
- 192 MiB
- 384 MiB

the SQL corpus found one distinct knee bracket:

`80 MiB < K <= 88 MiB`

at the current 8 MiB resolution.

### Clean floor

REC-004 clean pre-observer medians span:

`0.248046875 MiB`

across 96 / 192 / 384 MiB.

This remains a bounded floor observation, not a smooth capacity law.

### Observer effect

The query surface preserves REC-003/004 observer-effect rows separately from clean workload-floor rows.

The semantic separation prevents legacy post-observer measurements from silently entering clean-floor queries.

## Axis coverage

Tested:

- pressure
- hot live set
- runner image
- cold capacity
- observer hygiene

Untested in the current corpus:

1. access pattern
2. concurrent streams
3. read chunk size
4. write path

## Research consequence

The SQL corpus is now a working hypothesis-discovery and counterexample-search surface.

It does not create causal proof, but it can:

- rediscover interval incompatibilities;
- test transformed invariants;
- expose missing experimental axes;
- keep corrected measurement semantics machine-readable.

## Next hypothesis

A separate discrete-memory-accounting hypothesis is now high-value.

Current Linux source defines:

`MEMCG_CHARGE_BATCH = 64U`

and the kernel cgroup selftest describes memcg charging as occurring in per-CPU batches 64 pages large.

On a 4 KiB base-page system:

`64 pages * 4 KiB/page = 256 KiB`

This numerically matches the coarse ~256 KiB observer/accounting steps seen in REC-003/004.

This is only a mechanism candidate. It must be tested directly.

## Authority boundary

Hosted research only.
No local-PC execution is authorized by this result.
No memory-control policy is authorized.
