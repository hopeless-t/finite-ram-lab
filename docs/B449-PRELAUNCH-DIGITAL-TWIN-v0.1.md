# B449 — Clean Dynamic Frontier Prelaunch Digital Twin v0.1

Status: **PRELAUNCH MODEL CHECK ONLY**. No physical run.

## 1. Why a digital twin before launch

B447/B448 produced a qualified study design and implementation.

Before consuming hosted execution budget, B449 asks:

> Under the existing B445 model and the frozen PRIMARY objectives, what frontier topology should the study produce if nothing surprising happens?

This catches a common experimental-design failure: collecting many trials for a frontier question whose answer is structurally predetermined or uninformative.

## 2. Candidate versus reference arms

The buffered arm is retained as a physical reference but excluded from the DONTNEED candidate frontier.

Candidate arms:

- DONTNEED 32
- 48
- 64
- 80
- 96 MiB.

Primary objectives are proxied by:

- peak RAM
- clean ephemeral excess
- MemoryHigh events
- pgscan
- advice calls.

The twin does not include hosted timing.

## 3. Expected frontier

Using:

B_peak = 78.609 MiB

and:

P_peak = min(B_peak + K, H),

the expected candidate Pareto set is the same at all three capacities:

**{32, 48, 96 MiB}.**

### Why 32 survives

It minimizes peak/ephemeral state but uses three advice calls.

### Why 48 survives

It spends more memory than 32 but reduces advice calls from three to two.

### Why 64 is dominated

It has the same modeled advice-call count as 48 but a larger live-state frontier and no better pressure behavior.

### Why 80 is dominated in the PRIMARY proxy

It also has two advice calls, but higher memory and equal-or-worse pressure response than 48.

It remains scientifically important as a clamp-threshold mechanism arm.

### Why 96 survives

It is the one-call DONTNEED arm.

Even when pressured, it trades more memory/reclaim exposure for fewer interventions.

## 4. Expected pressure transitions

### MemoryHigh 144

Expected pressure:

- 80
- 96.

Expected pressure-free:

- 32
- 48
- 64.

### MemoryHigh 160

Expected pressure:

- 96.

Expected pressure-free:

- 32
- 48
- 64
- 80.

### MemoryHigh 176

All tested DONTNEED arms expected pressure-free.

These predictions derive from B445 and are not acceptance criteria.

## 5. Important design consequence

The experiment should **not** be sold as expecting new Pareto arms to appear with more capacity.

Its high-information questions are instead:

1. Does the expected {32,48,96} PRIMARY frontier remain monotone/stable?
2. Do the objective vectors move with capacity as predicted?
3. Does DONTNEED-80 cross from pressured to pressure-free between H144 and H160?
4. Does DONTNEED-96 cross between H160 and H176?
5. Is B_peak stable when measured against a clean pre-observer floor?
6. How large is observer contamination relative to the clean ephemeral excess?

If an existing frontier arm disappears as capacity increases, that is a B438/B439 runtime signal.

## 6. Two-layer arm semantics

B449 freezes a useful distinction.

### Frontier arms

- 32
- 48
- 96

These test memory/intervention Pareto structure.

### Mechanism arms

- 64
- 80

These improve threshold localization and continuity even though they are expected to be dominated under the chosen PRIMARY objective set.

A dominated arm can still be high-value scientific evidence.

This is important: **Pareto irrelevance is not mechanism irrelevance.**

## 7. Buffered reference

Buffered remains in the trial matrix because it provides:

- no-advice baseline;
- natural pressure reference;
- file-residency contrast.

It is not mixed into the DONTNEED candidate frontier because "perform no intervention" is a different control family and its zero-call coordinate would obscure the narrower release-cadence question.

## 8. Prelaunch verdict

The design remains worth running.

Expected null topology:

- candidate frontier membership constant;
- capacity-dependent objective values and pressure states change.

Unexpected high-value observations include:

- loss of a predicted frontier arm;
- failure of the B445 pressure transition;
- large clean-floor drift with capacity;
- observer delta comparable to ephemeral excess;
- instability below the predeclared 0.90 threshold.

No launch is authorized by this bounce.
