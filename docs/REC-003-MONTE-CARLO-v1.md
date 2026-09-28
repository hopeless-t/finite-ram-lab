# REC-003 Monte Carlo Corruption Campaign v1

> **Status:** IMPLEMENTED / ORDINARY CI IN PROGRESS
> **Authority:** SYNTHETIC REPOSITORY VALIDATION ONLY

## Intellectual lineage

This campaign borrows the design logic of JAXA stochastic robust-design work:

- Toshikazu Motoda, Robust Design Parameter Optimization Incorporating Monte Carlo Simulation (2019), JAXA AIREX a-is/944874, DOI 10.14822/kjsass.67.11_375.
- Taro Tsukamoto, Probability Inference Approach for Stochastic Robust Flight Control Design (2019), DOI 10.2322/tastj.17.197.

The transferable pattern is: vary uncertain or adversarial inputs, measure requirement failure, locate fragile regions, feed counterexamples back into design, and rerun.

## Truth boundary

Monte Carlo rates here are not estimates of real filesystem, hardware, power-loss, or production failure probability.
They are false-accept / false-reject frequencies under the declared synthetic corruption generator only.

## Generator

Each world starts from a valid REC-001 run with randomized run identity, completion state, record count, record kinds, Unicode payloads, and selected configuration values.

20% remain valid controls. 80% receive one to four random corruption operators:

- record after run_end;
- second run_end;
- sequence gap;
- duplicate sequence;
- mixed run_id;
- unsupported schema;
- dropped run_start;
- unknown record type;
- missing required field;
- non-finite numeric sample;
- empty phase;
- non-zero run_start sequence.

## Oracles

The production StreamContractValidator is the strict candidate.
A deliberately relaxed legacy-like per-record validator is retained as a negative control. The attack generator is considered weak if it cannot make that relaxed control admit corrupt worlds.

## Outputs

- false-accept and false-reject counts/rates;
- Wilson 95% intervals;
- convergence checkpoints;
- per-mutation exercise counts.

A zero observed strict false-accept result is never reported as proof that the true rate is zero.

## Atomic writer ownership

Separate adversarial review found a TOCTOU race in the original check-then-open append constructor. Raw evidence paths are now claimed with exclusive creation. Existing paths, including empty files, are rejected rather than shared.

## Feedback loop

Synthetic uncertainty -> Monte Carlo -> counterexample -> deterministic regression -> minimal fix -> Monte Carlo again.
