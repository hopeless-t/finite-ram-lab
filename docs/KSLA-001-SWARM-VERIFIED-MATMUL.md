# KSLA-001 — Kitten Swarm Linear Algebra

Status: **SYNTHETIC VERIFIED-SWARM MATRIX QUALIFICATION**

## Research question

Can a large population of extremely small matrix workers, each knowing only a
tiny local block, collectively recover an exact matrix product when correctness
is delegated to cheap mathematical verification and selective recomputation?

The deliberately silly version is:

> Can a large number of stupid kittens solve a matrix problem if the kittens are
> given tiny jobs and the mathematics, rather than worker intelligence, is
> responsible for catching mistakes?

## Novelty boundary

The ingredients are not claimed as new algorithms.

Relevant prior work includes:

- Freivalds' randomized matrix-product verification;
- randomized / resource-aware matrix multiplication;
- randomized Kaczmarz methods that consume small random pieces of a system;
- coded distributed matrix multiplication for straggler tolerance.

KSLA is a **systems composition hypothesis**:

```text
tiny worker contract
  × decomposition
  × cheap mathematical verifier
  × local fault localization
  × selective recomputation
  × finite-residency accounting
  × later precision escalation
```

The experiment tests whether that composition is coherent before attempting a
real distributed runtime.

## Exact micro fixture

The executable test uses exact arithmetic modulo the prime:

`p = 65537`.

Matrices:

- A: 24 × 24
- B: 24 × 24
- block grid: 4 × 4
- block width: 6

The product is written as:

[
C_{ij} = sum_k A_{ik}B_{kj}.
]

Each weak worker receives exactly one triple:

`(A_ik, B_kj) -> partial C_ij`.

There are:

`4^3 = 64 worker tasks`.

No worker needs the whole matrix.

## Synthetic weak-worker faults

Four deterministic tasks are corrupted after computing their local product.

This does not model a measured hardware or low-precision failure rate.

It creates a controlled adversary for the verifier.

The raw swarm output must therefore be wrong.

## Verification

The experiment uses a Freivalds-style identity check over the finite field:

[
A(Br) = Cr.
]

For a bad product and a random vector sampled uniformly from the field, one
round has false-accept probability at most approximately:

[
1/p.
]

The frozen fixture uses two rounds.

Per bad task the analytical upper bound is therefore:

[
1 / 65537^2.
]

The deterministic CI vectors are reproducibility fixtures. A production
probabilistic verifier would require fresh independent randomness.

## Fault localization

The global verifier first rejects the aggregated candidate.

Then each tiny task result is verified independently against its two input
blocks.

Only failed tasks are recomputed by the exact fallback.

Frozen result:

| endpoint | result |
|---|---|
| raw swarm equals exact | no |
| initial global verification | reject |
| injected bad tasks | 4 |
| localized bad tasks | 4 |
| recomputed tasks | 4 |
| repaired product equals exact | yes |
| final global verification | pass |

Therefore the system does not redo the complete matrix product merely because a
minority of workers are wrong.

## Large synthetic scaling model

A second model asks what the worker contract looks like at:

- matrix dimension: 4096
- block grid: 16
- task count: 4096
- modeled bad-task rate: 1%
- verifier rounds: 2

This is an arithmetic / residency proxy only.

### One kitten's compute obligation

One block triple is a 256 × 256 multiply.

Relative to one full 4096 × 4096 multiply:

[
rac{256^3}{4096^3}
=
rac{1}{4096}.
]

So one worker owns only:

**0.0244% of the full multiplication work.**

### One kitten's working-set obligation

A task needs approximately:

- one A tile;
- one B tile;
- one output tile.

Relative to the analogous three full matrices:

[
rac{1}{16^2}
=
rac{1}{256}.
]

So the local working-set proxy is:

**0.390625% of the strong-worker working set.**

This is the core Finite RAM result.

The entire information obligation still exists, but no weak worker must hold it
all at once.

## Aggregate work

The swarm does not magically delete arithmetic.

The base block products still sum to one ordinary matrix multiplication.

The scale model additionally pays:

- local verification: 2.34375% of one full multiply;
- global verification: 0.146484% ;
- selective recomputation at the frozen 1% fault model: 1.000977%.

Total:

[
1.034912109375
]

full-multiply work units.

So the synthetic verified swarm spends about:

**3.49% additional arithmetic**

to obtain tiny worker contracts and selective fault recovery.

## The communication tax

The ugly part is important.

If every block-triple task returns its tile independently, the returned scalar
volume is:

[
16 	imes
]

the final output matrix size.

This can dominate the design.

Therefore a real KSLA runtime needs hierarchical reduction:

```text
tiny workers
    ↓
local C_ij reducers
    ↓
verified output tiles
    ↓
global result
```

This is a central result, not an implementation footnote.

**Making workers stupid moves complexity into coordination.**

## Strong worker vs kitten swarm

The first KSLA hypothesis is therefore not:

`swarm uses fewer total FLOPs`.

It is:

```text
strong worker:
  large local residency
  large single-worker compute obligation
  simple communication
  failure may require large redo

kitten swarm:
  tiny local residency
  tiny local compute obligation
  slightly greater aggregate work
  cheap independent verification
  selective repair
  much harder communication / reduction
```

The question is whether that resource exchange is favorable under finite RAM,
heterogeneous workers, cheap compute, or unreliable workers.

## Why this connects to the Kitten Circuit

The numerical architecture matches the existing model-review idea:

```text
many cheap workers
      ↓
candidate pieces
      ↓
cheap deterministic / probabilistic checks
      ↓
only suspicious work escalates
      ↓
expensive expert fallback
```

The expensive solver is no longer required to perform every operation.

It becomes an exception handler.

## Why this connects to earlyoom replacement work

The same escalation structure now appears in two different domains.

Memory control:

```text
fold demand
 -> downshift representation
 -> migrate
 -> drop
 -> background exit
 -> kill
```

Numerical control:

```text
cheap block worker
 -> mathematical verify
 -> local retry
 -> stronger precision
 -> exact fallback
```

Both systems reserve the expensive destructive action for the narrow region
where cheaper interventions fail.

## Next lanes

### KSLA-002 — Coded kittens

Use Polynomial / MatDot-style coded distributed multiplication so the reducer
does not need every worker to return.

Target:

`straggler survival without duplicating every task`.

### KSLA-003 — Floating-point kittens

Replace finite-field exact products with:

- FP8 / FP16 workers;
- residual-based verification;
- compensated arithmetic;
- FP32 / FP64 repair;
- Ozaki fallback.

Target:

`precision escalation only where numerical evidence demands it`.

### KSLA-004 — Kaczmarz swarm

Give each worker only one row or small row group of a linear system.

Compare:

- centralized solver;
- randomized Kaczmarz;
- asynchronous weak-worker updates;
- verifier / residual-gated escalation.

This is closer to the literal "many dumb kittens each look at one equation"
idea.

## Claim ceiling

**SYNTHETIC_VERIFIED_SWARM_MATMUL_ONLY**

No real distributed cluster performance is claimed.

No floating-point superiority is claimed.

No underlying randomized linear algebra algorithm is claimed as newly invented.
