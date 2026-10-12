# FRL-REINSTALL-003 Artifact Epoch Result — 2026-10-12

Status: LOCAL 2,000×2 VERIFICATION PASS

## Question

Once an immutable runtime artifact has been cryptographically verified, must every activation re-read and re-hash the entire artifact?

## Design

A canonical wheel is built from an isolated temporary source projection. Its SHA-256 is computed once to establish an artifact epoch. Two activation checks are then randomized for 2,000 blocks:

- `full_sha256`: read and SHA-256 the full wheel on every activation.
- `epoch_identity`: compare `(st_dev, st_ino, st_size, st_mtime_ns, st_ctime_ns)` against the verified epoch.

A mutation probe rewrites one byte without changing file size and restores the original mtime. The probe asks whether ctime-backed epoch identity still detects the ordinary local modification.

## Result

| Check | Median | p95 | Relative |
|---|---:|---:|---:|
| full SHA-256 | 0.94296 ms | 1.08413 ms | 1.0x |
| epoch identity | 0.003665 ms | 0.014271 ms | **257.29x** |

The mutation probe passed:

- same size: yes
- original mtime restored: yes
- ctime changed: yes
- epoch identity detected mutation: yes
- SHA-256 detected mutation: yes

Canonical build residue delta remained 0 bytes.

## Interpretation

For the local immutable-artifact threat model, cryptographic verification can move from every activation to the artifact-epoch boundary. Normal activations can cheaply validate filesystem identity and fall back to full hashing when identity changes.

This is not a cryptographic replacement under a privileged/filesystem-level adversary. The SHA-256 remains the trust root; the identity tuple is an optimization inside a bounded local trust domain.

At ~3.7 microseconds median, reinstall/projection verification is no longer a meaningful contributor to the ~50 ms cold workload path. Further local optimization must move upward into process lifecycle, imports, or workload execution.
