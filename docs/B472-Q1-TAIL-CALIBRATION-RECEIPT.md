# B472 — q=1 Tail Calibration Receipt

Status: **PASS / q1 EMPIRICAL MAX STABLE IN TARGETED PANEL**

## Frozen execution

- workflow run: 36934277076
- job: 110610746354
- execution head: d86f0fec9b16e434b551e41dfa8e94f7b4814502
- tests: 4/4 PASS
- artifact ID: 11196744741
- artifact ZIP SHA256: 41d31af50ef14f76359628debe64c5fd1396ab391f8938f06e979a291851542c
- panel SHA256: 824d0c067b44a2f2229fe3207e3076fb7519433249a4daa606b0fdc576532f95

## New q1 tail panel

Additional fresh-process samples:

`12`

Observed peaks:

```text
66,916,352
66,994,176
66,994,176
66,985,984
66,994,176
67,014,656
67,014,656
66,985,984
66,949,120
66,994,176
67,014,656
66,985,984
```

New-panel maximum:

`67,014,656 B`

Prior pooled q1 maximum from B469+B471:

`67,117,056 B`

New samples exceeding that prior maximum:

`0/12`

Therefore the pooled empirical maximum remains:

`67,117,056 B`

Classification:

**Q1_EMPIRICAL_MAX_STABLE_IN_TARGETED_PANEL**

## Pooled sample count

Comparable q1 fresh-process observations:

- B469: 4
- B471: 4
- B472: 12

Total:

`n=20`

## Exchangeability-conditional rank bound

For n exchangeable comparable observations, the probability that the next
observation is a strict new maximum is at most:

`1/(n+1)`.

For n=20:

```text
exceedance ceiling <= 1/21 ~= 4.762%
coverage floor      >= 20/21 ~= 95.238%
```

This is not a worst-case guarantee.

It assumes the next observation is exchangeable with the pooled observations and
does not protect against runtime, workload, runner, or environment drift.

## Research consequence

The old phrase `observed_upper` can now be refined.

For q1, the empirical maximum has enough comparable samples to attach a
distribution-free one-step rank coverage statement above 95%, conditional on
exchangeability.

The other q values currently have only eight comparable samples each
(B469 four + B471 four), which implies only:

`8/9 ~= 88.89%`

rank-max one-step coverage floor.

## Next

B473 should calculate the required sample budget for explicit target coverage.

For 95%:

`n >= 19`.

Therefore q2, q4, and q7 each need 11 additional comparable observations to
reach the same 95%-class rank-max calibration.

q1 already satisfies that sample-count requirement.
