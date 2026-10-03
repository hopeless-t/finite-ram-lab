# FR-FP-016 Failure Biopsy — COLD restore is not one linear bandwidth

Status: **SCIENTIFIC MODEL FAILURE / REPLICATION REQUIRED**

Failed run:
- workflow: 37145768871
- job: 111269263616
- head: ade878de61fbfddd790767accb370aad3fb483c9

## What passed

Physical tier separation remained clean:

- every WARM file was >=95% resident before restore;
- every COLD file was <=10% resident before restore;
- all state restores passed exact sentinel checks;
- COLD was slower than WARM at every size;
- both WARM and COLD median latencies increased with state size.

WARM median restore:

- 4 MiB: 0.287 ms
- 8 MiB: 0.557 ms
- 16 MiB: 1.468 ms
- linear fit R²: 0.987

## What failed

The frozen hypothesis required a single linear COLD restore model with R²>0.95.

Observed COLD medians:

- 4 MiB: 3.406 ms
- 8 MiB: 4.750 ms
- 16 MiB: 36.574 ms

Single-line COLD fit:

- R²: 0.914
- negative fitted intercept
- effective single-slope bandwidth estimate is therefore not trusted.

COLD/WARM ratios:

- 4 MiB: 11.86x
- 8 MiB: 8.53x
- 16 MiB: 24.92x

The 16 MiB point is qualitatively different.

## Theory update

Do not loosen the R² threshold.

The new hypothesis is a nonlinear COLD restore knee between 8 and 16 MiB.

The first-run marginal slopes are:

    4 -> 8 MiB:
      about 0.336 ms / MiB

    8 -> 16 MiB:
      about 3.978 ms / MiB

The second segment is more than 10x steeper.

## Replication contract

v0.2 reruns the same physical sizes and paired design.

It requires:

- WARM remains reasonably linear;
- COLD single-line R² remains below 0.95;
- COLD 8->16 marginal slope remains >5x the 4->8 slope;
- tier residency and integrity gates remain unchanged.

Raw per-block restore timings are now emitted in the result marker.

If the knee does not replicate, classify the first result as host variance
rather than a stable size boundary.

## Claim ceiling

**HOSTED_COLD_RESTORE_NONLINEARITY_REPLICATION_ONLY**
