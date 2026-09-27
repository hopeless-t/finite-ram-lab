# CURRENT

> **Latest bounce:** B180
> **Stage:** STRATA-002 / PILOT PASS

## Finding

Sliding per-chunk POSIX_FADV_DONTNEED reduced page-cache pressure to approximately O_DIRECT level in the hosted pilot while retaining ordinary buffered reads.

NOREUSE did not materially reduce immediate pressure.

## Canonical evidence

- `docs/STRATA-002-PILOT-RESULT.md`
- `evidence/STRATA-002-PILOT/summary.json`

## Next action

Converge confirmatory Council and Monte Carlo size `buffered_dontneed vs buffered`.

## Local dogfood

The MVCA tunnel remains transport-ready but has no finite-ram-specific active execution grant.

## Authority boundary

Hosted research only.
