# Bounce Handoff

> **Bounce ID:** B063
> **Status:** COMPLETE / CANARY INVALID

## Evidence

Run 36249088056:

- produce: SUCCESS
- upload-artifact@v7: SUCCESS
- download-artifact@v8: SUCCESS
- consume verifier: FAIL

The failure is a checksum path bug in the maintenance workflow.

## Next recommended bounce

Fix only the checksum-generation path, commit, and let the maintenance roundtrip rerun.

## Authority boundary

Do not classify download-artifact@v8 as failed from this run.
