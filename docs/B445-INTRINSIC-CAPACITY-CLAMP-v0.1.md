# B445 — Intrinsic Demand + Capacity Clamp Model v0.1

Status: **qualified STRATA-005 structural response model**. No new physical experiment ran.

## 1. Qualified dataset only

B444 rejected merging STRATA-004 into STRATA-005 as one stable-plan sweep because observer semantics changed.

B445 therefore fits only the internally consistent STRATA-005 capacity pair:

- MemoryHigh 144 MiB
- MemoryHigh 176 MiB

with common DONTNEED release intervals:

- 48
- 64
- 80
- 96 MiB.

## 2. A surprisingly simple coordinate

For every pressure-free DONTNEED cell define:

B_i = peak_i - release_interval_i.

The observed values are approximately:

- 78.598
- 78.609
- 78.609
- 78.734
- 78.609
- 76.736 MiB.

The robust median is:

**B_peak = 78.609 MiB.**

The 176/96 point is visibly different, but the median is insensitive to it.

## 3. Model

For release interval K and MemoryHigh H:

**intrinsic peak demand**

P_intrinsic(K) = B_peak + K

and observed peak:

P_peak(H,K) ~= min(P_intrinsic(K), H).

Pressure onset is predicted when:

B_peak + K > H.

Equivalently:

K > H - B_peak.

This is the same additive-headroom geometry discovered empirically in STRATA-005/006, now expressed as an intrinsic-demand/capacity-clamp model.

## 4. STRATA-005 classification

At H=144:

- K=48 -> intrinsic 126.609 < 144 -> no pressure
- K=64 -> intrinsic 142.609 < 144 -> no pressure
- K=80 -> intrinsic 158.609 > 144 -> pressure
- K=96 -> intrinsic 174.609 > 144 -> pressure

Observed median MemoryHigh events:

- 0
- 0
- 7
- 14.

At H=176:

- K=48 -> no pressure
- K=64 -> no pressure
- K=80 -> no pressure
- K=96 -> intrinsic 174.609 < 176 -> no pressure

Observed median MemoryHigh events:

- 0
- 0
- 0
- 0.

Pressure/no-pressure classification:

**8 / 8 correct.**

## 5. Peak-amplitude fit

Using:

P_hat = min(78.609 + K, H)

seven of eight observed median peaks are within 0.133001 MiB of prediction.

The exception is:

- H=176
- K=96
- observed 172.736 MiB
- predicted 174.609 MiB
- residual -1.873 MiB.

This cell remains pressure-free, so the amplitude deviation does not alter the threshold classification.

B445 leaves its mechanism unresolved rather than fitting an extra parameter from one point.

## 6. Contextual STRATA-004 check

B444 forbids merging the 160 MiB STRATA-004 measurements into the fit.

They can still be used as an independent contextual mechanism check.

With B_peak=78.609:

- H=160, K=80 -> 158.609 < 160 -> predict no pressure
- H=160, K=88 -> 166.609 > 160 -> predict pressure.

STRATA-004 observed:

- K80 median high events = 0
- K88 median high events = 2.

So the predicted bracket matches the independent historical result.

This is not treated as a stable-plan three-point fit.

## 7. Why this matters for Live-State Frontier

The model separates two quantities:

### Intrinsic state demand

B_peak + K

What the plan would like to keep live absent the capacity boundary.

### Capacity clamp

H

What the cgroup permits before pressure machinery activates.

This creates a physical analogue of the B437 activation geometry:

- below the intrinsic requirement, runtime pressure modifies behavior;
- above it, the plan expresses its intrinsic live-state frontier.

The capacity threshold is therefore not merely a percentage utilization target.

It is the crossing of a plan-specific state requirement.

## 8. Relation to Capacity-Activated Strategy

B436/B437 described a combinatorial plan-activation cliff.

B445 describes another boundary:

**runtime state-expression cliff.**

A plan may remain legally executable on both sides, but below its intrinsic live-state demand the runtime starts reclaiming/pressuring state.

So the two major finite-memory boundaries are now:

1. plan feasibility/activation boundary;
2. runtime intrinsic-demand clamp boundary.

They should not be conflated.

## 9. Claim boundary

B_peak=78.609 MiB is specific to the frozen hosted workload/observer contract.

It is not:

- a Linux constant;
- an OSS default;
- a universal safety margin;
- a controller setting.

The useful object is the model form, not this one fitted number.

## 10. Next bounce B446

Decompose B_peak into:

- retained/post-scan live floor;
- transient scan overhead.

STRATA-005 already reports a retained DONTNEED floor around 76.72 MiB.

If:

B_peak ~= B_retained + B_transient

then the difference is only around 1.9 MiB.

Testing that decomposition may connect:

- the old pressure-knee work;
- observer hygiene;
- the newer Live-State Frontier distinction between persistent and ephemeral state.
