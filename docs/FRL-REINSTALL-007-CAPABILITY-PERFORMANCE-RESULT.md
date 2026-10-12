# FRL-REINSTALL-007 Capability / Performance Search — 2026-10-12

Status: 50-LOOP HARD-CAP COMPLETE / BOUNDED CONVERGENCE

## Goal

The earlier reinstall lane made runtime reconstruction almost disappear. This stage deliberately shifted the search objective toward **more capability and more performance at the same time**.

The frozen correctness requirement remained unchanged: a candidate is eligible only when its LRU/OPT answers match the reference implementation.

## New capability surface

`adaptive_cache_engine.PreparedTrace` now provides:

- arbitrary hashable page IDs via dense canonicalization;
- reusable prepared next-use state;
- LRU single-capacity queries;
- OPT single-capacity queries;
- multi-capacity LRU/OPT sweeps;
- a complete LRU fault curve;
- LRU-vs-OPT comparison including avoidable faults and fault rates;
- inverse queries: minimum capacity required to satisfy a target fault rate;
- optional native acceleration;
- pure-Python fallback when a C compiler/native artifact is unavailable;
- content-addressed native accelerator reconstruction;
- bounded native parallelism for heavier OPT sweeps.

## Search history

Canonical search evidence:

- `evidence/FRL-REINSTALL-007/local-20261012-v3.json`
- 50-loop hard cap
- 64 pre-search reference-parity cases
- four trace families: stable hot set, sequential scan, shifting hot set, bursty
- search axes: reference/prepared, Python/native, scan/heap victim selection, heap-scan crossover, 1/2/4 workers, auto backend, query shape

Earlier v1/v2 evidence is retained as a failure biopsy: the first convergence rule could stop at a phase boundary before the 4-worker region had been explored. The canonical v3 run therefore required all coarse regions before convergence was allowed.

## Baseline

Median reference-scalar task times in the canonical run:

| Task | Reference median |
|---|---:|
| single OPT query | 4.309835 ms |
| mixed LRU+OPT comparison | 37.845663 ms |
| full LRU curve | 74.536563 ms |
| full OPT curve | 345.128008 ms |

## Pareto progression

Selected updates from the bounded search:

1. scalar reference;
2. reusable `PreparedTrace` + Python algorithms;
3. native scan backend;
4. hybrid heap/scan backend;
5. 2-worker native sweeps;
6. 4-worker native sweeps;
7. auto backend capability;
8. threshold refinement.

The raw fastest performance score appeared at loop 28 (`hybrid_h28_w4`). Its medians were:

| Task | Loop 28 |
|---|---:|
| single OPT | 0.089161 ms |
| mixed compare | 0.829146 ms |
| full LRU curve lookup after preparation | 0.000362 ms |
| full OPT curve | 5.010756 ms |

The formal capability-aware Pareto tracker later accepted loop 43 (`refine_h20_w4`) because the auto-backend capability had already been added. The distinction matters: the tracker optimizes capability and performance together, while the raw timing minimum is a separate observation.

## Why the search stopped

The hard cap of 50 loops was reached. The last >=1% Pareto update occurred at loop 43, followed by seven non-updating loops. The predeclared stale criterion was eight, so **formal stale convergence missed by one loop**.

No 51st search candidate was run. This is therefore called **bounded convergence at the hard cap**, not proof of a global optimum.

## Post-search confirmatory selection

No new threshold was introduced after loop 50. Existing candidates 20, 22, 26, and 28 were re-measured across three scales and all four trace families.

Evidence: `evidence/FRL-REINSTALL-007/external-validity-v1.json`.

Normalized geometric-mean regret versus each scale's best point:

| heap_max | aggregate normalized score |
|---|---:|
| 20 | 1.03497 |
| 22 | 1.03359 |
| 26 | 1.02409 |
| **28** | **1.00269** |

`heap_max=28` won small and standard, placed second on large, and was the most robust aggregate choice. It is therefore the final automatic default.

## End-to-end validation

Evidence: `evidence/FRL-REINSTALL-007/final-validation-v2.json`.

For the original shifting-hotset workload, preserving identical LRU faults, OPT faults, and trace hash:

- old median: **11.3916 ms**
- adaptive median: **9.1994 ms**
- speedup: **1.238x**
- median latency reduction: **19.24%**
- parity gate: 10/10 seeds

The engine is more capable and still faster on the original task. Repeated local validations in this session varied around roughly 1.24-1.26x speedup, so the stable claim is approximately 20% end-to-end reduction rather than a single exact ratio.

## Concrete new answers

On the frozen 12,000-reference shifting-hotset example:

- capacity 41: LRU = 1,961 faults; OPT = 754 faults; 1,207 avoidable faults;
- fault-rate <=10%: minimum capacity LRU = 46, OPT = 36;
- fault-rate <=5%: minimum capacity LRU = 86, OPT = 50;
- complete LRU curve contains 248 capacity points.

These are query capabilities that did not exist in the original scalar simulator surface.

## Native artifact is still disposable

The optional native accelerator is content-addressed and reconstructible from canonical source embedded in the Python module.

Final validation physically deleted the 15,672-byte `.so` cache artifact:

- rebuild from canonical source: **177.0 ms**;
- subsequent cached reload: **0.197 ms**;
- reconstructed digest/path: unchanged;
- semantic parity after rebuild: PASS.

Therefore native acceleration does not become irreplaceable installed state.

## Frozen conclusion

The new stable shape is not "one fastest algorithm". It is a query-aware engine:

```text
trace
  -> PreparedTrace
      -> dense canonical IDs
      -> next-use state
      -> LRU full curve (native when available)
      -> OPT hybrid heap/scan
      -> bounded native parallel sweep when query shape justifies it
      -> Python fallback otherwise
      -> compare / curve / inverse-capacity queries
```

The reinstall principle survived capability growth:

> **Keep meaning, source, and trust evidence. Treat compiled acceleration and runtime state as reconstructible caches.**
