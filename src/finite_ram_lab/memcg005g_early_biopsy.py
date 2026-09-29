from __future__ import annotations
import argparse,json,mmap,os,struct,subprocess,time,math
from collections import Counter
from pathlib import Path
from typing import Any
from scipy.stats import fisher_exact,beta
from scipy.special import betaln

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
    s=Path(f"/proc/{pid}/stat").read_text(); return int(s[s.rfind(")")+2:].split()[36])
def _wait_cpu(pid,cpu): _wait(lambda:_proc_cpu(pid)==cpu,5)
def _current(cg): return int((cg/"memory.current").read_text().strip())
def _q64(spec,d): return spec["q64_min_pages"]<=d<=spec["q64_max_pages"]

def _start(worker,root,name,p):
    ctl=root/f"{name}.ctl"; fd=os.open(ctl,os.O_RDWR|os.O_CREAT|os.O_TRUNC,0o600)
    os.ftruncate(fd,CONTROL_BYTES); mm=mmap.mmap(fd,CONTROL_BYTES,access=mmap.ACCESS_WRITE)
    _run(["sudo","systemd-run","--quiet","--collect",f"--unit={name}",f"--uid={os.getuid()}",
          "-p","MemoryAccounting=yes","-p",f"CPUAffinity={p}",str(worker),
          "--shared",str(ctl),"--max-pages","70"])
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

def _one_touch(u,s,page,spec):
    _set(u["mm"],OFF_MODE,2);_set(u["mm"],OFF_TARGET,s);_set(u["mm"],OFF_DONE,0);_set(u["mm"],OFF_ERROR,0)
    pre=_current(u["cg"]);_set(u["mm"],OFF_GO,1);_wait(lambda:_u32(u["mm"],OFF_DONE)==1)
    post=_current(u["cg"]);d=(post-pre)/page
    return d,_u32(u["mm"],OFF_OBS_CPU),_u32(u["mm"],OFF_ERROR),_u32(u["mm"],OFF_TOUCHED)

def run_probe(spec,worker,root,block,identity,p,s):
    name=f"fr-m5g-{os.getenv('GITHUB_RUN_ID','local')}-{block}-{identity}"
    u=_start(worker,root,name,p); page=spec["required_page_size"]
    try:
        pre=_current(u["cg"]);pre_pages=pre/page
        stratum="LOW" if pre_pages<=spec["low_threshold_pages"] else "HIGH"
        t0=time.monotonic_ns();os.sched_setaffinity(u["pid"],{s});_wait_cpu(u["pid"],s)
        mid=_current(u["cg"]);mig=(mid-pre)/page;lat=(time.monotonic_ns()-t0)/1000
        d,cpu,err,touched=_one_touch(u,s,page,spec)
        valid=(cpu==s and err==0 and touched==1)
        biopsy=[];depth=None;censored=False
        if valid and stratum=="LOW" and d==0:
            for touch_idx in range(2,spec["biopsy_max_total_touches"]+1):
                dd,cc,ee,tt=_one_touch(u,s,page,spec); biopsy.append(dd)
                if cc!=s or ee!=0 or tt!=touch_idx:
                    valid=False; break
                if _q64(spec,dd):
                    depth=touch_idx-1; break
            if valid and depth is None: censored=True
        return {
          "experiment_id":spec["experiment_id"],"block":block,"identity":identity,
          "phase":"EARLY" if identity<=spec["early_end_identity"] else "STEADY",
          "prep_cpu":p,"stock_cpu":s,"pre_current_pages":pre_pages,"stratum":stratum,
          "migration_delta_pages":mig,"affinity_to_go_us":lat,
          "first_touch_delta_pages":d,"q64_pass":_q64(spec,d),"cpu_match":cpu==s,
          "worker_error":err,"valid":valid,"biopsy_delta_sequence":biopsy,
          "residual_depth_candidate":depth,"biopsy_censored_gt64":censored
        }
    finally:_stop(u)

def _sum(rows):
    n=len(rows);f=sum(not r["q64_pass"] for r in rows)
    return {"n":n,"failures":f,"successes":n-f,"failure_rate":f/n if n else None,
            "zero_failures":sum((not r["q64_pass"]) and r["first_touch_delta_pages"]==0 for r in rows),
            "other_failures":sum((not r["q64_pass"]) and r["first_touch_delta_pages"]!=0 for r in rows)}

def _beta_ci(f,n,a=.05):
    s=n-f
    return [float(beta.ppf(a/2,f+1,s+1)),float(beta.ppf(1-a/2,f+1,s+1))]

def analyze(spec,trials):
    expected={(b,i) for b in range(spec["runner_blocks"]) for i in range(spec["identities_per_block"])}
    got={(int(t["block"]),int(t["identity"])) for t in trials}
    if got!=expected: raise ValueError("incomplete matrix")
    valid=[t for t in trials if t["valid"] and t["stratum"]=="LOW"]
    early=[t for t in valid if t["phase"]=="EARLY"]; steady=[t for t in valid if t["phase"]=="STEADY"]
    es=_sum(early);ss=_sum(steady)
    p=None;odds=None
    if es["n"] and ss["n"]:
        x=fisher_exact([[es["failures"],es["successes"]],[ss["failures"],ss["successes"]]],alternative="greater")
        p=float(x.pvalue);odds=float(x.statistic)
    rd=None if not es["n"] or not ss["n"] else es["failure_rate"]-ss["failure_rate"]
    rr=((es["failures"]+.5)/(es["n"]+1))/((ss["failures"]+.5)/(ss["n"]+1)) if es["n"] and ss["n"] else None
    logbf=(betaln(es["failures"]+1,es["successes"]+1)+betaln(ss["failures"]+1,ss["successes"]+1)
           -betaln(es["failures"]+ss["failures"]+1,es["successes"]+ss["successes"]+1))
    bf=float(math.exp(logbf))
    cpu_mis=sum(not t["cpu_match"] for t in trials)
    other=es["other_failures"]+ss["other_failures"]
    support=(es["n"]>=spec["support_min_early_low_n"] and ss["n"]>=spec["support_min_steady_low_n"]
      and es["failure_rate"]>=spec["support_min_early_failure_rate"]
      and ss["failure_rate"]<=spec["support_max_steady_failure_rate"]
      and p is not None and p<spec["support_fisher_p_max"] and cpu_mis==0 and other==0)
    reject=(es["n"]>=spec["support_min_early_low_n"] and ss["n"]>=spec["support_min_steady_low_n"]
      and (es["failure_rate"]<=spec["reject_max_early_failure_rate"]
           or (rd is not None and rd<spec["reject_min_rate_difference"] and (p is None or p>=.10))))
    decision="SUPPORT_EARLY_TRANSIENT" if support else "REJECT_EARLY_TRANSIENT" if reject else "INCONCLUSIVE"
    depths=[t["residual_depth_candidate"] for t in valid if t["residual_depth_candidate"] is not None]
    cens=sum(bool(t["biopsy_censored_gt64"]) for t in valid)
    byid={}
    for i in range(spec["identities_per_block"]):
        r=[t for t in valid if int(t["identity"])==i]; byid[str(i)]=_sum(r)
    return {
      "experiment_id":spec["experiment_id"],"decision":decision,
      "EARLY":es,"STEADY":ss,"risk_difference":rd,"haldane_risk_ratio":rr,
      "fisher":{"odds_ratio":odds,"one_sided_p":p},
      "beta_posterior_95":{"EARLY":_beta_ci(es["failures"],es["n"]),"STEADY":_beta_ci(ss["failures"],ss["n"])},
      "bayes_factor_two_rate_vs_shared":bf,"cpu_mismatches":cpu_mis,
      "failure_by_identity":byid,"residual_depth_candidates":depths,
      "residual_depth_histogram":dict(Counter(map(str,depths))),
      "biopsy_censored_gt64":cens,"trials":trials
    }

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True)
    rb=sp.add_parser("run-block");rb.add_argument("--spec",required=True);rb.add_argument("--block",type=int,required=True);rb.add_argument("--worker",required=True);rb.add_argument("--out-root",required=True)
    ag=sp.add_parser("aggregate");ag.add_argument("--spec",required=True);ag.add_argument("--input-root",required=True);ag.add_argument("--json-out",required=True)
    a=ap.parse_args();spec=load_spec(a.spec)
    if a.cmd=="run-block":
        cpus=sorted(os.sched_getaffinity(0));c,p,s=cpus[0],cpus[1],cpus[-1];os.sched_setaffinity(0,{c})
        root=Path(a.out_root);root.mkdir(parents=True,exist_ok=True)
        for i in range(spec["identities_per_block"]):
            rr=root/f"id-{i}";rr.mkdir(parents=True,exist_ok=True)
            t=run_probe(spec,Path(a.worker).resolve(),rr,a.block,i,p,s)
            (root/f"trial-{a.block}-{i}.json").write_text(json.dumps(t,indent=2,sort_keys=True)+"\n")
        return
    trials=[json.loads(x.read_text()) for x in sorted(Path(a.input_root).rglob("trial-*.json"))]
    r=analyze(spec,trials);out=Path(a.json_out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"decision":r["decision"],"EARLY":r["EARLY"],"STEADY":r["STEADY"],"depths":r["residual_depth_histogram"]},sort_keys=True))
if __name__=="__main__":main()
