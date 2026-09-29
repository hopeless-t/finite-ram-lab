# EVIDENCE-RESIDENCY v1 — HOT / WARM / COLD research evidence

> **Status:** v1 IMPLEMENTATION CONTRACT
> **Authority:** EVIDENCE_LIFECYCLE_ONLY
> **Does not authorize experiment launch or evidence deletion.**

## Goal

Keep GitHub useful as a hot research index without making GitHub Actions artifact retention the long-term authority for raw evidence.

The evidence itself remains content-addressed.

Location is metadata.

A file moving from GitHub to local storage or Google Drive must not change what evidence it is.

## Core invariant

`location != identity`

Evidence identity is the ordered file set:

- relative path;
- byte length;
- SHA-256.

The manifest derives a stable `content_set_sha256` from that set.

Therefore:

`HOT -> WARM -> COLD -> RESTORE -> VERIFY`

must preserve the same content-set digest.

## Residency tiers

### HOT

Fast-path evidence that should remain immediately visible from GitHub.

Typical contents:

- aggregate summary;
- frozen spec;
- result document;
- rare / anomalous specimen receipts;
- evidence residency manifest;
- small machine-readable canonical sidecars needed by current analysis.

GitHub Actions raw block artifacts are a transient HOT cache, not permanent authority.

Recommended raw block retention for new experiments:

`7 days`

Aggregate artifacts may remain longer when useful, but their digest should also be recorded.

### WARM

Recent full evidence likely to be re-opened.

Preferred location:

- private Google Drive research folder;
- optionally a local working copy.

WARM is not required to be public or directly addressable from the Git repository.

### COLD

Full raw evidence not needed for normal day-to-day analysis.

Preferred replicas:

1. local archive;
2. private Google Drive archive.

For important runs, two independent COLD copies are preferred.

A COLD locator committed to a public repository should be opaque.

Good:

`COLD:google-drive:frl-cold/MEMCG-005G-G0/run-123`

Avoid:

- absolute local paths containing usernames;
- private bearer URLs;
- share URLs whose disclosure changes access;
- credentials or tokens.

## Manifest contract

Schema:

`schemas/EVIDENCE-RESIDENCY-MANIFEST-v1.schema.json`

Implementation:

`src/finite_ram_lab/evidence_residency.py`

Each manifest binds:

- experiment ID;
- run ID;
- source commit;
- current residency tier;
- file count;
- total bytes;
- every file path / size / SHA-256;
- stable `content_set_sha256`;
- zero or more opaque storage references;
- optional origin metadata such as GitHub Actions artifact ID/digest.

The manifest may live inside the evidence directory; the CLI excludes the output manifest itself from the content set to avoid self-hash recursion.

## CLI

Create a manifest:

```bash
frl evidence-manifest evidence/MEMCG-005G-G0/aggregate \
  --out evidence/MEMCG-005G-G0/evidence-manifest.json \
  --experiment-id MEMCG-005G-G0 \
  --run-id 123456789 \
  --source-commit deadbeef \
  --tier HOT \
  --origin-provider github-actions \
  --origin-ref artifact:123456 \
  --origin-digest sha256:... \
  --storage-ref COLD:local:frl-cold/MEMCG-005G-G0/123456789 \
  --storage-ref COLD:google-drive:frl-cold/MEMCG-005G-G0/123456789
```

Verify a restored directory:

```bash
frl evidence-verify restored/MEMCG-005G-G0/123456789 \
  --manifest evidence-manifest.json
```

A digest/size/missing/extra mismatch returns FAIL and process exit code 2.

## Demotion protocol

Do not remove the GitHub raw copy merely because an upload command succeeded.

Before a HOT raw artifact is allowed to expire or be deleted:

1. freeze the manifest;
2. copy the complete raw evidence off GitHub;
3. restore/read the off-GitHub copy as ordinary files;
4. run `frl evidence-verify`;
5. record the opaque storage locator in the manifest or run result;
6. commit the small HOT manifest/result references.

For high-value evidence, verify both local and Drive replicas before intentional GitHub deletion.

Natural GitHub artifact expiry is acceptable only after at least one verified off-GitHub copy exists.

## Promotion protocol

When COLD evidence becomes active again:

1. restore into a clean directory;
2. run `frl evidence-verify`;
3. require PASS;
4. only then ingest/analyze it;
5. mark the working copy HOT/WARM separately if desired.

`exists` is not equivalent to `verified`.

## Relationship to REC-001

REC-001 defines canonical raw JSONL semantics.

EVIDENCE-RESIDENCY defines where those raw bytes live over time.

SQLite projections remain rebuildable derivatives.

Therefore:

`REC-001 raw bytes + EVIDENCE-RESIDENCY manifest`

is the durable evidence contract.

## G-F sizing audit

MEMCG-005G-F run `36577573774` currently contains:

- 48 block artifacts;
- 1 aggregate artifact;
- total compressed GitHub artifact size: about 1.395 MiB;
- block mean: about 29.0 KiB;
- aggregate: 37,159 bytes.

So current MEMCG experiments are not a storage-cost emergency.

The value of this protocol is long-term integrity and scaling to recorder-heavy studies, not emergency deletion.

## G0 policy

Before MEMCG-005G-G0 Stage A:

- generate residency manifests for aggregate output;
- set raw block artifacts to short HOT retention;
- retain aggregate + manifest longer;
- archive full raw evidence to local and/or Google Drive after aggregation;
- never make a scientific verdict depend on an unverified remote-only copy.

## Non-goals

v1 does not:

- embed Google Drive credentials;
- call Google Drive APIs from the experiment worker;
- automatically delete GitHub artifacts;
- change scientific conclusions;
- authorize hosted compute;
- make local/Drive storage authoritative without digest verification.
