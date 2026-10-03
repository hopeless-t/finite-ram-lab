# FR-META-012 Receipt

Status: **PASS / SPECULATIVE STORAGE BOUNDARY CORRECTED**

- workflow run: 37138222223
- job: 111247031542
- execution head: 072f102a922d34e90d9e881f5b000f5e21e6519d
- qualification artifact ID: 11279530907
- artifact ZIP SHA256: dc0ff207f11452840bdfe1cd5b388515cf3fef075fd146d3681740a6b2d8ba2f

Observed failure specimen:

- prepared unreferenced commit:
  5f8b37de4694652064eeef7f468294de5f4c5fb0
- later Contents API retrieval: 404
- later Git commit-object API retrieval: 404
- canonical parent/child branches: unaffected

Theory update:

- unreferenced Git objects are not a durable prepared-work contract on this tool path;
- build-ahead before parent receipt is ephemeral only;
- durable/canonical child Git materialization begins after the parent receipt is frozen;
- speculative depth remains one;
- repository state remains authoritative.

Decision:

**EPHEMERAL_BUILD_AHEAD_DURABLE_MATERIALIZATION_AFTER_RECEIPT**

Claim ceiling:

**SPECULATIVE_STORAGE_RELIABILITY_BOUNDARY_ONLY**
