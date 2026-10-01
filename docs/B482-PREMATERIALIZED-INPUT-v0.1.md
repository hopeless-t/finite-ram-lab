# B482 — Pre-materialized Input Isolation v0.1

Status: **CONTENT VS GENERATION-HISTORY ISOLATION**.

## 1. Why this experiment exists

B481 resolved a q2 seed-sensitive total HWM effect.

However the measured child itself still created its input vectors with the seeded
NumPy RNG before running the numerical kernel.

Therefore "seed effect" could still mean:

- numerical input **content** changes later memory behavior;
- RNG/input-generation history changes allocator/process state;
- both.

B482 removes RNG generation from the measured child.

## 2. Pre-materialization

For content seeds 474 and 476, the runner-block parent process generates the
deterministic input vectors and writes them as fixed-size raw int64 files.

The measured child receives only:

- a left-vector file path;
- a right-vector file path;
- the q value.

The child never instantiates the RNG.

Both content variants have exactly the same dtype, length, and file size.

## 3. Child phases

The fresh child records:

1. pre-load HWM;
2. post-load HWM after `np.fromfile`;
3. post-work HWM.

Derived:

```text
load_growth = post_load - pre_load
work_growth = post_work - post_load
total_growth = post_work - pre_load
```

with:

```text
total_growth = load_growth + work_growth
```

as a hard identity.

## 4. Runner-block design

Eight independent hosted-runner blocks.

Per block:

- q2 content474 x2
- q2 content476 x2
- q4 content474 x2
- q4 content476 x2

with order + reverse order.

Total:

`64 fresh measured child processes`.

Input generation occurs only in the parent and outside child HWM measurement.

## 5. Confirmatory hypotheses

From B481, the independent B482 hypotheses are directional:

- q2 content476 has lower work growth;
- q2 content476 has lower total growth;
- q4 content476 has lower work growth;
- q4 content476 has lower total growth.

Familywise alpha 0.05 with Holm step-down across the four tests.

Load-phase differences are retained as diagnostics but are not part of the
confirmatory family.

## 6. Interpretation

### PREMATERIALIZED_CONTENT_EFFECT_REPLICATED

Both work and total effects replicate after removing RNG generation from the
measured process.

This supports content-sensitive execution behavior.

### CONTENT_EFFECT_NOT_REPLICATED

The prior signal collapses once input generation history is removed.

This points away from content itself and toward process-history / measurement
semantics.

## 7. Claim ceiling

**GITHUB_HOSTED_PREMATERIALIZED_CONTENT_ISOLATION**

A replicated content effect does not yet identify which numerical primitive or
allocator event is content-sensitive.

## 8. Next

If q2 replicates, B483 should isolate individual numerical stages such as
residue production versus CRT fold using fixed pre-materialized content.

If it collapses, B483 should focus on RNG/input-generation history and allocator
state rather than workload-conditioned Governor policy.
