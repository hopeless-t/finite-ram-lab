# B424 — Count-only ambient tracefs backend

Date: 2026-09-30

## Goal

Provide the first physical-capture backend for AMBIENT-STOCK-CATCHER without
turning the user's daily machine into a stress-test or high-volume trace sink.

This bounce freezes backend semantics only. It does not arm probes on the host.

## Long-window event policy

During the ambient window:

- refill_stock(owner_memcg) -> histogram only;
- successful consume_stock(owner_memcg) -> histogram only;
- page_counter_uncharge(owner_counter) -> histogram only;
- owner Q64 -> ordinary event logging, owner-filtered.

The three histogram events remain ordinary-event disabled.

This is intentionally different from the earlier high-detail physical pilots.
The ambient catcher is optimized for low-rate long-window observation.

## Why Q64 remains logged

The final diagnostic boundary requires exact temporal attribution to measured
canary touches. The Q64 stream is therefore kept as an ordinary event, but
filtered to:

```text
counter == owner_counter && nr_pages == 64
```

The canary performs zero touches during the ambient interval, so any owner Q64
inside that interval is itself a noteworthy receipt.

## Histogram arithmetic

The backend parses tracefs histogram buckets such as:

```text
{ nr_pages: 1 } hitcount: 7
{ nr_pages: 3 } hitcount: 2
```

and freezes both:

- total event count;
- total pages = sum(nr_pages * hitcount);
- bucket distribution;
- Dropped count.

Example above:

```text
hits=9
pages=13
```

The parser rejects mismatched Totals rather than silently trusting malformed
histogram text.

## Inline owner filters

Histogram triggers carry their own filter clause in addition to the ordinary
event filter.

Frozen examples:

```text
refill:
hist:keys=nr_pages if memcg == <owner_memcg>

consume:
hist:keys=nr_pages if memcg == <owner_memcg> && ret != 0

owner uncharge:
hist:keys=nr_pages if counter == <owner_counter>
```

This preserves the lesson from the earlier histogram scope bug: an ordinary
event filter does not scope a histogram trigger by itself.

## drain_stock

Long-window drain_stock logging remains disabled by default in v1.

Reason:

- drain_stock cannot be owner-memcg filtered directly;
- high-volume global event logging is unnecessary for the immediate hidden
  consumption question;
- direct slot-eviction evidence already exists from the active pressure pilot.

Future direct drain attribution can be added as a separately qualified
short-window/snapshot observer.

## Frozen files

- src/finite_ram_lab/ambient_stock_tracefs_backend.py
- tests/test_ambient_stock_tracefs_backend.py

The backend remains source-neutral above tracefs because it emits receipt rows
consumed by ambient_stock_log_reducer.py.

## Important reducer correction

B424 exposed a design bug before physical execution:

The reducer originally expected exactly one HISTOGRAM receipt per session.
The count-only backend correctly produces separate histogram receipts for
consume/refill/uncharge.

The reducer was corrected to accept multiple histogram receipts and sum their
Dropped counts. A session still requires at least one histogram receipt.

This correction was made before any physical ambient evidence existed.

## Current architecture

```text
private tracefs instance
    |
    +-- refill histogram
    +-- consume-success histogram
    +-- owner-uncharge histogram
    +-- owner-Q64 filtered event
    |
    v
JSONL receipts
    |
    v
ambient_stock_log_reducer
    |
    v
ambient_stock_catcher classifier
```

## Claim ceiling

No host probes were armed in this bounce.

No ambient session has run.
No daemon or system service was installed.
No stress workload was generated.

## Next atomic bounce

Implement the ephemeral one-canary session orchestrator:

1. exact VERIFY R0=63;
2. consume 32 measured target pages;
3. configure the count-only backend;
4. ambient sleep (first run: 600 seconds);
5. freeze histograms + probe coverage;
6. bounded final Q64 chase;
7. emit JSONL receipts;
8. reduce and classify;
9. cleanup and exit.

The first physical session must remain one canary with no helper memcgs and no
synthetic pressure.
