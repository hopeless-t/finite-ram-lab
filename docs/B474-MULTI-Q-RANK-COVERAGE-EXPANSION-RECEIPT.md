# B474 — Multi-q Rank-Coverage Expansion Receipt

Status: **PASS / ALL q AT 95%-CLASS RANK FLOOR**

## Frozen execution

- workflow run: 36934779258
- job: 110612361898
- execution head: ee4d80ac4f9adbc4f4e2e23b977a5e5a3eab07ac
- tests: 4/4 PASS
- artifact ID: 11197503134
- artifact ZIP SHA256: 8f99c18ab6a58172c2551624a9d69daa45574462e2114a4ca4169b60de92949f
- panel SHA256: f4bf5bffd95d7ebef026de112c895cb4ac3a8f42953120a439f2a4e08a296846

## Budget spent

Fresh-process additions:

- q2: +11
- q4: +11
- q7: +11

Total:

`33`

Every new observation preserved exact numerical semantics.

## q2

Prior union maximum:

`67,108,864 B`

New 11-run maximum:

`67,194,880 B`

New samples above prior maximum:

`2/11`

Updated pooled maximum:

`67,194,880 B`

Maximum moved by:

`+86,016 B = 21 pages`

Pooled sample count:

`19`

Rank-max coverage floor:

`19/20 = 95%`

## q4

Prior union maximum:

`71,303,168 B`

New 11-run maximum:

`71,389,184 B`

New samples above prior maximum:

`5/11`

Updated pooled maximum:

`71,389,184 B`

Maximum moved by:

`+86,016 B = 21 pages`

Pooled sample count:

`19`

Rank-max coverage floor:

`95%`

## q7

Prior union maximum:

`71,507,968 B`

New 11-run maximum:

`71,544,832 B`

New samples above prior maximum:

`1/11`

Updated pooled maximum:

`71,544,832 B`

Maximum moved by:

`+36,864 B = 9 pages`

Pooled sample count:

`19`

Rank-max coverage floor:

`95%`

## Combined calibration state

q1 from B472:

- n=20
- max=67,117,056 B
- rank floor ~=95.238%

q2/q4/q7 from B474:

- n=19 each
- rank floor=95%

All q now satisfy the frozen 95%-class sample-count target.

## Important lesson

Passing a small observed-upper dogfood panel did not mean the frontier had
stopped moving.

B474 moved all three q2/q4/q7 empirical maxima despite B471 having no misses for
those q values.

This validates the shift from the vague label:

`observed_upper`

to an explicit pair:

`(empirical maximum, comparable sample count / rank coverage)`.

## Claim ceiling

**EXCHANGEABILITY_CONDITIONAL_MULTI_Q_CALIBRATION**

## Next

B475 should build Governor v1 using:

- q1 max 67,117,056 B, n=20, coverage floor 20/21;
- q2 max 67,194,880 B, n=19, coverage floor 0.95;
- q4 max 71,389,184 B, n=19, coverage floor 0.95;
- q7 max 71,544,832 B, n=19, coverage floor 0.95.

Latency ordering can remain sourced from the balanced B469 Pareto sweep.

The decision receipt must expose the coverage floor and exchangeability
assumption.
