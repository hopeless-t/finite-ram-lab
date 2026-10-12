# FRL-REINSTALL-001 Pilot Result — 2026-10-12

Status: LOCAL PILOT PASS / follow-up required

## Question

How much reinstall/reconstruction machinery can be discarded while preserving the same verified useful behavior?

The pilot compares three fresh-runtime paths on GAYA-CENTRAL:

1. `pip_source`: build/install from the source tree for every trial.
2. `pip_wheel`: build one canonical wheel, then ask pip to install that wheel for every trial.
3. `wheel_extract`: build one canonical wheel, then directly extract it into a fresh runtime directory.

Each reconstructed runtime executes the same deterministic finite-RAM workload and is then deleted. The host page cache is *not* globally dropped; "cold" here means a fresh runtime directory, not a globally cold machine.

## Frozen pilot evidence

Evidence:

- `evidence/FRL-REINSTALL-001/local-20261012-pilot-v1-run2/summary.json`
- `evidence/FRL-REINSTALL-001/local-20261012-pilot-v1-run2/trials.jsonl`
- 10 randomized blocks / 30 total trials

All 30 trials produced the same semantic hash:

`c8bbd8d0eddfea03aa6674b2201be8a6cf060303a8c2b7dab096252442e2cc97`

All per-trial runtime directories reached zero residual bytes after discard.

## Result

| Arm | Median reconstruct | Speedup vs source | Runtime bytes before workload | Workload median |
|---|---:|---:|---:|---:|
| pip_source | 1638.96 ms | 1.00x | 3,698,309 | 52.65 ms |
| pip_wheel | 836.57 ms | 1.96x | 3,698,589 | 52.70 ms |
| wheel_extract | 17.07 ms | 96.04x | 1,470,365 | 52.62 ms |

Direct wheel extraction preserved the measured semantics while removing almost all package-manager work from the reinstall path.

The runtime-size difference is also material: direct extraction started about 2.23 MiB smaller than the pip-installed runtime. During the workload it generated only 6,303 additional bytes, then all of that state was discarded.

## Failure biopsy: canonical-tree pollution

The source-build arm exposed a more important defect than latency.

Running `pip install --target ... .` repeatedly left generated state in the canonical source tree:

- `build/`: about 1.46 MB
- `src/finite_ram_lab.egg-info/`: about 9.7 KB

Those paths were outside the disposable runtime directory, so a target-only cleanup incorrectly reported a perfectly clean discard. They were removed after measurement.

Therefore the next loop must distinguish:

- **runtime residue**: state inside the disposable projection;
- **canonical residue**: state leaked back into the source/canonical tree;
- **shared immutable artifact**: state intentionally retained for many reconstructions.

A reinstall strategy is not clean merely because its target directory disappears.

## Interpretation

The first loop supports the narrow claim that, for this pure-Python package/workload, the package manager is not required in the repeated reconstruction path once a verified wheel exists. A much thinner projection preserved the tested behavior and was roughly two orders of magnitude faster.

This does **not** establish a universal 96x packaging result. Page cache is uncontrolled, the package is small and pure Python, and the wheel was built once outside the per-trial reconstruction timer.

## Immediate next loop

Test whether extraction itself is unnecessary:

`canonical wheel -> direct zipimport -> execute -> discard pointer`

Target hypothesis:

- no copied package tree;
- semantic hash unchanged;
- reconstruction latency approaches metadata-check cost;
- per-runtime materialized bytes approach zero;
- immutable wheel cost is reported separately and amortized rather than hidden.
