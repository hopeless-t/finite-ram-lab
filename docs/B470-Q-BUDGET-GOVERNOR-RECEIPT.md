# B470 — Budget-Aware q Governor Receipt

Status: **PASS / FIRST OBSERVED-FRONTIER GOVERNOR**

## Frozen execution

- workflow run: 36929942407
- job: 110596452138
- execution head: 6dcced4ce7ef6e793fcbcb182833c73bf158bd1f
- tests: 5/5 PASS
- artifact ID: 11195063591
- artifact ZIP SHA256: 0eb9233130c972a6805ab87350fb4b5e59538b9343bd7a3cf7d3c6083fcd7e3c
- governor JSON SHA256: 5442c5cf8abd6910fd231006bab865cd616a4e01d14bb611ddc57181d54b9f89
- source B469 sweep SHA256: 537bbf6304937a7e3864f38ffb0b41f2cd67492d76f5f1064688b8836ef66394

## Selection rule

The governor does not compute one weighted efficiency score.

It uses:

```text
minimize observed median latency
subject to:
  chosen peak model <= declared peak budget
  exact semantic gate previously passed
```

## Median policy

Breakpoints:

```text
budget 67,014,656 B -> q=1

budget 67,024,896 B -> q=2
  extra headroom vs q1 = 10,240 B

budget 71,217,152 B -> q=4
  extra headroom vs q1 = 4,202,496 B

budget 71,507,968 B -> q=7
  extra headroom vs q1 = 4,493,312 B
```

## Observed-upper policy

This mode uses the maximum peak observed in the four B469 repetitions.

Breakpoints:

```text
budget 67,022,848 B -> q=1

budget 67,108,864 B -> q=2
  extra headroom vs q1 = 86,016 B

budget 71,303,168 B -> q=4
  extra headroom vs q1 = 4,280,320 B

budget 71,507,968 B -> q=7
  extra headroom vs q1 = 4,485,120 B
```

The observed-upper mode is deliberately more conservative around q=2.

It is not a certified worst-case bound; it is only the upper peak observed in the
frozen four-run panel.

## Example decisions

Median mode with peak budget 67,024,896 B:

`q=2`

Observed-upper mode with peak budget 67,050,000 B:

`q=1`

This demonstrates that risk mode is part of the resource contract, not a hidden
implementation choice.

## Research milestone

The line from theory to usable runtime is now:

```text
Obligation != residency
-> exact streamed CRT
-> physical peak effect
-> active experiment runtime
-> GitHub Actions dogfood perturbation
-> cross-run feedback
-> axis selection
-> q Pareto surface
-> budget-aware q governor
```

The governor is now an executable software component rather than only a research
diagram.

## Claim ceiling

**OBSERVED_FRONTIER_CONSTRAINT_GOVERNOR_V0**

The policy must be relearned for a new workload/runtime/environment.

## Next

B471 should dogfood the governor itself:

1. provide frozen peak budgets;
2. let B470 select q;
3. execute that q in a fresh process;
4. compare observed peak to the declared budget;
5. freeze any miss as a calibration specimen.

That is the next step from "governor decision" to "governor-enforced execution."
