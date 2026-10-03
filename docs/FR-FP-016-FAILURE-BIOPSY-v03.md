# FR-FP-016 Replication Update

Status: **NEGATIVE REPLICATION RESULT**

Second physical run:

- workflow: 37145960094
- job: 111269831053
- head: 4abd6fcd9e80649949d16ee5ec9e220c5a857c56

## Specific knee rejected

First-run COLD medians:

- 4 MiB: 3.406 ms
- 8 MiB: 4.750 ms
- 16 MiB: 36.574 ms

Second-run COLD medians:

- 4 MiB: 27.695 ms
- 8 MiB: 140.907 ms
- 16 MiB: 165.444 ms

The first run put the large marginal jump between 8 and 16 MiB.

The second run put the large jump between 4 and 8 MiB.

Therefore a fixed 16 MiB restore knee is not replicated.

## Stable negative result

WARM remained comparatively regular:

- first-run WARM R2: 0.987
- second-run WARM R2: 0.999

A single linear COLD model failed twice:

- first-run COLD R2: 0.914
- second-run COLD R2: 0.730

Second-run within-size COLD coefficient of variation:

- 4 MiB: 1.08
- 8 MiB: 0.77
- 16 MiB: 0.61

Second-run COLD ranges:

- 4 MiB: about 3.8 to 122 ms
- 8 MiB: about 14.9 to 216.6 ms
- 16 MiB: about 81 to 449 ms

## Theory update

Reject a single stationary COLD restore bandwidth.

Do not promote a fixed size knee.

The next experiment fixes state size and increases repeated observations to
measure:

- tail quantiles;
- coefficient of variation;
- temporal ordering;
- burst/run structure;
- lag correlation;
- WARM control.

The Governor needs a restore-latency distribution or deadline-miss probability,
not only a median restore time.

## Claim ceiling

**HOSTED_COLD_RESTORE_NONSTATIONARITY_NEGATIVE_RESULT_ONLY**
