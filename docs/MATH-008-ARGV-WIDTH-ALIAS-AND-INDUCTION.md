# MATH-008 — Decimal-Width Alias Audit and Rare-State Construction Route

> **Status:** EXPLORATORY DESIGN AUDIT
> **Input:** MEMCG-005G-B/D/E/F and current Linux memcg source
> **No causal claim. No launch authorization.**

## 1. New identifiability problem

The capacity experiments passed `--max-pages` through argv as:

`str(max_pages)`

and the worker parsed it with `atoi()`.

Across the relevant experiments, the observed capacity split is therefore aliased with decimal token width.

### MEMCG-005G-B

- CAP8 token: one decimal digit
- CAP70 token: two decimal digits
- exact-zero capture: 3/240 vs 26/249

### MEMCG-005G-D

- one-digit arm: CAP8 = 2/101
- two-digit arms: CAP32/63/64/65/70 = 56/526

### MEMCG-005G-E

- one-digit arm: CAP8 = 1/74
- two-digit arms: CAP12/16/19/22/26/32/70 = 46/525

### MEMCG-005G-F exact-zero endpoint

- one-digit arms CAP8+CAP9: 14/451
- two-digit arms CAP10+CAP11+CAP12+CAP32: 77/921

In 005G-F specifically, the candidate T10 split is mathematically identical to:

`len(str(cap_pages)) >= 2`

for every frozen arm.

Therefore existing data cannot distinguish a genuine capacity threshold at 10 pages from a launch/argv representation discontinuity at two decimal characters.

## 2. Stratified exploratory audit

Treat each experiment as a stratum and compare two-digit against one-digit arms.

Results:

- 005G-B OR ~= 9.21
- 005G-D OR ~= 5.90
- 005G-E OR ~= 7.01
- 005G-F exact-zero OR ~= 2.85

Exploratory Cochran-Mantel-Haenszel common OR:

`~4.20`

CMH null p:

`~1.33e-10`

Equal-odds heterogeneity p:

`~0.270`

This strongly establishes that the one-digit/two-digit partition reproduces the observed arm effect.

It does **not** establish argv width as the cause because token width is perfectly or near-perfectly confounded with capacity in these designs.

## 3. Why this matters mechanistically

The target anonymous region is mapped before first touch but remains untouched.

Changing mapping length can still alter virtual address placement, but it does not directly imply proportional physical-page charging before the measured fault.

Meanwhile argv strings are copied into the new process image during exec.

Thus the current T10 localization has an unresolved launch-path alias that must be broken before spending on a 5760-candidate exact-zero replication.

## 4. Q64 remains independently real

This audit does not weaken the 64-page accounting quantum.

Current Linux source defines:

`MEMCG_CHARGE_BATCH = 64U`

and the charge path attempts a 64-page batch for a one-page charge, then refills the per-CPU stock with the unused remainder.

This matches the finite-ram-lab calibrated staircase:

fresh one-page miss -> +64 batch -> 63 residual pages -> 63 stock-consuming touches -> next +64.

So:

- Q64 remains source-grounded and experimentally reproduced.
- T10 capacity localization remains unresolved with respect to argv/launch representation.

These are separate claims.

## 5. Alias-breaker design principle

Do not pass capacity numerically through a capacity-dependent argv token.

Instead:

1. controller creates/maps the existing shared control page;
2. controller writes `max_pages_u32` before worker launch;
3. worker receives only the shared-control path in argv;
4. worker reads the integer from shared memory;
5. worker mmaps exactly that many anonymous pages;
6. first-touch path remains unchanged.

Also record, before READY and without touching the anonymous region:

- worker control mapping address;
- anonymous region start address;
- anonymous region end address;
- region start modulo 2 MiB;
- PTE index `(region_addr >> 12) & 511`.

This separates:

- capacity;
- argv decimal width;
- virtual placement / page-table-boundary effects.

## 6. Candidate alias-breaker scale

Using the 005G-F exact-zero planning rates:

- low-side ~= 3.10%
- high-side ~= 8.36%
- valid-LOW admission ~= 47.7%

Monte Carlo for the six-arm frozen panel `{8,9,10,11,12,32}` after removing the capacity argv token gives approximately:

| hosted blocks | total candidates | P(direction correct) | P(two-sided Fisher <.05 and direction correct) |
| ---: | ---: | ---: | ---: |
| 16 | 960 | 99.1% | 56% |
| 24 | 1440 | 99.8% | 77% |
| 32 | 1920 | ~99.96% | 89% |
| 40 | 2400 | ~99.99% | 95% |
| 48 | 2880 | ~99.99% | 98% |

These are design simulations, not evidence.

For an alias-breaking discovery run, 32 blocks / 1920 candidates is a reasonable middle scale.

No hosted run is authorized by this document.

## 7. Route toward near-deterministic rare-state capture

The separate controlled-induction route remains stronger for the operational goal of "catch rate -> 100%".

Given a verified fresh Q64 primer, define total pre-target touches in that batch as `b`.

Ideal source-consistent residual state:

`R_target = 64 - b`

Prospective examples:

- b16 -> depth48
- b19 -> depth45
- b30 -> depth34
- b50 -> depth14
- b63 -> depth1

The b63 arm is the direct near-deterministic depth1 constructor: leave exactly one cached stock page immediately before the measured target touch.

Literal 100% probability cannot be proven from finite trials. For calibration, if all trials succeed:

- 59/59 gives a one-sided exact 95% lower bound just above 95%;
- 299/299 gives a one-sided exact 95% lower bound just above 99%.

Operational goal:

move from rare natural capture to verified state construction.

## 8. Council conclusion

Priority order:

1. break the capacity/argv-width alias before the large 005G-G replication;
2. instrument virtual address placement as a secondary explanatory axis;
3. revive MEMCG-005G-C controlled induction as the main "rare Pokemon construction" track;
4. keep Q64 and T10 as separate hypotheses.

The existing 5760-candidate 005G-G should remain deferred until the alias is broken.

Hosted research only.
No local-PC execution.
