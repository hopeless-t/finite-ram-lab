# FR-FP-027 Receipt

Status: **PASS / EXACT BINOMIAL REUSE EVIDENCE BUDGET QUALIFIED**

Parent: **FR-FP-026**

- workflow run: 37192808376
- job: 111408379578
- execution head: e92c5cfecd55fabb11f9af2a98d0db0d3e287b77
- confidence levels: 95% / 99%
- new physical runs: 0

Decision rule:

    certify COLD only if
      p_upper <= reuse_ceiling

where p_upper is a one-sided exact Clopper-Pearson reuse upper bound.

Zero-reuse closed form:

    p_U = 1 - (1-confidence)^(1/n)

Qualified 95% zero-reuse observation budgets:

- reuse ceiling 0.50 -> 5 observations
- reuse ceiling 0.25 -> 11 observations
- reuse ceiling 0.10 -> 29 observations
- FR-FP-026 slow/strict ceiling 0.08333 -> 35 observations

Observed reuse increases the required evidence.

At 95% confidence:
- ceiling 0.10:
  - 0 reuse -> 29 observations
  - 1 reuse -> 46 observations
  - 2 reuse -> 61 observations

At 99% confidence the required evidence is never smaller.

Decision:

**CONVERT_REUSE_CEILING_INTO_A_DECISION_SPECIFIC_OBSERVATION_BUDGET**

Governor consequence:

The system can stop collecting reuse evidence once the exact upper bound is
below the current tier-decision ceiling.

It no longer needs an arbitrarily large reuse trace.

Important assumption:

The result assumes a stable Bernoulli decision window. It does not prove real
reuse is stationary, iid, or exchangeable.

Next:

Test how cumulative reuse evidence should be invalidated when the workload reuse
rate changes after qualification.

Claim ceiling:

**EXACT_BINOMIAL_EVIDENCE_BUDGET_UNDER_STABLE_BERNOULLI_REUSE_ASSUMPTION_ONLY**
