# EXP-003 Design Council — High-Headroom Semantic Intervention

> **Status:** COUNCIL CONVERGED / DESIGN MONTE CARLO REQUIRED BEFORE EXPERIMENT FREEZE
> **Scientific evidence:** NONE YET

## Question

Can an existing application semantic action capture part of the HYP-003 / VOI-001 decision headroom under the high-headroom 160–162 MiB pressure regime, while keeping wrong/stale-action harm explicit?

## Why this is not a post-hoc retry of EXP-002

EXP-002 and VAL-003 tested `MADV_PAGEOUT` at 164 MiB and did not establish benefit.

Later independent work changed the scientific state:

- CHAR-002 identified initial fault/touch order as a strong residency determinant;
- HYP-003 independently randomized that historical cue and future semantic demand;
- HYP-003 showed a large same-experiment mismatch cost at 160–162 MiB;
- VOI-001 quantified material idealized headroom in that regime.

Therefore EXP-003 is a new prospectively defined condition and question, not a threshold retune of EXP-002.

The earlier negative 164 MiB evidence remains binding context.

## Pseudo-Council convergence

### Kernel / VM reviewer

Use the shared-VMA substrate from HYP-003:

- one 64 MiB anonymous mapping;
- lower / upper 32 MiB logical regions;
- independent initial fault/touch order;
- independent future HOT position.

This avoids the separate-VMA creation/address confound found in CHAR-002.

### Intervention reviewer

Reuse `MADV_PAGEOUT` as the intervention probe.

Reason:

- ENV-005 found `MADV_COLD` ineffective in this hosted workload;
- ENV-006 established that 16 MiB `MADV_PAGEOUT` preparation can steer later natural reclaim;
- EXP-002 established strong wrong-direction harm but no benefit at 164 MiB.

Do not tune the PAGEOUT range after seeing EXP-003 data.

Freeze the already-tested 16 MiB subrange.

This is a **mechanism probe**, not endorsement of PAGEOUT as architecture.

### Factorial-design reviewer

Candidate frozen factors:

```text
MemoryHigh:
160 / 162 MiB

initial fault order:
lower→upper / upper→lower

future HOT position:
lower / upper

arm:
CORRECT_PAGEOUT / NO_HINT / WRONG_PAGEOUT
```

Thus one complete repeat contains:

```text
2 × 2 × 2 × 3 = 24 cells per runner block
```

Definitions:

- CORRECT_PAGEOUT: prepare 16 MiB of semantic COLD;
- NO_HINT: no advice;
- WRONG_PAGEOUT: prepare 16 MiB of semantic HOT.

The future workload always retouches HOT.

### Information-gap reviewer

The pre-registered benefit comparison must focus on trials where future HOT demand **conflicts** with the historical fault-order cue:

```text
HOT == first-faulted
```

These are the cases where HYP-003 exposed decision headroom.

Aligned trials remain mandatory as a control stratum because they reveal unnecessary-action cost and whether the intervention damages already-good residency.

### Performance reviewer

Keep two different outcomes separate.

#### Mechanism-sensitive primary outcome

HOT retouch latency.

Primary contrast in the naturally misaligned stratum:

```text
CORRECT_PAGEOUT
vs
NO_HINT
```

Use runner-block mean log latency.

A lower CORRECT value means the semantic intervention captured some of the measured residency headroom.

#### End-to-end cost outcome

Measure a broader interval that includes:

- advice-call latency;
- burst work;
- HOT retouch.

This is required for classifying:

- net benefit;
- cost shifting only;
- net harm.

A HOT-retouch improvement alone must not be called net benefit.

### Red-Team reviewer

WRONG_PAGEOUT is mandatory.

Pre-register:

```text
WRONG_PAGEOUT
vs
NO_HINT
```

and

```text
WRONG_PAGEOUT
vs
CORRECT_PAGEOUT
```

for both HOT-retouch and total interval.

The wrong arm is not optional even if CORRECT shows benefit.

EXP-002 demonstrated that wrong semantic preparation can be dramatically harmful.

### Statistics reviewer

Runner remains the top-level replication unit.

Use blocked comparisons; do not treat individual trials as independent top-level replicates.

Primary inference candidate:

- runner-block log-latency contrast in misaligned trials;
- exact sign-flip when block count permits;
- deterministic Monte Carlo sign-flip if block count exceeds the exact enumeration budget;
- runner-cluster bootstrap interval for the geometric mean ratio.

Do not pool 160 and 162 blindly in interpretation; the primary can average the frozen levels, but level-specific estimates must be reported.

### Design-Monte-Carlo reviewer

A design Monte Carlo is required before freezing runner count / repeat count.

Why:

- HYP-003 latency is strongly heavy-tailed;
- EXP-002 showed asymmetric wrong-action harm;
- within-runner repeats and independent runner blocks trade off differently;
- the scientifically interesting effect is a fraction of the HYP-003 perfect-information headroom, not a known fixed effect size.

Candidate designs should compare more independent blocks against more within-block repeats.

At minimum evaluate:

```text
D1: 16 blocks × 1 complete repeat = 384 trials
D2: 24 blocks × 1 complete repeat = 576 trials
D3: 32 blocks × 1 complete repeat = 768 trials
D4: 16 blocks × 2 complete repeats = 768 trials
D5: 24 blocks × 2 complete repeats = 1152 trials
```

### Simulation scenarios

The design study should use empirical block structure rather than invented Gaussian noise.

For CORRECT_PAGEOUT benefit in naturally misaligned trials, simulate capture fractions of the HYP-003 aligned-vs-misaligned log-latency gap:

```text
0%   — null / false-positive calibration
25%  — weak capture
50%  — moderate capture
75%  — strong capture
```

The design should not be chosen only for the 75% scenario.

EXP-002 wrong-action observations may be used as a separate Red-Team stress distribution, but must not be numerically pooled into the HYP-003 benefit model as if they came from the same pressure regime.

### Falsification reviewer

EXP-003 weakens the intervention hypothesis if:

- CORRECT_PAGEOUT does not improve HOT retouch in naturally misaligned trials;
- any HOT-retouch improvement disappears in the total interval;
- CORRECT damages the aligned stratum enough to offset benefit;
- WRONG/stale harm remains large relative to achievable correct-action benefit.

A negative result is valid and should end further PAGEOUT tuning unless new independent evidence changes the question.

## Design-MC input requirement

Before implementing the Monte Carlo, snapshot only the minimum empirical inputs needed:

- HYP-003 runner/trial structure for aligned vs misaligned latency and residency;
- EXP-002 block/trial summaries needed only for PAGEOUT call cost and wrong-arm stress calibration.

Store compact derived inputs plus provenance in GitHub.

Do not make Actions artifacts the sole durable source for the design simulation.

## Authority boundary

This Council authorizes only an EXP-003 **design Monte Carlo**.

It does not authorize the EXP-003 experiment itself and does not revive PAGEOUT as a preferred coordination mechanism.
