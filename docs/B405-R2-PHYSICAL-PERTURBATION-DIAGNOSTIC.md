# B405 R2 — Physical perturbation matrix diagnostic

> Run: 36646317346
> Launch commit: `50666ddf9bf96dad0e356936e5b7eb20c09f1ceb`
> Status: PHYSICAL RUN COMPLETE / 13 OF 16 CHALLENGES PASS / THREE DISTINCT MORPHOLOGIES
> TARGET_FAIL: 0

## Frozen aggregate

- CLEAN: 3/4
- RELEASE_ONLY: 3/4
- UNEXPECTED_REFILL: 4/4
- PTE_GROWTH: 3/4
- challenge pass: 13/16
- matrix_pass: false
- TARGET_FAIL: 0

R2 is frozen and is not to be rewritten after later observer or generator changes.

## 1. RELEASE_ONLY — INTERVENTION_NOT_REALIZED

Trial 1:1 did not produce the intended owner release.

Facts:

- trigger stock prime refill: touch 58
- pre-VERIFY shared-LRU scrub flush: touch 43
- target NORMALIZE depth: 58 touches
- producer: 17 target pages
- discard net observation: -2 pages
- OBSERVE residual before/after: 46 / 46
- no relevant drain inside the OBSERVE window
- no grounded owner release inside the OBSERVE window

The key error is ordering.

The LRU scrub happened before target normalization. The subsequent 58 target normalization faults advanced the per-CPU LRU batch phase again.

Therefore the intended geometry:

`empty batch + 17 producer + 14 trigger = 31`

was no longer guaranteed when the release challenge began.

Name:

`INTERVENTION_NOT_REALIZED`

This is a setup/generator failure, not a RELEASE_ONLY semantic failure.

Prospective fix:

- prime helper memcg stocks before target VERIFY;
- target NORMALIZE / VERIFY;
- post-VERIFY helper scrub to the next LRU flush;
- then producer17 -> discard -> trigger14.

## 2. CLEAN — ASYNCHRONOUS_STOCK_DRAIN_OWNERSHIP_UNRESOLVED

Trial 2:0 was invalidated at CLEAN CONSUME touch 43.

The direct stack was:

```text
drain_stock
<- refill_stock
<- mem_cgroup_sk_uncharge
<- __sk_mem_reduce_allocated
<- __sk_mem_reclaim
<- tcp_clean_rtx_queue
<- tcp_ack
<- network softirq
```

The drain ran on stock CPU 3.

The trace line showed `comm="frltx405"`, but this is the interrupted current task name. The call stack establishes that the causal path was network softirq reclaim, not the target worker's anonymous-page touch path.

Current observer knowledge is insufficient to say whether the drained stock slot belonged to the target memcg or another memcg cached on CPU 3.

Name:

`ASYNCHRONOUS_STOCK_DRAIN_OWNERSHIP_UNRESOLVED`

This result motivates memcg-identity correlation for drain events.

## 3. PTE_GROWTH recovery — POST_REPRIME_IMMEDIATE_REFILL / COVERAGE_AMBIGUOUS

Trial 3:3 correctly classified the intended challenge:

- PTE escape caused VmPTE +4 KiB
- challenge epoch -> INVALIDATED / PTE_GROWTH
- no challenge-epoch commit

The recovery epoch then observed:

```text
NORMALIZE touch 1:
  direct Q64 + refill63
  expected residual -> 63

CONSUME touch 1:
  direct Q64 + refill63 again
  -> UNEXPECTED_REFILL
```

The second Q64 occurred only about 286.8 ms after verification.

No target-CPU drain was visible in the marker windows.

However block 3 kprobe profile included non-zero probe misses:

- refill_stock: 175 missed
- drain_stock: 3 missed
- page_counter_try_charge64: 0 missed
- page_counter_uncharge17: 3 missed

Therefore absence of a visible intervening drain is not proof that no state-changing event occurred.

Name:

`POST_REPRIME_IMMEDIATE_REFILL / COVERAGE_AMBIGUOUS`

Do not promote this to a new kernel mechanism until observer coverage is improved.

## 4. Strong repeated result

Across B405 R1 and R2:

`UNEXPECTED_REFILL`

was deliberately generated and classified correctly in **8/8** physical challenge identities.

Across the valid PTE challenge epochs:

`PTE_GROWTH`

was deliberately generated and the challenge epoch was invalidated before commit in **8/8** identities. R2 trial 3:3 failed only in the later recovery epoch.

No complete physical challenge path produced TARGET_FAIL.

These are causal-challenge observations, not population reliability estimates.

## 5. Next observer resolution

R3 should not merely retry R2.

It should add two missing axes.

### Drain ownership

Capture the memcg pointer passed by `memcg_uncharge()` and correlate it to the epoch-local target memcg learned from direct `refill_stock(memcg,63)`.

A same-CPU drain is state-destroying only when its drained memcg is shown to be the target memcg.

### Inter-window continuity

Current PRE/POST touch receipts leave gaps between touches.

The epoch needs continuity telemetry capable of detecting state-changing events after one packet POST and before the next packet PRE.

This is especially important when Python-side trace readback creates hundreds of milliseconds between measured touches.

## 6. R3 design principle

Do not loosen the classifier.

Increase observability and intervention purity.

The research object is now explicitly decomposed into:

- challenge classification;
- intervention realization;
- incidental natural invalidation;
- recovery success;
- observer coverage.

This decomposition is a direct consequence of naming previously conflated state transitions.

## Evidence

Raw manifest:

- files: 88
- bytes: 53,948,401
- content-set SHA-256:
  `8f1311b317978d1f596e90523e983ceacea215cc393b39e0f488913402bf531b`

Aggregate artifact:

- ID: `11067669529`
- digest:
  `sha256:838cdcb35193fb4e8713720386de6ac9526360401abc4a0bd0a6c98122d39740`

Machine-readable freeze:

- `analysis/inputs/B405-R2-PHYSICAL-RESULT-v1.json`
