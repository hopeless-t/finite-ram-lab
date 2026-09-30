# CURRENT

> Latest bounce: B417
> Stage: REFILL1 PROVENANCE RESOLVED
> Stop: PRE-VERIFY TAXONOMY CLOSED ENOUGH / RETURN TO VERIFIED-STATE AGE DECOUPLING

## Chapter II frontier

Historical SUCCESS/FAIL has been decomposed into explicit state transitions.

Established named states/mechanisms:

- VERIFIED_DIRECT_Q64_RESET: measured one-page direct Q64 establishes verified residual R0=63.
- PREVERIFY_S64 / MAX_STOCK_BOUNDARY: natural pre-VERIFY S0=64.
- STARTUP_STOCK_SEED: startup Q64/refill63 can leave large inherited stock on the future stock CPU.
- SMALL_RESIDUAL_REFILL: one-page refill can create S0=1 and measured T=2 without a contemporaneous direct Q64.
- SLAB_FREE_OBJCG_REFILL1: source-grounded provenance subtype for a complete refill1 specimen.
- TARGET_STOCK_EVICTION: verified residual stock can be asynchronously drained before the next measured transition.
- RELEASE_ONLY: source-grounded shared-LRU release changes accounting without consuming the target residual.

No complete verified B405 target path has produced TARGET_FAIL.

## R13-A corrected replay

Historical run 36693262942 remains frozen under original semantics.

Prospective corrected replay bounded retrospective evidence to the current trial STARTUP PRE marker:

- T1_NO_SMALL_REFILL=127
- SMALL_REFILL_EXPLAINS_DELAY=1
- CLASSIC_REFILL63_LEAK=0
- T histogram: T1=127, T2=1

This proved the original 35 classic-leak classifications were caused by cross-identity retrospective scope / memcg pointer reuse.

## R13-B1 — SMALL_RESIDUAL_REFILL established

Run 36697763027.

32 fresh CPUSET_PREP_ONLY identities:

- valid=31
- T1_NO_OWNER_REFILL1=29
- SMALL_RESIDUAL_REFILL_ESTABLISHMENT=2
- INVALID_OBSERVER=1
- promoted trials 1:4 and 2:7
- both promoted specimens are zero-miss

Both promoted specimens have:

systemd PID1 on future stock CPU
-> refill_stock(owner_memcg,1)
-> no current-trial owner refill63 before measurement
-> S0=1
-> measured first direct Q64 at T=2

Mechanism status:

SMALL_RESIDUAL_REFILL = ESTABLISHED_IN_TWO_ZERO_MISS_PHYSICAL_SPECIMENS

## R13-B2 — provenance capture

Run 36699038147.

Frozen physical aggregate:

- trial_count=32
- valid_trial_count=27
- T1_NO_OWNER_REFILL1=26
- PROVENANCE_CAPTURED=1
- INVALID_OBSERVER=5
- captured trial=1:7
- T histogram: T1=26, T2=1
- measured probe miss trials=0
- startup refill1 probe miss trials=5
- frozen automatic provenance class=OTHER_REFILL1_CALLER
- workflow completed SUCCESS

The physical aggregate is not rewritten.

### Source-grounded replay of trial 1:7

Complete zero-miss specimen:

- T=2
- S0=1
- one owner refill1 during STARTUP
- emitter=systemd PID1
- future stock CPU
- stack captured

Observed stack includes:

refill_stock
<- __memcg_slab_free_hook
<- kfree
<- skb_free_head
<- skb_release_data
<- consume_skb
<- skb_free_datagram
<- __unix_dgram_recvmsg
<- unix_dgram_recvmsg
<- sock_recvmsg
<- systemd userspace receive path

Linux source grounds the chain:

__memcg_slab_free_hook
-> __refill_obj_stock(..., uncharge=true)
-> page-boundary objcg byte-credit release
-> obj_cgroup_uncharge_pages(...,1)
-> refill_stock(owner_memcg,1)

Resolved provenance:

SLAB_FREE_OBJCG_REFILL1

This is a subtype of OBJCG_UNCHARGE_REFILL1.

Evidence:

- analysis/inputs/REFILL1-PROVENANCE-STAGE1-PHYSICAL-RESULT-v1.json
- analysis/inputs/REFILL1-PROVENANCE-SOURCE-REPLAY-v1.json
- docs/OBS-012-SLAB-FREE-OBJCG-REFILL1-PROVENANCE.md
- raw files=84
- bytes=25,081,990
- content-set SHA-256=3c8ddfa552036917db315f3a797f79c673e8659d924b53bcbaa24e0bb73ff247
- aggregate artifact ID=11089576790
- aggregate digest=sha256:bec9236cb19603d6822ac24c2a14ca6197e425f1854afc23480f3b9ca8ba0adf

## Observer lesson

Do not widen the net indiscriminately.

Preferred capture architecture:

1. SCOUT: phase-gated minimal event probes with zero-miss receipts.
2. BIND: current-trial epoch + owner memcg/counter + stock CPU + target PID.
3. SNIPER: conditional stacktrace only for the narrow event class under investigation.
4. PRESERVE UNKNOWN: unknown stack fingerprints remain first-class evidence; do not collapse them into FAIL or discard them.
5. SOURCE REPLAY: classify unknown captured stacks against source after the physical aggregate is frozen.

This architecture caught trial 1:7 even though the original runtime taxonomy lacked the slab-free objcg fingerprint.

## Research boundary

The immediate pre-VERIFY taxonomy is closed strongly enough for Chapter-II purposes.

Do not continue expanding refill1 subtypes merely for completeness.

Return to the already-frozen TX-AGE-DECOUPLING design to study verified-state hazards and time dependence.

## Authority

Physical continuation remains authorized by the user.

Standard public-repository GitHub-hosted runner only.
No paid larger runner.
No local-PC execution.
No automatic scale expansion.
No reliability certification.
