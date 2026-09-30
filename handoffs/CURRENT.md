# CURRENT

> Latest bounce: B414
> Stage: SMALL-RESIDUAL REFILL SPECTRUM PREFLIGHT
> Stop: READY TO LAUNCH TX-SMALL-RESIDUAL-REFILL-SPECTRUM-v1 AFTER CI

## Chapter II frontier

The research has moved beyond the B405 perturbation matrix into the origin of natural pre-VERIFY stock.

Established named mechanisms/states:

- VERIFIED_DIRECT_Q64_RESET: measured one-page direct Q64 establishes R0=63.
- PREVERIFY_S64 / MAX_STOCK_BOUNDARY: natural pre-VERIFY S0=64 established for frozen R8 specimen by sandwich proof.
- TARGET_STOCK_EVICTION: verified residual stock can be asynchronously drained, moving the next boundary earlier.
- STARTUP_STOCK_SEED: transient service/worker startup can charge/refill the future stock CPU before historical _start() returns, leaving inherited stock that delays the measured boundary.

No complete B405 path has produced TARGET_FAIL.

## R9 normalize boundary chase

Run 36686845958:

- 32/32 valid
- 32/32 WITHIN_BOUND
- critical Q64 coverage PASS
- bound violations 0
- max T=48
- T histogram: 1x26, 2x2, 27x1, 46x2, 48x1

The R8 64-touch specimen plus the source upper bound proves S0=64 under the frozen assumptions.

## R10 post-start localization

Run 36688225173:

- 32/32 valid
- target-PID Q64 between historical _start() return and first measured touch: 0/32
- 0 ms vs 5 ms settle showed no persuasive difference in this panel

This localized high-S0 construction to the earlier transient service / worker startup interval.

## R11 STARTUP_STOCK_SEED establishment

Run 36689570716:

- 32/32 within bound
- four complete startup-seed specimens
- final MainPID future-stock-CPU Q64/refill63 before _start() return
- promoted T/S0: 45/44, 45/44, 48/47, 44/43
- seeding begins PRE_EXEC and continues POST_EXEC
- stack callpaths include folio prealloc, anon folio allocation, memcg slab/anon-vma setup, and wp_page_copy

Mechanism status:

STARTUP_STOCK_SEED = ESTABLISHED_IN_FOUR_PHYSICAL_SPECIMENS.

## R12 cpuset causal falsifier

Run 36691073336.

Intervention:

- CONTROL uses historical _start().
- CPUSET_PREP_ONLY creates service with CPUAffinity=prep and AllowedCPUs=prep.
- after READY, AllowedCPUs expands to prep+stock and only then MainPID migrates to stock CPU.

Frozen result:

CONTROL:
- n=32
- valid=31
- classic STARTUP_STOCK_SEED=5
- large high-T cluster: T=46,47,48,49,49
- one clean T=2
- one observer-invalid T=1

CPUSET_PREP_ONLY:
- n=32
- valid=31
- classic startup seed=0
- release-gap seed=0
- CPUSET_SUPPRESSED=30
- one clean T=2
- one observer-invalid T=1

Strict preregistered causal_support=false because the complete-panel rule required 64/64 valid and all valid intervention identities T=1.

Nevertheless the large mechanism shows strong causal intervention support:

- classic seed: CONTROL 5/32 vs CPUSET 0/32
- T>=3 high-residual phenotype: CONTROL 5/32 vs CPUSET 0/32
- no CPUSET startup leak
- no CPUSET release-gap classic seed

Do not rewrite the strict result as PASS.

Frozen evidence:
- analysis/inputs/STARTUP-STOCK-SEED-CPUSET-R1-PHYSICAL-RESULT-v1.json
- raw files=148
- bytes=1,369,413
- content-set SHA=232af44c0867d2a064abfb744b3ef8d0afd3d19ff2ed2dde7aeb35ecaf9bfc7d
- aggregate artifact ID=11085837349
- artifact digest=sha256:ffcf3fa37829957d77ced1cad9d527bce513eecd535d343c61150892cf4fd5d5

## New source-grounded missing mechanism family

The two clean T=2 / inferred S0=1 specimens have:

- no classic Q64/refill63 startup seed on stock CPU
- no classic release-gap seed
- zero relevant probe misses

Linux source shows refill_stock() is not only used for Q64 excess.

At least these paths can add stock without a contemporaneous direct Q64:

- try_charge_memcg -> refill_stock(batch - nr_pages)
- obj_cgroup_uncharge_pages -> refill_stock(memcg, nr_pages)
- mem_cgroup_sk_uncharge -> refill_stock(memcg, nr_pages)

mem_cgroup_css_offline drains all stock, so stale stock from a destroyed transient memcg is strongly disfavored.

Candidate family:

SMALL_RESIDUAL_REFILL / SMALL_RESIDUAL_SEED

Possible subtypes, not yet promoted:

- KMEM_UNCHARGE_REFILL
- SOCKET_UNCHARGE_REFILL

## R13-A next experiment

TX-SMALL-RESIDUAL-REFILL-SPECTRUM-v1

Purpose:

Capture owner-memcg refill sizes 1..8 before the first measured Q64 while classic STARTUP_STOCK_SEED is suppressed by the CPUSET_PREP_ONLY intervention.

Design:

- 4 blocks x 32 = 128 fresh identities
- CPUSET_PREP_ONLY only
- Q64 probe: nr_pages=64
- refill spectrum probe: nr_pages<=8 OR nr_pages=63
- no stacktrace
- keep both probes active through first measured Q64
- obtain owner_memcg from the measured Q64/refill63 boundary
- retrospectively match earlier refill events by owner_memcg + stock CPU

Phase buckets:

- STARTUP
- RELEASE_GAP
- TAIL_GAP_AFTER_RELEASE
- MEASURED_PREBOUNDARY_TOUCHES

Key classes:

- T1_NO_SMALL_REFILL
- SMALL_REFILL_EXPLAINS_DELAY
- SMALL_REFILL_PARTIAL
- HIGH_T_WITHOUT_SMALL_REFILL
- CLASSIC_REFILL63_LEAK
- INVALID_OBSERVER

Discovery and panel coverage are reported separately.

If a complete small-refill specimen is captured, R13-B should conditionally stacktrace only small refill events to distinguish obj_cgroup_uncharge_pages, mem_cgroup_sk_uncharge, or another caller.

Files:

- specs/TX-SMALL-RESIDUAL-REFILL-SPECTRUM-v1.json
- src/finite_ram_lab/small_residual_refill_spectrum.py
- tests/test_small_residual_refill_spectrum.py
- .github/workflows/small-residual-refill-spectrum.yml

## Authority

R13-A physical continuation is authorized.

Standard public-repository GitHub-hosted runner only.
No paid larger runner.
No local-PC execution.
No reliability certification.
