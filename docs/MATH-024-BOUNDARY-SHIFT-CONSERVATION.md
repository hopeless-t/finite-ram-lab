# MATH-024 — Boundary-shift conservation under full residual stock eviction

> Status: SOURCE-GROUNDED SINGLE PHYSICAL SPECIMEN / GENERAL ALGEBRAIC CONSEQUENCE
> Physical source: B405 R6 run 36650670428, CLEAN trial 0:0
> Claim ceiling: mechanism identity and boundary arithmetic; not a population-rate claim.

## 1. Clean verified epoch

After an exact direct Q64 primer, the target memcg stock residual is:

```text
R0 = 63 pages
```

With one page consumed by each measured post-primer touch and no state-changing event:

```text
R_k = 63 - k
```

The canonical next direct Q64 is therefore:

```text
T0 = 64
```

and the Chapter-II boundary deviation is:

```text
Delta = T - 64
```

## 2. Full residual eviction after k clean touches

Suppose the verified target stock is fully drained after exactly `k` clean post-primer touches and before touch `k+1`.

Immediately before eviction:

```text
d = R_k = 63 - k
```

where `d` is the number of target pages removed by the stock drain.

After the eviction, residual stock is zero, so the next measured page touch must acquire a new Q64 batch at:

```text
T = k + 1
```

Therefore:

```text
Delta
  = T - 64
  = (k + 1) - 64
  = k - 63
  = -(63 - k)
  = -d
```

Hence the full-residual-eviction fingerprint is:

```text
Delta = -d
```

The observed boundary shift is the negative of the evicted residual page count.

## 3. B405 R6 physical specimen

Trial:

- run: `36650670428`
- block/identity: `0:0`
- arm: CLEAN
- owner counter: `0xffff8e6e9c04a2c0`

The verified epoch executed 25 measured clean touches.

Predicted residual immediately after touch 25:

```text
R_25 = 63 - 25 = 38
```

Observed between touch 25 and touch 26:

- touch25 POST: 252.780535 s
- target-stock `drain_stock`: 252.786942 s
- same owner `page_counter_uncharge(..., 38)`: 252.786944 s
- touch26 PRE: 252.789381 s
- same owner `page_counter_try_charge(..., 64)`: 252.789493 s
- target `refill_stock(..., 63)`: 252.789494 s

Thus:

```text
predicted drain residual = 38
observed owner uncharge  = 38
T                         = 26
Delta                     = 26 - 64 = -38
```

and therefore:

```text
observed Delta = - observed drained residual = -38
```

The state transition is named:

```text
TARGET_STOCK_EVICTION
```

## 4. Why this matters

Before Chapter II, an early Q64 could have been summarized as a generic failure or an anomalous boundary.

The transactional observer now distinguishes:

```text
VERIFIED
  -> 25 canonical consumes
  -> TARGET_STOCK_EVICTION(d=38)
  -> residual becomes 0
  -> touch26 direct Q64
  -> UNEXPECTED_REFILL
```

The early boundary is therefore a downstream symptom. The causally earlier event is the target-owned eviction.

## 5. General diagnostic barcode

For a complete full-residual eviction:

```text
d = -Delta
```

| Eviction after k touches | Residual d | Next Q64 T | Delta |
|---:|---:|---:|---:|
| 8 | 55 | 9 | -55 |
| 25 | 38 | 26 | -38 |
| 32 | 31 | 33 | -31 |
| 56 | 7 | 57 | -7 |
| 62 | 1 | 63 | -1 |

This is the same geometry anticipated by the age-decoupling HOLD-position experiment, but B405 R6 produced a naturally occurring physical specimen.

## 6. Falsification value

For a future complete specimen:

- if an owner stock drain removes `d` pages and the next direct Q64 gives `Delta != -d`, then the single-eviction model is incomplete;
- if `Delta = -d` but no target-owned drain/refill is observed under zero-miss coverage, then a hidden equivalent state transition remains;
- if multiple state-changing events occur, their algebra must be modeled compositionally rather than assigning the entire Delta to one event.

## 7. Research consequence

The Chapter-II search should retain both `Delta` and the event-side quantity `d = owner residual removed/added by a verified state transition`.

A matching `Delta = -d` is a mechanistic fingerprint. A complete `Delta` with no matching event-side accounting is the higher-value rare specimen.
