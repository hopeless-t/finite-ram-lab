# MATH-012 — G0 Stage-A Sensitivity and Mechanism Decomposition

> **Status:** COMPLETE / POST-STAGE-A ANALYSIS
> **Input:** MEMCG-005G-G0 run 36591417373
> **No new physical trials.**

## 1. Why the pooled Fisher result is not enough

The Stage-A primary data are block-randomized and the LOW admission rate is not identical across arms.

Therefore the pooled comparison was stress-tested against:

1. block-conditioned CMH;
2. block-conditioned Monte Carlo permutation;
3. restriction to the dominant pre_current mode 97..100.

All three preserve the capacity signal and fail to rescue the argv-width explanation.

## 2. Block-conditioned Monte Carlo

Within each block, condition on:

- the number of valid LOW candidates in the two compared groups;
- the total number of exact-zero specimens.

Randomly reallocate zero specimens under the no-arm-effect null using the corresponding hypergeometric distribution.

1,000,000 draws.

### Capacity high vs padded low

Observed:

- high: 14 / 162
- padded: 2 / 179
- risk difference: +7.5247 pp

Monte Carlo:

- two-sided p ~= **0.001772**
- directional p ~= **0.001631**
- MC standard error ~= 4.2e-5

### Padded vs canonical

Observed:

- padded: 2 / 179
- canonical: 3 / 155
- risk difference: -0.8182 pp

Monte Carlo:

- two-sided p ~= **0.6549**

### H10 vs H32

Observed difference:

+8.25 pp

Monte Carlo:

- two-sided p ~= **0.0858**
- directional p ~= **0.0660**

Treat as a follow-up clue.

## 3. LOW-gate sensitivity

496 trials entered LOW.

The histogram is dominated by:

- 97 pages
- 98 pages
- 99 pages
- 100 pages

Restricting to exactly those values retains 486 LOW trials.

Capacity high vs padded remains:

- 14/159 vs 2/176
- Fisher p ~= 0.001267
- block CMH OR ~= 8.83
- CMH p ~= 0.00206

Thus unusual LOW baseline values do not create the signal.

## 4. Important HIGH-state observation

Across HIGH trials, exact-zero is common rather than rare.

This is expected to represent a different hidden-stock regime and confirms why the LOW gate is mechanistically important.

The scientific claim is therefore not:

“capacity changes zero-delta universally.”

It is:

“capacity changes the probability of exact-zero within the selected low-memory-current state.”

The interaction with hidden state is part of the phenomenon.

## 5. PTE allocation is an H32-specific mediator candidate

Observed VmPTE +4 KiB:

- H32: 8/160
- all other arms combined: 0/800

The event is therefore strongly associated with H32 mapping capacity.

Within LOW, 5/5 H32 PTE-growth specimens produced Q64.

This is exactly the direction predicted if the low-stock state is near exhaustion and the newly charged PTE page consumes stock before the data page.

However H32 no-PTE-growth exact-zero remains only 3/68, below H10 11/89.

Therefore PTE growth can explain part of H32 suppression but is not yet a complete explanation for H10/H32 heterogeneity.

## 6. Rehabilitating the boundary model only where appropriate

MATH-009 rejected a naive 8-vs-10 2 MiB-boundary explanation because changing two pages changes uniform boundary probability by only roughly 2/512 ~= 0.39%.

For H10 vs H32, the length difference is 22 pages.

A uniform-order estimate is:

22/512 ~= 4.30%

The observed H32-only PTE growth incidence is:

8/160 = 5.0%

These are now of the same order.

This does **not** explain the old T10 onset, because H10 itself has the largest Stage-A exact-zero rate and no observed PTE growth.

It does make page-table boundary geometry a credible explanation for the H32-specific suppressor.

## 7. Two-state decomposition

A useful working decomposition is now:

### Trigger component

Capacity around 10+ changes probability of entering/carrying the rare LOW exact-zero stock state.

This survives argv-width control.

### Suppressor component

At larger VMA footprint, a first-fault PTE allocation can consume stock before the data charge.

H32 directly exposes this component through VmPTE +4 KiB.

These can coexist and produce a non-monotone response.

## 8. Controlled-spawn consequence

To construct the rare R1 state intentionally:

1. ensure the target and next page already have a PTE table allocated;
2. only then calibrate a fresh Q64 stock batch;
3. consume stock to residual one page;
4. touch the untouched target data page;
5. require target delta0;
6. require next adjacent touch Q64;
7. verify VmPTE delta0 across both measured touches.

This turns the newly discovered H32 suppressor into an explicit exclusion/control condition rather than noise.

## Council conclusion

The next high-value work is not more samples of the old aliased panel.

It is:

- a fixed-width dense onset panel around 08/09/10/11/12;
- explicit PTE geometry receipt/control;
- and a PTE-preconditioned controlled-induction pilot.

The “rare Pokémon” objective should now optimize **state construction**, not merely natural capture rate.
