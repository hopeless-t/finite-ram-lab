# Fast Reinstall Loop — Convergence v2

Date: 2026-10-12
Status: BOUNDED CONVERGENCE AT LOOP CAP 50

v1 converged the pure-Python projection/reinstall lane. v2 widened the objective to ask a harder question:

> Can the system become more capable and faster without turning generated runtime state back into a permanent dependency?

## What changed after v1

The search produced a reusable adaptive cache-analysis engine with:

- prepared traces;
- complete LRU curves;
- accelerated OPT;
- multi-capacity sweeps;
- LRU-vs-OPT regret analysis;
- target-fault-rate -> minimum-capacity inversion;
- optional content-addressed native acceleration;
- pure-Python fallback;
- bounded parallel native sweeps.

## Performance shape

Reference scalar -> selected engine path:

- single OPT: 4.31 ms -> ~0.09 ms in the raw fastest search point;
- mixed compare: 37.85 ms -> ~0.83 ms;
- full OPT curve: 345.13 ms -> ~5.01 ms;
- end-to-end original workload: 11.39 ms -> 9.20 ms while preserving outputs.

## Reinstall invariant still holds

The native accelerator is only 15,672 bytes and was physically deleted during validation. It rebuilt from canonical source in ~177 ms and then reloaded from cache in ~0.20 ms.

Therefore the new performance layer is not an installation dependency. It is another projection cache.

## Stop condition

The bounded search reached loop 50. The last >=1% Pareto update was loop 43; loops 44-50 did not update the frontier. The predeclared eight-stale rule would have required loop 51, which was forbidden by the hard cap.

The lane therefore stops as **bounded convergence**, with post-search confirmation restricted to already-tested candidates only.

External validity selected `heap_max=28` as the robust default across small, standard, and large traces.

## Current architecture

```text
canonical Python source
        |
        +--> pure-Python backend --------------------+
        |                                            |
        `--> content-addressed native cache           |
                 |                                    |
                 +-- missing? compile from source ----+
                                                      |
trace -> PreparedTrace -> query-aware controller -----+
                            |
                            +-- LRU curve
                            +-- OPT hybrid heap/scan
                            +-- serial / bounded parallel
                            +-- compare
                            +-- minimum-capacity inverse query
```

Nothing generated is sacred. Capability is retained in canonical source and evidence; acceleration is allowed to disappear and regrow.
