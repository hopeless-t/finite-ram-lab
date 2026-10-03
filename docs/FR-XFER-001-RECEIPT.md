# FR-XFER-001 Receipt

Status: **PASS / HOSTED LINUX TRANSFER-STAGING PSS PEAK VALIDATED**

- workflow run: 37123741414
- job: 111204797013
- execution head: f6293a4ec0a046becf25d286bf100b5ea1a97678
- artifact ID: 11273653481
- artifact ZIP SHA256: 9c7d8c31f256718e6baefd86dd36839860e92ab257d9c65acee6f7bdcfb99a7f
- spec SHA256: f6ac7221f38d209809660bfceebe641e45290fd5f2b5830265887c66763d8051
- result SHA256: 584c996cb5027731528ba2caf74463535cd22a38b1e64b879e0510677253559c

32 MiB payload, four identical repetitions:

- SOURCE_ONLY: 32,772 KiB baseline-subtracted PSS
- DIRECT_COPY: 65,544 KiB
- STAGED_COPY: 98,316 KiB
- SHARED_VIEW: 32,772 KiB

Derived:

- DIRECT / SOURCE = 2.0x
- STAGED / SOURCE = 3.0x
- SHARED_VIEW / SOURCE = 1.0x
- explicit staging tax over direct = +50%
- shared-view PSS saving vs staged = 66.6667%

Boundary:

Python host-memory proxy only; no CUDA/pinned/PCIe/VRAM claim.

Claim ceiling:

**HOSTED_LINUX_PYTHON_TRANSFER_STAGING_PROXY_ONLY**
