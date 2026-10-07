# FR-P9-024 — Semantic prefix validity and release closure

## Why this follows P9-023

FR-P9-023 physically showed that chunk-level release can improve deadline feasibility and logical buffering when chunks are independently processable. That result must not be generalized into `bytes arrived => prefix safe to consume`.

Many runtime representations may require dictionaries, manifests, provenance, integrity evidence, headers/trailers, index state or other semantic atoms before a received byte range is meaningful or verified.

## Candidate contract

Each prefix atom declares:

```text
PrefixAtom(
  atom_id,
  arrival_index,
  requires[],
  verification_roots[]
)
```

The earliest semantic release of atom `a` is:

```text
R(a) = max arrival time over the transitive closure of
       {a} + requires(a) + verification_roots(a)
```

Unknown dependencies and dependency cycles fail closed.

This is an analytic declared-dependency contract. It does not infer dependencies from arbitrary binary formats.

## Frozen adversary

```text
chunk0 arrives at 1
chunk0 requires dictionary arriving at 3
chunk0 requires manifest verification root arriving at 4
```

Naive byte release marks `chunk0` ready at 1. Semantic release must wait until 4.

An independent chunk with no dependencies arrives and releases at 2.

## Qualification

### Exhaustive DAGs

Four atoms with dependencies restricted to lower-index atoms:
- six possible directed edges -> 64 DAGs;
- each atom arrival index 1..4 -> 256 arrival assignments per DAG;
- compare all four release times with an independent topological dynamic-programming oracle.

Expected comparisons: **65,536**.

### Monte Carlo

Generate six-atom acyclic dependency/verification graphs with random arrivals. Compare naive byte release and compiled semantic release against an independent explicit-closure oracle.

The expected result is not that early release always loses. Independent prefixes should remain early-releasable. The safety property is that declared dependencies never release early merely because the payload bytes arrived.

## Architectural consequence

Part9's release contract becomes:

```text
bytes available
   + semantic dependency closure
   + verification roots
   + current resource/service epoch
   -> semantic release candidate
   -> resource-feasible schedule candidate
   -> separate authority gate
```

## Next physical gate

Use two concrete representation shapes:
- independently decompressible/verified chunk members;
- a monolithic compressed/verified representation that cannot satisfy the same prefix contract without later state.

Measure when each shape becomes safely usable and whether the compiler's release contract predicts the difference.

Claim ceiling:
`ANALYTIC_DECLARED_PREFIX_DEPENDENCY_AND_VERIFICATION_CLOSURE_ONLY_NO_GENERAL_FORMAT_DECODABILITY_OR_APPLICATION_CLAIM`
