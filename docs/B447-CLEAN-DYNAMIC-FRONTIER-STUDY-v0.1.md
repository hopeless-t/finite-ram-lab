# B447 — Clean Dynamic Frontier Study v0.1

Status: **FROZEN DESIGN / NOT LAUNCHED**.

## 1. Goal

Produce the first prospectively qualified dynamic-capacity dataset that can simultaneously measure:

- intrinsic scan peak;
- clean persistent floor;
- phase-local ephemeral excess;
- observer contamination;
- pressure/reclaim response;
- intervention cost.

The design directly addresses the failure modes found in B440-B446.

## 2. Capacity axis

Change only:

**memory.high**

at:

- 144 MiB
- 160 MiB
- 176 MiB.

All points run under the same source and observer contract.

The 160 MiB point is measured again prospectively. Historical STRATA-004 is not silently reused because B444 rejected its observer identity.

## 3. Fixed workload

Freeze:

- Ubuntu 24.04 runner family;
- Python 3.12;
- MemoryMax 320 MiB;
- hot anonymous allocation 64 MiB;
- cold file 96 MiB;
- read chunk 4 MiB;
- identical cold-file preparation;
- identical integrity checks;
- identical checkpoint observer implementation.

Only MemoryHigh and release arm vary inside the frozen design matrix.

## 4. Arms

- buffered
- DONTNEED 32 MiB
- DONTNEED 48 MiB
- DONTNEED 64 MiB
- DONTNEED 80 MiB
- DONTNEED 96 MiB.

These preserve:

- a low-peak/high-intervention arm;
- intermediate arms;
- the known boundary region;
- the one-call end-of-stream arm;
- a no-advice reference.

## 5. Replication

Independent unit:

**runner block**

Eight blocks per capacity.

Total:

3 capacities
x 6 arms
x 8 blocks
=
**144 trials**.

The number eight is a study-specific directional choice, not a universal replication rule.

B442 showed that four blocks were insufficient for stable timing topology. Timing remains descriptive here, but the larger block count also improves estimation of clean floor and ephemeral excess.

## 6. Measurement ordering

Inside each measured trial:

1. before_scan
2. scan
3. **post_scan_pre_observer**
4. file/hot residency diagnostics
5. **post_scan_post_observer**
6. post_retouch.

This ordering gives paired quantities in the same trial.

### Clean persistent floor

post_scan_pre_observer

### Observer contribution

post_scan_post_observer
-
post_scan_pre_observer

### Clean phase-local ephemeral excess

max_scan_memory
-
post_scan_pre_observer.

This is the quantity B446 could not identify retrospectively.

## 7. Primary measurements

- peak_ram_bytes
- clean_floor_bytes
- ephemeral_excess_bytes
- MemoryHigh events
- pgscan
- advice_calls.

### Why advice_calls is primary

The old pressure-only Pareto projection makes shorter release intervals dominate larger intervals almost trivially.

Advice-call count captures a deterministic intervention-frequency cost and creates a real memory-versus-intervention tradeoff without relying on noisy hosted timing.

## 8. Descriptive measurements

- scan elapsed
- throughput.

B440/B442 showed why hosted timing must not create the primary frontier claim.

It remains available for sensitivity analysis under B441.

## 9. Diagnostics

- observer_current_delta
- file post-residency
- pgsteal
- hot retouch
- swap
- OOM.

Observer delta is a measurement-quality diagnostic, not a workload performance benefit.

## 10. Primary frontier

The predeclared minimized objectives are:

- peak RAM
- clean ephemeral excess
- MemoryHigh events
- pgscan
- advice calls.

This allows several meaningful frontier arms to coexist:

- smaller cadence may reduce peak but increase advice frequency;
- larger cadence may reduce advice calls but approach pressure;
- additional MemoryHigh may activate pressure-free versions of larger-cadence plans.

No timing coordinate is needed for this tradeoff.

## 11. Stability gate

The study freezes:

- independent unit = runner block
- minimum units/cell = 8
- frontier stability threshold = 0.90
- missing data = FAIL_CLOSED
- raw receipts required.

The 0.90 threshold is specific to this directional hosted study and is not a universal standard.

Any primary frontier transition below that stability threshold remains exploratory.

## 12. Expected structural predictions

B445 gives a design heuristic:

B_peak ~= 78.609 MiB

so pressure onset is expected near:

K > H - 78.609.

Predicted directional regions:

### H=144

- 32/48/64 likely pressure-free
- 80/96 likely pressured.

### H=160

- 32/48/64/80 likely pressure-free
- 96 likely pressured.

### H=176

- all tested DONTNEED intervals likely pressure-free.

These are **predictions**, not acceptance criteria.

Observed data may falsify them.

## 13. Analysis order after execution

1. validate complete 144-trial matrix;
2. validate source/observer identity;
3. freeze raw receipts;
4. evaluate PRIMARY objectives only;
5. estimate clean floor and ephemeral excess;
6. resample by runner block;
7. test 0.90 frontier stability;
8. run descriptive timing sensitivity separately;
9. compare with B445 clamp model;
10. only then discuss mechanism.

## 14. Launch boundary

This bounce does not launch the workflow.

Design freeze grants no:

- GitHub Actions execution;
- retry;
- paid-resource use;
- local-PC execution;
- controller/default promotion.

Implementation may proceed in a separate bounce without launch authority.
