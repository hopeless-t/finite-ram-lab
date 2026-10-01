# B451 — Clean Dynamic Frontier Post-run Analyzer v0.1

Status: **ANALYSIS PLANE FROZEN BEFORE PHYSICAL OBSERVATION**.

No Clean Dynamic Frontier physical workflow was launched in this bounce.

## 1. Purpose

B447-B450 froze:

- the prospective study design;
- its implementation;
- stable identity requirements;
- prelaunch predictions.

B451 freezes the analysis path before any physical result exists.

This prevents changing:

- frontier objectives;
- candidate arms;
- bootstrap unit;
- stability threshold;
- capacity-transition logic;
- clamp replay rules

after seeing the measurements.

## 2. Candidate and reference families

Candidate Pareto arms:

- dontneed_32m
- dontneed_48m
- dontneed_64m
- dontneed_80m
- dontneed_96m

Reference only:

- buffered

The buffered arm remains in the physical experiment but is not mixed into the narrower DONTNEED cadence frontier.

## 3. PRIMARY and DESCRIPTIVE projections

PRIMARY objectives:

- peak_ram_bytes
- ephemeral_excess_bytes
- memory_high_events
- pgscan
- advice_calls

DESCRIPTIVE extension:

- scan_elapsed_ns

The analyzer always evaluates PRIMARY first.

Timing can alter only the descriptive sensitivity result and cannot silently acquire primary authority.

## 4. Block bootstrap semantics

The independent experimental unit is the runner block.

Within one capacity, a sampled block ID is applied to **all candidate arms together**.

This preserves block-common runner variation.

The analyzer does not independently resample each arm.

For a capacity transition such as 144 -> 160 MiB:

- the lower-capacity block sample is drawn jointly across its arms;
- the upper-capacity block sample is drawn jointly across its arms;
- the two capacity samples are independent.

This matches the prospective design.

## 5. Frozen outputs

For each capacity:

- aggregate PRIMARY frontier;
- aggregate PRIMARY+DESCRIPTIVE frontier;
- bootstrap membership probability for every candidate arm;
- whether every aggregate PRIMARY frontier arm meets the frozen 0.90 stability threshold;
- whether the observed PRIMARY frontier matches the B449 prelaunch twin.

For each adjacent capacity pair:

- probability of any PRIMARY frontier loss;
- per-arm PRIMARY loss probability;
- corresponding DESCRIPTIVE transition sensitivity.

The analyzer also emits:

- aggregate lost-arm sets;
- projection classification;
- B445 intrinsic-capacity-clamp replay;
- fitted transient base;
- clean-floor median;
- clean ephemeral base excess;
- pressure classification accuracy.

## 6. Clamp replay

The physical result is not forced to use the old B445 fitted value.

Instead the post-run analyzer re-estimates the transient base from the new prospective cells using the same frozen estimator:

median(peak_mib - release_interval_mib)

over zero-MemoryHigh-event cells.

It then evaluates:

P_peak(H,K) ~= min(B_peak + K, H)

and reports the pressure classification accuracy and residuals.

This lets the new study confirm, shift, or falsify B445 without changing the formula after observation.

## 7. Prelaunch twin comparison

The analyzer compares the measured PRIMARY aggregate frontier against the frozen B449 expectation:

- H144: {32,48,96}
- H160: {32,48,96}
- H176: {32,48,96}

A mismatch is evidence.

It is not automatically failure.

In particular, disappearance of an old frontier arm under capacity expansion would trigger the B438/B439 dynamic investigation path.

## 8. CLI

The analyzer can be run as one fixed command against:

- the frozen study spec;
- the aggregate summary artifact.

Default settings:

- bootstrap iterations = 100,000
- seed = 2026100151.

It writes one JSON analysis receipt.

## 9. Software qualification

A temporary isolated subtree:

- research candidate lane
- b451_qual/

was used.

No host write, canonical write, promotion, or physical workload occurred.

Pure analyzer unit tests:

- 4 run
- 4 PASS
- 0 failures
- 0 errors
- ~0.425 s

Output digest:

- sha256:d1a18fbeda8a1f2f70e0bc00db2b8015674466555158283b56d2e3831b8664c0

## 10. CLI qualification

A synthetic B449-world summary was written to files and passed through the CLI entry point.

The first direct `python -m` attempt failed only because the temporary subtree was not installed or on PYTHONPATH.

The branch module itself had already imported successfully in the unit suite.

With the qualification subtree explicitly placed on `sys.path`, the actual `main()` CLI path returned:

- return code 0
- 500 bootstrap iterations
- seed 451

Recovered synthetic result:

- PRIMARY H144 = {32,48,96}
- PRIMARY H160 = {32,48,96}
- PRIMARY H176 = {32,48,96}
- 144->160 any-loss probability = 0
- 160->176 any-loss probability = 0
- clamp pressure classification accuracy = 1.0
- transient base ~= 78.609 MiB
- clean floor ~= 76.7 MiB
- clean ephemeral base excess ~= 1.909 MiB

CLI output digest:

- sha256:77c351e12391838d5ba372aaf3c92d2b3020c167b178d1f572ece4fd736479f3

## 11. Cleanup

The B451 qualification subtree was removed.

Post-cleanup research-lane status returned only the pre-existing:

- rich59_staging/

No B451 qualification files remain in the local candidate workspace.

## 12. New principle H451 — Analysis Freeze Before Observation

> When a physical study is intended to test frontier topology, the analysis projection and resampling semantics are part of the experimental contract and should be executable before the physical observations exist.

This complements:

- B441 Objective Evidence Gate;
- B442 Frontier Stability Gate;
- B443 Dynamic Frontier Qualification Contract.

## 13. Current boundary

The prospective experiment now has:

- frozen design;
- frozen implementation;
- software qualification;
- frozen digital twin;
- frozen post-run analyzer.

The remaining missing element is the physical dataset itself.

B451 does not authorize:

- workflow launch;
- retries;
- paid-resource use;
- B425 ambient execution;
- controller/default promotion.
