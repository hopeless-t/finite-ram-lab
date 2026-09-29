from __future__ import annotations
import argparse,json,mmap,os,struct,subprocess,time,math
from pathlib import Path
import numpy as np
from scipy.stats import fisher_exact,chi2

OFF_READY=0;OFF_MODE=4;OFF_TARGET=8;OFF_GO=12;OFF_DONE=16;OFF_STOP=20
OFF_OBS_CPU=24;OFF_TOUCHED=28;OFF_ERROR=32;CONTROL_BYTES=4096

def load_spec(p): return json.loads(Path(p).read_text())
def _run(cmd,check=True): return subprocess.run(cmd,text=True,capture_output=True,check=check)
def _u32(mm,o): return struct.unpack_from("<I",mm,o)[0]
def _set(mm,o,v): struct.pack_into("<I",mm,o,int(v))
def _wait(pred,timeout=10):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if pred(): return
        time.sleep(.001)
    raise TimeoutError("timeout")
def _proc_cpu(pid):
    s=Path(f"/proc/{pid}/stat").read_text()
    return int(s[s.rfind(")")+2:].split()[36])
def _wait_cpu(pid,cpu): _wait(lambda:_proc_cpu(pid)==cpu,5)
def _current(cg): return int((cg/"memory.current").read_text().strip())
def _q64(spec,d): return spec["q64_min_pages"]<=d<=spec["q64_max_pages"]
def _arm(block,identity):
    return "CAP8" if ((block+identity)%2==0) else "CAP70"

def _start(worker,root,name,p,max_pages):
    ctl=root/f"{name}.ctl"
    fd=os.open(ctl,os.O_RDWR|os.O_CREAT|os.O_TRUNC,0o600)
    os.ftruncate(fd,CONTROL_BYTES)
    mm=mmap.mmap(fd,CONTROL_BYTES,access=mmap.ACCESS_WRITE)
    _run(["sudo","systemd-run","--quiet","--collect",f"--unit={name}",f"--uid={os.getuid()}",
          "-p","MemoryAccounting=yes","-p",f"CPUAffinity={p}",str(worker),
          "--shared",str(ctl),"--max-pages",str(max_pages)])
    _wait(lambda:_u32(mm,OFF_READY)==1)
    pid=int(_run(["systemctl","show",f"{name}.service","--property=MainPID","--value"]).stdout.strip())
    cgt=_run(["systemctl","show",f"{name}.service","--property=ControlGroup","--value"]).stdout.strip()
    cg=Path("/sys/fs/cgroup")/cgt.lstrip("/")
    _wait_cpu(pid,p)
    return {"name":name,"pid":pid,"cg":cg,"fd":fd,"mm":mm}

def _stop(u):
    try:_set(u["mm"],OFF_STOP,1)
    except Exception:pass
    _run(["sudo","systemctl","stop",u["name"]+".service"],check=False)
    try:u["mm"].close();os.close(u["fd"])
    except Exception:pass

def run_probe(spec,worker,root,block,identity,p,s):
    arm=_arm(block,identity)
    max_pages=spec["cap8_pages"] if arm=="CAP8" else spec["cap70_pages"]
    name=f"fr-m5gb-{os.getenv('GITHUB_RUN_ID','local')}-{block}-{identity}"
    u=_start(worker,root,name,p,max_pages)
    page=spec["required_page_size"]
    try:
        pre=_current(u["cg"]); pre_pages=pre/page
        stratum="LOW" if pre_pages<=spec["low_threshold_pages"] else "HIGH"
        t0=time.monotonic_ns()
        os.sched_setaffinity(u["pid"],{s}); _wait_cpu(u["pid"],s)
        mid=_current(u["cg"]); mig=(mid-pre)/page
        lat=(time.monotonic_ns()-t0)/1000.0
        _set(u["mm"],OFF_MODE,2);_set(u["mm"],OFF_TARGET,s)
        _set(u["mm"],OFF_DONE,0);_set(u["mm"],OFF_ERROR,0)
        before=_current(u["cg"])
        _set(u["mm"],OFF_GO,1)
        _wait(lambda:_u32(u["mm"],OFF_DONE)==1)
        after=_current(u["cg"])
        d=(after-before)/page
        cpu=_u32(u["mm"],OFF_OBS_CPU);err=_u32(u["mm"],OFF_ERROR);touched=_u32(u["mm"],OFF_TOUCHED)
        valid=(cpu==s and err==0 and touched==1)
        return {
          "experiment_id":spec["experiment_id"],"block":block,"identity":identity,
          "arm":arm,"max_pages":max_pages,"prep_cpu":p,"stock_cpu":s,
          "pre_current_pages":pre_pages,"stratum":stratum,
          "migration_delta_pages":mig,"affinity_to_go_us":lat,
          "first_touch_delta_pages":d,"q64_pass":_q64(spec,d),
          "cpu_match":cpu==s,"worker_error":err,"valid":valid
        }
    finally:_stop(u)

def _sum(rows):
    n=len(rows);f=sum(not r["q64_pass"] for r in rows)
    return {"n":n,"failures":f,"successes":n-f,
            "failure_rate":f/n if n else None,
            "zero_failures":sum((not r["q64_pass"]) and r["first_touch_delta_pages"]==0 for r in rows),
            "other_failures":sum((not r["q64_pass"]) and r["first_touch_delta_pages"]!=0 for r in rows)}

def _dist(xs):
    if not xs:return None
    a=np.asarray(xs,dtype=float)
    q=np.quantile(a,[0,.25,.5,.75,1])
    return {"min":float(q[0]),"q1":float(q[1]),"median":float(q[2]),"q3":float(q[3]),"max":float(q[4]),"mean":float(a.mean())}

def _block_tables(rows,spec):
    out={}
    for b in range(spec["runner_blocks"]):
        br=[r for r in rows if int(r["block"])==b]
        out[str(b)]={a:_sum([r for r in br if r["arm"]==a]) for a in ("CAP8","CAP70")}
    return out

def _mh_and_heterogeneity(by_block):
    num=0.0;den=0.0;logs=[];weights=[]
    for v in by_block.values():
        a=v["CAP70"]["failures"]; b=v["CAP70"]["successes"]
        c=v["CAP8"]["failures"]; d=v["CAP8"]["successes"]
        n=a+b+c+d
        if n:
            num += a*d/n
            den += b*c/n
        aa,bb,cc,dd=[x+.5 for x in (a,b,c,d)]
        lor=math.log((aa*dd)/(bb*cc))
        var=1/aa+1/bb+1/cc+1/dd
        logs.append(lor);weights.append(1/var)
    mh=(num/den) if den>0 else math.inf
    sw=sum(weights)
    common=sum(w*l for w,l in zip(weights,logs))/sw if sw else float("nan")
    q=sum(w*(l-common)**2 for w,l in zip(weights,logs))
    df=max(0,len(logs)-1)
    p=float(chi2.sf(q,df)) if df>0 else None
    return {"mantel_haenszel_or_cap70_vs_cap8":mh,
            "woolf_q":q,"df":df,"heterogeneity_p":p,
            "weighted_log_or":common}

def analyze(spec,trials):
    expected={(b,i) for b in range(spec["runner_blocks"]) for i in range(spec["identities_per_block"])}
    got={(int(t["block"]),int(t["identity"])) for t in trials}
    if got!=expected: raise ValueError("incomplete matrix")
    valid_low=[t for t in trials if t["valid"] and t["stratum"]=="LOW"]
    c8=[t for t in valid_low if t["arm"]=="CAP8"];c70=[t for t in valid_low if t["arm"]=="CAP70"]
    s8=_sum(c8);s70=_sum(c70)
    x=fisher_exact([[s70["failures"],s70["successes"]],[s8["failures"],s8["successes"]]],alternative="two-sided")
    diff=s70["failure_rate"]-s8["failure_rate"]
    cpu_mis=sum(not t["cpu_match"] for t in trials)
    other=s8["other_failures"]+s70["other_failures"]
    support=(s8["n"]>=spec["support_min_low_per_arm"] and s70["n"]>=spec["support_min_low_per_arm"]
      and abs(diff)>=spec["support_min_abs_failure_rate_difference"]
      and float(x.pvalue)<spec["support_fisher_p_max"] and cpu_mis==0 and other==0)
    reject=(s8["n"]>=spec["support_min_low_per_arm"] and s70["n"]>=spec["support_min_low_per_arm"]
      and abs(diff)<spec["reject_max_abs_failure_rate_difference"]
      and float(x.pvalue)>=spec["reject_fisher_p_min"])
    decision="SUPPORT_FOOTPRINT_EFFECT" if support else "REJECT_FOOTPRINT_EFFECT" if reject else "INCONCLUSIVE"
    by_block=_block_tables(valid_low,spec)
    return {
      "experiment_id":spec["experiment_id"],"decision":decision,
      "CAP8":s8,"CAP70":s70,"failure_rate_difference_cap70_minus_cap8":diff,
      "fisher":{"odds_ratio":float(x.statistic),"two_sided_p":float(x.pvalue)},
      "cpu_mismatches":cpu_mis,"other_delta_failures":other,
      "by_block":by_block,"stratified":_mh_and_heterogeneity(by_block),
      "pre_current_distribution":{"CAP8":_dist([r["pre_current_pages"] for r in c8]),
                                  "CAP70":_dist([r["pre_current_pages"] for r in c70])},
      "latency_us_distribution":{"CAP8":_dist([r["affinity_to_go_us"] for r in c8]),
                                 "CAP70":_dist([r["affinity_to_go_us"] for r in c70])},
      "trials":trials
    }

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True)
    rb=sp.add_parser("run-block");rb.add_argument("--spec",required=True);rb.add_argument("--block",type=int,required=True);rb.add_argument("--worker",required=True);rb.add_argument("--out-root",required=True)
    ag=sp.add_parser("aggregate");ag.add_argument("--spec",required=True);ag.add_argument("--input-root",required=True);ag.add_argument("--json-out",required=True)
    a=ap.parse_args();spec=load_spec(a.spec)
    if a.cmd=="run-block":
        cpus=sorted(os.sched_getaffinity(0)); c,p,s=cpus[0],cpus[1],cpus[-1]; os.sched_setaffinity(0,{c})
        root=Path(a.out_root); root.mkdir(parents=True,exist_ok=True)
        for i in range(spec["identities_per_block"]):
            rr=root/f"id-{i}";rr.mkdir(parents=True,exist_ok=True)
            t=run_probe(spec,Path(a.worker).resolve(),rr,a.block,i,p,s)
            (root/f"trial-{a.block}-{i}.json").write_text(json.dumps(t,indent=2,sort_keys=True)+"\n")
        return
    trials=[json.loads(x.read_text()) for x in sorted(Path(a.input_root).rglob("trial-*.json"))]
    r=analyze(spec,trials);out=Path(a.json_out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"decision":r["decision"],"CAP8":r["CAP8"],"CAP70":r["CAP70"],
                      "diff":r["failure_rate_difference_cap70_minus_cap8"],"fisher":r["fisher"],
                      "stratified":r["stratified"]},sort_keys=True))
if __name__=="__main__":main()
