# Bounce Handoff

> **Bounce ID:** B323
> **Status:** EXTERNAL_WAIT / MEMCG-005 HOSTED RUN QUEUED

Exact launch commit:
`b8c1cfbf4e54fef37a314fbe629fceef4734ff0b`

Scientific run:
`36545631176`

Single B323 status read:
`queued`

No second read was performed.

Scientific signature:
- calibrated EMPTY normalization for every identity;
- verified +64 slot insertion receipts;
- independent m={0,5,6,7,8};
- one-shot target probe;
- source K7 prediction: 0/5/6 PRESENT, 7/8 ABSENT.

Next fresh bounce:
- read run `36545631176` exactly once;
- success -> fetch aggregate once and canonicalize;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Hosted research only.
No local-PC execution.
