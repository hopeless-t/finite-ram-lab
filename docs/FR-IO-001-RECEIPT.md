# FR-IO-001 — Page-cache Residency Receipt

Status: **PASS / PHYSICAL FILE-BACKED RESIDENCY TRANSITION VALIDATED**

## Qualification

- workflow run: 37120535913
- job: 111195602743
- execution head: 0cc08a994f0465fad447636c76b80bd95b1e9af4
- artifact ID: 11272848198
- artifact ZIP SHA256: 00c07a4976eb4957c3b55250d8f10c0ca9b567fd1b07ae5af2d9e6f4a4a9c29a
- spec SHA256: 2e532964cb3fbdbbfb4d2978ac67628175f44b3c8f9e97dd7ad8a34b04cbf57b
- result SHA256: c0a095d4d8bc70e669988a3dc4d86b70ff91039740bbfa0de209039492aee29f

## Physical fixture

- Ubuntu 24.04 GitHub-hosted runner
- 4 repetitions
- 32 MiB clean file per repetition
- 4 KiB pages
- 8,192 pages per file
- residency measured with mincore()
- reclaim hint: POSIX_FADV_DONTNEED

## Frozen result

All 4 repetitions were identical:

- initial/cold: 0 / 8,192 resident pages = **0%**
- after touching every page: 8,192 / 8,192 = **100%**
- after unmap + POSIX_FADV_DONTNEED + remap: 0 / 8,192 = **0%**

## Main invariant

`backing location != current residency location`

and therefore:

`SSD-backed bytes != RAM-free bytes`

The result physically demonstrates that reading clean file-backed state can
materialize the full mapping into resident RAM/page cache.

## Boundary

POSIX_FADV_DONTNEED is advisory in general.

The observed 0% post-DONTNEED result is specific to this clean hosted-Linux
fixture and is not promoted to a universal eviction guarantee.

## Claim ceiling

**HOSTED_LINUX_CLEAN_FILE_PAGE_CACHE_RESIDENCY_ONLY**
