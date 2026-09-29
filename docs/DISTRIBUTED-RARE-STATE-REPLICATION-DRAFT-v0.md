# Distributed Rare-State Replication — Draft v0

> **Status:** DRAFT
> **Purpose:** make future rare-state findings independently reproducible by external collaborators.

## Principle

External participants produce **evidence receipts**, not authoritative conclusions.

Proposal != Decision.
Visualization != Evidence.

## Candidate replication capsule

A future public capsule should pin:
- repository commit;
- worker source hash;
- experiment spec;
- kernel/image metadata;
- page size and cgroup-v2 preflight;
- raw per-trial JSON;
- aggregate JSON;
- artifact digest;
- analysis version.

Each contributor should run independent block IDs and return signed/hash-addressed receipts.

The canonical repository aggregates receipts without silently rewriting them.

## Environment strata

At minimum record:
- Linux kernel release;
- distribution / hosted runner image;
- CPU count/model where exposed;
- page size;
- cgroup mode;
- systemd version;
- memcg availability.

Cross-environment differences are results, not failed replications.

## Visualization

A future Rare-State Field can visualize:
- capacity;
- exact-zero capture posterior;
- nonzero morphology incidence;
- residual-depth species;
- uncertainty;
- environment stratum.

The field is a navigation/participation surface only.
It must link every visual mark back to evidence receipts.

This design is compatible with the visual-front-door pattern used in the separate dissociated-control-systems project.

No distributed execution is authorized by this draft.
