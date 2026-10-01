# B468 — Axis Leverage Receipt

Status: **PASS / NEXT AXIS SELECTED**

## Frozen execution

- workflow run: 36929197015
- job: 110593981361
- execution head: 5e3538fbe89c8b4d21d425c401ea89cfab7724ab
- tests: 3/3 PASS
- artifact ID: 11195825236
- artifact ZIP SHA256: a268842f10161db17c187db0d4d192d1db7836b077217fb87634c004c531cdb5
- axis result SHA256: 51118d5e34af669fa64e38631a7fc88c7907f3f06a08101a6c8fdb1e3bb87ca8

## Effect-scale comparison

B463 representation/residency median peak effect:

`25,155,584 B`

Largest tested tile-row median peak effect:

`36,864 B`

Ratio:

```text
25,155,584 / 36,864
= 682.3889
```

This is an experiment-prioritization ratio for the current workload, not a
universal constant.

## Axis decision

Deprioritize for peak-memory research:

`tile_rows`

Next bounded axis:

`resident_lane_concurrency_q`

Frozen coarse sweep:

```text
q = 1, 2, 4, 7
```

Interpretation:

- q=1: one residue lane resident at a time;
- q=7: all seven residue lanes resident before folding;
- q=2/4: grouped streaming between the two extremes.

Hold:

- total lane count = 7;
- tile_rows = 64;
- exact numerical workload and semantic gate.

Measure:

- normalized peak growth;
- latency;
- exactness.

## Why this axis matters

q directly connects:

- Finite RAM residency;
- Ozaki/CRT representation scheduling;
- KMEP-style operating-point search;
- the future adaptive governor.

It is the first control variable in this lane with a natural continuum between
the exact low-residency and high-residency endpoints already measured.

## Claim ceiling

**OFFLINE_AXIS_LEVERAGE_ANALYSIS**

B468 did not execute the q sweep.

## Next

B469 should implement grouped residue production/folding and execute q={1,2,4,7}.
