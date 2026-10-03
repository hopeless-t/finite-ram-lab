# FR-META-013 — CI pip Cache

Status: **DOGFOOD PERFORMANCE CANDIDATE**

Parent: **FR-META-012**

## Fixed-cost biopsy

Recent uncached CI Install spans were approximately:

- 19.006 s;
- 16.256 s;
- 14.679 s;
- 16.397 s.

Median is above 16 seconds.

The repository installs the analysis extras on every CI run:

- numpy;
- scipy;
- pandas;
- statsmodels.

## Candidate

Use the cache support built into actions/setup-python@v7:

    cache: pip
    cache-dependency-path: pyproject.toml

Official setup-python and GitHub Actions documentation describe this as caching
pip's global package data keyed by the dependency file.

The scientific test suite, compiler checks, MC smoke, environment probe, and
meta qualifier are unchanged.

## Experiment semantics

The first implementation run may be a cache miss. That is expected.

It can populate the cache after a successful run.

The meaningful speed observation is a later same-key receipt/PR or descendant
run:

- cache restore receipt;
- Install step wall duration;
- full CI still PASS.

No speed claim is made merely because the YAML contains a cache option.

## Sources

- https://github.com/actions/setup-python
- https://docs.github.com/actions/automating-builds-and-tests/building-and-testing-python

## Claim ceiling

**CI_DEPENDENCY_CACHE_OPTIMIZATION_ONLY**
