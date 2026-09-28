# STRATA-006 Live-Set Headroom Result

> **Status:** PASS / DIRECT MECHANISM SUPPORT
> **Run:** `36434232753`
> **Launch commit:** `f9fc73fcf8170b129f2e1a91e1f8614d3927ed8e`
> **Aggregate artifact:** `STRATA-006-LIVESET-HEADROOM-36434232753`
> **Artifact id:** `10974842004`
> **Artifact digest:** `sha256:4bee6f7e6cd1b0efdc342187d08204513f2f3e05e7422ad8a87c5d05353e6eb7`

## Validity

The hosted study completed successfully.

- expected trials: 48
- aggregate trial count: 48
- execution status: PASS
- 2 hot-anon settings x 4 blocks x 6 arms
- all block jobs succeeded
- no local-PC execution

All eight block-level onset brackets agreed with their corresponding aggregate bracket.

## Response surface

### hot anon = 56 MiB

Median outcomes:

| arm | high events | positive trials | peak MiB | post-scan live floor MiB |
| --- | ---: | ---: | ---: | ---: |
| buffered | 2 | 4/4 | 159.84 | 158.67 |
| DONTNEED 64 | 0 | 0/4 | 134.59 | 68.61 |
| DONTNEED 72 | 0 | 0/4 | 142.61 | 68.73 |
| DONTNEED 80 | 0 | 0/4 | 150.86 | 68.86 |
| DONTNEED 88 | 0 | 0/4 | 158.61 | 68.61 |
| DONTNEED 96 | 2 | 4/4 | 159.84 | 68.73 |

Onset:

`88 MiB < K <= 96 MiB`

Transformed:

`144 MiB < K + hot <= 152 MiB`

Each of 4 blocks independently produced the same 88–96 MiB bracket.

### hot anon = 72 MiB

Median outcomes:

| arm | high events | positive trials | peak MiB | post-scan live floor MiB |
| --- | ---: | ---: | ---: | ---: |
| buffered | 10 | 4/4 | 159.84 | 158.72 |
| DONTNEED 64 | 0 | 0/4 | 150.67 | 84.79 |
| DONTNEED 72 | 0 | 0/4 | 158.80 | 84.80 |
| DONTNEED 80 | 3 | 4/4 | 159.84 | 84.73 |
| DONTNEED 88 | 7 | 4/4 | 159.84 | 84.61 |
| DONTNEED 96 | 10 | 4/4 | 159.32 | 84.98 |

Onset:

`72 MiB < K <= 80 MiB`

Transformed:

`144 MiB < K + hot <= 152 MiB`

Each of 4 blocks independently produced the same 72–80 MiB bracket.

## Existing center anchor

STRATA-004, hot anon = 64 MiB:

`80 MiB < K <= 88 MiB`

therefore:

`144 MiB < K + hot <= 152 MiB`

The three hot-set conditions are exactly aligned in the transformed interval:

- hot=56: `144 < K+hot <= 152`
- hot=64: `144 < K+hot <= 152`
- hot=72: `144 < K+hot <= 152`

while their raw-MiB onset intervals move by the expected inverse amount.

## Measured non-hot floor

For the 20 DONTNEED trials at each newly measured hot setting:

- hot=56: median `post_scan_live_floor - hot = 12.734375 MiB`
- hot=72: median `post_scan_live_floor - hot = 12.794921875 MiB`

Observed ranges are narrow:

- hot=56: approximately 12.586–13.359 MiB
- hot=72: approximately 12.609–13.109 MiB

This directly supports a decomposition of the retained floor into:

`effective_live_set ~= hot_anon + non_hot_floor`

with a substrate/workload-specific non-hot component near 12.8 MiB in this experiment.

## Hypothesis discrimination

### Fixed raw cadence

Not supported for the tested conditions.

Changing hot anon by +/-8 MiB moved the pressure-event onset by the corresponding opposite amount.

### Additive live-set headroom

Strongly supported directionally on this hosted substrate.

A compact descriptive model is:

`pressure onset when release_interval + effective_live_set approaches MemoryHigh`

or equivalently:

`K ~= MemoryHigh - effective_live_set`

with:

`effective_live_set ~= hot_anon + ~12.8 MiB`

for this particular runner/workload.

The ~12.8 MiB value is an observation, not a portable constant.

## Pseudo-Council convergence

- **Systems:** accept the inverse hot-set/knee movement as a direct mechanism replication.
- **Causal inference:** the single changed axis behaved in the direction and magnitude predicted before execution.
- **Statistics:** 4/4 block agreement at both hot settings is strong directional replication, but the cadence grid still interval-censors the exact threshold.
- **Portability:** the non-hot floor may depend on kernel, systemd, runner image, process/runtime footprint, page-cache behavior, and instrumentation.
- **Safety/authority:** no controller or default follows automatically.

Consensus:

**Promote effective-live-set headroom from a plausible interpretation to the leading tested mechanism on the current hosted substrate. Next test portability by changing substrate/image while freezing the workload.**

## Monte Carlo

Not run in this bounce.

The block-level deterministic replication already discriminates the two current hypotheses without invented priors. A Monte Carlo portability model would still need evidence for cross-substrate threshold/floor variation.

## Next research question

Does the transformed relation survive a materially different hosted software substrate while the workload, pressure, live set, cadence panel, and Recorder contract remain fixed?

## Authority boundary

Hosted research only.
No local-PC execution.
No OSS default cadence or memory controller authorized.
