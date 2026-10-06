# FR-P9-006 — Joint residency × concurrency composition falsifier

Status: **SYNTHETIC JOINT PLANNER / PART 9**

Parent: **FR-P9-005**

## Why this experiment exists

Part 9 has now qualified two different decision surfaces:

- residency across phases;
- concurrency under shared immutable capability state.

A tempting architecture is to optimize them independently:

```text
best worker count
+
best residency policy
=
best joint runtime plan
```

FR-P9-006 is designed to break that assumption.

## Evidence inputs and boundary

The worker profiles use the qualified FR-P9-005 hosted medians as frozen evidence
anchors:

| workers | active PSS | work wall |
|---:|---:|---:|
| 1 | 15,395 KiB | 256,454,324 ns |
| 2 | 24,937 KiB | 128,979,271 ns |
| 4 | 42,864 KiB | 70,568,943 ns |

The residency side is a deliberately synthetic 8 MiB warm/fault fixture shaped
by FR-P9-003:

```text
KEEP_WARM
  +8192 KiB prestart residency
  0 requested transfer
  0 resume penalty

FAULT_IN
  +0 KiB prestart residency
  8 MiB requested transfer
  +2,668,202 ns resume penalty
```

These two evidence surfaces were measured under different hosted proxies and
payload geometry. They are **not physically composable measurements**.

FR-P9-006 uses them only to construct a falsifiable synthetic composition
problem. No physical joint optimum is claimed.

## Frozen memory cap

```text
50,000 KiB
```

The number is a synthetic admission constraint, not a recommendation for any
host.

## Independent selection

If concurrency is selected alone by observed work wall time:

```text
N = 4
```

If residency is selected alone by resume latency then requested transfer:

```text
KEEP_WARM
```

Naive composition gives:

```text
N=4 + KEEP_WARM
prestart PSS
  = 42,864 + 8,192
  = 51,056 KiB
```

which violates the 50,000 KiB cap.

Thus:

```text
locally attractive A
+
locally attractive B
!=
globally admissible A×B
```

## Joint enumeration

The exact six candidates are:

```text
N={1,2,4}
×
residency={KEEP_WARM,FAULT_IN}
```

Every candidate carries the typed vector:

```text
(
  prestart_pss_kib,
  requested_transfer_bytes,
  predicted_completion_ns,
  resident_byte_seconds
)
```

The planner first removes infeasible candidates and only then computes the
non-dominated set.

No weighted score is invented.

## Important surviving alternatives

The frozen fixture deliberately preserves at least two different ways out of the
composition failure:

```text
N=4 + FAULT_IN
```

keeps the high-concurrency shape while paying fault/transfer cost.

```text
N=2 + KEEP_WARM
```

keeps warm residency while reducing concurrency residency.

Which one is preferable requires a real external constraint or price.

## Decision

```text
DO_NOT_COMPOSE_INDEPENDENT_CONCURRENCY_AND_RESIDENCY_OPTIMA
SOLVE_THE_JOINT_FEASIBLE_TYPED_FRONTIER
```

The order is important:

```text
semantic correctness
    ↓
resource feasibility
    ↓
typed Pareto optimization
    ↓
caller-specific selection
    ↓
authority admission
```

Optimization is not allowed to repair infeasibility by silently dropping
semantic requirements.

## Part 9 accumulation

```text
P9-001  semantic projection
P9-002  resource-certified placement/replan
P9-003  phase residency tradeoff
P9-004  parallelism residency tax
P9-005  concurrency frontier
P9-006  joint residency × concurrency feasibility
```

This supports a stronger candidate description of the Part 9 compiler:

> Compile the smallest verified semantic projection together with a jointly
> feasible representation, placement, lifetime, and concurrency plan; keep
> heterogeneous costs typed until the caller supplies a real constraint or
> price.

## Authority boundary

A resource-feasible joint plan is still not execution permission.

`authority_effect = NONE`

## Claim ceiling

`SYNTHETIC_JOINT_COMPOSITION_USING_QUALIFIED_PROXY_SHAPES_ONLY_NO_PHYSICAL_JOINT_OPTIMUM_CLAIM`

## Next falsifier

FR-P9-007 should remove the cross-proxy limitation.

Run one hosted experiment where, under the **same**:

- payload;
- worker counts;
- job workload;
- PSS accounting;
- start barrier;
- runner;

both `KEEP_WARM` and `FAULT_IN` are measured.

Only then can the joint planner acquire a hosted-physical-proxy evidence class.
