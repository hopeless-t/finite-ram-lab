# MEMCG-005G-D Footprint Dose-Response Result v1

> Status: PASS / DISCOVERY COMPLETE
> Run: `36571375684`
> Launch: `0fbe92a6a3309092f58c56d4d657be91616d2c0a`
> Aggregate artifact: `11033838616`
> Digest: `sha256:b41019a30f531980e4b420ded73a098c00efa566d871dab43ba5f63179b2c3b4`

## Frozen-arm results

Valid REMOTE_LOW first-touch-zero capture:

- CAP8: 2/101 = **1.9802%**
- CAP32: 14/103 = **13.5922%**
- CAP63: 8/104 = **7.6923%**
- CAP64: 14/105 = **13.3333%**
- CAP65: 9/103 = **8.7379%**
- CAP70: 11/111 = **9.9099%**

CPU mismatches: **0**
Non-{0,Q64} failures: **0**

## Frozen model comparison

AIC:
- CONSTANT: **388.5996**
- LOGISTIC_LINEAR: **387.5676**
- STEP64: **389.0581**
- CATEGORICAL: **385.1930**

Frozen discovery label:

`FLAT_OR_UNRESOLVED`

Therefore MEMCG-005G-D does **not** support a descriptive step specifically at 64 pages.

Mean:
- cap <64: 7.7922%
- cap >=64: 10.6583%

This split was insufficient for the frozen STEP64 gate.

## Adjacent contrasts

Only 8 -> 32 showed a strong adjacent difference:

- rate difference: **+11.6120 points**
- Fisher two-sided p: **0.002946**
- posterior P(p32 > p8): **0.99906**

Other adjacent comparisons:
- 32 ->63: p=.1838
- 63 ->64: p=.2596
- 64 ->65: p=.3775
- 65 ->70: p=.8178

P(p70 > p8) = **0.99139**.

## Accepted conclusion

The confirmed CAP8-vs-CAP70 enrichment is real, but the new six-point map does not look like a privileged 64-page transition.

The main unresolved transition now lies between CAP8 and CAP32.

Any narrower threshold claim requires a new prospectively frozen refinement experiment.

No K7 inference.
No hardware-memory claim.
Hosted research only.
