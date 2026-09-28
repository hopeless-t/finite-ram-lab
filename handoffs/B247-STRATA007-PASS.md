# Bounce Handoff

> **Bounce ID:** B247
> **Status:** COMPLETE / STRATA-007 PASS / CROSS-IMAGE PORTABILITY SUPPORTED

## Hosted result

STRATA-007 run `36435758885` completed successfully.

- 24 / 24 trials
- aggregate artifact id `10975842099`
- digest `sha256:1f677697ec810dd1f25dee0c7657044d55a52dee3874806579266bbae2370eb4`

## Cross-image result

Ubuntu 24.04 anchor:

`80 < K <= 88 MiB`

Ubuntu 26.04:

`80 < K <= 88 MiB`

Both:

`144 < K+hot <= 152 MiB`

All 4 Ubuntu 26.04 blocks reproduced the same bracket.

Ubuntu 26.04 DONTNEED non-hot floor across 20 trials:

- median 12.8125 MiB
- range approximately 12.805–13.313 MiB

## Executed substrate

All blocks recorded:

- Ubuntu 26.04.1 LTS
- kernel 7.0.0-1012-azure
- image version 20260920.143.1
- cgroup2fs

`systemd_version` was blank. Treat this as a Recorder/environment-receipt defect. Do not claim measured systemd-version difference.

## Council

Effective-live-set headroom is now the leading portable mechanism candidate across the tested GitHub-hosted Ubuntu images.

Next highest-information axis: total cold-data volume.

## Monte Carlo

Deferred; only two image families exist and the current interval grid does not identify a meaningful substrate-offset distribution.

## Next action

Freeze a total-cold-volume study using the Ubuntu 26.04 result as the 96 MiB anchor.

Also repair future environment receipts to use `systemd-run --version`.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
