# B422 — Ambient Stock Catcher v1

Date: 2026-09-30

## Question

Can a verified target memcg stock state be changed by ordinary host activity,
without deliberately generating same-CPU helper pressure or any other stress
workload?

The immediate motivation is the frozen Same-CPU R2 block2 specimen:

- diagnostic boundary reached T=33;
- owner uncharge31 was observed;
- no classified target drain was attributed;
- owner refill contamination was zero.

This bounce does not reinterpret that historical specimen. It creates a
low-disturbance capture model for future observations.

## Direction change

The previous physical-pilot path asked:

> Can we actively cause and directly observe a stock transition?

B422 adds a second research mode:

> Can we place a known canary state on a normal host, stop touching it, and
> infer what ordinary ambient kernel/memcg activity did from low-rate receipts
> plus the final boundary?

This is explicitly not a stress test.

## Canary geometry

The bounded session begins from the already established geometry:

1. VERIFY establishes R0=63.
2. Exactly 32 measured target touches are performed.
3. Expected residual becomes 31.
4. The target performs zero touches during the ambient window.
5. Ordinary host activity continues.
6. A bounded final diagnostic chase measures the next owner Q64 boundary.

No helper memcgs are generated and no synthetic pressure workload is injected.

Default synchronous LDC capability exposure is 60 seconds; 600 seconds is a later qualification target. The v1 hard maximum is 1800 seconds.

## Core low-rate observer

The long ambient window should prioritize owner-filtered or count-only
observation:

- successful consume_stock return for owner_memcg;
- refill_stock for owner_memcg;
- page_counter_uncharge for owner_counter;
- owner Q64;
- kprobe_profile miss deltas;
- histogram dropped count.

Long-window ordinary drain_stock logging is not required by v1 because the
probe cannot be directly owner-memcg filtered and may add unnecessary load on
a daily-use host. A later qualified short snapshot mode may add direct drain
attribution.

The design therefore treats drain evidence as optional enrichment, not as a
requirement for discovering hidden stock consumption.

## Classification principle

Event presence alone never proves causality.

A direct mechanistic label is promoted only when an isolated mechanism predicts
the observed final boundary exactly.

Baseline:

```text
next Q64 T = 64
```

For an isolated stock loss of d pages:

```text
predicted T = 64 - d
```

Direct slot-eviction promotion additionally requires matching attributed owner
uncharge pages.

Examples:

```text
drain31 + owner_uncharge31 + T33
  -> DIRECT_SLOT_EVICTION_FINGERPRINT

consume31 + T33
  -> DIRECT_STOCK_CONSUMPTION_FINGERPRINT

consume31 + T64
  -> UNKNOWN_COMPLETE

owner_uncharge31 + no drain/consume/refill + T33
  -> UNATTRIBUTED_OWNER_UNCHARGE

no mechanism signal + no owner uncharge + T64
  -> STABLE_RESIDUAL
```

Refill involvement is intentionally not reduced to simple arithmetic in v1.
It remains REFILL_MUTATION_PRESENT, or MULTI_PATH_TRANSITION when multiple
mechanism classes are present.

Complete observations that do not fit an exact fingerprint remain
UNKNOWN_COMPLETE.

## Pseudo-Council

### Position A — keep active same-CPU pressure as the primary tool

Strength:
- fast causal intervention;
- already produced a clean T33 / Delta=-31 specimen.

Weakness:
- does not answer whether ordinary host activity naturally reaches the same
  state transition;
- less suitable for continuous use on the user's daily machine.

Verdict:
- retain as a causal falsifier, not the only observation mode.

### Position B — run a completely passive system observer with no canary

Strength:
- minimal intervention.

Weakness:
- initial memcg stock state is unknown;
- observed kernel activity cannot be tied to a known residual boundary.

Verdict:
- insufficient for mechanism inference by itself.

### Position C — verified canary plus passive ambient window

Strength:
- known initial state;
- nearly zero target activity during exposure;
- normal host workload supplies the intervention naturally;
- final boundary provides an independent state readback.

Weakness:
- canary setup and final diagnostic are still small interventions;
- long-window attribution must remain low-rate and conservative.

Verdict:
- selected for B422.

## Classifier implementation

Frozen files:

- specs/TX-AMBIENT-STOCK-CATCHER-v1.json
- src/finite_ram_lab/ambient_stock_catcher.py
- tests/test_ambient_stock_catcher.py

The classifier separates:

- PREVERIFY_HOLD
- OBSERVATION_HOLD
- INSTRUMENTATION_HOLD
- CANARY_CONTAMINATED
- STABLE_RESIDUAL
- DIRECT_SLOT_EVICTION_FINGERPRINT
- DIRECT_STOCK_CONSUMPTION_FINGERPRINT
- REFILL_MUTATION_PRESENT
- MULTI_PATH_TRANSITION
- UNATTRIBUTED_OWNER_UNCHARGE
- BOUNDARY_CENSORED
- UNKNOWN_COMPLETE

A deterministic 100,000-case offline fuzz pass completed during authoring with:

- no classifier exception for valid generated inputs;
- every result inside the registered classification set;
- exact_mechanistic_fingerprint only emitted for the two direct fingerprint
  classes;
- direct drain fingerprints requiring matching owner-uncharge pages and exact
  boundary arithmetic.

This is software-model validation only, not physical evidence.

## Current claim ceiling

B422 establishes an observation and classification design.

It does not establish:

- that ambient host activity actually changes target stock;
- that R2 block2 was caused by consume_stock;
- an ambient hazard rate;
- a reliability percentage;
- a production-ready daemon.

No B422 physical ambient session has been launched.

## Next atomic bounce

Implement the bounded ambient session runner around the frozen classifier.

The first physical session should remain small:

- one canary;
- 10-minute ambient window;
- no synthetic pressure;
- no helper memcgs;
- owner-filtered/count-only core observers;
- private tracefs instance;
- final bounded boundary chase;
- one frozen receipt.

Only after a complete zero-miss session should duration or sample count expand.
