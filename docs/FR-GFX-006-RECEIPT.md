# FR-GFX-006 — Read-only Collector Qualification Receipt

Status: **PASS / RUNNABLE READ-ONLY COLLECTOR HARNESS VALIDATED**

## Qualification

- workflow run: 37109243492
- job: 111163783088
- execution head: 3877eedd251b1482294f6bfb5778dd0cef3c0cd0
- targeted tests: 4/4 PASS
- artifact ID: 11268788826
- artifact ZIP SHA256: 8968f0341bbd907fe857dcf9f6e6e6c3ac4c755cc61cf6c195a19c5278da956a
- spec SHA256: 4040213c49d906d7deb8eace3446525cbea9aed4b0bf77e744ec11214ab0d20f
- self-trace SHA256: e4ec73c43472dcab68b6b53c0215c3fcaed9824a5c7d21411076f317ae4920ba
- self-receipt SHA256: dc66c6a27a5a7dd2f4f4fe6307d9671e464045e30ecf1d72c8e3d82df2a3bc1d

## Hosted-runner self measurement

Stress cadence only:

- samples: 20
- interval: 10 ms
- wall time: 0.205224 s
- collector CPU time: 0.013940 s
- one-core equivalent CPU: 6.7924%
- peak observed collector RSS: 18,996 KiB
- JSONL bytes: 12,360
- bytes/sample: 618

These numbers are **not transferred to the user's machine**.

They exist to prove that read-only sampling has non-zero CPU/RSS/IO cost and
that the collector can account for its own overhead.

## Read-only contract

The harness:

- does not write sysfs;
- does not change driver or game settings;
- does not inject or signal the target process;
- does not launch frame/GPU telemetry processes;
- writes only the requested output stream.

## Claim ceiling

**RUNNABLE_READ_ONLY_COLLECTOR_HARNESS_ONLY**
