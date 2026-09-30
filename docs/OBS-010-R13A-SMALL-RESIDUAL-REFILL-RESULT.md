# OBS-010 — R13-A small-residual refill spectrum result

## Frozen run

- Experiment: TX-SMALL-RESIDUAL-REFILL-SPECTRUM-v1
- GitHub Actions run: 36693262942
- Launch commit: 9930da8b0999d3b324d0400ba61a83d3e8f43e73
- Four physical block jobs completed successfully.
- Aggregate completed, then failed only at the frozen discovery assertion.
- Trials: 128
- Observer-valid under the original R13-A reducer: 117
- Frozen discovery_pass: false
- Frozen panel_coverage_pass: false

Frozen aggregate classes:

CLASSIC_REFILL63_LEAK = 35
INVALID_OBSERVER = 11
T1_NO_SMALL_REFILL = 82

The historical aggregate must not be rewritten.

## Important forensic correction

R13-A contains a retrospective scoping bug.

The reducer learns owner_memcg from the measured first-Q64 boundary and then scans all earlier refill-spectrum rows in the whole block for the same memcg pointer and stock CPU.

That is too broad. Fresh transient identities are sequential and kernel object addresses can be reused. An older identity can therefore carry the same numerical memcg pointer as the current identity, so an older refill can be falsely attached to the current trial.

Therefore the frozen count CLASSIC_REFILL63_LEAK=35 is not scientifically interpretable as 35 current-trial classic leaks.

This is a reducer-scope defect, not a physical result. Future reducers must restrict retrospective evidence to the current trial epoch beginning at that trial's STARTUP PRE marker.

## Trial 0:28 — direct small-refill candidate

Trial 0:28 is the highest-value R13-A specimen.

Frozen properties:

- arm: CPUSET_PREP_ONLY
- startup cpuset effective: prep CPU only
- release cpuset effective: prep + stock CPU
- single process in target cgroup
- PTE guard clean
- CPU guard clean
- worker sequence clean
- trace windows complete
- first measured direct Q64: T=2
- inferred initial residual: S0=1

During the current trial STARTUP window, a direct refill receipt was observed:

- emitter: systemd PID 1
- CPU: future stock CPU
- nr_pages: 1
- phase: STARTUP
- memcg: later measured owner memcg

The later measured boundary at touch 2 resolves the same owner memcg.

Source-compatible sequence:

systemd PID1 on future stock CPU -> refill_stock(owner_memcg,1) -> natural pre-VERIFY residual S0=1 -> first measured direct Q64 at T=2.

This is the first direct physical observation matching the SMALL_RESIDUAL_REFILL hypothesis.

## Why it is not promoted yet

The direct-Q64 probe had zero missed hits for the identity.

The refill-spectrum probe reported one missed hit.

The frozen promotion contract requires zero missed hits for mechanism promotion.

Therefore trial 0:28 remains DIRECT_SMALL_REFILL_CANDIDATE, not SMALL_RESIDUAL_REFILL = ESTABLISHED.

This is an evidence-discipline decision, not a claim that the observed refill1 did not happen.

## Why the old refill63 match is stale

The current trial STARTUP PRE marker occurs at approximately 94.167 s in the block trace.

The direct systemd refill1 occurs at approximately 94.186 s, inside that STARTUP interval.

The old refill63 row attached by the original reducer occurs at approximately 83.905 s, about ten seconds before the current trial begins, and belongs to an earlier worker identity.

The original reducer admitted it only because the numerical memcg pointer was later reused. This demonstrates the retrospective-scope bug directly.

## Source grounding

Linux refill_stock() is not limited to storing the 63-page excess from a one-page Q64 batch.

Source paths include:

- try_charge_memcg -> refill_stock(memcg, batch - nr_pages)
- obj_cgroup_uncharge_pages -> refill_stock(memcg, nr_pages)
- mem_cgroup_sk_uncharge -> refill_stock(memcg, nr_pages)

Therefore stock can increase by small amounts without a contemporaneous direct Q64 charge.

The observed nr_pages=1 receipt is source-compatible with this mechanism family.

Also, memcg offline processing drains its stock, so stale stock from an already-destroyed transient memcg is disfavored as the explanation.

## Evidence manifest

- files: 276
- bytes: 18,845,986
- content-set SHA-256: f2971d6ceb5a59007974f3935d5c23b4a5019d4c5bc12c03950aacb13434242a
- manifest created: 2026-09-30T09:02:48Z
- aggregate artifact ID: 11086807735
- aggregate digest: sha256:00ab1ca0feebdb501445b06a03dec449d9e10150012bef69acd5649b1d658de5

Machine-readable freeze:

- analysis/inputs/SMALL-RESIDUAL-REFILL-R1-PHYSICAL-RESULT-v1.json

## Decision

Do not rerun the same broad R13-A design unchanged.

Next sequence:

1. Repair retrospective scope to current-trial STARTUP PRE and later only.
2. Narrow the physical refill probe to nr_pages == 1.
3. Keep CPUSET_PREP_ONLY to suppress the large refill63 startup path.
4. Require zero misses for the narrow refill1 probe.
5. After a complete T=2 + owner refill1 specimen is captured, stacktrace refill1 only.
6. Use the stack to distinguish obj_cgroup_uncharge_pages, mem_cgroup_sk_uncharge, or another caller.

## Claim ceiling

R13-A captured a direct small-refill candidate consistent with S0=1 -> T=2, but did not satisfy the frozen zero-miss promotion rule.

The classic refill63 aggregate count is contaminated by a retrospective scope bug and must not be used as causal evidence.
