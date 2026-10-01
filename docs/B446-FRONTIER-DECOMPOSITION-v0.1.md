# B446 — Persistent / Observer / Ephemeral Frontier Decomposition v0.1

Status: **partially identified historical decomposition**. No new physical experiment ran.

## 1. B445 left one hidden quantity

B445 fitted the STRATA-005 transient base:

**B_peak = 78.609 MiB**

from the pressure-free peak relation:

P_peak ~= min(B_peak + K, H).

The natural next question is:

> How much of B_peak is persistent state and how much exists only during the scan?

STRATA-005 contains a post-scan floor, but later measurement-hygiene work changed the semantics of that field.

## 2. STRATA-005 legacy post-scan floor

Across the eight DONTNEED cells, the median post-scan total memory values are:

- 76.609375
- 76.734375
- 76.609375
- 76.705078125
- 76.609375
- 76.734375
- 76.732421875
- 76.736328125 MiB.

Their median is:

**B_legacy_post = 76.71875 MiB.**

Relative to this legacy floor:

B_peak - B_legacy_post
=
78.609 - 76.71875
=
**1.89025 MiB.**

So the scan transient frontier is about 1.89 MiB above the historical post-scan floor.

## 3. Why this is not yet a clean ephemeral-state measurement

REC-004 later established that the historical STRATA ordering was:

scan
-> file residency observer
-> hot residency observer
-> post_scan memory.current.

Therefore historical `post_scan` is a **post-observer quantity**.

REC-004 also observed coarse observer-induced cgroup charges and froze the prospective rule:

> workload floor must be sampled before the residency observer.

So the correct structural decomposition is:

**B_peak = B_clean + O_observer + E_transient**

while STRATA-005 directly gives only:

**B_legacy_post = B_clean + O_observer.**

Subtracting the two identifies:

**E_transient relative to the legacy floor = 1.89025 MiB.**

It does not separately identify:

- clean persistent floor;
- observer contribution;
- clean transient excess.

## 4. Why REC-004 cannot numerically repair STRATA-005 after the fact

REC-004 is invaluable for measurement semantics, but it ran under a different hosted image and a later observer contract.

Therefore B446 does not take a REC-004 observer delta and subtract it from STRATA-005.

That would manufacture a clean floor by cross-study subtraction.

REC-004 is used only to establish:

- the direction of the semantic correction;
- the need for paired pre/post observer measurements;
- the fact that the observer contribution may be quantized and trial-dependent.

## 5. Partial identification result

Identified from the same STRATA-005 historical dataset:

- B_peak = 78.609 MiB
- B_legacy_post = 76.71875 MiB
- B_peak - B_legacy_post = 1.89025 MiB.

Not identified:

- B_clean
- O_observer
- B_peak - B_clean.

This is a useful result because it says exactly what the old evidence can and cannot answer.

## 6. Live-State Frontier interpretation

The three terms have different meanings.

### B_clean

State that remains physically resident after the scan, before the observer perturbs the process.

This is the closest physical analogue of persistent live state.

### O_observer

State introduced by the measurement mechanism itself.

This belongs to instrumentation, not the workload frontier.

### E_transient

Additional state needed while the scan is active.

This is the ephemeral physical frontier.

The target quantity for Live-State Frontier is not simply peak minus any later snapshot.

It is:

**peak minus a semantically clean persistent baseline measured in the same contract.**

## 7. New hypothesis H446 — Frontier Separability

> A physical live-state frontier can be decomposed into persistent workload state, measurement state, and phase-local ephemeral state, but the components are identifiable only when measurement ordering exposes them separately.

This connects:

- old observer-hygiene work;
- the B445 capacity clamp;
- the newer semantic/physical frontier model.

## 8. Experimental consequence

The next clean physical study should capture, in one trial:

1. pre-scan baseline;
2. scan peak;
3. immediate post-scan pre-observer floor;
4. post-observer diagnostic floor.

Then:

E_transient_clean
=
scan_peak - post_scan_pre_observer

and:

O_observer
=
post_scan_post_observer - post_scan_pre_observer.

This gives a paired decomposition rather than cross-run subtraction.

## 9. Current conclusion

The old STRATA-005 data already says something useful:

the transient peak base is only about 1.89 MiB above its very stable historical post-observer floor.

But B446 deliberately stops before calling that 1.89 MiB a clean ephemeral working-set size.

That stronger claim requires paired pre/post observer measurements in the same dynamic-capacity study.
