> **SUPERSEDED NOTE (2026-09-30):** This file records an early capability attempt. Later corrected tracefs/kprobe capability gates succeeded and OBS-001..005 used the hosted substrate successfully. Preserve this document as historical failure evidence; do not treat TRACEFS_HOLD as the current substrate verdict.

# OBS-002 — Tracefs capability result

> **Status:** TRACEFS_HOLD
> **Run v1:** 36604850771
> **Run diagnostic v2:** 36605171745
> **Scientific rare-state trials:** 0

## Result

The standard GitHub-hosted ubuntu-26.04 substrate does not expose a usable tracefs dynamic-event interface.

Diagnostic v2 on kernel `7.0.0-1012-azure` found:
- CONFIG_TRACEPOINTS=y
- CONFIG_KPROBES=y
- CONFIG_KPROBE_EVENTS=y
- CONFIG_DYNAMIC_EVENTS=y
- CONFIG_TRACING=y
- CONFIG_FTRACE=y
- CONFIG_DEBUG_FS=y
- kernel lockdown: none

However:
- `/sys/kernel/tracing` exists but exposes no `dynamic_events`, `kprobe_events`, `available_events`, or `trace` file to the job
- `/sys/kernel/debug/tracing` is not exposed
- attempting to mount tracefs reports it is already mounted
- only `try_charge_memcg` and `refill_stock` were visible among the four desired `/proc/kallsyms` symbols
- `consume_stock` and `memcg_uncharge` were not visible as probeable symbols in the runner build

Therefore the direct call-stack observer cannot be validated on this hosted substrate.

## Interpretation

This is an infrastructure capability limit, not evidence against H17-STOCK or folio-uncharge alternatives.

Do not:
- fall back to an unvalidated kprobe parser
- move the experiment to the local PC under current authority
- use a larger/paid runner
- reinterpret any existing spawn endpoint

## Next

Use a user-space-only discrimination experiment that asks whether the 17-page component disappears during an idle interval and whether process RSS/file/anon residency changes with it.

This becomes OBS-003.
