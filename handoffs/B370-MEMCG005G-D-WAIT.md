# B370 — MEMCG-005G-D wait

Launch:
`0fbe92a6a3309092f58c56d4d657be91616d2c0a`

Scientific run:
`36571375684`

Single B370 read:
`queued`

No second poll this bounce.

Frozen capacities:
`{8,32,63,64,65,70}`

Scale:
16 independent blocks x72 candidates =1152.

Analysis:
CONSTANT / LOGISTIC_LINEAR / STEP64 / CATEGORICAL AIC.
The result will be used to choose the next capacity points by model-disagreement / information-gain design rather than manual guessing.

Next fresh bounce:
read run `36571375684` exactly once.

Hosted research only.
