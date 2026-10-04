# FR-META-023 — Cross-Repo Decision-Relevance Receipt

Status: CROSS-REPO EXPORT CANDIDATE / NO NEW PHYSICAL RUN

FR-META-022 already qualified one resident pruning capsule across three independent
decision planes.

This tranche does not add another pruning rule. It packages the qualified evidence for
consumption by the Catfood Meta-Meta observatory.

## Why the receipt is a vector

The qualified costs use different physical units:

- MiB-opportunity residency;
- milliseconds of calibration latency;
- physical action counts.

They are not added into one synthetic utility.

The receipt therefore requires:

    scalar_gain = null

and preserves each comparator and cost delta separately.

## Exported evidence

Reuse monitoring:
- 40 -> 0 MiB-opportunity resident integral;
- same 17 restores and 136 MiB storage reads;
- 4 -> 0 drift alarms.

Calibration measurement:
- 15 leave-one-run-out cases;
- 2 safe early stops;
- 0 unsafe early stops;
- 4 cases where probe 2 remains relevant;
- 23.969 ms counterfactual probe latency saved.

Physical placement:
- 24 observed minimal-delta actions;
- 40-action full-reenforcement reference;
- 40% reduction;
- one decision-irrelevant transition with zero tier actions and unchanged physical snapshot.

Meta compilation:
- one resident capsule;
- skill count 17;
- skill-count growth 0;
- catalog budget gate PASS under the frozen <30% ceiling.

## Cross-repo invariant

The central consumer may conclude that this producer has quantitative evidence with
explicit comparators and lineage.

It may not convert heterogeneous cost units into a scalar gain without a separately
qualified utility contract.

## Authority

Export only:
- no new physical run;
- authority_effect = NONE;
- canonical_write = false;
- promotion = false.

## Claim ceiling

THREE_PLANE_DECISION_RELEVANCE_RECEIPT_WITH_HETEROGENEOUS_COST_VECTOR_ONLY
