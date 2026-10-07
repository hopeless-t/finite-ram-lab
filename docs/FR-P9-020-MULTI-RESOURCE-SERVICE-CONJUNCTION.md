# FR-P9-020 — Typed multi-resource ServiceCurve conjunction

## Problem

P9-018/P9-019 establish one-resource deadline admission and stale-epoch invalidation. Real materialization is usually a pipeline: storage/remote transfer, CPU reconstruction, verification, device upload, and sometimes queue service are distinct resources.

The dangerous shortcut is to collapse these resources into a single scalar budget. CPU surplus cannot pay a transfer-byte deficit, and spare bandwidth cannot replace missing verification compute.

## Candidate rule

For every required typed resource `r`:

```text
current_epoch(r)
and
S_r(D_r) >= W_r
```

Admission is the conjunction over all required resources. Resource units remain explicit and incompatible units are never added together.

```text
CPU service        : cpu_quanta
storage transfer   : byte_quanta
future GPU queue   : device-specific service unit
```

This is still resource feasibility, not execution authority.

## Analytic qualification

1. Exhaustively enumerate two independent 3-bin curves, with each bin contributing 0..2 service units, requirements 0..6 for each resource, and compare typed conjunction against a direct two-condition oracle.
2. Freeze a scalarization adversary where CPU surplus numerically masks a transfer deficit if incompatible units are illegally summed.
3. Make only the transfer resource stale and require the whole materialization plan to return `REPLAN_REQUIRED`.
4. Intentionally mismatch transfer service units and require fail-closed behavior.
5. Run deterministic Monte Carlo and count false admits from an illegal scalar sum versus the typed conjunction.

## Expected architectural consequence

The Semantic Residency Compiler should compile a **vector of service obligations**, not one generic budget:

```text
ProjectionAtom
   -> CPU demand curve
   -> transfer demand curve
   -> verification demand curve
   -> residency-byte demand
   -> all current and feasible?
      yes: resource-feasible candidate
      no : insufficient / replan
```

Only after this gate may a separate authority plane consider invocation.

## Next physical gate

Build a bounded two-resource proxy where capability materialization needs both:
- measured transfer service from a cold representation;
- measured CPU reconstruction service.

Vary them independently and show that satisfying only one resource curve cannot satisfy the end-to-end deadline.

Claim ceiling:
`ANALYTIC_TWO_RESOURCE_DISCRETE_SERVICE_CURVE_CONJUNCTION_ONLY_NO_PHYSICAL_MULTI_DEVICE_OR_APPLICATION_CLAIM`
