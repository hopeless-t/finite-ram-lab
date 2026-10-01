# B461 — Obligation–Residency Separation v0.1

Status: **UNIFIED HYPOTHESIS + EXACT SOFTWARE BITE**. No physical RAM experiment ran.

## 1. Why this bounce exists

Several research branches had converged on the same shape without naming the common
object.

Finite RAM / Live-State Frontier:

```text
future obligation
!=
all future state resident now
```

B454–B459 controller work:

```text
physical plan multiplicity
!=
decision-relevant state multiplicity
```

Ozaki/CRT-style exact decomposition:

```text
wide exact result obligation
!=
all residue results simultaneously resident
```

Ternary model execution:

```text
task capability obligation
!=
BF16 weight representation resident
```

Kitten Circuit:

```text
review coverage obligation
!=
one monolithic context resident in one worker
```

The shared research question is therefore not merely "how to compress memory."

It is:

> **What is the minimum physical representation that must be resident now to
> preserve the required future obligation?**

## 2. H461 — Obligation–Residency Separation

Let `O` be a future obligation and let `R_t` be the physical representation
resident at time `t`.

The hypothesis is:

> If a representation schedule carries a future-sufficient invariant, satisfying
> the obligation does not require every source representation to remain
> simultaneously resident.

This is intentionally conditional.

A release is allowed only after the remaining state is proven sufficient under the
domain's fidelity contract.

## 3. Fidelity classes

The domains must not be collapsed into one equivalence claim.

### EXACT

The final answer is mathematically identical.

Example: CRT reconstruction when the moduli are pairwise coprime and

```text
product(moduli) > 2 * conservative_signed_result_bound
```

### BOUNDED_ERROR

A numerical approximation has an explicit error bound.

This class exists in the model but is not exercised by B461.

### EMPIRICAL_CAPABILITY

Equivalence is defined by a frozen evaluation contract rather than bit identity.

Examples:

- ternary model versus a higher-precision representation;
- microsharded review versus monolithic review.

These need held-out quality, semantic-fidelity, rare-miss, and runtime-identity
gates. They must not inherit CRT's exactness claim.

## 4. First exact bite — resident CRT lanes versus streamed fold

B461 freezes two algorithms over the same residue GEMMs.

### Reference — ALL_RESIDENT

1. compute every residue result `C mod m_i`;
2. retain every residue matrix;
3. reconstruct the wide integer result.

### Treatment — STREAMED_FOLD

1. compute one residue result;
2. fold it into the future-sufficient CRT state `(x mod M, M)`;
3. release that residue matrix;
4. continue with the next modulus.

The incremental fold is:

```text
t  = (r - x) * inverse(M mod m, m) mod m
x' = x + M*t
M' = M*m
```

The pair `(x', M')` is sufficient for every future CRT lane already admitted by
the contract. Earlier residue matrices no longer need to remain live.

## 5. Frozen toy result

For:

- A = [[3,5],[-2,7]]
- B = [[11,-4],[6,9]]
- moduli = [127,125,121]
- product = 1,920,875
- conservative absolute result bound = 71

both schedules reconstruct exactly:

```text
[[63,33],
 [20,71]]
```

Under the B461 logical intermediate-byte model:

- ALL_RESIDENT peak = 24 bytes
- STREAMED_FOLD peak = 16 bytes
- reduction = 8 bytes / 33.33%

These are **logical modeled intermediate bytes**, not process RSS.

## 6. Software panel

The fixed software panel uses:

- deterministic seed 461;
- 32x32 signed integer matrices;
- element range [-8,8];
- residue-lane prefixes of length 2..7 from
  [127,125,121,119,113,109,107].

Primary acceptance:

1. exact reference integer GEMM equality;
2. all-resident / streamed output equality;
3. uniqueness proof passes before execution;
4. streamed logical peak is below all-resident logical peak.

The dedicated workflow freezes the resulting JSON artifact.

## 7. Connection to the existing Live-State Frontier

B426 stated:

```text
rewrite state graph
-> schedule / placement / lifetime
```

B461 sharpens the release proof.

A representation can be released when either:

- a smaller future-sufficient exact/bounded representation exists; or
- the domain-specific fidelity gate proves the replacement sufficient.

For exact CRT, the fold state is constructive proof.

For ternary models and Kitten review, sufficiency remains empirical.

So the common architecture becomes:

```text
OBLIGATION
   |
   v
admissible representations
   |
   v
fidelity / safety proof
   |
   v
future-sufficient active state
   |
   v
residency schedule
   |
   v
release / rematerialize / move
```

## 8. Connection to B454–B459

B454 introduced:

> retain the information obligation, discard redundant representation.

B458/B459 then showed that exact optimization should scale with the surviving
decision frontier and that ordering changes intermediate-state cost without
changing the final answer.

B461 generalizes the same separation to numerical representation.

This suggests a broader scheduling principle:

> Optimize the trajectory of the **minimum future-sufficient frontier**, not the
> raw amount of source state.

The frontier may consist of:

- memory pages;
- exact residue fold state;
- compressed weights plus scales;
- selected evidence;
- review shards plus coverage receipts;
- optimizer decision states.

The mechanisms differ; the accounting question is shared.

## 9. What this does not prove

B461 does not prove:

- physical RSS decreases by the modeled logical-byte amount;
- a streamed CRT implementation is faster;
- a particular Ozaki implementation uses this exact residency schedule;
- ternary compression preserves the original model exactly;
- Kitten shard synthesis is mathematically equivalent to CRT;
- one common governor can already control every domain.

Those are later experiments.

## 10. Next bite

The next useful physical/software boundary test is:

**B462 — Representation Schedule Peak Test**

Run matched fresh-process implementations of:

- all-resident residue outputs;
- streamed fold;

with exact output equality frozen first.

Measure:

- normalized peak RSS growth as primary physical endpoint;
- wall time;
- materialized intermediate bytes;
- allocator/final RSS as supporting diagnostics.

Use order-balanced repetitions and targeted biopsy for any rare positive
treatment-minus-reference peak.

That imports the strongest lesson from the PCG handoff directly into the
Finite RAM program.

## New principle H461

> **Obligation is semantic/informational. Residency is physical. A system should
> retain the smallest future-sufficient representation whose fidelity contract is
> actually proven, and no smaller.**
