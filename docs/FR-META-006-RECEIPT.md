# FR-META-006 Receipt

Status: **PASS / EXACT ABA MEMOIZATION VALIDATED**

- workflow run: 37136605291
- job: 111242297773
- execution head: b6959f70b499c149257cf57029a2db39a057b72a
- qualification artifact ID: 11278793910
- artifact ZIP SHA256: 7697519f8ef6e527d942191fe02147cfe0b365e45b28270223016ca359fbac79

Scientific parameters unchanged:

- episodes: 8192
- frames per segment: 120
- blocks per decision: 8
- frozen FR-GFX-005 exact output checks: PASS

Compute graph:

- baseline segment evaluations: 98,304
- unique memoized segment means: 40,960
- structural duplicate-compute reduction: 58.33%

Observed CI hotspot timing:

- prior ABA test completion gap: 29,091 ms
- memoized ABA test completion gap: 22,951 ms
- observed reduction: 21.11%

The wall-clock reduction is smaller than the structural reduction because the
test still pays unavoidable hashing, list/statistics work, Python overhead, and
runner noise.

Decision:

**MEMOIZE_DETERMINISTIC_SEGMENT_MEANS**

No statistical sample size, threshold, or evidence claim was weakened.

Claim ceiling:

**TEST_HARNESS_COMPUTE_OPTIMIZATION_ONLY**
