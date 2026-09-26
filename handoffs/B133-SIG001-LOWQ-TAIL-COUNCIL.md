# Bounce Handoff

> **Bounce ID:** B133
> **Status:** COMPLETE / SIG-001 LOW-Q TAIL COUNCIL CONVERGED

## Trigger

B132 left one materially unresolved design question:

> How large is the calibration burden for a low-q provider only slightly above the conservative admission frontier?

The frozen sample-size grid stopped at N=8192, where LQ_BORDERLINE certified only 4.175% of Monte Carlo repetitions.

## Council

### Statistics

The B132 result is right-censored by the current sample-size grid.

A focused tail extension can distinguish:

- merely-large calibration burden; from
- practically prohibitive calibration burden.

No statistical rule should be relaxed.

### Systems

No additional memory execution is required.

The tail question is pure offline calibration Monte Carlo.

### Red Team

Retain the unsafe low-q control at the larger N values.

If false certification rises above the frozen 5% limit, fail the tail study.

### Economics

This is substantially cheaper and lower-authority than launching a new memory experiment or collecting a large calibration dataset before knowing its likely burden.

### Decision

Run one focused low-q tail Monte Carlo.

Freeze:

- q = 0.10;
- sensitivity = 0.90;
- specificity = 0.85 borderline;
- specificity = 0.90 intermediate;
- specificity = 0.75 unsafe control;
- N = 2048 / 4096 / 8192 / 16384 / 32768 / 65536 / 131072;
- 20,000 repetitions per cell;
- exact same family-wise alpha, Clopper-Pearson bounds, action-cost uncertainty and primary log/geometric admission rule as SIG-001 Design-MC.

## Stop rule

After this tail study, do not extend sample size again automatically.

Use the result to freeze a practical observational calibration requirement or to mark low-q borderline operation as impractical under the current evidence contract.

## Authority boundary

Offline calibration-design computation only.
No predictor, deployed gate, or memory intervention is authorized.
