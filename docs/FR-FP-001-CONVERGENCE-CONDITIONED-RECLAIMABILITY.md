# FR-FP-001 — Convergence-conditioned trajectory reclaimability

> Status: SOURCE INTAKE / EXPERIMENT DESIGN
> Execution: NOT YET AUTHORIZED BY THIS DOCUMENT
> Claim class: application-memory research, not generic Linux-memory evidence

## Research question

Can an application expose **convergence** as semantic memory intent so that
intermediate trajectory state becomes reclaimable only when an endpoint is
demonstrably sufficient?

This question is triggered by Huang et al. (2026), *Towards Looped Models Done
Right — Part II: Rethinking at Fixed Points*.

Primary public sources:

- https://www.alphaxiv.org/abs/2610.looped-models-fixed-points
- https://github.com/ifm-ai/xllm-loop
- official paper PDF:
  https://github.com/ifm-ai/xllm-loop/blob/main/papers/part2.pdf

The paper is an application/model result. It does not establish a Linux memory
policy.

## Why this fits the Finite RAM North Star

Finite RAM Lab distinguishes:

~~~text
application-local meaning / lifecycle / rebuild cost
from
OS-global residency / pressure / reclaim state
~~~

A recurrent application may know something the kernel cannot infer from page
access alone:

~~~text
these intermediate states were necessary while the computation was still
moving, but the terminal state is now a sufficient replacement under a declared
error bound
~~~

That is a candidate **semantic reclaimability signal**.

The key point is conditionality:

~~~text
converged enough + endpoint sufficient
    -> intermediate trajectory MAY become reclaimable

not converged / endpoint gap too large
    -> intermediate trajectory remains semantically live
~~~

## Atomic decomposition of the upstream result

### A1 — recurrence creates state-history cost

Repeated model loops can create memory and compute cost in training, decoding,
prefill, and RL.

Finite RAM abstraction:

~~~text
iterative compute
  -> sequence of intermediate states
  -> residency pressure proportional to retained history
~~~

### A2 — fixed-point residual is application-local information

For recurrent state:

~~~text
x_(t+1) = F(x_t)
~~~

define:

~~~text
r_t = ||F(x_t) - x_t||
~~~

The application can measure or estimate r_t. The OS generally cannot infer this
semantic distance from physical residency alone.

### A3 — endpoint reuse is not universally safe

The upstream work reports that terminal KV sharing works when training shapes
settled states, while fixed-depth training can break under the same sharing
intervention because states continue to drift.

Finite RAM consequence:

> "old" memory is not equivalent to "reclaimable" memory.

An intermediate state can be old in wall-clock time and still be necessary
because the computation has not converged.

### A4 — convergence depth is heterogeneous

The upstream analysis reports heterogeneous settling across tokens and says
95% of tokens are stable by loop 8 in the studied configuration.

Finite RAM consequence:

~~~text
one global reclaim epoch
!=
per-object semantic liveness
~~~

A future application-side contract may need object- or group-specific
convergence state.

### A5 — terminal KV sharing reduces retained banks

For the reported R=5 setup, terminal sharing keeps 4 KV banks instead of 12.
At 1.6B, the learned-prior model with the smaller shared cache reaches a
downstream average comparable to fixed-depth training with the full cache in
the reported evaluation.

Finite RAM consequence:

This is direct evidence that **representation / lifecycle choice can alter
application memory demand**, but only for the tested model family and training
conditions.

### A6 — endpoint substitution can accelerate other phases

The source reports:

- distilled prefill up to 1.79x faster for an 8K prompt at 1.6B, retaining 93%
  of the teacher downstream score;
- fixed-point reuse makes RL scoring/backward about 2x faster in the reported
  1.6B GSM8K / MBPP+ setup;
- truncated BPTT can match full backprop after a small window threshold in the
  reported learned-depth configuration.

These are upstream application results, not yet Finite RAM Lab measurements.

## New object: semantic reclaimability

For memory object or state bank m_i define:

~~~text
R_i(t) in {LIVE, CANDIDATE, RECLAIMABLE, UNKNOWN}
~~~

A convergence-aware application may propose:

~~~text
CANDIDATE
when
    residual <= epsilon
~~~

but promotion to RECLAIMABLE requires an endpoint-sufficiency check:

~~~text
endpoint_gap <= delta
AND
recovery / recomputation cost <= declared budget
AND
no unresolved consumer still references the intermediate state
~~~

If any prerequisite is missing:

~~~text
R_i = UNKNOWN
~~~

and UNKNOWN is not reclaim permission.

## Endpoint-sufficiency gap

Define a task-local output or loss function Q.

~~~text
g_t =
    | Q(full trajectory through t)
      - Q(endpoint-only representation at t) |
~~~

The exact metric depends on the application:

- task loss / accuracy delta;
- logit or prediction divergence;
- solver residual;
- reconstruction error;
- downstream state mismatch.

The memory decision is allowed to depend on g_t only after the metric and
tolerance are frozen.

## Candidate memory lifecycle

~~~text
EARLY / DRIFTING
  full trajectory or conservative representation
        |
        v
NEAR-CONVERGED
  compress / deduplicate / cold-tier older state if replay cost allows
        |
        v
ENDPOINT-VALIDATED
  terminal representation retained
  intermediate trajectory eligible for discard
        |
        v
PRESSURE / REUSE
  endpoint remains hot; discarded history is absent or reconstructible
~~~

This creates a continuum for the earlier Finite RAM Lab idea of RAM + SSD
cooperation:

~~~text
hot RAM:
    active endpoint + states still required for correctness

cold RAM / SSD:
    expensive-to-rebuild history that may still be needed

discard:
    endpoint-sufficient intermediate state with accepted reconstruction risk
~~~

Convergence alone does not choose the tier.

## Hypotheses

### FR-FP-H1 — convergence residual has value of information

Application-provided convergence state improves reclaim decisions relative to
age / recency alone.

Prediction: at matched memory budget, a convergence-aware policy reduces
correctness failures or unnecessary retention.

### FR-FP-H2 — endpoint sufficiency has a pressure knee

As the residual falls, endpoint substitution error eventually crosses a useful
threshold.

Prediction: there exists an empirical region where memory drops materially
while task loss remains inside a frozen tolerance.

A monotone relationship is not assumed.

### FR-FP-H3 — premature reclamation creates a distinct failure mode

Discarding trajectory state before convergence can produce failures that are
not predicted by physical memory pressure alone.

Prediction: early terminal-only arms lose correctness even when they use less
RAM.

### FR-FP-H4 — heterogeneous convergence rewards fine-grained reclaimability

Per-token / per-object convergence state outperforms one global "iteration is
done" flag when convergence depths are heterogeneous.

### FR-FP-H5 — training / application design can move the memory frontier

If a model is trained or engineered to form endpoint-sufficient states, memory
demand can move before the OS policy changes at all.

This directly tests the Finite RAM Lab distinction:

~~~text
memory-management improvement
vs
application-demand reduction
~~~

They must be measured separately.

## Experiment matrix

### Phase 0 — source reproduction / extraction

No local physical claim.

Record from the upstream release:

- architecture / parameter scale;
- recurrence depth;
- KV-bank count;
- cache bytes if exposed;
- convergence threshold;
- downstream metric;
- hardware and software environment.

### Phase 1 — small controlled looped workload

Use the smallest reproducible upstream or independently defined looped model
that can run within the declared environment.

Arms:

| Arm | State retention | Gate |
|---|---|---|
| A | full trajectory | baseline |
| B | terminal only from first loop | premature negative control |
| C | terminal only after residual threshold | convergence-conditioned |
| D | terminal only after residual + endpoint-gap threshold | validated endpoint |
| E | cold-tier history then discard after validation | RAM/SSD hybrid |

### Phase 2 — pressure sweep

For each arm, sweep memory pressure and record:

- peak RSS / cgroup memory peak;
- model or task correctness;
- endpoint gap;
- convergence depth;
- faults / refaults;
- swap / I/O bytes if used;
- time to first result;
- steady-state latency;
- bytes retained per logical state;
- reconstruction cost;
- failure-state biopsy.

### Phase 3 — policy comparison

Compare:

~~~text
age-only reclaim
pressure-only reclaim
convergence-only reclaim
convergence + endpoint-gap
convergence + endpoint-gap + rebuild-cost
~~~

The winning policy is not assumed in advance.

## Required negative controls

1. **non-convergent / drifting recurrence**
   - proves the harness does not label every old state reclaimable.

2. **false small residual**
   - construct a trajectory with locally small updates but a materially wrong
     endpoint; residual alone must not pass.

3. **multi-basin / oscillatory case**
   - catches systems that look locally settled and then depart.

4. **endpoint-gap disagreement**
   - residual passes, correctness gap fails -> keep history.

5. **pressure-free run**
   - distinguishes intrinsic application speedups from pressure-relief effects.

## Evidence boundary

The upstream source reports models from 100M to 1.6B parameters and uses a
specific looped-model training setup; the public release documents H200-based
paper experiments. The alphaXiv summary notes one training seed per
configuration and says larger scales / other configurations / real-world
feasibility remain untested.

Therefore Finite RAM Lab must not write:

~~~text
fixed points solve KV memory
Linux should reclaim intermediate KV
terminal cache is always safe
~~~

The allowed initial claim is narrower:

> fixed-point / endpoint-sufficiency measurements are a credible source of
> application-local memory intent worth testing against recency- and
> pressure-only policies.

## Cross-repository connection

Dissociated Control Systems now has a deterministic fixed-point measurement
probe for:

- contraction ratio;
- convergence depth;
- fixed-point residual;
- orthogonal injection.

Those primitives may inform a toy harness, but DCS evidence does not establish
Finite RAM Lab systems performance.

Recovery Dynamics separately uses the same mathematical language to distinguish
first success from stable recovery.

Shared mathematics is not shared mechanism.

## Stop conditions

Stop or downgrade FR-FP-001 if:

- the smallest runnable workload cannot expose memory state reproducibly;
- endpoint-gap metrics are unstable;
- convergence-aware policy gives no held-out benefit over simpler recency;
- memory savings disappear after accounting for recomputation / I/O;
- correctness tails worsen outside the frozen tolerance.

## Claim ceiling

Until a controlled experiment runs:

~~~text
CONVERGENCE_CONDITIONED_RECLAIMABILITY_DEFINED
UPSTREAM_FIXED_POINT_MEMORY_RESULT_INTAKE_COMPLETE
NO_LOCAL_MEMORY_GAIN_CLAIM
~~~
