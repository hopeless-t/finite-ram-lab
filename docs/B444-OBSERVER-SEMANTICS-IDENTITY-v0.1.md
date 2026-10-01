# B444 — Observer Semantics Are Part of Plan Identity v0.1

Status: **historical cross-study identity audit**. No new physical experiment ran.

## 1. Candidate

A tempting next step after B443 was to combine:

- STRATA-005 MemoryHigh=144 MiB;
- STRATA-004 MemoryHigh=160 MiB;
- STRATA-005 MemoryHigh=176 MiB

into a three-point capacity sweep.

At the experiment-description level this looks attractive because both studies use the same hosted runner family, 64 MiB hot anonymous state, 96 MiB cold file, 4 MiB reads, MemoryMax=320 MiB, and overlapping DONTNEED arms.

B444 rejects that merge.

## 2. Why the merge fails the B443 identity contract

The launch commits do not execute byte-identical measured workload code.

STRATA-004 launch:

- 4d22de0570030c987db3e76416c009e67c58341a

STRATA-005 launch:

- 9f0ed686406a49b42e14d855e3d941970e55c94d

Between them, the shared `strata004_knee_workload.py` acquired a scan `checkpoint_hook`.

STRATA-005 passes a hook that calls:

`recorder.sample("memory.current", ...)`

at scan checkpoints.

STRATA-004 has no equivalent in-scan Recorder hook.

Therefore the measurement observer is inside the measured execution path in STRATA-005 but not STRATA-004.

## 3. Why this is not merely metadata drift

The observer may affect:

- Python execution between reads;
- cgroup memory accounting;
- allocation behavior;
- scan elapsed time;
- exact checkpoint timing.

Even if its perturbation is small, the scientific contract cannot assume it is zero after the fact.

The correct identity relation is therefore:

same application intent != same measured plan identity.

## 4. Frozen decision

Do not merge the 160 MiB STRATA-004 point into the STRATA-005 pair as a B443-qualified dynamic sweep.

Allowed:

- use STRATA-004 as historical/contextual mechanism evidence;
- use its knee bracket as an independent replication line;
- compare transformed intervals qualitatively where the older studies already did so.

Not allowed:

- present 144/160/176 as one stable-plan capacity response curve;
- bootstrap all three points as if observer semantics were constant;
- infer a capacity-dependent objective delta using the 160 point.

## 5. New invariant

**Observer semantics are part of plan identity.**

A dynamic capacity comparison must freeze not only:

- workload/model;
- code path;
- plan parameters;
- runtime;
- cgroup controls;

but also any instrumentation executed inside the measured interval.

This extends B443's stable plan identity requirement.

## 6. Consequence for future experiments

Instrumentation should ideally be:

- identical across every capacity point;
- low-perturbation;
- version-pinned;
- included in the source identity receipt.

If instrumentation must change, the new data belongs to another observation plane unless an explicit equivalence study qualifies the change.

## 7. Result

The attempted three-point merge failed closed before statistical analysis.

This is preferable to creating a smoother capacity curve by silently joining non-identical measurement contracts.

The internally consistent STRATA-005 144/176 MiB pair remains usable and is the next analysis target.
