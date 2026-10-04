# FR-FP-034 Receipt

Status: **PASS / MULTI-STATE FINITE WARM-BUDGET ALLOCATOR QUALIFIED**

Parent: **FR-FP-033**

- workflow run: 37204552869
- job: 111442919433
- execution head: 81bdaf79348d33aaf6d03a372a2a19d4759e8213
- state count: 10
- state size: 8 MiB
- hosted COLD baseline: 3.299338 ms
- new physical runs: 0
- reuse confidence: 95%
- deadline: 10 ms
- miss tolerance: 5%

Reuse upper bounds are exact one-sided Clopper-Pearson bounds from 35 synthetic
reuse observations per state with counts 0..9.

## Deadline-mandatory WARM states

The shared conditional 10 ms miss probability is multiplied by each state's
reuse upper bound.

Mandatory WARM:

    states 7, 8, 9

Their unconditional deadline risks exceed 5%.

## 40 MiB WARM budget

Five 8 MiB WARM slots.

After the three mandatory states, the allocator chooses optional states by
descending conservative expected penalty avoided per MiB.

Qualified WARM set:

    {5, 6, 7, 8, 9}

Qualified COLD set:

    {0, 1, 2, 3, 4}

Expected residual COLD penalty:

    4.382983 ms

Maximum COLD-state deadline risk:

    3.6408%

Exhaustive comparison:
- feasible exact subsets: 21
- greedy/value-density solution: exact optimum
- selected set: exact match
- expected penalty: exact match

Every feasible budget in the 3..10 WARM-slot sweep matches exhaustive optimum.

## Endogenous shadow price

At five WARM slots:

    highest optional COLD value density
      = 0.160356 ms/MiB

    lowest optional WARM value density
      = 0.183123 ms/MiB

Therefore an endogenous shadow price can lie in:

    0.160356 <= lambda <= 0.183123 ms/MiB

No external lambda is required for this allocation.

Marginal expected-penalty savings per added MiB decrease monotonically across
the budget frontier.

Decision:

**ENDOGENIZE_MEMORY_SHADOW_PRICE_FROM_A_FINITE_MULTI_STATE_WARM_BUDGET**

Next:

Physically instantiate ten 8 MiB durable states under one shared 40 MiB WARM
budget and compare the qualified value/risk allocation against a same-capacity
anti-value control.

Claim ceiling:

**SYNTHETIC_TEN_STATE_EQUAL_SIZE_ALLOCATION_USING_ONE_HOSTED_BASELINE_AND_REUSED_RESTORE_PRIORS_ONLY**
