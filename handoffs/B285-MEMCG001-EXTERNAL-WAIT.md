# Bounce Handoff

> **Bounce ID:** B285
> **Status:** EXTERNAL_WAIT / MEMCG-001 HOSTED RUN IN PROGRESS

Exact launch commit:

`68f9e1f9f170ff4181255b6669ebcb94221b70a5`

Scientific run:

`36449072026`

Single status read in B285:

`in_progress`

No second read was performed.

## Next mathematical lenses after MEMCG-001

Do not add all methods blindly. Select based on the observed signal.

Candidate lenses:

1. **Periodogram / FFT**
   - detect stable periodicity in the first-difference or jump-indicator sequence;
   - candidate periods 2,4,8,...,64,128 pages;
   - useful if spacing is approximately stationary.

2. **Wavelet / multiresolution analysis**
   - detect periodicity whose phase or scale changes during the trial;
   - useful if charge-stock refill produces nonstationary staircase behavior.

3. **Bayesian change-point detection**
   - infer posterior locations of regime changes without fixing 64 pages;
   - compare posterior spacing distribution against the H64 hypothesis.

4. **Hidden Markov / state-space model**
   - model latent states such as stock-available vs refill/charge event;
   - useful if the observed memory.current sequence is a noisy projection of hidden accounting state.

5. **Minimum Description Length / compression score**
   - ask which model compresses the observed sequence best:
     page-linear, 64-page staircase, arbitrary staircase, or noise.

6. **Entropy / mutual information**
   - measure information between allocation-step modulo Q and jump occurrence;
   - scan Q without privileging 64.

7. **Symbolic regression**
   - only after enough independent axes exist;
   - search simple relations among H, hot, K, chunk, streams, capacity while penalizing complexity.

8. **Integer-relation / rational lattice search**
   - test whether observed step sizes are integer combinations of 4 KiB, 64 KiB, 256 KiB, 2 MiB.

9. **Allan variance / scale-dependent noise**
   - distinguish quantized drift from white/readout noise and slow runner drift across sampling scales.

10. **Counterfactual model comparison**
    - compare predictive error of H64 against learned alternative Q and against no-quantization controls using held-out blocks.

Priority after MEMCG-001:
- if clear periodic jumps: FFT + MDL + held-out prediction;
- if phase shifts/nonstationary: wavelet + Bayesian change-point;
- if noisy/latent: HMM/state-space + Allan variance;
- if no visible pattern: entropy/mutual-information scan + counterexample SQL.

No mathematical method may upgrade a mechanism without independent block replication and control separation.

## Next fresh-bounce action

Read run `36449072026` exactly once.

- success -> fetch artifacts once, evaluate preregistered H64 decision, then choose mathematical follow-up based on signal morphology;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Hosted research only.
No local-PC execution.
No memory-control policy.
