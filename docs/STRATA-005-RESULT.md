# STRATA-005 External Validity Result

> **Status:** PASS / CROSS-PRESSURE DIRECTIONAL EVIDENCE
> **Run:** `36431449193`
> **Launch commit:** `9f0ed686406a49b42e14d855e3d941970e55c94d`
> **Aggregate artifact:** `STRATA-005-EXTERNAL-VALIDITY-36431449193`
> **Artifact id:** `10973632531`
> **Artifact digest:** `sha256:8702206b4cb645796f0c2ca17f60bc155898d380225f6216804b790396592554`

## Validity

The hosted relaunch completed successfully.

- expected trials: 40
- aggregate trial count: 40
- execution status: PASS
- frozen matrix: 2 MemoryHigh settings x 4 runner blocks x 5 arms
- aggregate completed only after all block jobs succeeded
- no local-PC execution

The predecessor run `36430416271` remains excluded because it failed before scientific measurement.

## STRATA-005 response surface

### MemoryHigh = 144 MiB

| arm | median high events | positive trials | median peak MiB | peak/high | post-scan file residency |
| --- | ---: | ---: | ---: | ---: | ---: |
| buffered | 14 | 4/4 | 143.936 | 0.99955 | 0.6875 |
| DONTNEED 48 | 0 | 0/4 | 126.598 | 0.87915 | 0 |
| DONTNEED 64 | 0 | 0/4 | 142.609 | 0.99034 | 0 |
| DONTNEED 80 | 7 | 4/4 | 143.867 | 0.99908 | 0 |
| DONTNEED 96 | 14 | 4/4 | 143.869 | 0.99909 | 0 |

Observed onset bracket:

`64 MiB < knee <= 80 MiB`

### MemoryHigh = 176 MiB

| arm | median high events | positive trials | median peak MiB | peak/high | post-scan file residency |
| --- | ---: | ---: | ---: | ---: | ---: |
| buffered | 0 | 0/4 | 172.734 | 0.98145 | 1.0 |
| DONTNEED 48 | 0 | 0/4 | 126.609 | 0.71937 | 0 |
| DONTNEED 64 | 0 | 0/4 | 142.734 | 0.81099 | 0 |
| DONTNEED 80 | 0 | 0/4 | 158.609 | 0.90119 | 0 |
| DONTNEED 96 | 0 | 0/4 | 172.736 | 0.98146 | 0 |

Observed onset screen:

`knee > 96 MiB`

## Combined with STRATA-004 anchor

STRATA-004 at MemoryHigh=160 MiB established:

`80 MiB < knee <= 88 MiB`

The three interval observations are therefore:

- H=144: `K in (64, 80]`
- H=160: `K in (80, 88]`
- H=176: `K > 96`

A single fixed raw-MiB knee cannot satisfy all observations.

## Additive live-set headroom interpretation

Define an interval model:

`K = H - B`

where:

- `H` = MemoryHigh;
- `K` = release-cadence pressure-event onset;
- `B` = resident live-set / reserve floor that must remain below MemoryHigh.

Transforming the observed brackets gives:

- H=144 -> `B in [64, 80)`
- H=160 -> `B in [72, 80)`
- H=176 -> `B < 80`

Common feasible region:

`B in [72, 80) MiB`

The STRATA-005 DONTNEED cells have median post-scan resident memory of approximately `76.72 MiB`, which lies inside that common region.

This is directional support for an additive available-headroom mechanism:

`safe release cadence ~= MemoryHigh - effective live-set floor - safety margin`

It is not a controller formula and does not authorize an OSS default.

## Why the fixed-cadence hypothesis loses support

A fixed raw knee would require one K value to satisfy all pressure configurations. The interval intersection is empty.

In contrast, the additive-headroom representation has a non-empty physically plausible common interval that overlaps the measured retained resident floor.

This is stronger evidence for headroom tracking than for a universal raw-MiB cadence.

## Throughput boundary

Hosted scan timing remains noisy and non-monotonic. Timing is retained as descriptive secondary evidence only and is not used to choose a cadence.

## Pseudo-Council convergence

- **Systems:** pressure onset moved upward when MemoryHigh increased; fixed cadence is not portable across these pressure settings.
- **Mechanism:** the nearly pressure-independent peak for a given release interval, until MemoryHigh clamps it, is consistent with release interval plus a retained live-set floor.
- **Statistics:** interval-censored evidence supports model discrimination but not a precise fitted coefficient.
- **OSS portability:** one hosted substrate and one hot-anon setting do not authorize a general controller or default.
- **Authority:** Proposal != Decision; measurement does not grant execution or deployment authority.

Consensus:

**Accept STRATA-005 as directional evidence for effective-live-set headroom, reject a universal fixed raw-MiB knee for the tested conditions, and test live-set variation next.**

## Monte Carlo

Deferred.

A probabilistic fit now would still require inventing the distribution of per-run threshold jitter from only three aggregate onset brackets, one of which is right-censored. The deterministic interval result already discriminates the fixed-knee and additive-headroom hypotheses without invented priors.

## Next research question

If MemoryHigh is held fixed while the hot/live resident set changes, does the knee move in the opposite direction by approximately the same amount?

That experiment can directly test the additive mechanism rather than merely adding more pressure levels.

## Authority boundary

Hosted research only.
No local-PC execution.
No OSS default cadence or controller authorized.
