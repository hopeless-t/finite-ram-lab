# MATH-028 — CPU-local memcg stock-slot pressure

## Motivation

Age-Decoupling Stage A R2 created a large wall-clock separation while holding measured target touch count fixed.

Frozen R2:

- FAST zero-miss canonical n=3
- HOLD32 zero-miss canonical n=9
- no known verified-state hazard
- no unexplained boundary deviation
- no complete unknown owner emission
- no true target failure
- realized median exposure factor ~= 13.3793

This bounded no-specimen result weakens a high-frequency pure wall-clock TIME explanation but does not exclude rare time hazards.

TARGET_STOCK_EVICTION is already established physically.

The next causal question is therefore:

> Is verified target stock lost because it simply ages, or because competing memcg stock slots on the same CPU create eviction pressure?

## Linux source geometry

At Linux source commit:

`551c722f40809618230001baccf219193e22fc5a`

`mm/memcontrol.c` defines:

```text
NR_MEMCG_STOCK = 7
```

The stock is per CPU.

Each CPU therefore has seven memcg stock slots:

```text
cached[0..6]
nr_pages[0..6]
drain_idx
```

### consume_stock

`consume_stock(memcg, nr_pages)` searches only the current CPU's seven slots.

If the target memcg is present and the slot contains enough pages, the requested pages are consumed from that slot.

### refill_stock

For a new refill:

1. if the same memcg is already cached, its slot is increased;
2. otherwise, the first empty slot is used;
3. if no slot is empty:
   - select `stock->drain_idx`;
   - advance `drain_idx` modulo 7;
   - `drain_stock(stock, i)`;
   - install the new memcg in that slot.

Therefore new distinct memcgs on the same CPU can causally evict an existing target stock slot.

Distinct memcgs on another CPU do not operate on the target CPU's `memcg_stock` array.

## Thirteen-helper eviction bound

Assume the target has successfully reached VERIFIED state and its residual stock occupies one of the seven slots on the selected stock CPU.

We do not know:

- the target slot index;
- the current `drain_idx`;
- how many of the other six slots are already occupied.

Worst case:

1. target occupies one slot;
2. all six remaining slots are empty;
3. six distinct new helper memcgs are needed to fill them;
4. the stock array is now full;
5. each additional distinct helper refill evicts exactly one slot selected by round-robin `drain_idx`;
6. in at most seven such replacements, every slot index is selected once.

Thus:

```text
6 fill insertions + 7 replacement insertions = 13
```

and therefore:

```text
<= 13 distinct same-CPU helper memcg insertions
```

are sufficient to force selection of the target slot, absent intervening slot changes.

The experiment should stop early when the target drain is directly observed.

The number 13 is a worst-case causal bound, not a required fixed workload.

## Proposed intervention point

Use a verified b63 transaction.

After measured direct-Q64 primer:

```text
R0 = 63
```

Consume exactly 32 measured fresh pages:

```text
R32 = 31
```

Then stop target touches and apply one intervention.

After intervention, resume target measurement.

### QUIET

No helper slot pressure.

Prediction:

```text
next owner Q64 at T=64
Delta = 0
```

### OFFCPU_SLOT_PRESSURE

Create/prime distinct helper memcgs on a different CPU.

Prediction under CPU-local slot pressure:

```text
target stock remains on target stock CPU
T=64
Delta=0
```

Any source-grounded target drain invalidates the clean control interpretation.

### SAMECPU_SLOT_PRESSURE

Create/prime distinct helper memcgs on the target stock CPU, stopping as soon as target-owner drain is observed, with hard cap 13.

If the full residual 31 is evicted before another target touch:

```text
expected residual becomes unavailable
next target touch requires direct Q64
```

The first post-primer direct Q64 should then occur at:

```text
T = 33
Delta = 33 - 64 = -31
```

This gives a strong mechanistic fingerprint:

```text
TARGET_STOCK_EVICTION after touch 32
<-> Delta = -31
```

under the full-drain/simple-boundary assumptions.

## Why OFFCPU is essential

A helper workload has many possible non-stock side effects:

- systemd activity;
- slab allocation/free;
- scheduler activity;
- memory accounting;
- shared-LRU activity;
- wall-clock delay.

OFFCPU_SLOT_PRESSURE preserves much of that workload while changing the causal variable of interest:

```text
same per-CPU memcg_stock array?
```

Thus the core contrast is:

```text
QUIET
vs
OFFCPU helper activity
vs
SAMECPU helper activity
```

not merely workload versus no workload.

## Observer requirement

R2 showed that ordinary event logging for owner `refill_stock` is the remaining completeness bottleneck.

The target owner can receive stock through paths that do not immediately emit an owner page_counter_uncharge, so refill observation cannot simply be removed.

Before the full slot-pressure panel, validate a lower-write-amplification refill observer.

Preferred architecture:

1. keep Q64 as a normal event receipt;
2. keep owner-uncharge as a normal event receipt;
3. aggregate owner refill sizes/counts through a soft-disabled tracefs histogram trigger;
4. retain kprobe-profile missed-hit accounting;
5. if any refill is detected, classify the epoch as a known state change unless source semantics prove it neutral;
6. preserve unknown complete evidence.

## Claim ceiling

The slot-pressure experiment is a causal mechanism test for verified-state eviction.

It does not estimate hazard prevalence or certify reliability.
