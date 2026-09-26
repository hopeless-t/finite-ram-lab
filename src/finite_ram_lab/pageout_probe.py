from __future__ import annotations
import argparse,hashlib,json,mmap,time
from pathlib import Path
from .obs_workload import _self_cgroup_path,_snapshot,_touch
from .region_workload import PAGE_SIZE,_mapping,residency

def digest(mm,size):
    h=hashlib.sha256()
    for i in range(0,size,PAGE_SIZE): h.update(bytes([mm[i]]))
    return h.hexdigest()

def retouch(mm,size):
    t=time.perf_counter_ns()
    for i in range(0,size,PAGE_SIZE):
        x=mm[i]; mm[i]=x
    return time.perf_counter_ns()-t

def run(target,hot_mib,burst_mib,target_mib):
    hot=_mapping(hot_mib*1024*1024); burst=_mapping(burst_mib*1024*1024)
    _touch(hot); _touch(burst)
    mm=hot if target=="hotset" else burst
    size=target_mib*1024*1024
    cg=Path("/sys/fs/cgroup")/_self_cgroup_path().lstrip("/")
    before=residency(mm,size); os0=_snapshot(cg); d0=digest(mm,size)
    advice=getattr(mmap,"MADV_PAGEOUT",21); error=None; call_ns=None
    ok=False
    try:
        t=time.perf_counter_ns(); mm.madvise(advice,0,size); call_ns=time.perf_counter_ns()-t; ok=True
    except Exception as e: error=f"{type(e).__name__}: {e}"
    time.sleep(0.10)
    after=residency(mm,size); os1=_snapshot(cg)
    touch_ns=retouch(mm,size)
    restored=residency(mm,size); os2=_snapshot(cg); d1=digest(mm,size)
    reduction=(before["resident_pages"]-after["resident_pages"])/before["total_pages"]
    out={"experiment_id":"ENV-003","target":target,"call_success":ok,"error":error,
      "call_duration_ns":call_ns,"residency_before":before,
      "residency_after":after,"residency_after_retouch":restored,
      "reduction_fraction":reduction,"retouch_ns":touch_ns,
      "content_match":d0==d1,
      "swap_before":os0["memory_swap_current"],"swap_after":os1["memory_swap_current"],
      "swap_after_retouch":os2["memory_swap_current"],
      "oom":os2["memory_events"].get("oom",0),"oom_kill":os2["memory_events"].get("oom_kill",0)}
    hot.close(); burst.close(); return out

def main():
    p=argparse.ArgumentParser(); p.add_argument("--target",choices=("hotset","burst"),required=True)
    p.add_argument("--hotset-mib",type=int,required=True); p.add_argument("--burst-mib",type=int,required=True)
    p.add_argument("--target-mib",type=int,required=True); p.add_argument("--out",required=True); a=p.parse_args()
    z=run(a.target,a.hotset_mib,a.burst_mib,a.target_mib); Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(z,indent=2,sort_keys=True)+"\n"); print(json.dumps(z,indent=2,sort_keys=True))

if __name__=="__main__": main()
