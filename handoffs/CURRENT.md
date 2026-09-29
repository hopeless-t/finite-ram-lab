# CURRENT

> Latest bounce: B385
> Stage: G0 STAGE A COMPLETE / CAPACITY SIGNAL SURVIVES / PTE SUPPRESSOR EXPOSED
> Stop: NEXT PHYSICAL RUN REQUIRES NEW HUMAN LAUNCH SCOPE

## G0 Stage A

Run:
`36591417373 = success`

All:
- 16/16 blocks PASS
- 960/960 trials valid
- CPU mismatches 0
- LOW 496
- HIGH 464
- LOW morphology only Q64 or exact-zero

## Argv alias

Canonical 8/9:
3/155 = 1.94%

Padded 08/09:
2/179 = 1.12%

Fisher:
`p=0.666`

Block CMH:
`p=0.503`

1M block permutation:
`p~=0.655`

Verdict:
`ARGV_WIDTH_EFFECT_NOT_SUPPORTED`

## Capacity after width control

Padded 08/09:
2/179 = 1.12%

10/32:
14/162 = 8.64%

RD:
`+7.52pp`

OR:
`8.37`

Fisher:
`p=0.00128`

Block CMH:
`p~=0.00204`

1M block permutation:
`p~=0.00177`

Core LOW pre_current 97..100 sensitivity remains essentially identical.

Verdict:
`CAPACITY_SIGNAL_SURVIVES_ARGV_WIDTH_CONTROL`

## H10 vs H32

- H10 11/89 = 12.36%
- H32 3/73 = 4.11%

Suggestive heterogeneity only.

Do not assume monotonicity.

## PTE

VmPTE +4KiB:

- H32 8/160
- all other arms 0/800
- Fisher p ~=5.13e-7

LOW PTE-growth specimens:
5/5 Q64.

No LOW PTE-growth specimen was exact-zero.

This is compatible with page-table charge consuming the same near-exhausted memcg stock.

## Two-touch

LOW exact-zero:
19

- R1_CANDIDATE 12
- OTHER/second-zero 7
- R2 0
- PTE_BOUNDARY 0

R1 fraction:
63.16%

## mTHP

All small exposed mTHP orders:
`[never]`

2MiB:
`[inherit]`

global:
`[madvise]`

Small mTHP explanation is closed for this run.

## Evidence residency

Raw set:
- 1936 files
- 4,854,520 bytes
- content SHA:
  `dd80fb2551833bd001cc27680c6ef3bf3053f7360421667b256b94851ab8798e`

Drive COLD:
`Catfood Lab Evidence/finite-ram-lab/MEMCG-005G-G0/run-36591417373`

17/17 Drive archives:
`BYTE-IDENTICAL PASS`

## Next design

Track A:
fixed-width dense onset around
`08,09,10,11,12`

Track B:
PTE-preconditioned controlled spawn:

`preallocate target PTE -> verified Q64 primer -> consume to residual1 -> target zero -> next Q64`

Track B is the direct route toward intentional rare-state generation.

No new physical launch is authorized yet.
No local-PC execution.
