# MEMCG-005G-C v2 Controlled-Spawn Pilot Result

> **Status:** COMPLETE / PHYSICAL PILOT
> **Run:** `36595481746`
> **Launch commit:** `28ff2185934cfc2d350ef70f8256fd481fd75429`
> **Aggregate artifact:** `MEMCG-005G-C-v2-PILOT-36595481746`
> **Aggregate ZIP SHA-256:** `812cd88b5c845c9a160ddb5de0d19d0ffa4c76fab181018e4a20365c29b31bad`

## 1. Execution integrity

- 8/8 hosted blocks: PASS
- 72/72 frozen raw identities executed
- replacement trials: 0
- dynamic scale expansion: 0
- CPU mismatches across measured touches: 0
- worker errors across measured touches: 0
- guard/preparation CPU mismatches: 0
- same-PTE geometry violations: 0
- measured VmPTE growth events: **0**

Total measured touches:

- calibration: 644
- bait: 3,405
- target/follow-up pattern: 115
- total: **4,164**

The PTE-preconditioning intervention achieved its immediate engineering goal:
no measured touch allocated additional page-table memory.

## 2. Frozen primary result

The preregistered strict endpoint counts any nonzero bait delta as failure.

### b62

- n=24
- primer found=23
- strict exact recovery=22/24 = **91.67%**
- failures:
  - CALIBRATION_OTHER_DELTA: 1
  - BAIT_NONZERO: 1

Expected terminal phase:
`ZERO -> ZERO -> Q64`

### b63

- n=24
- primer found=14
- strict exact recovery=11/24 = **45.83%**
- failures:
  - CALIBRATION_OTHER_DELTA: 10
  - BAIT_NONZERO: 3

Expected terminal phase:
`ZERO -> Q64`

### b64

- n=24
- primer found=18
- strict exact recovery=16/24 = **66.67%**
- failures:
  - CALIBRATION_OTHER_DELTA: 6
  - BAIT_NONZERO: 2

Expected terminal phase:
`Q64`

### Overall frozen endpoint

- n=72
- primer found=55
- strict exact recovery=49/72 = **68.06%**

The frozen endpoint remains the primary report.
It is not rewritten after seeing the data.

## 3. Crucial pre-treatment imbalance

Primer discovery occurs **before any arm-specific bait count or target action**.

Therefore arm assignment cannot causally explain differences in primer-found rate.

Observed primer-found:

- b62: 23/24
- b63: 14/24
- b64: 18/24

The large difference is a pre-treatment / calibration-state imbalance.

It must not be interpreted as evidence that b63 is intrinsically worse at spawning the target phase.

## 4. Post-primer phase result

Among all 55 trials in which a Q64 primer was directly observed:

- terminal arm pattern matched prediction: **55/55**

By arm:

- b62: **23/23** matched `ZERO -> ZERO -> Q64`
- b63: **14/14** matched `ZERO -> Q64`
- b64: **18/18** matched `Q64`

This includes the six trials classified as BAIT_NONZERO by the frozen strict endpoint.

One-sided exact 95% lower bound for a 55/55 conditional pattern-match rate:

about **94.7%**

For the primary b63 arm alone, 14/14 gives a one-sided exact 95% lower bound of only about **80.7%**.

Therefore the pilot supports the mechanism strongly but is not yet a >95% reliability certification for b63.

## 5. The six BAIT_NONZERO failures did not shift the terminal phase

The six frozen bait failures were:

- -17 pages
- -17 pages
- -17 pages
- -13 pages
- -3 pages
- -2 pages

No positive unexpected bait charge occurred.

Despite these negative memory.current deltas:

- all six terminal phase patterns were exactly predicted.

Examples:

- b63 with bait -17 -> target 0 -> next Q64
- b64 with bait -2/-13 -> target Q64
- b62 with bait -17 -> target 0 -> next1 0 -> next2 Q64

This is evidence that the negative deltas are not equivalent to consuming or refilling the measured S-CPU stock phase.

They are best treated as an accounting/uncharge contaminant until directly identified.

Do not retroactively remove them from the frozen endpoint.

## 6. Calibration OTHER_DELTA has a striking signature

All 17 CALIBRATION_OTHER_DELTA failures were:

`-17 pages`

Additional bait observations bring the total nonstandard negative deltas to:

- -17 pages: 20 events
- -13 pages: 1
- -3 pages: 1
- -2 pages: 1

There were **no unexpected positive non-Q64 deltas**.

Linux v7.0 source establishes that `drain_stock()`:

1. reads the exact cached `stock->nr_pages[i]`;
2. calls `memcg_uncharge(old, stock_pages)`;
3. resets the cached count to zero.

Therefore a per-CPU stock drain can appear as an exact negative `memory.current` step without representing a data-page touch failure.

The current pilot does not prove that `-17` is specifically a stock drain from CPU P.
The signature and the unchanged terminal phase make that a high-priority explanatory hypothesis.

## 7. Primer morphology

Among the 55 directly observed Q64 primers:

- first measured touch: 47
- touch 3: 1
- touch 6: 1
- touch 47: 1
- touch 63: 3
- touch 64: 2

Thus the stock CPU sometimes begins calibration with residual charge already present.

The construction deliberately does not infer the starting residual state.

It waits for an actual Q64 primer and then anchors arithmetic from that observed reset.

This design choice is validated by the 55/55 terminal phase match.

## 8. PTE control result

G0 Stage A had exposed H32 first-fault VmPTE +4 KiB events.

Controlled-spawn v2 preallocated the PTE table on preparation CPU P and kept all measured pages inside one PTE table.

Result:

`0 / 4,164 measured touches with VmPTE growth`

This closes the specific PTE-steal path for the pilot's measured sequence.

## 9. Scientific interpretation

### Supported

Once:

1. target-time PTE allocation is removed;
2. a fresh Q64 batch is directly observed;
3. a fixed number of subsequent pages are consumed;

the terminal phase moves by exactly one page across b62/b63/b64 as predicted.

This is direct evidence that the rare exact-zero/depth1 morphology can be **constructed**, not merely found.

### Not yet supported

The pilot does not establish:

- literal 100% capture probability;
- a 100% reliable method from raw process start;
- the cause of the -17 accounting events;
- that every historical natural specimen arose from the same mechanism.

The remaining major reliability problem is now **primer acquisition / accounting cleanliness**, not the post-primer phase arithmetic.

## 10. Evidence

Raw manifest:

- file count: **152**
- total raw bytes: **1,705,625**
- content-set SHA-256:
  `e65281ad34ac9f8c0eaf366d2b35ccb07404f8fdf246bfeea4cbcd4d1c0602fd`

Google Drive COLD locator:

`Catfood Lab Evidence/finite-ram-lab/MEMCG-005G-C-v2/run-36595481746`

COLD contents:

- aggregate ZIP
- 8 block ZIPs

All 9 Drive archives were re-downloaded and SHA-256 matched to the GitHub Actions artifact digest.

Result:

`9 / 9 BYTE-IDENTICAL PASS`

## 11. Stop condition

Per Human instruction, no new physical experiment is launched after this result.

Next activity is retrospective analysis only.
