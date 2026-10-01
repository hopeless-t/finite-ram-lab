# CURRENT

> Latest bounce: B438
> Stage: CAPACITY PHASE DIAGRAM v0.1 FROZEN
> Stop: COMPARE STATIC PREDICTION WITH DYNAMIC MEASUREMENTS

## Chapter II frontier

Historical SUCCESS/FAIL has been decomposed into named state transitions.

Established:

- VERIFIED_DIRECT_Q64_RESET: one-page direct Q64 establishes verified residual R0=63.
- PREVERIFY_S64 / MAX_STOCK_BOUNDARY.
- STARTUP_STOCK_SEED.
- SMALL_RESIDUAL_REFILL.
- SLAB_FREE_OBJCG_REFILL1.
- TARGET_STOCK_EVICTION.
- RELEASE_ONLY.

No complete verified target path has produced TARGET_FAIL.

## Age-Decoupling Stage A v2

R1 run 36702673576 is a wiring-only failure:

- duplicate owner-uncharge trigger bind
- no scientific panel executed
- no HOLD exposure executed

Frozen diagnostic:

- analysis/inputs/AGE-DECOUPLING-STAGE-A-R1-WIRING-DIAGNOSTIC-v1.json

The duplicate bind was fixed prospectively.

R2 run 36703139110 completed successfully.

Physical panel:

- FAST x4
- HOLD32 x12
- b63
- requested dwell 22.077060 s
- no automatic Stage B
- no automatic sample expansion

All 16 physical identities reached:

- T=64
- final state SUCCESS
- target result MATCH

Frozen strict classification:

- CANONICAL_SUCCESS = 12
- INSTRUMENTATION_HOLD = 4
- KNOWN_STATE_CHANGE = 0
- UNEXPLAINED_BOUNDARY_DEVIATION = 0
- UNKNOWN_COMPLETE_EMISSION = 0
- TRUE_TARGET_FAIL = 0

By arm:

FAST:
- n=4
- zero-miss canonical=3
- instrumentation hold=1
- T64=4/4

HOLD32:
- n=12
- zero-miss canonical=9
- instrumentation hold=3
- T64=12/12

Stage B trigger=false.

## Realized exposure

Historical exact-b63 calibration:

- tau_fast median = 1.471804 s
- requested dwell = 22.077060 s

R2 zero-miss canonical medians:

- FAST verified -> first Q64 = 1.868684 s
- HOLD32 verified -> first Q64 = 25.001723 s
- realized exposure factor = 13.3793209552819
- observed HOLD checkpoint median = 22.077272 s

Interpretation:

Large wall-clock separation was achieved while measured target touches were fixed.

No complete verified-state hazard or unexplained boundary deviation was captured.

This is bounded no-specimen evidence, not evidence of absence.

## Instrumentation holds

Four identities:

- 0:3 HOLD32 refill_stock missed=1
- 2:3 HOLD32 refill_stock missed=2
- 3:0 HOLD32 refill_stock missed=1
- 3:2 FAST refill_stock missed=6

For all four:

- Q64 probe missed=0
- owner-uncharge probe missed=0
- T=64
- final state SUCCESS
- continuity clean

Do not retroactively promote them.

The only completeness bottleneck was the owner-memcg refill_stock observer.

## Frozen no-event sensitivity

Using only complete zero-miss identities:

- FAST n=3
- HOLD32 n=9
- events=0
- realized F=13.3793

B410 sensitivity replay:

- LOW BF TOUCH/TIME ~= 1.48
- CENTRAL BF TOUCH/TIME ~= 2.59
- HIGH BF TOUCH/TIME ~= 10.08

Interpretation:

- no-event evidence is more compatible with TOUCH than TIME in all frozen sensitivity ranges;
- rare TIME hazards remain weakly constrained;
- high-frequency pure TIME hazards are more strongly disfavored.

This is a design-sensitivity calculation, not an objective model probability.

## New mechanistic target: memcg stock-slot pressure

Linux source at commit 551c722f40809618230001baccf219193e22fc5a has:

- NR_MEMCG_STOCK = 7 per CPU
- per-CPU memcg_stock slots
- refill_stock first reuses a matching memcg slot
- otherwise it uses an empty slot
- if no empty slot exists, refill_stock selects stock->drain_idx, drains that slot, advances drain_idx modulo 7, and installs the new memcg

This gives a deterministic causal direction:

passive wall-clock age
versus
CPU-local stock-slot occupancy/eviction pressure.

Worst-case helper bound after target verification:

- target occupies one of 7 slots
- at most 6 new distinct helper memcgs are needed to fill remaining empty slots
- after the array is full, at most 7 additional distinct helper insertions cycle drain_idx across every slot
- therefore <=13 distinct same-CPU helper insertions are sufficient to force selection of the target slot, absent intervening slot changes

Candidate next arms:

- QUIET
- OFFCPU_SLOT_PRESSURE
- SAMECPU_SLOT_PRESSURE

Preferred target geometry:

1. verify target R0=63;
2. consume exactly 32 measured pages -> expected residual=31;
3. apply intervention with no target touches;
4. continue measurement.

Predictions:

- QUIET: canonical next Q64 T=64
- OFFCPU_SLOT_PRESSURE: canonical T=64 if CPU locality is causal
- SAMECPU_SLOT_PRESSURE: source-grounded target stock drain; after full residual-31 eviction, next target Q64 should occur at T=33, Delta=-31

The experiment must stop helper generation as soon as a source-grounded target drain is observed; cap at 13 distinct helper memcgs.

## Observer lesson for next experiment

Do not remove refill observation entirely.

refill_stock can change per-CPU target stock without an immediate owner page_counter_uncharge, including objcg/socket uncharge paths.

R2 shows full refill event logging is the main observer-load bottleneck.

Investigate a count-only / histogram-style owner refill observer before the full slot-pressure panel:

- dynamically bind to owner_memcg after VERIFY
- aggregate refill sizes/counts without writing every event into the trace ring
- retain kprobe missed-hit receipt
- keep Q64 and owner-uncharge as ordinary event receipts
- preserve UNKNOWN rather than collapsing to FAIL

## Frozen evidence

- analysis/inputs/AGE-DECOUPLING-STAGE-A-R2-PHYSICAL-RESULT-v1.json
- analysis/inputs/AGE-STAGE-A-R2-NO-EVENT-SENSITIVITY-v1.json
- docs/AGE-STAGE-A-R2-BOUNDED-NO-SPECIMEN.md

Raw R2 manifest:

- files=68
- bytes=7,056,729
- content-set SHA-256=e8fc47058103323eb46a3728235b51e4e7869921aed18c104bc9b943df532d9b
- aggregate artifact ID=11090363265
- aggregate digest=sha256:b370602350ab9fa60bba942d5c5b97ef16ef87a153bb13d3e77c7fdc68d5dda9

## Authority

Physical continuation remains authorized by the user.

As of 2026-09-30, bounded local execution through the Local MCP Gateway / Local Desktop Commander path is explicitly authorized for this research continuation.

No paid larger runner.
No paid-resource expansion.
No Remote Desktop Commander.
No automatic sample expansion.
No reliability certification.

Do not create the hosted launch trigger for TX-CONSUME-STOCK-RET-PILOT-v1 while the LDC-local one-identity path is the active execution plan.


## B419 observer pilot and next bounded intervention

Owner-refill histogram pilot run 36705123852 completed SUCCESS.

Frozen result:

- LOG n=4, valid=4, refill misses=0, owner refill counts=[0,0,0,0]
- HIST n=4, valid=4, refill misses=0
- HIST owner refill counts=[403,1385,682,596]
- histogram Dropped=0 for all HIST identities
- pilot_pass=true

Interpretation:

A soft-disabled tracefs histogram can aggregate owner-memcg refill_stock sizes/counts while ordinary refill event logging is disabled. This establishes observer capability only; it does not prove a lower miss rate than LOG because LOG identities had zero owner refill activity in this small panel.

Frozen evidence:

- analysis/inputs/OWNER-REFILL-HIST-PILOT-R1-RESULT-v1.json
- artifact ID=11091860816
- digest=sha256:24fe08ecedf10dcd569515ba98fff2e640319c3b7937c2c9022068e0cf3daaa2

Source derivation:

- docs/MATH-028-CPU-LOCAL-MEMCG-STOCK-SLOT-PRESSURE.md
- NR_MEMCG_STOCK=7 per CPU
- <=13 distinct same-CPU helper insertions are a worst-case bound to force selection of the target slot, absent intervening slot changes

Frozen next pilot:

- specs/TX-SAMECPU-STOCK-SLOT-PRESSURE-PILOT-v1.json
- four identities only
- VERIFY target R0=63
- consume 32 -> expected residual31
- no further target touches during pressure
- create distinct helper memcgs on target stock CPU with AllowedCPUs restricted from unit creation
- require each helper insertion to be physically realized by helper direct-Q64 evidence unless target drain occurs earlier
- stop helper generation immediately when target-owner drain is observed
- cap=13
- keep helpers alive through target diagnostic touch
- predicted clean fingerprint: target drain31 followed by immediate owner Q64 at T=33 / Delta=-31

Do not run the full QUIET/OFFCPU/SAMECPU panel until this four-identity causal pilot passes.


## Same-CPU slot-pressure R1

Run 36714755845 executed all four physical identities.

Frozen strict result:

- PRESSURE_CONFOUNDED_BY_OWNER_REFILL=3
- INSTRUMENTATION_HOLD=1
- pilot_pass=false
- zero-miss target eviction count=3
- frozen fingerprint_match_count=0

Do not rewrite this result.

Direct physical receipts common to all 4 identities:

- target residual before pressure=31
- target-owner stock drain observed=4/4
- drain size=[31] in every identity
- first post-pressure target touch emitted owner Q64=4/4
- physical boundary fingerprint corresponds to T=33 / Delta=-31
- helpers started before target drain by block: 2,4,8,5
- all drains occurred below the <=13 source-derived cap
- unknown emission count=0 in pressure windows

Block1 had refill kprobe missed=2; Q64 and owner-uncharge missed=0.
Blocks0/2/3 had zero critical misses.

Frozen evidence:

- analysis/inputs/SAMECPU-STOCK-SLOT-PRESSURE-R1-PHYSICAL-RESULT-v1.json
- raw files=59
- bytes=783,268
- content-set SHA-256=517b6cd372d9176e93f5f20196f85f3a43a961e3b58a6e7f1fa30031a810a9b6
- aggregate artifact ID=11095239363
- digest=sha256:47270f4f6fb337a347875f395f907124b806525aa81c434ebc5f373d8899a374

## Histogram scope bug

R1 owner-refill contamination labels are not scientifically usable.

The soft-disabled histogram implementation set an ordinary event filter:

memcg == owner_memcg

but attached an unfiltered histogram trigger:

hist:keys=nr_pages

Linux histogram-trigger syntax has its own explicit:

if <filter>

clause.

Empirically, R1 histogram hit totals nearly matched the global refill kprobe hit totals, showing the histogram was effectively aggregating broad refill activity rather than owner-only activity.

Prospective fix:

hist:keys=nr_pages if memcg == <owner_memcg>

The direct owner drain31 receipts and immediate target-Q64 receipts are ordinary event observations and remain valid. Only owner-refill contamination status is unresolved in R1.

Commits:

- 0f75c0f... inline histogram owner filter
- 35a3a92... regression test for histogram trigger filter

Next action:

- wait for fix CI
- rerun the identical four-identity frozen pilot as R2
- do not launch the full QUIET/OFFCPU/SAMECPU panel until a clean R2 specimen establishes drain31 -> T33 without owner-refill contamination and with zero critical misses


## B420 Same-CPU slot-pressure R2 frozen result

Run 36715482390 completed all four identities and is frozen at:

- analysis/inputs/SAMECPU-STOCK-SLOT-PRESSURE-R2-PHYSICAL-RESULT-v1.json

Frozen result:

- workflow conclusion=success
- trial_count=4
- pilot_pass=true
- EVICTION_FINGERPRINT_MATCH=1
- SLOT_EVICTION_BOUND_VIOLATION_CANDIDATE=2
- TARGET_DRAIN_SIZE_MISMATCH=1
- zero-miss target eviction count=2
- clean fingerprint trial=3:0

Clean trial 3:0:

- verified residual before pressure=31
- same-CPU helper pressure
- helpers_started=3
- target drain=[31]
- owner refill delta=0
- histogram dropped=0
- critical probe misses=0
- pressure unknown emission count=0
- first post-pressure target touch emitted direct owner Q64
- T=33
- Delta=-31

This is the clean mechanistic fingerprint supporting same-CPU stock-slot pressure -> target stock eviction.

The frozen result also preserves anomalies instead of rewriting them:

- block1 exposed a one-to-many drain/uncharge pairing bug; prospective pairing fix exists but historical classification stays frozen.
- block0 reached the helper cap without a classified target drain, but helper insertion identity was not strong enough to establish a real violation of the <=13 distinct-leaf source bound.
- block2 reached diagnostic T33 with owner uncharge31 and no classified target drain; this is the direct motivation for observing successful consume_stock returns.

Do not launch the full QUIET/OFFCPU/SAMECPU panel yet.

## B421 consume_stock return observer / LDC boundary

The consume_stock observer implementation is already ready on the pre-B421 baseline a6434626c087a0819bef5c33596e9803c8d166f7:

- specs/TX-CONSUME-STOCK-RET-PILOT-v1.json
- src/finite_ram_lab/consume_stock_ret_pilot.py
- consume_stock return parser and semantics tests
- .github/workflows/consume-stock-ret-pilot.yml
- prior CI PASS

The physical consume_stock pilot has NOT run.

Local MCP Gateway live checks on 2026-09-30 established:

- research candidate lane READY
- mode=INTERVENE
- BOUNDED_PROCESS granted
- network=false
- canonical_write=false
- promotion=false
- Remote Desktop Commander=false
- candidate.run candidate_selftest SUCCESS with retry_count=0 and MVCA_CANDIDATE_PROCESS_OK

The active generic candidate process capsule does not expose host /sys/kernel/tracing and only activates bounded test/selftest templates. Therefore it cannot produce a valid physical tracefs/kprobe observer-capability specimen.

This is a tool-surface capability gap, not a scientific negative result.

Frozen boundary/next-action contract:

- docs/B421-CONSUME-STOCK-RET-LDC-HOST-ACTION-BOUNDARY.md
- action id: finite_ram.consume_stock_ret_observer_pilot_v1
- local machine only
- exact block 0 / one identity
- fixed server-side command and experiment identities
- no raw model-supplied command
- no network
- no paid resource
- no retry
- no automatic scale expansion
- fail closed before trace mutation if privilege/probe/environment preflight is incomplete

Current disposition:

- experiment code ready = PASS
- parser/tests = PASS
- LDC bounded process plane = PASS
- host tracefs surface = NOT EXPOSED
- physical pilot dispatch = NOT DISPATCHED
- scientific consume_stock result = NONE

Next atomic bounce:

1. implement and qualify finite_ram.consume_stock_ret_observer_pilot_v1 in the Local MCP Gateway;
2. launch exactly one block-0 identity;
3. freeze the receipt;
4. expand to the original four identities only if the one-identity specimen is complete.


## B422 ambient stock catcher v1

Research direction now has two complementary modes:

- active causal falsifier: same-CPU slot pressure;
- low-disturbance ambient catcher: verified canary + passive host activity + final boundary readback.

Frozen files:

- specs/TX-AMBIENT-STOCK-CATCHER-v1.json
- src/finite_ram_lab/ambient_stock_catcher.py
- tests/test_ambient_stock_catcher.py
- docs/B422-AMBIENT-STOCK-CATCHER-v1.md

B422 does not launch a physical experiment.

Canary geometry:

- VERIFY R0=63;
- exactly 32 measured target touches;
- expected residual=31;
- zero target touches during ambient exposure;
- no helper memcgs;
- no synthetic pressure;
- final bounded Q64 boundary chase.

Default first physical exposure:

- one canary;
- 60 seconds;
- hard v1 ambient maximum=1800 seconds;
- private tracefs instance;
- owner-filtered or count-only core observers;
- no long-window ordinary drain_stock requirement.

Classifier promotion is deliberately conservative.

Direct slot-eviction fingerprint requires:

- isolated attributed drain d;
- matching owner uncharge d;
- 0<d<=31;
- final T=64-d.

Direct hidden-consumption fingerprint requires:

- isolated successful owner consume c;
- 0<c<=31;
- final T=64-c.

All complete mismatches remain non-promoted, including UNKNOWN_COMPLETE.

During authoring, a deterministic 100,000-case software fuzz pass completed with no out-of-domain classification and no exact-mechanism promotion outside the two exact direct fingerprint classes. This is classifier validation only, not physical evidence.

Next atomic bounce:

1. implement the bounded ambient session runner around the frozen classifier;
2. preserve the low-rate observer design;
3. run software tests only;
4. then launch one 10-minute local LDC session only after the runner/action surface is qualified.


## B423 source-neutral receipt reducer

The catcher architecture is now split into:

- capture backend;
- JSONL receipt stream;
- deterministic reducer;
- conservative classifier.

Frozen files:

- src/finite_ram_lab/ambient_stock_log_reducer.py
- tests/test_ambient_stock_log_reducer.py
- docs/B423-AMBIENT-CATCHER-RECEIPT-REDUCER.md

Reducer fail-closed rules:

- unknown record type -> structural error -> OBSERVATION_HOLD;
- duplicate singleton/coverage semantics -> structural error -> OBSERVATION_HOLD;
- session ID mismatch -> structural error -> OBSERVATION_HOLD;
- missing required consume/refill/uncharge/q64 coverage -> INSTRUMENTATION_HOLD;
- direct drain fingerprint additionally requires explicit drain coverage miss=0.

Synthetic replay semantics now include:

- T64 stable residual;
- consume31 -> T33 direct hidden-consumption fingerprint;
- drain31 + matching owner-uncharge31 + drain coverage0 -> T33 direct slot-eviction fingerprint;
- R2-block2-shaped owner-uncharge31 + T33 with no classified drain/consume/refill -> UNATTRIBUTED_OWNER_UNCHARGE.

No physical session, daemon, system service, or persistent probe was launched by B423.

Next atomic bounce:

Implement one ephemeral capture backend using a private tracefs instance and the frozen JSONL receipt schema. First live run remains one canary, 60 seconds, no synthetic pressure.


## B424 count-only ambient tracefs backend

Frozen files:

- src/finite_ram_lab/ambient_stock_tracefs_backend.py
- tests/test_ambient_stock_tracefs_backend.py
- docs/B424-COUNT-ONLY-AMBIENT-TRACEFS-BACKEND.md

Long-window observer policy:

- owner refill -> histogram only;
- successful owner consume_stock -> histogram only;
- owner page_counter_uncharge -> histogram only;
- owner Q64 -> filtered ordinary event.

The histogram triggers include their own owner filter clauses. Ordinary event filters alone are not relied upon.

Histogram receipts preserve:

- event count;
- weighted total pages;
- bucket distribution;
- Dropped count.

Malformed histogram Totals are rejected.

Long-window drain_stock event logging remains disabled by default in v1 because it cannot be directly owner-memcg filtered and would add unnecessary global event volume. Direct drain attribution remains a separately qualified optional observer.

B424 also corrected the B423 reducer to accept multiple histogram receipts per session and sum Dropped counts.

No host probe was armed and no physical ambient session ran in B424.

Next atomic bounce:

Implement the one-canary ephemeral session orchestrator:

1. VERIFY R0=63;
2. consume exactly 32 measured target touches;
3. arm count-only owner observers;
4. ambient window;
5. freeze histogram and kprobe coverage receipts;
6. bounded final Q64 chase;
7. emit JSONL;
8. reduce/classify;
9. cleanup and exit.

First live session remains one canary / 60 seconds / no synthetic pressure. 600 seconds is a later separately qualified target.


## B425 ephemeral one-canary ambient session orchestrator

Frozen files:

- src/finite_ram_lab/ambient_stock_session.py
- tests/test_ambient_stock_session.py
- docs/B425-EPHEMERAL-AMBIENT-SESSION-ORCHESTRATOR.md

The bounded session now composes the full scientific path:

- fresh verified epoch;
- exact R0=63;
- exactly 32 measured target touches;
- require residual31;
- switch qualified refill/consume/uncharge probes to count-only owner histograms;
- zero synthetic pressure and zero helper memcgs;
- 60-second synchronous ambient exposure;
- measure canary quiescence from worker touch counter, worker error, VmPTE, and CPU before/after;
- freeze ambient histograms before target touches resume;
- owner-Q64-only bounded final chase;
- emit source-neutral JSONL receipts;
- deterministic reduction and conservative classification;
- cleanup and exit.

The first synchronous LDC exposure is 60 seconds because the current bounded process surface is roughly two minutes. 600 seconds remains a separate later qualification target, not the first dispatch.

B425 also adds AMBIENT_Q64_RESET. Any owner Q64 during the zero-target-touch ambient interval blocks simple final-boundary arithmetic, because the canary state crossed a reset/charge boundary before the final diagnostic.

No physical ambient session has run.
No persistent daemon, service, or probe has been installed.

Next atomic bounce:

1. add one fixed zero-argument Local MCP Gateway action for the exact B425 orchestrator;
2. pin the finite-ram experiment source bytes;
3. qualify the action with local unit tests while preserving unrelated dirty LDC work;
4. publish only the selected finite-ram gateway files to an isolated mvca-hq research branch;
5. only after qualification, dispatch one physical 60-second canary session.


## B426 Live-State Frontier Formal Model v0.1

A new independent theoretical/software track is frozen on branch:

- research/live-state-frontier-b426

Frozen files:

- specs/TX-LIVE-STATE-FRONTIER-v0.1.json
- src/finite_ram_lab/live_state_frontier.py
- tests/test_live_state_frontier.py
- docs/B426-LIVE-STATE-FRONTIER-FORMAL-MODEL-v0.1.md

Core model:

- optimize the live-state frontier rather than RAM alone;
- objective vector=(peak live bytes, byte-seconds, memory traffic, compute/recompute, latency, error);
- rewrite the state graph before schedule/placement/lifetime optimization;
- release is fail-closed.

Safe release modes:

- REDUCE_AND_RELEASE only with an explicit smaller future-sufficient summary;
- DROP_REMATERIALIZE only with explicit recomputability;
- otherwise RETAIN_OR_MOVE.

The model maps Ozaki I/II, EmuGEMM, FlashAttention, PagedAttention, Checkmate/DTR, FlexGen, CUDA/ROCm managed memory, and recent Strata residency/lifetime techniques into six moves:

- COMPRESS
- REDUCE
- REMATERIALIZE
- MOVE
- SHARE
- REORDER

Isolated software validation during authoring:

- 11 unit tests PASS;
- deterministic 20,000-case capacity fuzz: no greedy capacity violation;
- deterministic 2,000-case small exact-vs-greedy fuzz: exact placement was never worse than greedy.

Claim ceiling remains SOFTWARE_MODEL_ONLY.

No physical RAM/VRAM experiment ran.
No B425 ambient canary ran.
No persistent probe/service was installed.
No paid resource was used.

New hypotheses:

- H426-1 rewrite-before-placement can reduce peak/byte-seconds when transformation overhead does not dominate;
- H426-2 marginal value of freed memory rises sharply near the effective-capacity cliff;
- H426-3 phase-dependent state value can make phase-aware residency superior to a globally fixed hot set.

Next bounded bounce B427:

1. encode Ozaki I, Ozaki II, FlashAttention, and Strata as common model inputs;
2. compute symbolic/model deltas in (P,A,Q,C,T,epsilon);
3. preserve unknown parameters rather than inventing hardware measurements;
4. keep this track independent from the pending B425 physical ambient catcher.


## B427 common live-state exemplars

Frozen branch:

- research/live-state-exemplars-b427

Frozen files:

- src/finite_ram_lab/live_state_exemplars.py
- tests/test_live_state_exemplars.py
- specs/LIVE-STATE-EXEMPLARS-v0.1.json
- docs/B427-COMMON-LIVE-STATE-EXEMPLARS.md

The B426 model now distinguishes:

- logical frontier: information future computation still requires;
- physical frontier: encoded/replicated/fragmented/runtime-reserved bytes;
- placement/lifetime frontier: where and how long physical state remains resident.

Mapped exemplars:

- Ozaki I -> wider materialized precision frontier;
- Ozaki II -> REDUCE + REORDER with streamed residues;
- EmuGEMM -> fusion / traffic reduction;
- FlashAttention -> tiled exact state and avoided N^2 score materialization;
- PagedAttention -> SHARE/MOVE reducing fragmentation/duplication;
- Checkmate/DTR -> REMATERIALIZE;
- FlexGen -> MOVE + COMPRESS;
- Strata -> mixed COMPRESS/MOVE/SHARE/REORDER and lifetime control.

Software validation during authoring:

- 9 unit tests PASS;
- deterministic 10,000-case randomized Ozaki invariant pass;
- no physical benchmark;
- no B425 ambient canary;
- no paid resources.

Key structural invariant:

For fixed simultaneous residue-pair count r, the B427 streaming Ozaki-II peak model is independent of total modulus count s, while compute count grows linearly with s. In the simplified materialized Ozaki-I model, peak grows linearly with slice count k and GEMM count grows as k(k+1)/2.

New next action B428:

Build a frontier compiler over annotated state DAGs to emit logical/physical peak, byte-seconds, safe-release opportunities, and bounded placement decisions. Feed identical compiler semantics to Ozaki-I, Ozaki-II, FlashAttention, and a minimal Strata phase trace.


## B428 frontier compiler v0.1

Frozen branch:

- research/frontier-compiler-b428

Frozen files:

- src/finite_ram_lab/frontier_compiler.py
- tests/test_frontier_compiler.py
- analysis/inputs/B428-NORMALIZED-STRUCTURAL-TRACES-v0.1.json
- docs/B428-FRONTIER-COMPILER-v0.1.md

The compiler consumes annotated state intervals and emits:

- logical peak bytes;
- physical peak bytes;
- logical byte-seconds;
- physical byte-seconds;
- peak windows;
- fail-closed safe release candidates;
- deduplication savings;
- capacity-cliff ratio.

Physical state accounts separately for:

- encoded bytes;
- replicas;
- per-replica metadata;
- fragmentation;
- workspace.

Isolated software validation:

- 7 unit tests PASS;
- deterministic 20,000-case randomized interval sweep;
- compiler peak outputs matched independent brute-force segment calculations in all randomized cases.

Normalized structural Ozaki example only:

- materialized Ozaki-I trace: peak=17 normalized state units, exposure=136 unit-seconds;
- streaming Ozaki-II trace: peak=3 units, exposure=24 unit-seconds.

These are not physical memory or performance ratios. They isolate liveness geometry under equal normalized state sizes and frozen schedule assumptions.

No B425 ambient canary ran.
No physical GPU/CPU benchmark ran.
No paid resource was used.

Next B429:

Translate one real implementation source into TraceState records, starting with Ozaki Scheme II / GEMMul8 if source structure is sufficiently visible. Preserve unknown sizes/timings symbolically rather than inventing values.


## B429 GEMMul8 source-backed live-state trace

Frozen branch:

- research/gemmul8-source-trace-b429

Upstream source pin:

- RIKEN-RCCS/GEMMul8@603b52363715796a0af5e4aa1ed8d386349b4251

Frozen files:

- src/finite_ram_lab/gemmul8_source_trace.py
- tests/test_gemmul8_source_trace.py
- analysis/inputs/B429-GEMMUL8-SOURCE-BACKED-TRACE-v0.1.json
- docs/B429-GEMMUL8-SOURCE-BACKED-LIVE-STATE-TRACE.md

Key correction:

The B428 one-residue-pair trace is an algorithmic streaming extreme, not a valid description of the current GEMMul8 INT8 real GEMM implementation.

Source-backed current behavior:

- INT8 real num_mat = NUM_MODULI;
- A_lo and B_lo allocate all num_mat planes before the product loop;
- C_hi is temporary by batch/group;
- prior products are retained in reduced C_mid or grouped uint32 CRT state;
- the final modulus/group can remain in high form for fused final CRT;
- grouped CRT is selected for sizeC <= 8192^2;
- CRT groups contain at most four moduli subject to uint32 product bound.

Current GEMMul8 memory-saving mode:

- keeps NUM_MODULI fixed;
- searches smaller m/n/k blocks;
- invokes the same Ozaki-II core repeatedly on those matrix blocks.

This motivates H429-AXIS-TEMPORALIZATION:

Finite-memory optimization can choose which independent computation axis is temporalized. Current GEMMul8 reduces workspace mainly by temporalizing m/n/k, while the modulus/precision axis remains fully represented in A_lo/B_lo inside each core invocation.

Source-derived static example only:

- real INT8 GEMM
- 4096^3
- 8 moduli
- fastmode
- no skip scaling
- WorkA=134,226,175 bytes
- WorkB=134,226,175 bytes
- WorkC=402,653,439 bytes
- total=671,105,789 bytes ~= 640.016 MiB

This is the pinned source workspace formula, not measured VRAM and not total process/GPU memory.

Isolated authoring validation:

- fixed 4096/8192/16384 source-formula vectors PASS;
- deterministic 20,000-case randomized structural sweep PASS.

Claim ceiling: SOURCE_BACKED_STATIC_MODEL.

No physical GPU benchmark ran.
No B425 ambient canary ran.
No paid resource was used.

Next B430:

Model axis temporalization explicitly. Compare legal m/n/k-only blocking with a hypothetical p/modulus blocking axis and hybrid blocking. The p-axis remains hypothetical until an explicit correctness-preserving incremental CRT state is specified.


## B430 axis temporalization v0.1

Frozen branch:

- research/axis-temporalization-b430

Frozen files:

- src/finite_ram_lab/axis_temporalization.py
- tests/test_axis_temporalization.py
- analysis/inputs/B430-AXIS-TEMPORALIZATION-NORMALIZED-v0.1.json
- docs/B430-AXIS-TEMPORALIZATION-v0.1.md

Core refinement:

Finite-memory scheduling must choose not only block size, but which semantically independent axis is allowed to be temporalized.

For a GEMM-like workload the model uses block vector:

- (b_m, b_n, b_k, b_p)

where p is precision/modulus work.

Fail-closed rule:

- b_p < p is rejected unless precision_streaming_proven=true.

This prevents a memory optimizer from inventing an invalid incremental CRT/reconstruction path.

Normalized exact-search example:

- extents m=n=k=16, p=8
- memory limit=100 units
- m/n/k-only best normalized invocation count=768
- with hypothetical proven p-axis streaming, best count=512

This is scheduling geometry only, not GEMMul8 performance.

New distinction:

- PARETO_IMPROVEMENT: modeled peak falls with no increase in modeled Q/C/T/epsilon;
- MEMORY_EXCHANGE: modeled peak falls while at least one other cost rises.

Classic communication lower bounds explain why ordinary tiling/blocking is generally an exchange rather than a free memory reduction.

Isolated authoring validation:

- proof gate PASS;
- fixed examples PASS;
- deterministic 10,000-case randomized feasible-plan sweep PASS.

Claim ceiling: NORMALIZED_OPTIMIZATION_MODEL_ONLY.

No physical benchmark ran.
No B425 ambient canary ran.
No paid resource was used.

Next B431:

Translate an unrelated real implementation, preferably FlashAttention, into the same Live-State Frontier schema and determine whether the model survives without adding ad-hoc state categories.


## B431 FlashAttention source-backed future-state trace

Frozen branch:

- research/flashattention-source-trace-b431

Upstream source pin:

- Dao-AILab/flash-attention@616b0e8abab13b87b01525b3916d5a863ab02ae0

Frozen files:

- src/finite_ram_lab/flashattention_future_state.py
- tests/test_flashattention_future_state.py
- analysis/inputs/B431-FLASHATTENTION-SOURCE-TRACE-v0.1.json
- docs/B431-FLASHATTENTION-SOURCE-BACKED-FUTURE-STATE.md

Source-backed mapping:

- acc_S = ephemeral score tile;
- row_max + row_sum = online softmax statistics;
- acc_O = running weighted output state;
- row_scale rescales prior acc_O when the running max changes;
- after the current score tile is consumed into the running state and V accumulation, the old score tile need not remain live.

Future-Sufficient State for one query row:

- m = running max
- l = sum exp(score-m)
- o = sum exp(score-m) * value
- retained summary phi=(m,l,o)

This summary can be updated exactly with each future KV block and finalizes to:

- O=o/l
- LSE=m+log(l)

Isolated recurrence validation:

- deterministic 10,000 randomized partition cases PASS;
- chunked online result and LSE matched full stable-softmax reference within floating tolerance.

Structural example only:

- tile_m=128
- tile_n=128
- head_dim_v=128
- active score tile=65,536 bytes
- row stats=1,024 bytes
- output accumulator=65,536 bytes
- modeled active frontier=132,096 bytes
- naive 4096x4096 FP32 score matrix=67,108,864 bytes

Do not interpret this as a total-memory ratio; Q/K/V/O, pipeline state, registers/shared memory and concurrency are outside the simple model.

Cross-domain result:

Both Ozaki/CRT and FlashAttention fit:

EPHEMERAL STATE -> FUTURE-SUFFICIENT STATE -> RELEASE

without adding a new semantic category to the B428 compiler schema.

New H431 Semantic Liveness:

An intermediate can become semantically dead before ordinary implementation/reference lifetime ends once every future-relevant effect has been transferred into a proven sufficient summary.

Claim ceiling: SOURCE_BACKED_STRUCTURAL_MODEL.

No physical GPU benchmark ran.
No B425 ambient canary ran.
No paid resource was used.

Next B432:

Use Strata as the complementary test of the physical frontier: representation, placement, sharing, phase residency, and lifetime. If it also fits without changing the core schema, freeze Live-State Frontier taxonomy v0.2.


## B432 Strata physical frontier v0.1

Frozen branch:

- research/strata-physical-frontier-b432

Upstream source pin:

- Niko1221/Strata@9259cad4cfa3543cd3b8decab5962672b968c649
- setup.py observed engine floor: 0.1.31

Frozen files:

- src/finite_ram_lab/strata_physical_frontier.py
- src/finite_ram_lab/tiered_frontier.py
- tests/test_strata_physical_frontier.py
- analysis/inputs/B432-STRATA-PHYSICAL-FRONTIER-v0.1.json
- docs/B432-STRATA-PHYSICAL-FRONTIER-v0.1.md

Source-backed Strata mappings:

- KV INT8/Q4 -> COMPRESS
- KV host/VRAM residency split -> MOVE
- GPU expert subset + RAM/file complement -> MOVE + duplicate avoidance
- one shared host expert arena -> SHARE
- prompt borrowing expert-cache slots -> phase-local REORDER / capacity lending
- multi-GPU session layer carve -> ownership partition
- idle unload -> lifetime contraction / byte-seconds reduction

Important current source facts:

- KV bytes/cell: FP16=2048, INT8=1056, Q4_0=576, K8V4=816
- K8V4 + KV streaming is rejected in current source
- current layer-split SessionState carves QSA/GDN state for the owned layer range instead of whole-model state on every stage
- mapped file size is backing storage, not resident RAM

Structural INT8 KV example only:

- 12 QSA layers
- max_cells=131072
- resident_cells=32768
- full encoded pool if all VRAM=1,660,944,384 B
- resident GPU pool=415,236,096 B
- host authoritative pool=1,660,944,384 B
- VRAM avoided=1,245,708,288 B

This isolates K/V pool bytes only and is not total Strata session memory.

Critical compiler finding:

The B428 semantic taxonomy survives Strata, but flat physical_bytes does not.

VRAM and RAM have independent capacity constraints. B432 therefore adds tier-aware frontier compilation:

- logical peak
- total resident peak
- per-tier peaks
- per-tier byte-seconds
- per-tier capacity ratios

Semantic state is counted once; host/GPU copies are physical placements only. File backing is excluded from resident RAM until page-cache residency is actually observed.

Validation:

- fixed source-backed arithmetic PASS
- fail-closed unsupported KV combination PASS
- complement/borrow/ownership/idle accounting PASS
- deterministic 20,000 randomized tier traces PASS

Claim ceiling: SOURCE_BACKED_STATIC_AND_STRUCTURAL_MODEL.

No physical Strata benchmark ran.
No B425 ambient canary ran.
No paid resource was used.

Next B433:

Freeze Live-State Frontier Taxonomy v0.2 with explicit semantic and physical planes, owner sets, resident tiers, backing tiers, phases, and a controller ordering from semantic-liveness reduction through placement/lifetime.


## B433 Live-State Frontier Taxonomy v0.2

Frozen branch:

- research/live-state-taxonomy-v02-b433

Frozen files:

- src/finite_ram_lab/live_state_taxonomy_v02.py
- tests/test_live_state_taxonomy_v02.py
- specs/LIVE-STATE-FRONTIER-TAXONOMY-v0.2.json
- docs/B433-LIVE-STATE-FRONTIER-TAXONOMY-v0.2.md

v0.2 explicitly separates two planes.

Semantic plane:

- logical state
- future obligation
- future-sufficient summary
- recomputability
- owner set
- semantic live interval

Physical plane:

- representation
- resident tier
- backing tier
- resident bytes
- replica count
- phase
- physical live interval
- per-tier capacity

Fail-closed semantic release:

1. REDUCE only with an explicit smaller future-sufficient summary
2. else REMATERIALIZE only with explicit recomputability
3. else RETAIN

Controller order:

1. SEMANTIC_REDUCTION
2. OWNERSHIP
3. REPRESENTATION
4. TEMPORALIZATION
5. PLACEMENT
6. PHASE_BORROWING
7. LIFETIME

Cross-domain mappings remain inside the same action vocabulary:

- Ozaki II -> REDUCE + REORDER
- FlashAttention -> REDUCE + REORDER
- PagedAttention -> SHARE + MOVE
- Checkmate/DTR -> REMATERIALIZE
- FlexGen -> COMPRESS + MOVE
- current GEMMul8 memory-saving -> REORDER
- Strata KV streaming -> COMPRESS + MOVE
- Strata expert residency -> SHARE + MOVE
- Strata prompt cache lending -> BORROW
- Strata idle unload -> UNLOAD

New frozen invariants:

- semantic owner count is not physical replica count
- backing size is not resident memory
- tier capacities are a vector, not one flat byte pool
- unknown recoverability does not authorize release
- phase borrowing can change use of capacity without raising allocation peak
- idle unload primarily reduces byte-seconds, not loaded peak

Validation:

- cross-domain unknown action count = 0
- deterministic 20,000 randomized action-order cases PASS

Claim ceiling: FORMAL_TAXONOMY_AND_SOURCE_BACKED_CROSS_DOMAIN_MODEL.

No physical benchmark ran.
No B425 ambient canary ran.
No paid resource was used.

Next B434:

Build a bounded controller that enumerates safe plans, rejects tier-capacity violations, preserves numerical/error dimensions, and emits a Pareto frontier. Solve tiny cases exactly and use them as an oracle for later heuristics.


## B434 exact bounded frontier controller v0.1

Frozen branch:

- research/bounded-frontier-controller-b434

Frozen files:

- src/finite_ram_lab/bounded_frontier_controller.py
- tests/test_bounded_frontier_controller.py
- analysis/inputs/B434-BOUNDED-CONTROLLER-NORMALIZED-v0.1.json
- docs/B434-EXACT-BOUNDED-FRONTIER-CONTROLLER-v0.1.md

Controller order inside a bounded optimization window:

1. enumerate one option per semantic state
2. reject unproven semantic release
3. reject unproven owner merge
4. reject non-zero error without an explicit bound
5. aggregate resident bytes per tier
6. reject per-tier capacity violations
7. compute full objective vector
8. remove Pareto-dominated plans

Objective vector:

- peak bytes per tier
- byte-seconds per tier
- traffic
- compute/recompute
- latency
- error

No scalar weighting is imposed by the exact controller.

Normalized example:

- VRAM capacity=6
- RAM capacity=16
- resident option uses VRAM=8 and is infeasible
- offload option uses VRAM=2/RAM=8 and pays traffic=20, latency=3
- compressed option uses VRAM=4 and pays bounded error=0.1
- exact frontier keeps both offload and compression because neither dominates the other

Validation:

- unsafe release gate PASS
- unsafe share gate PASS
- unknown lossy-error gate PASS
- per-tier capacity gate PASS
- dominated-plan removal PASS
- memory-exchange frontier retention PASS
- proven summary release admitted PASS
- deterministic 10,000 randomized Pareto cases: no dominated point survived

Claim ceiling: EXACT_TINY_WINDOW_MODEL_ONLY.

No physical benchmark ran.
No B425 ambient canary ran.
No paid resource was used.

Next B435:

Build a cheap pressure-aware heuristic and compare it against the B434 exact oracle on small random problems. Measure feasibility, dominated-output rate, and regret/distance from the exact Pareto set, especially near independent VRAM/RAM capacity cliffs.


## B435 Pareto beam controller v0.1

Frozen branch:

- research/pareto-beam-controller-b435

Frozen files:

- src/finite_ram_lab/pareto_beam_controller.py
- tests/test_pareto_beam_controller.py
- analysis/inputs/B435-PARETO-BEAM-EVAL-v0.1.json
- docs/B435-PARETO-BEAM-CONTROLLER-v0.1.md

Algorithm:

1. expand each partial plan with safe options only
2. reject per-tier capacity violations
3. remove dominated partial prefixes (lossless at a fixed prefix depth)
4. if the partial frontier exceeds beam width:
   - preserve one extreme per objective
   - fill remaining slots using a pressure-aware score
5. return the Pareto frontier of the retained beam

The pressure score includes:

- squared per-tier capacity ratio
- tier byte-seconds
- traffic
- compute
- latency
- bounded error

It is used only for beam truncation, not to choose a final winner.

Deterministic all-safe synthetic corpus:

- seed 435300
- 1,000 generated instances
- 695 with non-empty exact frontier
- 11,408 exact frontier objective vectors total

Recovery:

- beam 8: 35.68% exact-point coverage; 0.221% returned points dominated by exact
- beam 16: 56.28%; 0.0156% dominated
- beam 32: 76.02%; 0.0346% dominated
- beam 64: 91.34%; 0% dominated
- beam 128: 98.34%; 0% dominated
- beam 256: 99.81%; 0% dominated

At beam>=64 on this corpus the approximation primarily loses coverage rather than returning dominated plans.

Additional validation:

- large beam equals exact on 1,000 deterministic small random problems PASS
- unsafe-only group returns no plan PASS
- independent tier capacity filtering PASS
- exact self-recovery coverage=1, domination gap=0 PASS
- 5,000 width-64 random outputs feasible and internally non-dominated PASS

Claim ceiling: SYNTHETIC_HEURISTIC_VS_EXACT_ORACLE.

No physical benchmark ran.
No B425 ambient canary ran.
No paid resource was used.

Next B436:

Assemble one mixed source-backed scenario from Strata KV/expert residency plus one proven semantic-reduction option and one temporalization option. Compare exact and beam controllers near RAM/VRAM capacity cliffs.


## B436 mixed capacity-cliff scenario v0.1

Frozen branch:

- research/mixed-capacity-cliff-b436

Frozen files:

- src/finite_ram_lab/mixed_capacity_cliff.py
- tests/test_mixed_capacity_cliff.py
- analysis/inputs/B436-MIXED-CAPACITY-CLIFF-EVAL-v0.1.json
- docs/B436-MIXED-CAPACITY-CLIFF-SCENARIO-v0.1.md

Scenario composition:

- source-backed Strata INT8 KV pool sizes from B432
- source-anchored Strata expert placement proxy
- source-observed prompt cache lending size proxy
- normalized FlashAttention-pattern future-sufficient reduction
- normalized GEMMul8-pattern temporalization
- normalized idle-unload byte-second exchange

This is not one executable application. It is a mixed controller stress scenario.

Main exact capacity result:

- with RAM=8192 MiB, minimum VRAM=10544 MiB
- with RAM=9775 MiB, minimum VRAM remains 10544 MiB
- with RAM=9776 MiB, streamed INT8 KV becomes feasible and minimum VRAM drops to 9356 MiB

The 1188-MiB VRAM discontinuity exactly matches the B432 INT8 KV resident reduction:

1584 - 396 = 1188 MiB.

Thus B436 demonstrates a combinatorial policy cliff: one tier crossing a minimum requirement can activate a legal MOVE plan and sharply reduce another tier's minimum requirement.

Capacity grid:

- 15 VRAM capacities x 11 RAM capacities = 165 points
- 150 points with non-empty exact frontier
- 3506 exact frontier objective vectors total

Beam recovery on those 150 points:

- width 16: mean coverage 77.48%, min 20%, exact recovery 82/150, dominated fraction 0
- width 32: mean coverage 91.27%, min 40%, exact recovery 114/150, dominated fraction 0
- width 64: mean coverage 99.01%, min 80%, exact recovery 141/150, dominated fraction 0
- width 96: exact coverage 100%, exact recovery 150/150, dominated fraction 0

New H436 Capacity-Activated Strategy:

The marginal value of added capacity can be discontinuous when it crosses the minimum requirement of a previously infeasible transformation.

Distinguish:

- combinatorial activation cliffs: plan feasibility changes discretely
- runtime pressure cliffs: performance changes sharply near a tier limit

Claim ceiling: SOURCE_ANCHORED_MIXED_NORMALIZED_CONTROLLER_SCENARIO.

No physical benchmark ran.
No B425 ambient canary ran.
No paid resource was used.

Next B437:

Represent every safe plan by its per-tier capacity requirement vector and compute the minimal antichain (capacity activation frontier). For B436 it should recover the two non-dominated minimum vectors (RAM,VRAM)=(8192,10544) and (9776,9356).


## B437 capacity activation frontier v0.1

Frozen branch:

- research/capacity-activation-frontier-b437

Frozen files:

- src/finite_ram_lab/capacity_activation_frontier.py
- tests/test_capacity_activation_frontier.py
- analysis/inputs/B437-CAPACITY-ACTIVATION-FRONTIER-v0.1.json
- docs/B437-CAPACITY-ACTIVATION-FRONTIER-v0.1.md

Core formalization:

Each safe plan p has a tier-capacity requirement vector r(p).

The plan is feasible exactly when:

C >= r(p)

componentwise.

Therefore plan feasibility is an upper orthant in capacity space, and scenario feasibility is a union of upper orthants.

The minimal safe capacity boundary is the componentwise antichain of plan requirement vectors.

For the B436 mixed scenario this antichain is exactly:

- (RAM,VRAM)=(8192,10544) MiB
- (RAM,VRAM)=(9776,9356) MiB

No single minimum-memory scalar exists because neither point dominates the other.

Option activation frontiers were also frozen, including:

- full INT8 KV: (8192,10544)
- streamed INT8 KV: (9776,9356)
- materialized semantic state: (8192,11312), (9776,10124)
- future-sufficient summary: (8192,10544), (9776,9356)
- wide temporalization: (8192,12080), (9776,10892)
- blocked temporalization: (8192,10544), (9776,9356)
- dedicated prompt scratch: (8192,15275), (9776,14087)
- borrowed expert-cache capacity: (8192,10544), (9776,9356)

New distinction:

- combinatorial activation cliff: a plan becomes legal when a capacity threshold is crossed
- runtime pressure cliff: an already-legal plan suffers reclaim/paging/migration/latency near capacity

New H437 Activation/Pressure Duality:

The value of added memory capacity combines discrete plan activation with runtime pressure relief. These must be measured separately before synthesis.

Validation:

- fixed B436 activation antichain PASS
- option-specific activation frontiers PASS
- deterministic 10,000 randomized capacity-membership checks PASS

Claim ceiling: FORMAL_CAPACITY_GEOMETRY_ON_B436_SCENARIO.

No physical benchmark ran.
No B425 ambient canary ran.
No paid resource was used.

Next B438:

Build a capacity phase diagram over RAM/VRAM cells, label which transformation families appear on the exact Pareto frontier, and derive a transition graph between strategy regimes.


## B438 capacity phase diagram v0.1

Frozen branch:

- research/capacity-phase-diagram-b438

Frozen files:

- src/finite_ram_lab/capacity_phase_diagram.py
- tests/test_capacity_phase_diagram.py
- analysis/inputs/B438-CAPACITY-PHASE-DIAGRAM-v0.1.json
- docs/B438-CAPACITY-PHASE-DIAGRAM-v0.1.md

Capacity Monotonicity Theorem:

For componentwise capacity expansion C <= C_prime, if:

- plan resource requirements are capacity-independent
- every constrained resource coordinate is included as a minimized Pareto objective
- all other compared objective coordinates are capacity-independent

then:

Pareto(C) is a subset of Pareto(C_prime).

Proof sketch:

If a new plan q under C_prime dominated an old Pareto plan p, then dominance on every resource coordinate implies r(q) <= r(p) <= C. Therefore q was already feasible under C and would already have dominated p, contradiction.

B436 grid result:

- 165 total capacity cells
- 19 non-empty strategy regimes
- 102 neighboring cells with changed exact-frontier signatures
- 0 transitions with removed visible options

Thus the static phase diagram is a monotone additive strategy DAG: extra capacity adds tradeoff arms rather than replacing old ones.

Examples of newly visible arms as capacity grows:

- streamed KV after RAM expansion
- materialized semantic state after VRAM expansion
- full-VRAM KV
- wide temporalization
- dedicated prompt scratch
- richer expert-residency placements

Important caveat:

The theorem is static. It can fail for measured runtime when latency/traffic/error depends on capacity through reclaim, migration, cache behavior, page residency, or other pressure effects.

New H438 Monotonicity Violation as Runtime Signal:

If only capacity increases but a previously Pareto-relevant strategy disappears from the measured frontier, at least one non-memory objective is capacity-dependent, effective plan semantics changed, or the measurement/classification pipeline changed.

Validation:

- 19 B436 regimes PASS
- 102 changed-neighbor transitions checked
- zero removed-option transitions
- deterministic 5000 randomized static capacity-expansion instances preserve exact frontier inclusion

Claim ceiling: FORMAL_STATIC-COST_FRONTIER_THEOREM_ON_B436_GRID.

No physical benchmark ran.
No B425 ambient canary ran.
No paid resource was used.

Next B439:

Build a static-versus-dynamic frontier comparator that can ingest measured objective vectors at multiple capacities, detect monotonicity violations, and identify which objective coordinate changed enough to explain the measured reversal.
