# KSLA-MATH-001 — Swarm Width Model Receipt

Status: **PASS / ANALYTIC SWARM-WIDTH MODEL VALIDATED**

## Frozen qualification

- workflow run: 37100235479
- job: 111138167266
- execution head: cf5ff69363fadc15702213cec1a1043f49cb4aea
- targeted tests: 6/6 PASS
- artifact ID: 11266060496
- artifact ZIP SHA256: 3227e947b9a3228bddeec7181411507806adbf556679a0cefba075bb902b9038
- spec SHA256: 00a3f30a7ea7f5a8ac53387070a75ef5c77ea14920ac0fdb955291c09ef39d4c
- result SHA256: 079d22cbdfe85a2ae6f705b7b860f96ff2cb292e81099a172ee16721c450220a

## Core mathematical result

For useful per-proposal progress Y>=0 with CDF F_s and a best-of-b acceptance rule:

`G_b=max(Y_1,...,Y_b)`

`P(G_b<=y)=F_s(y)^b`

`E[G_b]=integral_0^inf (1-F_s(y)^b)dy`

The marginal expected progress of additional kittens is nonincreasing.

Therefore any positive per-proposal / validator / queue / residency cost creates
a natural finite-width tradeoff.

## KSLA-002 resource-price envelope

For:

`J(b)=proposal_count + lambda_round * round_count`

the frozen lower envelope is:

- b=8 for lambda in [0, 1272/73);
- b=16 for [1272/73, 2208/47);
- b=32 for [2208/47, 400/3);
- b=64 for [400/3, 5696/33);
- b=128 for >=5696/33.

Batch 1 and 4 do not lie on this two-resource lower envelope.

## Experimental-design correction

KSLA-002 used batch-specific random draw domains.

The next width experiment must use a common frozen proposal tape so width b
consumes the first b proposals from the same round.

Frozen random identity:

`seed + round_id + proposal_index + action_family + distribution_parameters`

## Optimizer hierarchy

1. exact enumeration / order statistics for low-dimensional stationary width;
2. marginal-gain-per-cost allocation for known multiple action families;
3. dynamic programming / approximate MDP for known state-dependent dynamics;
4. contextual / cost-aware bandit for unknown or drifting family value;
5. matched-seed Monte Carlo for complete-policy evaluation and tails;
6. importance sampling for rare harmful tails;
7. Bayesian optimization for expensive outer black-box hyperparameters.

## Claim ceiling

**ANALYTIC_AND_SYNTHETIC_SWARM_WIDTH_MODEL_ONLY**
