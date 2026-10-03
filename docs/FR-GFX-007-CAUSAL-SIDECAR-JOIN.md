# FR-GFX-007 — Causal Sidecar Join

Status: **OFFLINE CAUSAL JOIN CONTRACT**

Parent: **FR-GFX-006**

## Problem

The low-end observation plane is asynchronous.

A core procfs collector may sample at 500 ms.

Frame timing may arrive near every presented frame.

GPU PMU sampling may run at another cadence.

A backend / Proton identity may be static for the whole run.

If replay code simply joins the **nearest** timestamp, it can attach a future GPU
sample to a past frame.

That creates information the live controller did not possess.

Offline replay can then look artificially strong.

## Causal rule

For target timestamp t:

[
s^*(t)
=
max{
s_i : s_i le t
}.
]

Only the latest already-known sample may be joined.

Then enforce a source-specific maximum age.

If:

[
t-s^*(t) > A_{max}
]

the evidence is **stale** and its value becomes unavailable.

## Three evidence states

A source is not merely present/absent.

It can be:

1. fresh;
2. stale;
3. missing.

These must remain distinct.

In particular:

[
oxed{
	ext{missing GPU busy} 
eq 0% GPU busy
}
]

and:

[
oxed{
	ext{stale GPU busy} 
eq 	ext{current GPU busy}
}
]

## Frozen fixture

The synthetic fixture intentionally includes:

- a frame sample at t=3100;
- a control/base sample at t=3000.

A nearest-neighbor join could incorrectly attach t=3100 to t=3000.

FR-GFX-007 instead retains the last past frame sample at t=1900, then rejects
it as stale.

This explicitly prevents future leakage.

## Backend identity

Every replay record also carries backend metadata.

For Proton experiments, at minimum freeze:

- translation path;
- D3D/Vulkan API;
- Proton identity when known.

A D3D11/DXVK run must not silently mix with a D3D12/VKD3D run.

## CLI

The module can join pre-existing JSONL sidecars offline.

It does not launch telemetry processes.

## Next

FR-GFX-008 should consume a joined trace and perform **offline policy replay**.

The replay evaluator must use only evidence available at each timestamp.

An oracle may look into the future only when explicitly labeled as an offline
upper bound.

## Claim ceiling

**CAUSAL_OFFLINE_JOIN_CONTRACT_ONLY**
