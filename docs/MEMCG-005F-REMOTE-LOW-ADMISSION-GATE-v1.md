# MEMCG-005F Remote-Low Admission Gate v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Question

Does the composite condition:

`REMOTE_LOW := pre_current_pages <= 110 AND measured first touch occurs on S != startup CPU P`

prospectively identify fresh memcg identities that produce a Q64 first touch with very high reliability?

This is an independent confirmatory experiment.

## Frozen rules

Before launch:

- threshold = **110 pages**
- startup CPU = P
- measured CPU = S, with S distinct from P
- Q64 = 60..68 pages

No tuning after launch.

## CPU roles

Require >=3 allowed CPUs:

- C = controller
- P = startup CPU
- S = remote stock-test CPU

Controller pinned C.

All workers start on P using the unchanged MEMCG-005D shared-latch worker.

## Scale

Four independent hosted blocks.

Each block creates:

`64 fresh identities`

Total:

`256 identities`

Every identity is classified before migration:

- LOW if pre_current_pages <=110
- HIGH otherwise

All identities are then externally migrated P -> S and probed once.

Expected LOW yield from MEMCG-005E is descriptive only and is not assumed by the decision rule.

## Measured sequence

For each identity:

1. start worker on P;
2. wait for shared READY;
3. read pre-touch `memory.current`;
4. classify LOW/HIGH using frozen threshold;
5. externally set worker affinity to S;
6. externally confirm worker on S;
7. read mid current;
8. record affinity-to-GO elapsed time;
9. set shared GO;
10. worker immediately touches exactly one measured anonymous page;
11. worker sets DONE in shared memory;
12. read post current;
13. stop worker.

No worker FIFO/status I/O occurs in the measured path.

## Outcomes

Primary outcome:

`Q64_PASS = 60 <= touch_delta_pages <= 68`

Preserve exact:

- block / identity
- pre_current_pages
- LOW/HIGH
- migration_delta_pages
- touch_delta_pages
- affinity_to_go_us
- observed CPU
- validity

## Primary decision

### SUPPORT_REMOTE_LOW_GATE

Require all:

- at least **120 valid LOW** observations overall;
- LOW Q64 success rate >= **97%**;
- each block with >=20 LOW observations has LOW success >= **90%**;
- HIGH Q64 success rate <= **60%** when HIGH n>=40;
- one-sided Fisher exact LOW > HIGH: `p < 1e-10` when both strata are present;
- zero CPU mismatches;
- no non-{0,Q64} failure morphology.

### REJECT_REMOTE_LOW_GATE

If either:

- LOW Q64 success < **90%** with LOW n>=120; or
- at least two blocks with >=20 LOW observations have LOW success <80%.

### INCONCLUSIVE

Otherwise.

The gray zone prevents a marginal result from being promoted into an admission primitive.

## Secondary analysis

Report:

- LOW success by block;
- HIGH success by block;
- admission yield = LOW / total;
- failure rate by affinity-to-GO latency quartile;
- pre_current histogram;
- migration delta morphology.

Do not retune 110 pages from these diagnostics.

## Successor use

Only after SUPPORT_REMOTE_LOW_GATE:

A future capacity experiment may start candidate identities on P, discard HIGH candidates before they ever touch S, and admit only REMOTE_LOW identities to the measured S-side insertion sequence.

The successor experiment must still independently verify every admitted insertion with Q64.

## Non-claims

MEMCG-005F does not estimate:
- NR_MEMCG_STOCK;
- slot capacity;
- eviction order;
- hardware memory behavior.

It validates only an admission predicate for a later hosted memcg experiment.

## Launch boundary

Design only.
Do not implement or launch in this bounce.
No local-PC execution.
