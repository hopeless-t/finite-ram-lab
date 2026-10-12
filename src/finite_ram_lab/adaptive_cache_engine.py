from __future__ import annotations

import concurrent.futures
import ctypes
import hashlib
import heapq
import os
import platform
import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Hashable, Iterable, Sequence

from .sim import lru_faults, opt_faults

_C_SOURCE = r'''
#include <stdint.h>
#include <stdlib.h>
#include <stddef.h>
#include <limits.h>

typedef struct { uint32_t next; uint32_t page; uint32_t ticket; } Entry;
static inline int ent_gt(Entry a, Entry b){
    if(a.next!=b.next) return a.next>b.next;
    if(a.page!=b.page) return a.page>b.page;
    return a.ticket>b.ticket;
}
static inline void hpush(Entry *h,size_t *sz,Entry e){
    size_t i=(*sz)++; h[i]=e;
    while(i){ size_t p=(i-1)/2; if(!ent_gt(h[i],h[p])) break; Entry t=h[i];h[i]=h[p];h[p]=t;i=p; }
}
static inline Entry hpop(Entry *h,size_t *sz){
    Entry out=h[0]; h[0]=h[--(*sz)]; size_t i=0;
    for(;;){ size_t l=i*2+1,r=l+1,b=i; if(l<*sz&&ent_gt(h[l],h[b]))b=l; if(r<*sz&&ent_gt(h[r],h[b]))b=r; if(b==i)break; Entry t=h[i];h[i]=h[b];h[b]=t;i=b; }
    return out;
}
static uint64_t opt_heap_one(const uint32_t *trace,const uint32_t *next_use,size_t n,uint32_t universe,uint32_t cap){
    if(cap==0)return UINT64_MAX;
    uint8_t *resident=calloc(universe?universe:1,1);
    uint32_t *ticket=malloc((universe?universe:1)*sizeof(uint32_t));
    Entry *heap=malloc((n?n:1)*sizeof(Entry));
    if(!resident||!ticket||!heap){free(resident);free(ticket);free(heap);return UINT64_MAX;}
    for(uint32_t p=0;p<universe;p++)ticket[p]=UINT32_MAX;
    size_t hs=0;uint32_t size=0;uint64_t faults=0;
    for(uint32_t i=0;i<(uint32_t)n;i++){
        uint32_t p=trace[i]; ticket[p]=i;
        if(resident[p]){hpush(heap,&hs,(Entry){next_use[i],p,i});continue;}
        faults++;
        if(size>=cap){
            for(;;){ Entry e=hpop(heap,&hs); if(resident[e.page]&&ticket[e.page]==e.ticket){resident[e.page]=0;size--;break;} }
        }
        resident[p]=1;size++;hpush(heap,&hs,(Entry){next_use[i],p,i});
    }
    free(resident);free(ticket);free(heap);return faults;
}
static uint64_t opt_scan_one(const uint32_t *trace,const uint32_t *next_use,size_t n,uint32_t universe,uint32_t cap){
    if(cap==0)return UINT64_MAX;
    uint8_t *resident=calloc(universe?universe:1,1);
    uint32_t *current_next=malloc((universe?universe:1)*sizeof(uint32_t));
    if(!resident||!current_next){free(resident);free(current_next);return UINT64_MAX;}
    for(uint32_t p=0;p<universe;p++)current_next[p]=(uint32_t)(n+1);
    uint32_t size=0;uint64_t faults=0;
    for(size_t i=0;i<n;i++){
        uint32_t p=trace[i];current_next[p]=next_use[i];
        if(resident[p])continue;
        faults++;
        if(size>=cap){
            uint32_t victim=UINT32_MAX,far=0;
            for(uint32_t q=0;q<universe;q++)if(resident[q]&&(victim==UINT32_MAX||current_next[q]>far)){victim=q;far=current_next[q];}
            if(victim!=UINT32_MAX){resident[victim]=0;size--;}
        }
        resident[p]=1;size++;
    }
    free(resident);free(current_next);return faults;
}
int opt_hybrid_sweep_dense(const uint32_t *trace,const uint32_t *next_use,size_t n,uint32_t universe,const uint32_t *caps,size_t m,uint32_t heap_max,uint64_t *out){
    for(size_t j=0;j<m;j++){
        out[j]=(caps[j]<=heap_max)?opt_heap_one(trace,next_use,n,universe,caps[j]):opt_scan_one(trace,next_use,n,universe,caps[j]);
        if(out[j]==UINT64_MAX)return -1;
    }
    return 0;
}
static inline void bit_add(uint32_t *bit,size_t n,size_t idx0,int delta){size_t i=idx0+1;while(i<=n){bit[i]=(uint32_t)((int)bit[i]+delta);i+=i&(~i+1);}}
static inline uint32_t bit_sum(const uint32_t *bit,size_t idx0){uint32_t s=0;size_t i=idx0+1;while(i>0){s+=bit[i];i-=i&(~i+1);}return s;}
int lru_curve_dense(const uint32_t *trace,size_t n,uint32_t universe,uint64_t *out){
    uint32_t *bit=calloc(n+1,sizeof(uint32_t));int64_t *last=malloc((universe?universe:1)*sizeof(int64_t));uint64_t *hist=calloc((universe?universe:1),sizeof(uint64_t));
    if(!bit||!last||!hist){free(bit);free(last);free(hist);return -1;}
    for(uint32_t p=0;p<universe;p++)last[p]=-1;uint64_t cold=0;
    for(size_t i=0;i<n;i++){
        uint32_t p=trace[i];int64_t prev=last[p];
        if(prev<0)cold++;
        else{uint32_t before=i?bit_sum(bit,i-1):0;uint32_t through=bit_sum(bit,(size_t)prev);uint32_t d=before-through;if(d<universe)hist[d]++;bit_add(bit,n,(size_t)prev,-1);}
        bit_add(bit,n,i,1);last[p]=(int64_t)i;
    }
    uint64_t suffix=0;for(int64_t d=(int64_t)universe-1;d>=0;d--){suffix+=hist[d];if(d>=1)out[d-1]=cold+suffix;}if(universe>0)out[universe-1]=cold;
    free(bit);free(last);free(hist);return 0;
}
'''

_U32 = ctypes.c_uint32
_U64 = ctypes.c_uint64
_NATIVE_LOCK = threading.Lock()
_NATIVE: ctypes.CDLL | None | bool = None
_EXECUTOR: concurrent.futures.ThreadPoolExecutor | None = None
_COMPILER_FINGERPRINT: str | None = None


def _cache_root() -> Path:
    raw = os.environ.get("FRL_NATIVE_CACHE")
    return Path(raw).expanduser() if raw else Path.home() / ".cache" / "finite-ram-lab" / "native"


def _compiler_fingerprint() -> str:
    global _COMPILER_FINGERPRINT
    if _COMPILER_FINGERPRINT is not None:
        return _COMPILER_FINGERPRINT
    cc = shutil.which("cc")
    version = "unavailable"
    if cc is not None:
        try:
            proc = subprocess.run(
                [cc, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            if proc.stdout:
                version = proc.stdout.splitlines()[0]
        except OSError:
            pass
    _COMPILER_FINGERPRINT = "|".join(
        [
            cc or "no-cc",
            version,
            platform.system(),
            platform.machine(),
            ":".join(platform.libc_ver()),
        ]
    )
    return _COMPILER_FINGERPRINT


def _native_digest() -> str:
    key = (
        _C_SOURCE
        + "\n-O3 -shared -fPIC\n"
        + _compiler_fingerprint()
    ).encode()
    return hashlib.sha256(key).hexdigest()[:24]


def _compile_native() -> Path | None:
    cc = shutil.which("cc")
    if cc is None:
        return None
    root = _cache_root() / _native_digest()
    lib = root / "libfrl_cache.so"
    if lib.exists():
        return lib
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="frl-native-build-") as td:
        src = Path(td) / "cache.c"
        out = Path(td) / "libfrl_cache.so"
        src.write_text(_C_SOURCE, encoding="utf-8")
        proc = subprocess.run(
            [cc, "-O3", "-shared", "-fPIC", str(src), "-o", str(out)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return None
        tmp = root / f".{lib.name}.{os.getpid()}.tmp"
        shutil.copy2(out, tmp)
        os.replace(tmp, lib)
    return lib


def _load_native() -> ctypes.CDLL | None:
    global _NATIVE
    if isinstance(_NATIVE, ctypes.CDLL):
        return _NATIVE
    if _NATIVE is False:
        return None
    with _NATIVE_LOCK:
        if isinstance(_NATIVE, ctypes.CDLL):
            return _NATIVE
        if _NATIVE is False:
            return None
        path = _compile_native()
        if path is None:
            _NATIVE = False
            return None
        try:
            lib = ctypes.CDLL(str(path))
            lib.opt_hybrid_sweep_dense.argtypes = [
                ctypes.POINTER(_U32), ctypes.POINTER(_U32), ctypes.c_size_t, _U32,
                ctypes.POINTER(_U32), ctypes.c_size_t, _U32, ctypes.POINTER(_U64),
            ]
            lib.opt_hybrid_sweep_dense.restype = ctypes.c_int
            lib.lru_curve_dense.argtypes = [
                ctypes.POINTER(_U32), ctypes.c_size_t, _U32, ctypes.POINTER(_U64),
            ]
            lib.lru_curve_dense.restype = ctypes.c_int
        except OSError:
            _NATIVE = False
            return None
        _NATIVE = lib
        return lib


def native_status() -> dict[str, Any]:
    lib = _load_native()
    path = None if lib is None else str(_cache_root() / _native_digest() / "libfrl_cache.so")
    return {"available": lib is not None, "cache_path": path, "digest": _native_digest()}


def _executor() -> concurrent.futures.ThreadPoolExecutor:
    global _EXECUTOR
    if _EXECUTOR is None:
        _EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(4, os.cpu_count() or 1)))
    return _EXECUTOR


def _python_opt_dense(dense: Sequence[int], next_use: Sequence[int], universe: int, capacity: int) -> int:
    if capacity <= 0:
        raise ValueError("capacity must be positive")
    resident = [False] * universe
    ticket = [-1] * universe
    heap: list[tuple[int, int, int]] = []
    faults = 0
    size = 0
    for i, page in enumerate(dense):
        nxt = next_use[i]
        ticket[page] = i
        if resident[page]:
            heapq.heappush(heap, (-nxt, page, i))
            continue
        faults += 1
        if size >= capacity:
            while True:
                _neg, victim, stamp = heapq.heappop(heap)
                if resident[victim] and ticket[victim] == stamp:
                    resident[victim] = False
                    size -= 1
                    break
        resident[page] = True
        size += 1
        heapq.heappush(heap, (-nxt, page, i))
    return faults


def _python_lru_curve(dense: Sequence[int], universe: int) -> list[int]:
    n = len(dense)
    bit = [0] * (n + 2)
    last = [-1] * universe
    hist = [0] * universe
    cold = 0

    def add(index: int, delta: int) -> None:
        i = index + 1
        while i < len(bit):
            bit[i] += delta
            i += i & -i

    def prefix(index: int) -> int:
        if index < 0:
            return 0
        s = 0
        i = index + 1
        while i:
            s += bit[i]
            i -= i & -i
        return s

    for i, page in enumerate(dense):
        prev = last[page]
        if prev < 0:
            cold += 1
        else:
            dist = prefix(i - 1) - prefix(prev)
            hist[dist] += 1
            add(prev, -1)
        add(i, 1)
        last[page] = i

    out = [cold] * universe
    suffix = 0
    for dist in range(universe - 1, -1, -1):
        suffix += hist[dist]
        if dist >= 1:
            out[dist - 1] = cold + suffix
    return out


@dataclass
class PreparedTrace:
    dense: tuple[int, ...]
    next_use: tuple[int, ...]
    unique_pages: int
    symbols: tuple[Hashable, ...]
    _native_trace: Any = field(default=None, init=False, repr=False)
    _native_next: Any = field(default=None, init=False, repr=False)
    _lru_curve_cache: tuple[int, ...] | None = field(default=None, init=False, repr=False)

    @classmethod
    def prepare(cls, trace: Iterable[Hashable]) -> "PreparedTrace":
        codes: dict[Hashable, int] = {}
        symbols: list[Hashable] = []
        dense: list[int] = []
        for page in trace:
            code = codes.get(page)
            if code is None:
                code = len(codes)
                codes[page] = code
                symbols.append(page)
            dense.append(code)
        if not dense:
            raise ValueError("trace must not be empty")
        n = len(dense)
        universe = len(codes)
        last = [n + 1] * universe
        next_use = [n + 1] * n
        for i in range(n - 1, -1, -1):
            page = dense[i]
            next_use[i] = last[page]
            last[page] = i
        return cls(tuple(dense), tuple(next_use), universe, tuple(symbols))

    @property
    def length(self) -> int:
        return len(self.dense)

    def profile(self) -> dict[str, Any]:
        return {
            "length": self.length,
            "unique_pages": self.unique_pages,
            "compression_ratio": self.unique_pages / self.length,
            "native": native_status(),
        }

    def _arrays(self) -> tuple[Any, Any]:
        if self._native_trace is None:
            self._native_trace = (_U32 * self.length)(*self.dense)
            self._native_next = (_U32 * self.length)(*self.next_use)
        return self._native_trace, self._native_next

    def _native_opt_chunk(self, capacities: Sequence[int], heap_max: int) -> list[int]:
        lib = _load_native()
        if lib is None:
            raise RuntimeError("native backend unavailable")
        trace_arr, next_arr = self._arrays()
        caps = (_U32 * len(capacities))(*capacities)
        out = (_U64 * len(capacities))()
        rc = lib.opt_hybrid_sweep_dense(
            trace_arr, next_arr, self.length, self.unique_pages, caps, len(capacities), heap_max, out
        )
        if rc != 0:
            raise RuntimeError("native OPT sweep failed")
        return [int(x) for x in out]

    def opt_sweep(
        self,
        capacities: Sequence[int],
        *,
        backend: str = "auto",
        workers: int | str = "auto",
        heap_max: int = 28,
    ) -> dict[int, int]:
        caps = [int(c) for c in capacities]
        if not caps:
            return {}
        if any(c <= 0 for c in caps):
            raise ValueError("capacities must be positive")
        use_native = backend in {"auto", "native"} and _load_native() is not None
        if backend == "native" and not use_native:
            raise RuntimeError("native backend requested but unavailable")
        if not use_native:
            return {c: _python_opt_dense(self.dense, self.next_use, self.unique_pages, c) for c in caps}

        if workers == "auto":
            worker_count = min(4, os.cpu_count() or 1) if len(caps) >= 6 else 1
        else:
            worker_count = max(1, int(workers))
        worker_count = min(worker_count, len(caps))
        if worker_count <= 1:
            values = self._native_opt_chunk(caps, heap_max)
            return dict(zip(caps, values))

        def weight(c: int) -> float:
            if c <= heap_max:
                return 1.0
            return max(0.05, (self.unique_pages - min(c, self.unique_pages)) / max(1, self.unique_pages))

        buckets: list[list[int]] = [[] for _ in range(worker_count)]
        loads = [0.0] * worker_count
        for c in sorted(caps, key=weight, reverse=True):
            idx = min(range(worker_count), key=loads.__getitem__)
            buckets[idx].append(c)
            loads[idx] += weight(c)
        active = [b for b in buckets if b]
        parts = list(_executor().map(lambda b: self._native_opt_chunk(b, heap_max), active))
        merged: dict[int, int] = {}
        for bucket, values in zip(active, parts):
            merged.update(zip(bucket, values))
        return {c: merged[c] for c in caps}

    def lru_curve(self, *, backend: str = "auto") -> tuple[int, ...]:
        if self._lru_curve_cache is not None:
            return self._lru_curve_cache
        use_native = backend in {"auto", "native"} and _load_native() is not None
        if backend == "native" and not use_native:
            raise RuntimeError("native backend requested but unavailable")
        if use_native:
            lib = _load_native()
            assert lib is not None
            trace_arr, _next_arr = self._arrays()
            out = (_U64 * self.unique_pages)()
            rc = lib.lru_curve_dense(trace_arr, self.length, self.unique_pages, out)
            if rc != 0:
                raise RuntimeError("native LRU curve failed")
            curve = tuple(int(x) for x in out)
        else:
            curve = tuple(_python_lru_curve(self.dense, self.unique_pages))
        self._lru_curve_cache = curve
        return curve

    def lru_sweep(self, capacities: Sequence[int], *, backend: str = "auto") -> dict[int, int]:
        curve = self.lru_curve(backend=backend)
        result: dict[int, int] = {}
        for raw in capacities:
            c = int(raw)
            if c <= 0:
                raise ValueError("capacities must be positive")
            result[c] = curve[c - 1] if c <= self.unique_pages else self.unique_pages
        return result

    def faults(self, policy: str, capacity: int, *, backend: str = "auto") -> int:
        if policy == "lru":
            return self.lru_sweep([capacity], backend=backend)[capacity]
        if policy == "opt":
            return self.opt_sweep([capacity], backend=backend)[capacity]
        raise ValueError(f"unknown policy: {policy}")

    def sweep(
        self,
        capacities: Sequence[int],
        *,
        policies: Sequence[str] = ("lru", "opt"),
        backend: str = "auto",
        workers: int | str = "auto",
    ) -> dict[str, dict[int, int]]:
        result: dict[str, dict[int, int]] = {}
        for policy in policies:
            if policy == "lru":
                result[policy] = self.lru_sweep(capacities, backend=backend)
            elif policy == "opt":
                result[policy] = self.opt_sweep(capacities, backend=backend, workers=workers)
            else:
                raise ValueError(f"unknown policy: {policy}")
        return result

    def compare(
        self,
        capacities: Sequence[int],
        *,
        backend: str = "auto",
        workers: int | str = "auto",
    ) -> list[dict[str, Any]]:
        data = self.sweep(capacities, backend=backend, workers=workers)
        rows: list[dict[str, Any]] = []
        for c in capacities:
            cap = int(c)
            lru = data["lru"][cap]
            opt = data["opt"][cap]
            rows.append({
                "capacity": cap,
                "lru_faults": lru,
                "opt_faults": opt,
                "avoidable_faults": lru - opt,
                "lru_fault_rate": lru / self.length,
                "opt_fault_rate": opt / self.length,
            })
        return rows

    def minimum_capacity(
        self,
        policy: str,
        max_fault_rate: float,
        *,
        backend: str = "auto",
    ) -> int | None:
        if not (0.0 <= max_fault_rate <= 1.0):
            raise ValueError("max_fault_rate must be in [0, 1]")
        target = max_fault_rate * self.length
        lo, hi = 1, self.unique_pages
        if self.faults(policy, hi, backend=backend) > target:
            return None
        while lo < hi:
            mid = (lo + hi) // 2
            if self.faults(policy, mid, backend=backend) <= target:
                hi = mid
            else:
                lo = mid + 1
        return lo


def prepare_trace(trace: Iterable[Hashable]) -> PreparedTrace:
    return PreparedTrace.prepare(trace)
