# FR-P9-002 — Resource-certificate replan after materialization

Status: **SYNTHETIC FALSIFIER / PART 9**

Parent: **FR-P9-001**

## Why this experiment exists

FR-P9-001 separated canonical semantic truth from the minimum runtime projection
needed to preserve four contract planes:

- decision
- verification
- recovery
- capability

That result is still incomplete.

A semantically sufficient projection can be physically placed using a resource
snapshot that becomes stale while the runtime is being materialized.

The Part 9 question therefore becomes:

> When does a previously valid placement cease to be admissible, and how little
> must be re-evaluated before work continues?

## Core split

```text
Canonical truth
    !=
Semantic projection
    !=
Physical placement
    !=
Resource observation
    !=
Execution authority
```

FR-P9-002 deliberately changes only the physical/resource layers. The semantic
atom set comes directly from the FR-P9-001 `GENERATE_CHUNK` projection.

## The stale-startup-plan adversary

Startup planning sees:

```text
RAM free = 8192 B
SSD      = available
```

The 7968-byte semantic projection fits entirely in RAM, so the frozen planner
selects an all-RAM placement.

After runtime/page-cache/workspace materialization, a new observation sees:

```text
RAM free = 6144 B
SSD      = available
```

The semantic requirement did not change. The physical facts did.

Executing the startup placement would now exceed observed free RAM. The stale
plan must therefore be rejected before execution admission.

The replanner preserves the exact semantic atom set but moves the frozen
low-immediacy pair:

```text
checkpoint_manifest -> SSD
collision_verifier  -> SSD
```

for 1920 bytes of SSD residency while keeping all current `GENERATE`-phase atoms
out of the transfer path.

This is a synthetic fixture, not a recommendation for a real cache or SSD.

## Meta-meta correction: epoch identity is too coarse

A naive rule would be:

```text
plan.epoch != observed.epoch
    -> replan everything
```

That is safe but wasteful. It turns unrelated observation churn into planner
work.

Part 9 already has evidence that decision-irrelevant work should be pruned when a
qualified proof says the decision cannot change. FR-P9-002 applies the same rule
to resource observations.

The plan is therefore bound to a **planner-relevant resource certificate** over:

- `ram_free_bytes`
- `ssd_available`
- `ssd_read_bytes_per_second`

The global observation epoch and observer note remain provenance only.

Thus:

```text
new epoch + same resource certificate
    -> existing resource plan remains valid

changed resource certificate
    -> REPLAN_REQUIRED
```

This is narrower than global epoch equality while remaining fail-closed for every
resource fact used by the frozen planner.

## Topology-loss adversary

A second post-materialization snapshot keeps RAM at 6144 bytes but removes the
SSD tier.

The semantic projection still cannot be truncated.

Therefore:

```text
insufficient RAM + no backing tier
    -> no feasible placement
    -> fail closed
```

The planner does **not** silently drop verification/recovery atoms just to make
the budget fit.

## Typed objective

The frozen planner orders candidates by:

1. current-phase transfer bytes
2. migration bytes from the previous placement
3. SSD-resident bytes
4. deterministic tie break

The result still exposes the cost dimensions separately. No universal scalar
utility is claimed.

## Authority boundary

A fresh resource plan is not execution authority.

```text
resource plan valid
    != execution authorized

replan completed
    != retry permitted
```

`authority_effect = NONE`

`retry_authority = false`

This preserves the MVCA/LDC boundary: resource optimization cannot widen an
authority envelope.

## Relation to Strata-style failures

The motivating upstream pattern is a class of systems failures where a plan is
made before RAM copies/cache/runtime state are fully materialized, then the
post-materialization resource state differs from the state used for the original
decision.

FR-P9-002 does **not** claim to reproduce Strata or any upstream runtime. It
extracts only the falsifiable systems invariant:

```text
Plan(t0)
  -> materialize
  -> observe relevant resources(t1)
  -> compare resource certificate
  -> replan if changed
```

## Result contract

The experiment passes only if all of these hold:

- startup plan is all-RAM;
- irrelevant epoch-only observation does not force a placement change;
- materialization changes the resource certificate;
- the stale startup plan is rejected;
- the stale startup plan is physically infeasible under the new snapshot;
- replanning preserves the exact semantic projection;
- replanning restores physical feasibility;
- no current GENERATE-phase transfer is introduced in the frozen fixture;
- topology loss returns no feasible plan;
- authority and retry boundaries remain unchanged.

## Claim ceiling

`SYNTHETIC_RESOURCE_CERTIFICATE_AND_REPLAN_FIXTURE_ONLY_NO_PHYSICAL_PLACEMENT_OR_PERFORMANCE_CLAIM`

No physical RAM reduction, SSD latency, host threshold, game-frame improvement,
or production planner performance is claimed.

## Next falsifier

FR-P9-003 should introduce **phase transitions and measured transfer/recompute
costs**.

The next question is no longer just whether a capability can be cold. It is:

> At what reuse interval does repeated fault-in become more expensive than
> keeping a capability WARM across phases?

That opens the next Part 9 surface:

```text
semantic temperature
    x
physical tier
    x
phase lifetime
    x
fault/recompute cost
```
