# B493 — Repaired Governor v2.1 Receipt

Status: **PASS / GOVERNOR v2.1 QUALIFIED**

## Frozen execution

- workflow run: 36953891535
- job: 110672494146
- execution head: a22012256caf5da711fafdc44e2d8310912122d7
- artifact ID: 11205141567
- artifact ZIP SHA256: 4ae0fcc1a8f9989ca7c52c05cef1db98b6dc188212b031787f2bdca0eb87342a
- governor JSON SHA256: 27a1f6c68d64cce30d808748e7befa0b97f99610ab56bcaaf199166fa0cbc859

## Qualified policy

Implementation:

`TILED_WHERE`

Policy version:

`v2.1`

Breakpoints:

- 50,696,192 B -> q2
- 58,941,440 B -> q4
- 71,512,064 B -> q7

Every point carries:

- n = 27 independent hosted-runner observations
- rank-max one-step floor = 27/28 ~= 96.4286%

## Online-update behavior

The previous q7 v2 boundary was:

`71,507,968 B`

B491 observed one non-drift +4 KiB exceedance and B492 absorbed it.

Therefore v2.1 correctly treats:

`71,507,968 B`

as insufficient for q7 and selects q4.

q7 becomes eligible at:

`71,512,064 B`.

This verifies that runtime evidence can move a policy boundary without silently
discarding the observation.

## Fail-closed behavior

A requested coverage level unsupported by the current evidence remains
ineligible.

In particular, 99% still fails closed because n=27 is below n=99.

## Claim ceiling

**NON_DRIFT_UPDATED_REPAIRED_GOVERNOR_V2_1**

## Next

Expose v2.1 through a stable GitHub Actions application surface.

The surface should accept:

- peak budget;
- minimum evidence coverage;

and emit:

- selected q;
- selected empirical-max boundary;
- sample count;
- rank coverage floor;
- implementation version;
- evidence receipt.

The application surface must not require ordinary callers to import the research
harness directly.
