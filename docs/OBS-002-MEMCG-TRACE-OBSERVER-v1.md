# OBS-002 — Direct memcg charge/stock/uncharge trace observer v1

> **Status:** DESIGN / IMPLEMENTATION PREP
> **Physical scientific run:** NOT AUTHORIZED BY THIS DOCUMENT
> **Purpose:** distinguish stock drain from ordinary folio uncharge without changing the controlled-spawn scientific endpoint.

## 1. Source contract

Linux v7.0 dynamic kprobe events can probe ordinary kernel functions, fetch function arguments, attach filters, and attach stacktrace triggers when the distro kernel exposes the required capability.

Required target symbols:
- try_charge_memcg
- consume_stock
- refill_stock
- memcg_uncharge

Parser implementation:
src/finite_ram_lab/memcg_trace_observer.py

## 2. Probe definitions

Candidate dynamic events:

try_charge: p:frl_obs/try_charge try_charge_memcg memcg=$arg1:x64 request_pages=$arg3:u32

consume return: r:frl_obs/consume consume_stock memcg=$arg1:x64 request_pages=$arg2:u32 ret=$retval:u64

refill: p:frl_obs/refill refill_stock memcg=$arg1:x64 pages=$arg2:u32

uncharge: p:frl_obs/uncharge memcg_uncharge memcg=$arg1:x64 pages=$arg2:u32

Runtime capability probing is mandatory. No claim may assume a distro kernel preserves these static symbols.

## 3. Target-memcg binding

Do not filter final uncharge events by worker PID because a stock drain may run in a memcg workqueue or another task context.

Instead:
1. enable try_charge tracing before worker startup
2. start worker pinned to preparation CPU
3. obtain worker PID
4. parse try_charge events whose common PID equals worker PID
5. require exactly one memcg pointer
6. bind that pointer as target_memcg
7. filter consume/refill/uncharge events by target_memcg pointer

If target pointer cannot be uniquely established: TRACE_TARGET_BINDING_FAIL.

## 4. Stack classification

STOCK_SLOT_EVICTION_OR_OVERFLOW: stack contains drain_stock and refill_stock.

STOCK_GLOBAL_DRAIN: stack contains drain_stock and drain_local_memcg_stock or drain_all_stock.

FOLIO_UNCHARGE_BATCH: stack contains uncharge_batch or __mem_cgroup_uncharge_folios.

FOLIO_UNCHARGE_SINGLE: stack contains __mem_cgroup_uncharge.

OBJCG_RELEASE: stack contains obj_cgroup_release.

REFILL_DIRECT_UNCHARGE: stack contains refill_stock but not drain_stock.

Anything else: OTHER_UNCHARGE.

## 5. CPU-labelled stock receipts

The trace line supplies CPU identity.

Successful consume_stock return events establish target memcg, CPU, requested pages and a stock hit.

refill_stock establishes target memcg, CPU and pages entering stock.

This permits a measured-CPU stock ledger without inferring stock from global memory.current.

## 6. Touch-window markers

The future controller should write trace_marker records:
- FRL_TOUCH_BEGIN identity=<...> seq=<...> phase=<...>
- FRL_TOUCH_END identity=<...> seq=<...> current_delta_pages=<...>

Markers bracket the same interval used for memory.current measurement.

## 7. Primary observer decision

For every negative delta require one of:
- EXPLAINED_STOCK_DRAIN
- EXPLAINED_FOLIO_UNCHARGE
- EXPLAINED_OTHER_UNCHARGE
- UNEXPLAINED_NEGATIVE_DELTA

For a -17 specimen, the observer succeeds only if target-memcg uncharge pages within the bracket account for the observed decrement within the frozen tolerance.

Do not silently repair the scientific endpoint.

## 8. Capability gate

Before any scientific observer run, an isolated capability smoke must verify:
1. tracefs exists and is writable with sudo
2. dynamic kprobe events are available
3. all required symbols can be probed
4. argument fields appear in event format
5. stacktrace trigger works
6. cleanup removes all frl_obs probes
7. no trace lost-event condition is observed in the smoke

Failure means TRACEFS_HOLD, not fallback to an unvalidated observer.

## 9. Observer-effect gate

Direct tracing changes timing.

A later observer pilot must compare trace-OFF and trace-ON instrumentation on a non-confirmatory workload before the observer enters b63 reliability certification.

Required checks include touch latency distribution, pre_current distribution, primer-position distribution, Q64 morphology and CPU mismatch rate.

## 10. Relationship to frozen results

OBS-002 may explain old -17 events.

It may not rewrite controlled-spawn frozen 49/72, retroactively mark failures as successes, or change MATH-014 denominators.
