# FR-META-010 Receipt

Status: **PASS / IMMUTABLE EPISODE-TEMPLATE CACHE VALIDATED**

- workflow run: 37137757106
- job: 111245654146
- execution head: b89b852840de5e257dba00d6e49364b8b710edb5
- qualification artifact ID: 11279860507
- artifact ZIP SHA256: c46a774eda70be3c8d9b13fdfc21a353a5537a1f47b7afa660152252ce0a88ff

Scientific state unchanged:

- episodes: 512
- policies: 6
- existing frozen per-policy summaries: PASS
- each policy still receives fresh mutable target/permutation lists

Deterministic fixture construction:

- baseline template builds: 3,072
- candidate template builds: 512
- structural hash/sort template reduction: 83.33%

Observed hot-test completion gap:

- recent pre-change specimen: 11,366 ms
- cached-template specimen: 9,548 ms
- observed reduction: about 16.0%

Interpretation:

The hash/sort template was real duplicate work, but the state-transition
simulation remains the dominant cost. The optimization is retained because it
is exact and preserves policy isolation.

Decision:

**CACHE_IMMUTABLE_EPISODE_TEMPLATE_COPY_PER_POLICY**

Claim ceiling:

**TEST_HARNESS_TEMPLATE_REUSE_ONLY**
