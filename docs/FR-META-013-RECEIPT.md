# FR-META-013 Receipt

Status: **PASS / PIP CACHE CONFIGURATION QUALIFIED / CACHE-HIT SPEED PENDING PR DOGFOOD**

Implementation qualification:

- workflow run: 37138413480
- job: 111247595502
- execution head: 9ee0185018fde319041f0338c1b1f4ca1c00ee1e
- qualification artifact ID: 11279392283
- artifact ZIP SHA256: bd67068c2da8afc158fb0a64f93fc092b5c030dfb2d106ae920d169d8cb16678

Implementation-run cache observation:

- setup-python cache mode: write
- initial cache lookup: not found
- Install start: 2026-10-03T16:51:55.906Z
- next Compile start: 2026-10-03T16:52:16.094Z
- approximate uncached Install span: 20.19 s
- cache saved successfully after the run
- saved key:
  setup-python-Linux-x64-24.04-Ubuntu-python-3.12.14-pip-0297d4812f34fab52178c1cb36ba6dae036262df89c4b33cd7779c5cc05da388

Scientific CI surface unchanged:

- compile;
- full unit suite;
- MC smoke;
- environment probe;
- meta qualification.

Decision:

**ENABLE_SETUP_PYTHON_PIP_CACHE**

A speed claim requires the subsequent receipt/PR run to restore this key and
show an observed Install reduction.

Claim ceiling:

**CI_DEPENDENCY_CACHE_OPTIMIZATION_ONLY**
