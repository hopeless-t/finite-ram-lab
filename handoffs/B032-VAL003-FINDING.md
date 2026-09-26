# Bounce Handoff

> **Bounce ID:** B032  
> **Status:** COMPLETE

## Objective

Read the completed VAL-003 workflow using only the frozen confirmatory analysis, record the finding, update repository status, and stop.

## Evidence

Workflow:

- run: `36241864223`;
- conclusion: SUCCESS;
- 40 independent runner blocks;
- 800 total trials;
- all execution checks passed;
- no OOM;
- content integrity preserved.

Pre-registered >=500 ms catastrophic endpoint:

```text
CORRECT_PAGEOUT  6 / 400 = 1.50%
NO_HINT          7 / 400 = 1.75%
```

Primary runner-block risk difference:

```text
CORRECT - NO_HINT = -0.0025
```

Confirmatory inference:

```text
one-sided Monte Carlo sign-flip p = 0.4996345
MC standard error                 ≈ 0.0005000
cluster bootstrap 95% RD          = [-0.020, +0.015]
```

## Frozen finding

The pre-registered catastrophic-tail benefit of CORRECT_PAGEOUT versus NO_HINT is **not supported**.

The exploratory EXP-002 far-tail signal did not reproduce as the anticipated strong effect in independent data.

The study does not establish equivalence because the realized NO_HINT catastrophic-event rate (1.75%) was below the 3–8% baseline range used by the design Monte Carlo.

## Combined mechanism evidence

```text
CORRECT_PAGEOUT
  central tendency benefit: not supported
  >=500 ms tail benefit:   not supported

WRONG_PAGEOUT
  harm: strongly supported
```

## Frozen decision

Do not advance CORRECT_PAGEOUT as a candidate coordination mechanism on the current evidence.

Do not interpret this as zero value of application semantics.

## Repository updates

- `findings/VAL-003-initial.md`
- README evidence status updated through VAL-003.

## Next recommended bounce

> Step back from mechanism selection and run a pseudo-Council on the smallest experiment/calculation that can quantify **decision headroom / value of information** in the observed workload before another intervention is selected.

Use existing Exact Memory Oracle / information-gain tooling where appropriate, but do not force a mathematical model that cannot be tied to the observed workload.

## Authority boundary

The finding applies to the declared hosted memcg workload, the fixed >=500 ms endpoint, and the specific CORRECT_PAGEOUT operation.

It does not establish Linux optimality, zero semantic value, or the need for a new coordinator.
