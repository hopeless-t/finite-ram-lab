# CURRENT

> Latest bounce: B415
> Stage: R13-A SMALL-RESIDUAL RESULT FROZEN
> Stop: STRATEGY PAUSE BEFORE R13-B

## Chapter II frontier

The research has decomposed natural pre-VERIFY stock into multiple named mechanisms/states.

Established:

- VERIFIED_DIRECT_Q64_RESET: measured one-page direct Q64 -> verified residual R0=63.
- PREVERIFY_S64 / MAX_STOCK_BOUNDARY: natural S0=64 established for the frozen R8 specimen by lower/upper-bound sandwich proof.
- TARGET_STOCK_EVICTION: verified residual stock can be asynchronously drained before the next measured transition.
- STARTUP_STOCK_SEED: startup can charge/refill the future stock CPU before historical _start() returns, leaving inherited stock and delayed measured Q64 boundary.

Candidate, not yet promoted:

- SMALL_RESIDUAL_REFILL: small refill_stock increments, including nr_pages=1, may create low natural residuals such as S0=1 / T=2 without a contemporaneous direct Q64.

No complete B405 transactional path has produced TARGET_FAIL.

## R12 cpuset intervention

Run 36691073336.

CONTROL:
- n=32
- valid=31
- classic STARTUP_STOCK_SEED=5
- large high-T cluster T=46,47,48,49,49
- one clean T=2

CPUSET_PREP_ONLY:
- n=32
- valid=31
- classic startup seed=0
- release-gap classic seed=0
- 30 CPUSET_SUPPRESSED
- one clean T=2

Strict preregistered causal_support=false because complete-panel 64/64 and all intervention T=1 were required.

Large STARTUP_STOCK_SEED remains strongly causally supported by the intervention, while T=2 was separated as a different mechanism family.

Frozen result:
- analysis/inputs/STARTUP-STOCK-SEED-CPUSET-R1-PHYSICAL-RESULT-v1.json

## R13-A small-refill spectrum

Run 36693262942.
Launch commit 9930da8b0999d3b324d0400ba61a83d3e8f43e73.

Physical execution:
- four block jobs completed successfully
- 128 identities measured
- aggregate completed
- final workflow failure came from frozen Assert discovery

Frozen aggregate:
- trial_count=128
- valid_trial_count=117
- discovery_pass=false
- panel_coverage_pass=false
- CLASSIC_REFILL63_LEAK=35
- INVALID_OBSERVER=11
- T1_NO_SMALL_REFILL=82
- promoted small-refill count=0

The historical aggregate must not be rewritten.

## R13-A forensic correction

The original retrospective reducer searched all earlier block events by owner_memcg + stock_cpu.

That scope is invalid across sequential identities because memcg object addresses can be reused.

Therefore the frozen CLASSIC_REFILL63_LEAK=35 count is not scientifically interpretable as 35 current-trial leaks.

Required fix:

- retrospective lower bound = current trial STARTUP PRE
- never attach evidence from a previous identity solely because a memcg pointer was later reused

This correction is prospective. Do not rewrite the frozen aggregate.

## Trial 0:28

Highest-value R13-A specimen:

- CPUSET_PREP_ONLY
- T=2
- inferred S0=1
- startup cpuset effective = prep only
- release cpuset effective = prep + stock
- single-process cgroup
- geometry/PTE/CPU/worker/trace guards clean
- Q64 probe missed=0
- refill-spectrum probe missed=1

Inside the current STARTUP window:

- systemd PID1
- future stock CPU
- refill_stock(owner_memcg, 1)

The later measured boundary at touch 2 resolves the same owner memcg.

Source-compatible chain:

systemd PID1 on future stock CPU
-> refill_stock(owner_memcg,1)
-> S0=1
-> T=2

Status:

DIRECT_SMALL_REFILL_CANDIDATE

Promotion to SMALL_RESIDUAL_REFILL = ESTABLISHED is withheld because the refill probe had one missed hit and the frozen contract requires zero misses.

## Source grounding

refill_stock() is not Q64-excess-only.

Known source paths include:

- try_charge_memcg -> refill_stock(batch - nr_pages)
- obj_cgroup_uncharge_pages -> refill_stock(nr_pages)
- mem_cgroup_sk_uncharge -> refill_stock(nr_pages)

Therefore small stock increments can occur without a contemporaneous direct Q64.

mem_cgroup_css_offline drains all stock, which disfavors stale stock from an already-destroyed transient memcg.

## Frozen R13-A evidence

Machine-readable:
- analysis/inputs/SMALL-RESIDUAL-REFILL-R1-PHYSICAL-RESULT-v1.json

Narrative:
- docs/OBS-010-R13A-SMALL-RESIDUAL-REFILL-RESULT.md

Raw manifest:
- files=276
- bytes=18,845,986
- content-set SHA-256=f2971d6ceb5a59007974f3935d5c23b4a5019d4c5bc12c03950aacb13434242a
- aggregate artifact ID=11086807735
- aggregate digest=sha256:00ab1ca0feebdb501445b06a03dec449d9e10150012bef69acd5649b1d658de5

## Strategy pause

Do not launch R13-B yet.

Candidate next sequence for council review:

1. repair current-trial retrospective scope;
2. reduce refill observer to nr_pages == 1;
3. retain CPUSET_PREP_ONLY to suppress the large STARTUP_STOCK_SEED path;
4. require zero misses;
5. capture a complete T=2 + owner refill1 specimen;
6. only then add conditional stacktrace to refill1 to identify the caller.

Need strategic review before implementation to decide whether to:
- prioritize direct refill1 caller identification,
- first repair/replay R13-A reducer on frozen raw evidence,
- or use a narrower intervention that targets systemd PID1 / kmem-vs-socket refill provenance.

## Authority

Physical continuation remains authorized by the user.

Standard public-repository GitHub-hosted runner only.
No paid larger runner.
No local-PC execution.
No reliability certification.
