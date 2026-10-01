# B457 — Quotient-aware Pareto Beam v0.1

Status: **algorithmic equivalence within the current B434/B455 model**. No physical experiment ran.

## 1. Goal

B456 showed that B455 precompilation can greatly improve low-width beam coverage in redundancy-heavy systems.

B457 removes a workflow requirement:

> callers should not have to remember to precompile before invoking the beam.

The beam now performs decision-state quotienting at every prefix depth.

## 2. Per-depth algorithm

At each option-group depth:

1. expand raw safe options;
2. reject capacity-infeasible candidates;
3. apply the existing lossless partial Pareto prune;
4. group exact objective-vector ties within the same semantic-signature path;
5. keep one canonical prefix;
6. merge factorized provenance;
7. truncate to beam width.

The scale reference is computed from B455 safety-aware compiled groups so duplicate multiplicity does not alter scalar normalization.

## 3. Safety boundary

Exact objective equality is still insufficient to merge semantically different prefixes.

The quotient key includes:

- objective vector;
- semantic-signature path.

Therefore a proven-release prefix and a retain prefix remain separate even if their current costs match exactly.

This preserves the B455 safety boundary.

## 4. Factorized provenance

Enumerating every exact tied path would reintroduce combinatorial growth.

B457 stores instead:

- canonical choices;
- per-state union of source option IDs represented by the canonical prefix;
- equivalent tied-path count.

This is sufficient to know which physical choices contributed to a decision state without expanding every tied Cartesian path.

It is not an exact enumeration of all provenance path combinations.

## 5. Precompile Equivalence theorem

Within the current B434/B435 additive model:

**quotient-aware beam(raw groups, W)**

has the same distinct objective-space output as:

**B435 beam(B455-precompiled groups, W)**.

### Proof sketch

B457 deliberately uses the B455 compiled groups as its scale reference, so both pipelines use the same normalization.

At one prefix depth:

- unsafe options are absent from both;
- locally dominated same-signature options are absent before expansion in the precompiled pipeline and removed after expansion by the raw pipeline's lossless Pareto prune;
- exact same-signature ties are canonicalized before beam truncation in both;
- distinct semantic signatures remain distinct in both.

Thus the same canonical decision states reach truncation.

Induction over every prefix depth gives objective-space equivalence.

## 6. Qualification

Isolated research-lane tests:

- 5 tests
- 5 PASS
- runtime 4.340 s
- stderr SHA-256: sha256:5ad525a67c48e2711cf36df8533039631617ace9a81dff60723db13c84696911.

Checks include:

- duplicate multiplicity invariance;
- semantic-signature separation;
- factorized provenance;
- raw-input equivalence to precompiled beam;
- 500 random StateOption systems at beam widths 4/8/16.

All random equivalence checks passed.

## 7. B456 panel replay

The 200-case B456 redundancy panel was rerun using:

- raw B435 beam;
- B455 precompile + B435;
- raw B457 quotient-aware beam.

At widths 4/8/16/32:

- B457 and precompiled B435 differed in **0 cases**;
- B457 was worse than raw B435 in **0 cases** in this frozen panel.

Mean exact-frontier coverage:

- width 4: raw 34.41%, aware 34.41%
- width 8: raw 54.22%, aware 67.05%
- width 16: raw 66.68%, aware 95.20%
- width 32: raw 87.40%, aware 100%.

Panel output digest:

sha256:2155da43518ebafcbbf7fde98d28ac33d39354fc1190c22cf3d267c00a24d5ba

## 8. New principle H457 — Quotient at the Search Boundary

> Redundant plan multiplicity should be collapsed at the boundary where bounded search spends state capacity, not merely as an optional upstream optimization.

This makes beam capacity correspond more closely to distinct decision states rather than raw plan identities.

## 9. Bigger consequence

B435 already states that partial Pareto pruning at a fixed prefix depth is lossless because all surviving prefixes share the same future option groups.

Therefore beam truncation is the **only approximate step**.

If truncation is removed entirely, the same prefix algorithm becomes an exact dynamic Pareto controller without enumerating the full Cartesian product.

That is the next B458 research target.
