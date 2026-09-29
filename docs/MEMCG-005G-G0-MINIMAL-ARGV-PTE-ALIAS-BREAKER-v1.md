# MEMCG-005G-G0 Minimal Argv/PTE Alias Breaker v1

> **Status:** FROZEN-CANDIDATE DRAFT / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY
> **Supersedes:** G0 Draft v0 for the first alias-breaking experiment

## Question

Does the CAP8/9 vs CAP10+ exact-zero enrichment persist when decimal argv width is experimentally separated from numeric mapping capacity?

Secondary:

Is exact-zero capture associated with whether the measured first fault grows the process page-table footprint?

## 1. Preserve the worker

Use the existing `experiments/memcg005d_worker.c` unchanged.

Reason:

the experiment is studying mapping/exec layout. Recompiling a structurally modified worker to add instrumentation can itself change the layout.

## 2. Direct argv-width intervention

The worker parses `--max-pages` with `atoi()`.

glibc implements `atoi()` as `strtol(..., base=10)`.

Therefore:

- token `8` -> numeric capacity 8
- token `08` -> numeric capacity 8
- token `9` -> numeric capacity 9
- token `09` -> numeric capacity 9

This gives a same-capacity intervention on argv representation.

## 3. Frozen arm panel

Six arms:

| arm | argv token | parsed capacity | purpose |
| --- | --- | ---: | --- |
| C8 | `8` | 8 | canonical low |
| P8 | `08` | 8 | zero-padded low |
| C9 | `9` | 9 | canonical low |
| P9 | `09` | 9 | zero-padded low |
| H10 | `10` | 10 | high-side anchor |
| H32 | `32` | 32 | plateau anchor |

The primary argv-width contrast is:

`P8+P9 vs C8+C9`

The capacity-survival contrast is:

`P8+P9 vs H10+H32`

## 4. Primary endpoint

`ZERO_CAPTURE := valid && REMOTE_LOW && first_touch_delta_pages == 0`

Nonzero anomalies remain a separate morphology.

Do not merge +1/+57/etc into ZERO_CAPTURE.

## 5. Primary interpretations

### ARGV_WIDTH_EFFECT_SUPPORTED

Zero-padding 8/9 materially raises exact-zero capture relative to canonical 8/9 and brings it toward the H10/H32 regime.

### CAPACITY_SIGNAL_SURVIVES_WIDTH_CONTROL

Zero-padding has little/no material effect, while P8/P9 remain below H10/H32.

### MIXED_OR_UNRESOLVED

Both representation and numeric capacity appear relevant, or evidence is insufficient.

No post-hoc hard-threshold claim is allowed from this experiment.

## 6. Page-table receipt without worker modification

Controller reads `/proc/<worker_pid>/status`:

- immediately before measured GO: `VmPTE_pre_kib`
- immediately after DONE: `VmPTE_post_kib`

Derived:

`VmPTE_delta_kib = post - pre`

Interpretation:

- delta 0: no net page-table-footprint growth visible;
- positive delta: one or more page-table levels grew across the measured fault.

Do not require exactly +4 KiB; report the full integer delta distribution.

Also read `memory.stat:pagetables` pre/post as corroboration only.

Do not use memory.stat pagetables as the primary one-page PTE classifier because memcg rstat flushing may suppress small immediate changes.

## 7. PTE-mechanism exploratory prediction

Condition on valid REMOTE_LOW trials.

Compare ZERO_CAPTURE by:

`VmPTE_delta_kib == 0`

versus

`VmPTE_delta_kib > 0`

Candidate prediction from MATH-009:

exact-zero capture should be enriched when no new page-table footprint is required if the natural stock mass is concentrated near the one-page residual state.

This is exploratory in G0 and must not override the argv-width primary result.

## 8. Failure-only one-step biopsy

After the frozen first-touch endpoint, only when the first touch is exact-zero:

1. record `VmPTE_post1_kib`;
2. issue exactly one additional adjacent worker touch;
3. record `second_touch_delta_pages`;
4. record `VmPTE_post2_kib`.

Define:

`NEXT_Q64 := second_touch_delta_pages in [60,68]`

Mechanism classifications from MATH-011:

- first VmPTE delta = 0 + ZERO + NEXT_Q64 + second VmPTE delta = 0 -> candidate pre-target R=1;
- first VmPTE delta >0 + ZERO + NEXT_Q64 + second VmPTE delta = 0 -> candidate pre-target R=2 under the one-new-PTE-page model;
- second VmPTE delta >0 -> boundary phenotype; exclude from the simple R inference.

This biopsy occurs strictly after the primary first-touch endpoint.

It must not change whether the first specimen is counted as ZERO_CAPTURE.

Reference:
`docs/MATH-011-TWO-TOUCH-PTE-STOCK-DISCRIMINATOR.md`

## 9. Existing gate retained

- page size = 4096;
- startup CPU P;
- measured CPU S != P;
- `pre_current_pages <= 110`;
- migration delta recorded;
- observed CPU == S;
- worker_error == 0;
- first touch is exactly one worker touch.

## 10. Blocking and schedule

Within each independent hosted block:

- 60 candidates;
- 10 candidates per arm;
- rotate arm assignment by block and identity;
- never group all padded arms contiguously;
- preserve the same lifecycle style as G-F.

Staged ceiling:

- Stage A: 16 blocks / 960 total candidates / 160 raw candidates per arm;
- Stage B: cumulative 32 blocks / 1920 total / 320 per arm;
- Stage C: cumulative 48 blocks / 2880 total / 480 per arm.

This keeps the terminal ceiling equal to the completed G-F scale while allowing short resource-gated bounces.

## 11. Staged compute interpretation

MATH-010 calibrated the direct padded-vs-canonical contrast using the G-F planning rates.

Approximate Monte Carlo planning results:

- 16 blocks: correct direction 97.22%; Fisher p<.05 with correct direction 42.66%;
- 32 blocks: correct direction 99.76%; Fisher p<.05 with correct direction 75.83%;
- 48 blocks: correct direction 99.96%; Fisher p<.05 with correct direction 90.69%.

Stage A is therefore primarily an instrument-integrity and direction probe.

Do not treat lack of p<.05 at Stage A as evidence against the argv mechanism.

Ordinary p-values must not be repeatedly inspected and then presented as fixed-N confirmatory inference. Stage reads are exploratory unless a formal sequential rule is separately frozen.

Each hosted stage requires Human compute approval.

## 12. Why this is higher information-per-candidate than v0

G0 v0 removed capacity from argv by changing the control protocol.

That cleanly removes the alias, but it also modifies the worker/control ABI.

G0 v1 instead creates a direct same-capacity representation intervention while keeping the worker unchanged.

Therefore it can distinguish:

- token representation;
- parsed numeric capacity;
- first-fault page-table growth;

with less mechanism perturbation.

## 13. Follow-up only if signal survives

If numeric capacity remains predictive after zero-padding:

then and only then create an instrumented G0-B worker that publishes:

- anonymous region start/end;
- control mapping address;
- 2 MiB phase;
- PTE index.

That second experiment addresses exact virtual-layout geometry.

## Compute authority

No implementation or hosted launch from this document alone.

Planning calibration:
`docs/MATH-010-G0-MONTE-CARLO-CALIBRATION.md`

The 5760-candidate MEMCG-005G-G remains deferred.

No local-PC execution.
