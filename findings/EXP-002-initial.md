# EXP-002 Initial Finding

> **Status:** PRIMARY BENEFIT NOT SUPPORTED / RED-TEAM HARM CONFIRMED  
> **Run:** 36228994342

## Question

Can one bit of application semantic knowledge — which equal-size region is not needed next — improve future HOT reuse under natural 164 MiB pressure using existing `MADV_PAGEOUT`?

## Execution

All frozen execution checks passed:

- 20 independent runner blocks;
- 360 total trials;
- 120 trials per arm;
- HOT physical mapping identity balanced;
- no OOM events;
- all trial integrity checks passed.

## Arm summaries

| Arm | Median HOT retouch | P90 HOT retouch | Median work interval | Median HOT residency | Median PAGEOUT cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| CORRECT_PAGEOUT | 0.518 ms | 76.713 ms | 26.614 ms | 1.0000 | 12.954 ms |
| NO_HINT | 0.686 ms | 137.958 ms | 31.999 ms | 1.0000 | 0 ms |
| WRONG_PAGEOUT | 54.396 ms | 279.677 ms | 101.930 ms | 0.8108 | 12.613 ms |

## Primary pre-registered result

Primary contrast:

    CORRECT_PAGEOUT / NO_HINT

for runner-block mean log HOT-retouch latency:

    geometric mean ratio = 0.9030x
    exact 2^20 sign-flip p = 0.6684
    cluster-bootstrap 95% ratio interval = [0.5886, 1.4322]

The primary performance-benefit hypothesis is **not supported**.

The point estimate is in the beneficial direction, but uncertainty is wide and fully compatible with no effect or a moderate adverse effect.

## Net-cost result

For the broader interval including PAGEOUT call cost, burst work, and HOT retouch:

    CORRECT_PAGEOUT / NO_HINT geometric mean ratio = 0.9322x
    exact p = 0.5599
    cluster-bootstrap 95% interval = [0.7497, 1.1819]

There is no supported net benefit in the pre-registered central-tendency analysis.

## Red-Team result

WRONG_PAGEOUT versus CORRECT_PAGEOUT:

    geometric mean HOT-retouch ratio = 35.64x
    exact 2^20 sign-flip p = 1.91e-6
    cluster-bootstrap 95% ratio interval = [16.75x, 70.58x]

WRONG_PAGEOUT also produced:

- median HOT residency ≈ 0.8108;
- median HOT retouch ≈ 54.4 ms;
- median 1570 swap-ins/refaults during HOT reuse.

CORRECT_PAGEOUT preserved median HOT residency at 1.0 and had zero median HOT-retouch swap-ins/refaults.

## Interpretation

The experiment demonstrates a strong **asymmetry**:

    incorrect semantic preparation is clearly harmful
                 but
    correct semantic preparation did not robustly beat NO_HINT
    on the pre-registered central-tendency outcomes

This matters for architecture.

Application semantics can influence residency in the expected direction, but a mechanism that consumes semantic hints must be robust to stale or wrong information because the downside is large.

At the same time, the baseline Linux behavior left insufficient or too-variable central-tendency headroom for this particular correct hint to show a reliable benefit.

## Tail observation — exploratory only

The raw summaries show lower P90 HOT retouch and work-interval values in CORRECT_PAGEOUT than NO_HINT.

That tail pattern was **not** the pre-registered primary inference and must not be promoted to a finding from EXP-002.

It is a justified next research question.

## What this establishes

- semantic misinformation can be dramatically harmful through an existing Linux interface;
- correct semantic PAGEOUT reliably avoids the catastrophic wrong-hint direction;
- central-tendency benefit versus the kernel baseline was not established.

## What this does not establish

- that correct semantic information has no value;
- that tail-risk is improved;
- that a coordinator should or should not be built;
- that a new kernel API is needed.

## Next research direction

Pre-register a **tail-risk** study rather than reinterpreting EXP-002 post hoc.

The next question should be:

> Does correct semantic preparation reduce the probability or severity of rare transition-zone stalls, even though its central-tendency benefit was not established?

Wrong/stale-hint robustness must remain part of any later coordination design.
