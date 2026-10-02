# B490 — Repaired Coverage-Aware Governor v2 Receipt

Status: **PASS / REPAIRED GOVERNOR v2 QUALIFIED**

## Frozen execution

- workflow run: 36953182615
- job: 110670364892
- execution head: d1307dcc32575e560aa1163ea2985b64800b484a
- tests: 4/4 PASS
- artifact ID: 11203964385
- artifact ZIP SHA256: 0fecac7e1373eb57255b974633414b11ec24ebc7be14ce4d397698a8b996cf0b
- governor JSON SHA256: 4b13fd45460ab657904dd46abfd733644e5be1c49e444242f9c1b7d43ca98203

## Repaired 95% policy

```text
50,696,192 B -> q2
  n=19
  rank floor=95%

58,941,440 B -> q4
  n=19
  rank floor=95%

71,507,968 B -> q7
  n=19
  rank floor=95%
```

q1 is excluded because q2 dominated it on the repaired B487 median frontier.

## Example decision

Input:

- peak budget = 58,941,440 B
- minimum coverage = 0.95

Output:

- selected q = 4
- empirical max = 58,941,440 B
- sample count = 19
- rank floor = 0.95
- repaired-runtime median latency ~=0.387823 s

## Old vs repaired q2 memory threshold

Old B475 q2 95%-class threshold:

`67,194,880 B`

Repaired B490 q2 threshold:

`50,696,192 B`

Difference:

`-16,498,688 B ~= -15.73 MiB`

The Governor now exposes the resource benefit of the centering repair at the
policy boundary rather than only in a microbenchmark.

## Fail-closed evidence behavior

A 99% request still has no eligible q because all repaired Pareto q values have
n=19.

99% sample-max rank coverage requires n>=99.

## Claim ceiling

**EXCHANGEABILITY_CONDITIONAL_REPAIRED_GOVERNOR_V2**

## Next

B491 should dogfood v2 at and around all three calibrated boundaries.

A new exceedance should be treated as calibration/tail evidence, not as automatic
repair failure.
