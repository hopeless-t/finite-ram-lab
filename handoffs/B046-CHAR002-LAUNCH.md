# Bounce Handoff

> **Bounce ID:** B046  
> **Status:** COMPLETE / COMPUTE LAUNCHED

## Objective

Verify B045 implementation CI, create the frozen CHAR-002 Actions workflow, launch the 16-block / 192-trial experiment, record the run, and stop.

## Canonical inputs

- `handoffs/B045-CHAR002-IMPLEMENT.md`
- `docs/CHAR-002.md`
- `specs/CHAR-002.json`

## Validation before launch

B045 implementation CI completed successfully:

- CI run: `36246673873`
- conclusion: SUCCESS

## Launch

Workflow:

- `.github/workflows/char-002.yml`
- launch commit: `4a9a72b9e64100cd3534969967fcd39409e61bf6`
- CHAR-002 run: `36246723145`

Frozen evidence budget:

```text
16 runner blocks
12 factorial cells per block
192 total trials
```

## Frozen design preserved

No endpoint, factor, or inference rule was changed at launch.

Primary mechanism contrasts remain:

- S1 separate-VMA creation order;
- S2 separate-VMA fault order;
- H1 shared-VMA upper/lower address position;
- H2 shared-VMA fault order.

## Next recommended bounce

> Rehydrate from B046 only after run 36246723145 completes. Read the frozen aggregate, classify execution validity first, then record the scientific finding in a new handoff.

## Authority boundary

Launching compute is not scientific evidence.

No CHAR-002 result is authorized until aggregate execution checks pass.
