# FR-FP-012 Failure Biopsy — exported mmap pointer

Status: **IMPLEMENTATION FAILURE / SCIENTIFIC CONTRACT UNCHANGED**

Failed run:
- workflow: 37144791432
- job: 111266392766
- head: bf2d9d76e74201a603f3de1ab6e7140b01fbff24

Observed exception:

    BufferError: cannot close exported pointers exist

Location:

    _spill_region()
      -> memoryview(mmap)
      -> sliced memoryview used for writes
      -> mmap.close()

## Root cause

The spill implementation retained an exported Python buffer view while trying
to close the source mmap.

The experiment failed before any RSS / cgroup hypothesis gate was evaluated.

This is therefore an implementation failure, not evidence against the
hot/cold-memory hypothesis.

## Repair

Replace the exported memoryview write path with a bounded 1 MiB bytes copy per
write chunk.

Frozen scientific conditions remain unchanged:

- state size: 8 MiB;
- RSS budget: 32 MiB;
- calibrated hot-state budget: 4;
- safe step: 9;
- full state bytes written before source mmap close;
- fsync before close;
- sentinel verification before close;
- process-RSS budget margin: 4 MiB.

The bounded temporary copy is at most 1 MiB, below the already frozen 4 MiB
measurement margin.

## Theory update

A physical-tier primitive must include language/runtime buffer-lifetime
semantics in its implementation contract.

A logically correct move operation is not physically complete until all
exported references to the old resident object have been released.

Claim ceiling:

**IMPLEMENTATION_BUFFER_LIFETIME_BIOPSY_ONLY**
