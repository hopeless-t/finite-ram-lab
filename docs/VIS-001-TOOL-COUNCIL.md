# VIS-001 Tool Council — pmndrs/math

> **Status:** CONVERGED / DECISION FROZEN  
> **Scope:** visualization/tooling only  
> **Scientific authority:** NONE

## Question

Should `pmndrs/math` be incorporated into Finite RAM Lab now, given:

- its successful isolated dogfood in `finite-tool-surface-lab`;
- its small observed package footprint;
- its data-oriented / caller-owned API;
- its packaged Agent Skill;
- its potential usefulness for interactive evidence visualization;
- the fact that future visualization mathematics cannot be predicted precisely?

## External qualification evidence

The Council accepts the existing `finite-tool-surface-lab` DOGFOOD-001 result as cross-repository qualification evidence rather than repeating the same package probe.

Canonical external evidence supplied by that lab:

- candidate: `pmndrs/math@0.1.0`;
- verdict: `EDIBLE_WITH_BONES`;
- branch: `research/dogfood-pmndrs-math-v0`;
- implementation commit: `1fbf6c52d40c1d691038016c1e87f5fc3bc81e9a`;
- result commit: `31bea58625dfddd8f7f8c538665274795a426e7a`;
- Actions run: `36231954801`;
- artifact: `10902529835`;
- artifact SHA-256: `06a9fa99880e36826ab5e16a58fd84032d7806af583f5a7d5a928e8bfd7b8f86`.

Observed qualification characteristics included:

- import PASS;
- caller-owned output PASS;
- in-place aliasing PASS;
- seeded RNG replay PASS;
- QuickHull2 smoke PASS;
- packaged Agent Skill PASS;
- GitHub Actions PASS;
- approximately 2.02 MB unpacked / 199 files;
- no transitive runtime dependencies observed in that package probe.

The reported micro-timing is treated as descriptive only, not a performance claim.

## Council roles

The Council used seven roles:

1. scientific-integrity reviewer;
2. visualization / HCI reviewer;
3. systems / build reviewer;
4. contributor-onboarding reviewer;
5. AI-worker tool-surface reviewer;
6. supply-chain / reproducibility reviewer;
7. maintenance / scope reviewer.

## Round 1 — Initial positions

### Scientific-integrity reviewer

**Position:** reject from the scientific core.

Reason:

```text
visualization utility
!=
scientific computation authority
```

Canonical evidence generation must remain Python/Actions/statistics driven.

### Visualization / HCI reviewer

**Position:** adopt.

The library is well aligned with:

- page/region geometry;
- animated residency transitions;
- timeline interpolation;
- camera / spatial transforms;
- deterministic visual layouts;
- WebGL/WebGPU-facing math.

A static plotting library would cover charts, but not an interactive memory-state replay as naturally.

### Systems / build reviewer

**Position:** adopt only behind an isolated Node seam.

The package itself is small, but the meaningful cost is not 2 MB.

The real cost is:

```text
new runtime seam
+ lockfile
+ JS/TS build chain
+ update surface
+ worker context
```

Therefore it must not become a repository-root dependency.

### Contributor-onboarding reviewer

**Position:** adopt experimentally.

Finite RAM Lab has increasingly complex evidence:

- pressure regime transitions;
- residency loss;
- refault / swap behavior;
- rare catastrophic stalls;
- semantic-region interventions.

Interactive replay can reduce the time required for a third party to understand a run and may make external review/contribution more likely.

This is a usability hypothesis, not yet demonstrated.

### AI-worker tool-surface reviewer

**Position:** keep discoverable but do not expose globally.

The packaged Skill is interesting, but:

```text
Tool Visible
!=
Tool Needed
!=
Tool Understood
```

Only visualization workers should receive the tool/Skill context.

### Supply-chain reviewer

**Position:** conditional adoption.

Requirements:

- exact package version;
- committed lockfile;
- isolated build;
- no dependency in evidence-producing workflows;
- external qualification provenance retained.

### Maintenance reviewer

**Position:** do not pre-build a large explorer.

Approve one bounded VIS-001 dogfood only.

## Round 1 disagreement

The main disagreement was:

> install now because the future is unknown

versus

> wait until a concrete visualization exists.

## Round 2 — Optionality analysis

The Council separated three meanings of “having the tool”:

```text
A. discoverable qualification record
B. isolated optional dependency
C. active default worker surface
```

These are not equivalent.

The future-option value of A is nearly all of the option value needed today.

B is justified when a concrete explorer exists.

C has ongoing cognitive and maintenance cost and is not justified.

### Mathematical-coverage challenge

The Council also rejected the argument that `pmndrs/math` is generic future-proofing for unknown mathematical methods.

It is strong in:

- vectors / matrices / quaternions;
- geometry / spatial queries;
- seeded RNG;
- noise;
- easing / springs;
- IK;
- real-time numeric kernels.

It is **not** a substitute for:

- SciPy;
- sparse solvers;
- MILP;
- symbolic algebra;
- ODE/PDE solvers;
- Bayesian inference;
- JAX-style accelerator computing.

Therefore “future mathematics is unknown” supports keeping a **qualification/discovery mechanism**, not loading every math package into the active tool surface.

## Round 2 convergence candidate

The Council converged on:

> **Qualified Optional Visualization Dependency**

but one question remained:

> Should Monte Carlo be used to choose between “warehouse only” and “install now”?

## Round 3 — Monte Carlo review

The statistics reviewer rejected a decision Monte Carlo for this choice.

Reason:

A Monte Carlo model would require invented probability distributions or utility weights for:

- future visualization demand;
- external-contributor conversion;
- maintenance cost;
- worker cognitive cost;
- supply-chain risk.

Those quantities are not yet empirically calibrated.

Running millions of samples over arbitrary priors would create numerical precision without epistemic precision.

Therefore:

```text
Monte Carlo rejected for this decision
because the uncertainty is model uncertainty,
not sampling uncertainty.
```

This is itself a methodological decision.

The correct next evidence source is a bounded real dogfood:

```text
VIS-001
one canonical experiment
→ one interactive replay
→ compare comprehension / usefulness
→ keep or remove
```

## Final converged decision

### Classification

```text
pmndrs/math@0.1.0

Scientific core dependency        NO
Root repository dependency        NO
Canonical evidence dependency     NO
Global AI-worker tool surface     NO

Qualified inventory               YES
Visualization candidate           YES
VIS-001 allowed                    YES
Isolated explorer dependency       YES, when VIS-001 starts
Packaged Skill use                 CONDITIONAL, visualization worker only
Repeat package dogfood in FRL      NO
```

### Integration rule

If VIS-001 is opened, use an isolated structure such as:

```text
explorer/
  package.json
  lockfile
  src/
```

The scientific core communicates with the explorer only through exported, read-only evidence data.

```text
canonical evidence
      ↓
read-only adapter
      ↓
interactive explorer
```

The explorer must never write or reinterpret canonical scientific evidence.

## VIS-001 success criterion

The first dogfood should replay **one already-understood experiment**, not visualize unreconciled science.

Preferred initial target:

> an OBS/VAL residency-pressure timeline where application phase, hot/cold residency, swap/refault activity, and latency can be inspected together.

The success question is:

> Does the interactive replay materially reduce the effort required for a third party to understand the experiment and navigate to canonical evidence?

Visual attractiveness alone is insufficient.

## Final principle

> **Keep future option value in the inventory; keep present cognitive cost out of the active surface.**

And:

> **Pretty Card != Evidence, but a Pretty Card may be a high-value path to Evidence.**
