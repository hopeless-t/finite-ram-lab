# FR-P9-012 — Horizon/price residency policy regions

## Why this experiment exists

FR-P9-011 physically qualified a typed tradeoff on one hosted Linux hashing proxy:

- `FAULT_IN` repeatedly reduced kernel peak memory by roughly 27–32 MiB;
- `KEEP_WARM` avoided repeated materialization cost;
- the FAULT_IN materialization tax grew with reuse horizon.

Those facts do **not** identify a universal winner. FR-P9-012 therefore asks a narrower question: can the measured frontier be compiled into explicit policy regions **only after an external constraint or price is supplied**?

## Evidence boundary

P9-012 freezes the median P9-011 anchors from artifact:

`sha256:4ac83d72124f3982d8cebb860d04e54628d75dc8356f7cd703baf7fce5113b59`

This PR adds no new physical performance claim. Its evidence class is:

`ANALYTIC_COMPILATION_OVER_HOSTED_FR_P9_011_ANCHORS`

## Decision order

The compiler follows this order:

```text
P9-011 typed physical anchors
        ↓
hard capacity feasibility
        ↓
optional external materialization-latency SLO
        ↓
if one policy remains → select that feasible policy
        ↓
if both remain and no external price → TYPED_FRONTIER_UNRESOLVED
        ↓
if both remain and price exists → compare against exact break-even RAM price
```

An external RAM price has units **nanoseconds per MiB of peak memory**. This is deliberately explicit: the lab may consume a price but may not invent one.

For KEEP_WARM `K` and FAULT_IN `F`, when both remain feasible:

\[
C_p = L_p + \lambda B_p
\]

with the byte-to-MiB conversion explicit in the implementation. The exact break-even is:

\[
\lambda^*(H)=\frac{L_F(H)-L_K(H)}{B_K(H)-B_F(H)}
\]

where `lambda*` is expressed in ns/MiB.

## Compiled break-even boundaries

Using the frozen P9-011 medians:

| reuse horizon | break-even RAM price |
|---:|---:|
| 1 | ~0.909 ms/MiB |
| 2 | ~1.577 ms/MiB |
| 4 | ~4.688 ms/MiB |
| 8 | ~11.313 ms/MiB |

The required RAM price rises sharply with reuse horizon because the peak-memory saving saturates while repeated FAULT_IN materialization cost keeps accumulating.

## Policy geometry

For the qualified P9-011 shape (`FAULT_IN` lower peak, `KEEP_WARM` lower materialization time), each horizon compiles into these regions:

1. capacity below FAULT_IN peak → no feasible policy;
2. capacity between FAULT_IN and KEEP_WARM peaks → only FAULT_IN can fit, subject to latency SLO;
3. capacity admits both but latency SLO is tighter than KEEP_WARM → no feasible policy;
4. capacity admits both and SLO admits KEEP_WARM but not FAULT_IN → KEEP_WARM;
5. both are feasible → external RAM price below/tie/above `lambda*` selects KEEP_WARM / tie / FAULT_IN;
6. both are feasible and no price exists → remain typed and unresolved.

## Verification

The implementation uses two independent decision paths:

- a direct solver that filters hard feasibility then computes exact priced costs;
- a compiled threshold lookup specialized to the measured P9-011 shape.

A boundary-focused Cartesian grid spans capacity thresholds, latency thresholds, missing price, zero price, both sides of break-even, and the exact tie. The experiment fails if any direct/compiled decision differs.

## Invariants

- capacity/SLO feasibility precedes scalar price;
- missing external price must not be silently replaced by an internal preference;
- negative external price fails closed;
- policy selection does not grant execution authority;
- policy selection does not grant retry permission;
- hosted P9-011 physical evidence remains distinct from P9-012 analytic compilation.

Decision candidate:

`COMPILE_RESIDENCY_POLICY_FROM_EXTERNAL_CONSTRAINTS_AND_PRICES;CAPACITY_AND_LATENCY_FEASIBILITY_PRECEDE_PRICE;REUSE_HORIZON_SHIFTS_THE_BREAK_EVEN_RAM_PRICE;NO_EXTERNAL_PRICE_MEANS_NO_SCALAR_WINNER`

Next falsifier: run the same policy-boundary methodology on a different physical workload shape and test whether the horizon ordering survives beyond the hashing proxy.

Claim ceiling:
`ANALYTIC_POLICY_BOUNDARY_COMPILATION_OVER_HOSTED_FR_P9_011_MEDIAN_ANCHORS_ONLY_NO_UNIVERSAL_MEMORY_PRICE_OR_APPLICATION_POLICY_CLAIM`
