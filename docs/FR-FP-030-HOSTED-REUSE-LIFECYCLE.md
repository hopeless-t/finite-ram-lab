# FR-FP-030 — Hosted physical reuse-lifecycle Governor

Status: **HOSTED PHYSICAL INTEGRATION CANDIDATE**

Parent: **FR-FP-029**

## Why

FR-FP-025 through FR-FP-029 built a decision chain:

    tier economics and deadline risk
      -> reuse ceiling
      -> exact reuse evidence budget
      -> evidence staleness
      -> drift-alarm frontier

Those pieces still need to actuate a real memory tier.

FR-FP-030 connects the reuse-evidence lifecycle to hosted Linux WARM/COLD
page-cache behavior.

## Frozen state

One synthetic state:

    8 MiB regular file

Physical tiers:

WARM
: file is resident in page cache.

COLD
: file is fsynced and then released with POSIX_FADV_DONTNEED.

Reuse:

    restore the full file into a fresh anonymous hot mapping
    verify sentinel integrity
    close the hot mapping

## Frozen reuse schedule

One deterministic two-phase trace shared by all arms.

Seed:

    20261004

Phase 1:

    60 opportunities
    p(reuse)=0.02

Phase 2:

    60 opportunities
    p(reuse)=0.25

The frozen trace contains 17 reuse events.

## Arms

### ALWAYS_WARM

Keep the backing file WARM throughout.

### ALWAYS_COLD

Keep the backing file COLD throughout and reapply DONTNEED after every restore.

### LIFECYCLE_GOVERNOR

Start WARM.

Use the FR-FP-027 exact 95% reuse upper bound.

COLD is allowed when:

    p_upper <= 0.10

The 0.10 ceiling is intentionally frozen because FR-FP-028/029 validated the
drift fixture at that ceiling.

While qualified, monitor the FR-FP-029 k=4 frontier point:

    at least 4 reuse events in the most recent 35 observations

When that alarm fires:

- old reuse evidence is invalidated;
- the evidence epoch is reset;
- the state returns WARM;
- requalification requires fresh evidence.

The k=4 point is a pilot choice, not a universal default.

## Physical observations

For every opportunity:

- file residency from mincore;
- selected tier;
- policy action;
- cgroup memory.current when available.

For every reuse:

- pre-restore page residency;
- physical restore latency;
- process storage read_bytes when available;
- exact sentinel integrity.

## Qualification

The integration must show:

- identical reuse schedule across all arms;
- all restores verify;
- ALWAYS_WARM is physically resident on reuse;
- ALWAYS_COLD is physically nonresident on reuse;
- Governor uses both tiers;
- Governor performs fewer COLD restores than ALWAYS_COLD;
- Governor page-cache residency integral is below ALWAYS_WARM and above
  ALWAYS_COLD;
- drift alarm occurs after the high-reuse phase begins;
- Governor finishes WARM.

Latency superiority is not a PASS condition because prior work proved COLD
restore is nonstationary.

## Evidence boundary

Reuse semantics and the trace are synthetic.

The following are hosted physical evidence:

- file page-cache residency;
- POSIX_FADV_DONTNEED;
- anonymous hot restoration;
- storage read accounting;
- Linux cgroup memory observation;
- byte-integrity verification.

## Next

If this pilot passes, replace the fixed 0.10 reuse ceiling with the full
FR-FP-025/026 risk-aware ceiling computed from:

- current-run COLD calibration;
- residual-tail prior;
- WARM restore prior;
- external memory shadow price;
- deadline;
- miss tolerance.

## Claim ceiling

**HOSTED_PHYSICAL_TIER_ACTUATION_ON_ONE_SYNTHETIC_TWO_PHASE_REUSE_TRACE_ONLY**
