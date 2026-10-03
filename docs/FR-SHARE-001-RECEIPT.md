# FR-SHARE-001 — Duplication Tax Qualification Receipt

Status: **PASS / PHYSICAL IMMUTABLE SHARING EFFECT VALIDATED**

## Qualification

- workflow run: 37111627009
- execution head: 4697ae46453803ef699f33e795585db25c280622
- artifact ID: 11270018071
- artifact ZIP SHA256: 60aea3ca0eaa7647689fa8b20c1ab70fd102e56733201876a793b26c7ce9c2bb
- spec SHA256: 647d521134262bfe0e98edd17b77717d63f7a4ac0b464d4fdad65e1634da481e
- result SHA256: c758b671ae1059f7d95afaf06d4ec5e09f6ba92421c48bff5647adb37989eb3c

## Frozen fixture

- Ubuntu 24.04 GitHub-hosted runner
- six Python workers
- one 32 MiB immutable file
- BASELINE / PRIVATE_COPY / SHARED_MMAP

Primary metric:

`sum worker PSS - baseline sum worker PSS`

## Physical result

BASELINE:
- summed PSS: 46,385 KiB
- summed RSS: 86,200 KiB

PRIVATE_COPY:
- summed PSS: 243,021 KiB
- summed RSS: 282,592 KiB
- baseline-subtracted PSS: **196,636 KiB**

SHARED_MMAP:
- summed PSS: 79,156 KiB
- summed RSS: 282,488 KiB
- baseline-subtracted PSS: **32,771 KiB**

Therefore:

`shared/private PSS delta ratio = 0.1666581908`

`PSS delta reduction = 83.3342%`

The ratio is effectively the ideal 1/6 geometry for six workers.

## Important measurement result

Summed RSS is almost identical in PRIVATE_COPY and SHARED_MMAP:

- 282,592 KiB
- 282,488 KiB

Therefore summed RSS would almost completely hide the physical sharing effect.

PSS is the correct process-attributed metric for this experiment.

## Boundary

- immutable read-only payload only;
- no KSM;
- no sysfs writes;
- no writable KV/activation sharing claim;
- process-attributed PSS, not complete system page-cache accounting.

## Claim ceiling

**HOSTED_LINUX_IMMUTABLE_PROCESS_PSS_SHARING_ONLY**
