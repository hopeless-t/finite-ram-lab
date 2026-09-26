# Bounce Handoff

> **Bounce ID:** B044  
> **Status:** COMPLETE / DESIGN FROZEN

## Objective

Re-run the interrupted CHAR-002 pseudo-Council from B043 and converge the smallest defensible mechanism-decomposition design.

## Canonical inputs

- `handoffs/B043-CHAR002-DRAFT-CHECKPOINT.md`
- `docs/CHAR-002-COUNCIL-DRAFT.md`
- `findings/HYP-002-initial.md`
- `docs/NORTH_STAR.md`
- `docs/RESEARCH_CHARTER.md`

## Council result

The Council converged on a two-family factorial design.

### Family S — separate VMAs

- MemoryHigh: 160 / 162 MiB;
- creation order: AB / BA;
- initial fault order: AB / BA;
- 8 cells per runner block.

### Family H — shared VMA halves

- one 64 MiB mapping split into lower/upper 32 MiB halves;
- MemoryHigh: 160 / 162 MiB;
- initial fault order: lower→upper / upper→lower;
- 4 cells per runner block.

The arbitrary A/B-label orientation proposed in B043 was removed because it did not create an independent kernel-visible mechanism factor.

## Frozen allocation

```text
16 independent runner blocks
12 cells / block
192 total trials
```

## Frozen inference

Four separate runner-block contrasts:

- S1 creation-order effect;
- S2 separate-VMA fault-order effect;
- H1 shared-VMA upper-minus-lower address effect;
- H2 shared-VMA fault-order effect.

Each uses:

- exact two-sided (2^16) sign-flip inference;
- 20,000-resample runner-cluster bootstrap.

No grand weighted score.

## Monte Carlo decision

No design Monte Carlo.

The uncertainty is mechanism/confounding structure rather than rare-event sample allocation, and the complete factorial fits directly in every block.

## GitHub artifacts

- `docs/CHAR-002.md`
- `specs/CHAR-002.json`

## Next recommended bounce

> Implement CHAR-002 exactly as frozen, add known-answer/schedule tests, commit, and stop before launch.

## Authority boundary

No CHAR-002 scientific evidence exists yet.
