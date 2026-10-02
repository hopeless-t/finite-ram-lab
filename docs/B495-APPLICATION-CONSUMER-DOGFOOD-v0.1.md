# B495 — Application Consumer Dogfood v0.1

Status: **FIRST DOWNSTREAM CONSUMER OF THE GOVERNOR ACTION**.

## 1. Goal

B494 qualified the Governor as an application surface.

B495 verifies that an ordinary workflow can actually use that surface to drive a
physical workload.

The consumer flow is:

```text
declared RAM budget
-> Composite Governor Action
-> selected q
-> downstream repaired numerical workload
-> application execution receipt
```

## 2. Three consumer budgets

The dogfood matrix uses the three v2.1 breakpoints:

- 50,696,192 B
- 58,941,440 B
- 71,512,064 B

Expected selections:

- q2
- q4
- q7

Each matrix entry runs on an independent GitHub-hosted runner.

## 3. Separation of concerns

The Governor Action runs before the optional analysis stack is installed.

Therefore selection itself remains dependency-light.

Only the downstream numerical consumer installs the NumPy analysis/runtime
dependency needed for this representative workload.

## 4. Application receipt

The consumer combines:

- Governor decision receipt;
- physical execution output.

Schema:

`finite-ram-lab.application-execution-receipt/v0.1`

It records:

- requested budget;
- selected q;
- evidence boundary;
- n and coverage;
- exact semantic result;
- observed peak;
- headroom or overrun;
- execution latency;
- output digest.

A selected-q / executed-q mismatch fails closed.

## 5. Boundary semantics

A physical observation above the empirical-max boundary is not hidden and does
not mutate policy inside B495.

It is recorded as:

`EXCEEDS_CALIBRATED_BOUNDARY`

and can feed the already-established tail-vs-drift lane.

## 6. Aggregate gate

The application dogfood requires:

- one valid consumer receipt for q2, q4, and q7;
- exact semantics for all executions;
- one common output digest across q;
- internally consistent decision/execution contracts.

The aggregate preserves any observed boundary exceedance explicitly.

## 7. Claim ceiling

**APPLICATION_LEVEL_REPAIRED_GOVERNOR_DOGFOOD**

## 8. Next

If B495 passes, the GitHub Actions adapter is useful enough to become the
reference adapter contract.

B496 can then define the local/LDC adapter against exactly the same:

- request fields;
- decision receipt schema;
- application execution receipt schema;

while collecting a separate local-machine calibration before making local q
decisions.
