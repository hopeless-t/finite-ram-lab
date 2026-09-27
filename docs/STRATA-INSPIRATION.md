# Strata inspiration note

Finite RAM Lab's STRATA-001 study was prompted by **Niko1221/Strata**:

https://github.com/Niko1221/Strata

Strata demonstrates a concrete application-level memory hierarchy in which different model data are intentionally assigned to GPU VRAM, host RAM, and SSD.

The specific idea that triggered STRATA-001 was Strata's decision to keep a large SSD-resident lookup table out of host page-cache pressure by using direct I/O on Linux, while retaining mmap as a comparison path.

Finite RAM Lab does not copy that implementation. Instead, it asks a separate systems question:

> Does bypassing page cache for semantically COLD file data preserve semantically HOT anonymous memory under a finite cgroup memory budget?

Observed upstream revision during design:

`8117643ccc68e3d08f80d38e064333742d4474bb`

Thank you to the Strata project for making the architecture, measurements, A/B paths, and implementation rationale unusually inspectable. That openness made the research question here possible.
