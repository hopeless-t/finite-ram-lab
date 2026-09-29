# OBS-001 — Charge/uncharge discriminator for the 17-page emission

> **Status:** DESIGN / CAPABILITY GATE FIRST
> **Authority:** standard GitHub-hosted runner only
> **No reliability scaling.**

## Goal

Classify the recurrent -17 memory.current emission by observing the kernel path that performs the corresponding uncharge.

## Phase 0 — capability gate

Before running scientific candidates, verify on the exact hosted kernel:

1. tracefs exists;
2. kprobe events are enabled;
3. memcg_uncharge is visible/probeable;
4. refill_stock is visible/probeable;
5. a temporary probe can be installed and removed;
6. no persistent tracing configuration remains after cleanup.

If any item fails:

STOP = TRACE_CAPABILITY_HOLD.

Do not silently fall back to a different tracing mechanism.

## Proposed kprobe events

Primary:

memcg_uncharge:
- memcg pointer
- nr_pages
- common pid/cpu/timestamp

For nr_pages == 17, request a stacktrace trigger.

Supporting:

refill_stock:
- memcg pointer
- nr_pages

Optional if probeable:

try_charge_memcg:
- memcg pointer
- requested nr_pages

The purpose of refill/charge probes is correlation, not endpoint definition.

## Classification

### STOCK_DRAIN

The -17 memcg_uncharge stack contains drain_stock / drain_local_memcg_stock or equivalent stock-drain path.

### FOLIO_UNCHARGE

The stack contains uncharge_batch / uncharge_folio or equivalent ordinary folio release path.

### OTHER_UNCHARGE

The stack identifies another caller.

### UNCORRELATED

memory.current falls by -17 without a matching 17-page memcg_uncharge in the trace window.

### TRACE_INVALID

Probe loss, malformed trace, or cleanup failure.

## User-space receipts

Every measured touch should gain:

- monotonic timestamp pre/post
- memory.current pre/post
- VmRSS
- RssAnon
- RssFile
- RssShmem
- VmPTE

This allows a second discriminator:

- memory.current -17 with stable process RSS => stock/kernel/accounting candidate
- memory.current -17 with matching process RSS loss => process-page release candidate

RSS is corroborative, not authoritative.

## Minimal physical scale after capability PASS

Use a diagnostic scale only.

Suggested:

- 4 hosted blocks
- 12 identities/block
- 48 total
- no b62/b63/b64 reliability claim
- stop once the source class of -17 is directly observed enough times to establish a repeatable caller signature

Exact scale and stopping rule must be frozen before launch.

## Non-goals

OBS-001 does not:

- certify b63 reliability;
- estimate natural exact-zero incidence;
- alter the frozen v2 endpoint;
- infer causality from memory.current alone;
- use local PC or paid runners.
