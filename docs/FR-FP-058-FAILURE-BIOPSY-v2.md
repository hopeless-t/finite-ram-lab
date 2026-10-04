# FR-FP-058 Failure Biopsy v2 — Fixed Tie Tolerance Was Too Wide

Status: **NUMERICAL CONTRACT REFINEMENT / POLICY BOUNDARIES STILL UNCHANGED**

Second failed qualification:
- workflow: 37226910617
- head: a497f8032619d23bfc5abd178b2e57e98039d164

The first repair used a fixed score tie tolerance:

    1e-9 ms

That correctly canonicalized the exact first crossover, but it was too wide.

Four validation probes located exactly 1e-12 rent units *before* later
crossovers were incorrectly treated as ties and routed forward.

Those are not representation-only ties.

For the smallest adjacent resident-byte-time slope difference in this capsule,
moving 1e-12 in rent changes score by roughly 1.6e-10 ms, which is larger than
floating representation noise.

## Repair

Replace the fixed tolerance with a magnitude-scaled machine-precision contract:

    tie_tolerance
      =
    64 * machine_epsilon * max_abs_score

At ~1000 ms score magnitude this is ~1.4e-11 ms.

This:
- absorbs the exact-crossover arithmetic residue (~1.1e-13 ms);
- does not absorb the 1e-12-rent-neighbor decision difference.

No physical threshold or policy crossover is moved.

## Compiled lesson

**NUMERICAL_EQUIVALENCE_TOLERANCE_MUST_SCALE_WITH_MACHINE_PRECISION,
NOT_WITH_AN_ARBITRARY_FIXED_APPLICATION_UNIT.**

Claim ceiling:

**FP058_MACHINE_PRECISION_TIE_REPAIR_ONLY**
