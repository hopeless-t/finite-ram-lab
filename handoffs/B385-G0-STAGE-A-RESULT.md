# B385 — G0 Stage A complete / capacity survives / PTE suppressor exposed

## Status

COMPLETE.

Scientific hosted run:
`36591417373 = success`

No local-PC execution.

Google Drive COLD replica:
17 / 17 archive ZIPs byte-verified against GitHub Actions SHA-256 digests.

## Primary result

Direct argv-width intervention failed to reproduce the old signal.

Canonical 8/9:
- 3/155 exact-zero
- 1.94%

Padded 08/09:
- 2/179
- 1.12%

Pooled Fisher:
`p=0.666`

Block-conditioned CMH:
`p=0.503`

1M block-conditioned permutation:
`p~=0.655`

Conclusion:

`ARGV_WIDTH_EFFECT_NOT_SUPPORTED`

## Capacity result after width control

Matched-width comparison:

Padded 08/09:
- 2/179 = 1.12%

10/32:
- 14/162 = 8.64%

Risk difference:
`+7.52 pp`

OR:
`8.37`

Fisher:
`p=0.00128`

Block CMH:
- common OR ~=8.84
- p ~=0.00204

1M block permutation:
`p~=0.00177`

Restricting LOW to pre_current 97..100:
- high 14/159
- padded 2/176
- Fisher ~=0.00127
- CMH ~=0.00206

Conclusion:

`CAPACITY_SIGNAL_SURVIVES_ARGV_WIDTH_CONTROL`

Stage A remains exploratory-directional, but the alias explanation is now strongly downgraded.

## H10 / H32 clue

LOW exact-zero:

- H10 11/89 = 12.36%
- H32 3/73 = 4.11%

This difference is suggestive but not closed:
- Fisher ~=0.0907
- block permutation ~=0.0858
- posterior P(H10>H32) ~=0.965

Do not model the capacity response as monotone yet.

## PTE result

First-fault VmPTE +4KiB events:

- H32: 8/160
- every other arm combined: 0/800

Fisher H32 vs all other:
`p~=5.13e-7`

LOW H32 PTE-growth:
- 5 specimens
- 5/5 Q64
- 0/5 exact-zero

HIGH H32 PTE-growth:
- 3 specimens
- 2 Q64
- 1 exact-zero

This is source-compatible with a PTE charge consuming the same stock before data allocation.

memory.stat:pagetables remained delta0 during these VmPTE +4KiB events, validating VmPTE as the sharper receipt.

## Two-touch result

LOW exact-zero specimens:
19

- R1_CANDIDATE: 12
- second zero / OTHER: 7
- R2_CANDIDATE: 0
- PTE_BOUNDARY: 0

R1 fraction:
12/19 = 63.16%

Historical G-A depth1:
22/28 = 78.57%

Exploratory difference:
Fisher ~=0.324

The dominant depth1 population remains compatible with prior data.

## mTHP

All 16 blocks:
- kernel 7.0.0-1012-azure
- global THP [madvise]
- 2MiB [inherit]
- all smaller exposed mTHP sizes [never]

Small mTHP is inactive for this run.

## Evidence

Aggregate raw content set:
- 1936 files
- 4,854,520 bytes
- SHA-256:
  `dd80fb2551833bd001cc27680c6ef3bf3053f7360421667b256b94851ab8798e`

GitHub docs:
- `docs/MEMCG-005G-G0-STAGE-A-RESULT.md`
- `docs/MATH-012-G0-SENSITIVITY-AND-PTE.md`

COLD index:
- `evidence/MEMCG-005G-G0/STAGE-A-COLD-REPLICA-v1.json`

Drive locator:
`Catfood Lab Evidence/finite-ram-lab/MEMCG-005G-G0/run-36591417373`

All 17 Drive archives were re-downloaded and SHA-256 matched to GitHub artifact digests.

## Council

Do not simply add another 16 blocks to the old six-arm panel.

Next research should split into two tracks:

1. fixed-width dense onset:
   `08,09,10,11,12` plus geometry controls;
2. controlled spawn:
   pre-establish target PTE -> Q64 primer -> construct residual1 -> target zero -> next Q64.

The second track is the shortest path toward near-deterministic rare-state capture.

## Stop

New physical hosted experiment requires a new explicit Human launch scope.
