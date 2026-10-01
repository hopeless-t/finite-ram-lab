# B450 — Clean Dynamic Frontier Prelaunch Implementation Audit v0.1

Status: **SOFTWARE QUALIFIED / NOT PHYSICALLY EXECUTED**.

## 1. Scope

B450 audits the B448 Clean Dynamic Frontier implementation before any hosted workflow launch.

The audit covers:

- trial validity semantics;
- stable plan/source identity enforcement;
- schedule/aggregate software;
- guarded workflow structure;
- B444–B449 pure-model regressions.

It does not execute the memory workload.

## 2. Defect D1 — buffered file-residency validity

The initial B448 runner required:

post-observer file residency <= 0.1

for every arm.

That is correct for DONTNEED arms, whose intended post-scan state is cold.

It is incorrect for the buffered reference.

Buffered I/O is expected to retain file pages and historical STRATA results show substantial buffered post-residency.

If left unchanged, the reference arm could be invalidated for behaving correctly.

### Fix

B450 adds an arm-aware validity helper.

- buffered: this cold-residency check is not applicable and passes;
- DONTNEED: resident_fraction must remain within the frozen maximum;
- unknown arm family: fail closed.

This preserves buffered as a reference rather than forcing it to mimic DONTNEED semantics.

## 3. Defect D2 — identity enforcement existed in contract but not aggregate

B443/B444 require stable:

- source commit;
- observer contract;
- fixed workload parameters.

The B448 aggregate initially checked only matrix completeness and PASS trial status.

That was insufficient.

### Fix

The aggregate now fails closed unless all trials share exactly one:

- source_commit;
- observer_contract_version.

It also verifies fixed values for:

- MemoryMax;
- hot anonymous state;
- cold-file size;
- read chunk.

The capacity axis and arm remain the only designed varying coordinates.

## 4. Isolated software qualification

The new code was copied into a temporary candidate-only subtree:

b450_qual/

inside the existing product_sales candidate lane.

The lane reported:

- mode BUILD;
- PILOT_DEV_EXEC available;
- network false;
- canonical write false;
- promotion false;
- Remote Desktop Commander false.

The test process was workspace-only with host_write=false.

No canonical or host workspace was mutated.

## 5. First qualification run

The first isolated run produced:

- 16 branch tests PASS;
- 1 import error.

The error was not branch code.

A qualification-only dependency stub had been written with literal backslash-n text instead of actual newlines.

B450 did not reinterpret this as a product failure.

The stub was corrected and the identical branch suite rerun.

## 6. Final qualification result

Final result:

**22 tests / 22 PASS**

Return code:

0

Test output digest:

sha256:63f2a28376977a5444db766122d1b7e188353f667de114352b95c02499e1d707

Covered behaviors include:

- complete 144-trial design matrix;
- clean floor / observer separation arithmetic;
- arm-aware buffered/DONTNEED validity;
- source identity drift rejection;
- workflow has no push auto-trigger;
- workflow requires explicit launch acknowledgment;
- cold verification precedes systemd-run;
- B444 observer identity;
- B445 intrinsic clamp;
- B446 partial decomposition;
- B449 prelaunch frontier predictions.

## 7. Cleanup

After qualification, only the B450-owned:

b450_qual/

subtree was removed.

The prior pre-existing product_sales temporary residue:

- finite_ram_lab/
- tests/

was intentionally left unchanged.

Post-cleanup git status returned exactly those two old untracked paths and no B450 subtree.

## 8. What is qualified

Qualified:

- Python import/syntax path for the bounded copied surface;
- pure model arithmetic;
- scheduler/aggregator logic exercised by fake complete matrices;
- identity fail-closed checks;
- workflow static guards.

Not qualified:

- actual cgroup behavior;
- systemd-run execution;
- file-residency behavior on a fresh runner;
- physical observer perturbation;
- 144-trial scientific outcome.

Those require the separately authorized physical workflow.

## 9. Launch readiness

The implementation is now a reasonable launch candidate, but B450 does not launch it.

The workflow remains:

- workflow_dispatch only;
- no push trigger;
- gated on launch_ack=EXPLICITLY_AUTHORIZED.

No retry authority is implied.

## 10. Current research boundary

The next information gain requires one of two choices:

1. explicitly launch the qualified hosted Clean Dynamic Frontier study; or
2. continue offline/historical theory work without claiming new physical evidence.

B450 itself grants neither launch nor paid-resource authority.
