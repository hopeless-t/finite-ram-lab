# Bounce Handoff

> **Bounce ID:** B157
> **Status:** COMPLETE / STRATA-001 CAPABILITY LAUNCHED

## Launch mechanism

The connected GitHub tool surface does not expose a workflow_dispatch mutation.

To launch the already-authorized bounded capability probe, the workflow now also triggers only when its own file changes on main:

`.github/workflows/strata-001-capability.yml`

This does not broaden the scientific contract or trigger on probe/spec/source edits.

## Expected external effect

Exactly one STRATA-001 capability run should be created from this commit.

## Next action

Discover the STRATA-001 run for this launch commit exactly once.

- completed SUCCESS → inspect its artifact/result;
- queued/in_progress → checkpoint EXTERNAL_WAIT;
- failure → inspect failure only.

## Authority boundary

Capability only.
