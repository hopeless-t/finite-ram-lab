# Bounce Handoff

> **Bounce ID:** B033  
> **Status:** COMPLETE / DESIGN COMPUTE LAUNCHED

## Objective

Step back from mechanism selection and choose an observation design that can map the natural frequency of semantic HOT-region residency misalignment across the 160–168 MiB transition region.

## Pseudo-Council conclusion

The next missing quantity is the baseline opportunity rate:

> How often does NO_HINT reach reuse with the future-needed HOT region not fully resident?

This should be measured before another control mechanism is selected.

Primary observable:

```text
misaligned = HOT resident fraction < 1.0
```

measured by mincore immediately before HOT reuse.

## Candidate map

MemoryHigh:

```text
160, 162, 164, 166, 168 MiB
```

Candidate block/repeat designs:

```text
D1  12 blocks x 4 repeats/level = 240 trials
D2  16 blocks x 4 repeats/level = 320 trials
D3  24 blocks x 3 repeats/level = 360 trials
D4  32 blocks x 2 repeats/level = 320 trials
```

## Monte Carlo

The design simulation stresses:

- transition location;
- transition width;
- runner-level heterogeneity.

It evaluates prevalence-estimation error, full-curve error, cluster-interval behavior, and whether enough 164 MiB misalignment events / affected runner blocks are observed for useful conditional diagnostics.

## Workflow

- design workflow commit: `53e68df5454a520fb33426a606dcb4f7c1391f8f`
- run: `36242326971`

## Next recommended bounce

> Read the design Monte Carlo, choose a Pareto-efficient design without inventing a weighted score, freeze OBS-003, and stop before launch.

## Authority boundary

The design Monte Carlo allocates sampling effort only.

It is not evidence about real Linux misalignment prevalence.
