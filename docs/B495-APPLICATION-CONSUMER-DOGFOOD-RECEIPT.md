# B495 — Application Consumer Dogfood Receipt

Status: **PASS / FIRST DOWNSTREAM APPLICATION LOOP COMPLETE**

## Frozen execution

- workflow run: 36965325825
- aggregate job: 110707823155
- execution head: dcd8b963b46b8746a05329f847be04114034669a
- targeted tests: 4/4 PASS
- consumer jobs: 3
- aggregate artifact ID: 11208769565
- aggregate artifact ZIP SHA256: a773ffdf4595096f189cad0bd20fb2ce8ddcf0cca8fc6300c0572057e69020ea
- aggregate JSON SHA256: 693303788db8d3a8141ab46c2f2664d4bd3bea2bc483b90d2b3c9a554d00cd58

## Consumer loop

Every consumer used the B494 Composite Action before running the representative
numerical workload.

The selected q was passed downstream as an Action output and bound to the
physical execution receipt.

### q2 consumer

- requested budget: 50,696,192 B
- selected q: 2
- observed peak: 50,511,872 B
- headroom: 184,320 B
- overrun: 0

### q4 consumer

- requested budget: 58,941,440 B
- selected q: 4
- observed peak: 58,773,504 B
- headroom: 167,936 B
- overrun: 0

### q7 consumer

- requested budget: 71,512,064 B
- selected q: 7
- observed peak: 71,356,416 B
- headroom: 155,648 B
- overrun: 0

All three physical executions produced the same exact output digest:

`671c782eacaec6ae75a49121a1ea832c3ec7c3db01c31c8414389ef9c76faaa8`

No calibrated boundary was exceeded.

## Application contract evidence

The dogfood established the full path:

```text
application RAM request
-> Governor Composite Action
-> selected q output
-> downstream physical execution
-> exact semantic gate
-> observed HWM
-> application execution receipt
```

The consumer did not need to call the Governor research calibration modules.

## Why this matters

B494 proved the selector can be exposed.

B495 proves a separate workflow can consume it as an application decision and
use the returned q to configure real execution.

This is the first application-level use of the repaired Governor line.

## Claim ceiling

**APPLICATION_LEVEL_REPAIRED_GOVERNOR_DOGFOOD**

## Next

B496 should define the local/LDC bootstrap contract.

The local adapter must reuse the B494 request/decision/receipt schemas but must
not copy GitHub-hosted thresholds onto the development machine.

The local machine must first establish its own q frontier and calibration.
