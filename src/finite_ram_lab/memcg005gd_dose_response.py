from __future__ import annotations
import argparse,json,mmap,os,struct,subprocess,time,math
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import betaln,expit
from scipy.stats import beta,fisher_exact

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
def capacity_for(spec,block,identity):
    caps=spec["capacities"]
    return int(caps[(block+identity)%len(caps)])

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
    cap=capacity_for(spec,block,identity)
    name=f"fr-m5gd-{os.getenv('GITHUB_RUN_ID','local')}-{block}-{identity}"
    u=_start(worker,root,name,p,cap);page=spec["required_page_size"]
    try:
        pre=_current(u["cg"]);pre_pages=pre/page
        stratum="LOW" if pre_pages<=spec["low_threshold_pages"] else "HIGH"
        t0=time.monotonic_ns();os.sched_setaffinity(u["pid"],{s});_wait_cpu(u["pid"],s)
        mid=_current(u["cg"]);mig=(mid-pre)/page;lat=(time.monotonic_ns()-t0)/1000.0
        _set(u["mm"],OFF_MODE,2);_set(u["mm"],OFF_TARGET,s);_set(u["mm"],OFF_DONE,0);_set(u["mm"],OFF_ERROR,0)
        before=_current(u["cg"]);_set(u["mm"],OFF_GO,1);_wait(lambda:_u32(u["mm"],OFF_DONE)==1)
        after=_current(u["cg"]);d=(after-before)/page
        cpu=_u32(u["mm"],OFF_OBS_CPU);err=_u32(u["mm"],OFF_ERROR);touched=_u32(u["mm"],OFF_TOUCHED)
        valid=(cpu==s and err==0 and touched==1)
        return {"experiment_id":spec["experiment_id"],"block":block,"identity":identity,
          "capacity_pages":cap,"prep_cpu":p,"stock_cpu":s,"pre_current_pages":pre_pages,
          "stratum":stratum,"migration_delta_pages":mig,"affinity_to_go_us":lat,
          "first_touch_delta_pages":d,"q64_pass":_q64(spec,d),
          "cpu_match":cpu==s,"worker_error":err,"valid":valid}
    finally:_stop(u)

def _sum(rows):
    n=len(rows);f=sum(not r["q64_pass"] for r in rows)
    return {"n":n,"failures":f,"successes":n-f,"capture_rate":f/n if n else None,
            "zero_failures":sum((not r["q64_pass"]) and r["first_touch_delta_pages"]==0 for r in rows),
            "other_failures":sum((not r["q64_pass"]) and r["first_touch_delta_pages"]!=0 for r in rows)}

def _dist(xs):
    if not xs:return None
    a=np.asarray(xs,float);q=np.quantile(a,[0,.25,.5,.75,1])
    return {"min":float(q[0]),"q1":float(q[1]),"median":float(q[2]),"q3":float(q[3]),"max":float(q[4]),"mean":float(a.mean())}

def _posterior(f,s):
    a,b=f+1,s+1
    return {"alpha":a,"beta":b,"median":float(beta.ppf(.5,a,b)),
            "ci95":[float(beta.ppf(.025,a,b)),float(beta.ppf(.975,a,b))]}

def _ll_binom(rows,ps):
    ll=0.0
    for r,p in zip(rows,ps):
        p=min(max(float(p),1e-12),1-1e-12)
        ll += r["failures"]*math.log(p)+r["successes"]*math.log(1-p)
    return ll

def _models(caps,sums):
    rows=[sums[str(c)] for c in caps]
    total_f=sum(x["failures"] for x in rows);total_n=sum(x["n"] for x in rows)
    p=total_f/total_n
    ll0=_ll_binom(rows,[p]*len(rows))
    out={"CONSTANT":{"k":1,"loglik":ll0,"aic":2-2*ll0}}

    x=np.asarray(caps,float)
    center=float(x.mean());scale=float(x.std()) or 1.0
    z=(x-center)/scale
    def neg(th):
        ps=expit(th[0]+th[1]*z)
        return -_ll_binom(rows,ps)
    fit=minimize(neg,np.array([math.log((p+1e-6)/(1-p+1e-6)),0.0]),method="BFGS")
    lll=-float(fit.fun)
    out["LOGISTIC_LINEAR"]={"k":2,"loglik":lll,"aic":4-2*lll,
      "a":float(fit.x[0]),"b_scaled":float(fit.x[1]),"center":center,"scale":scale}

    lo=[r for c,r in zip(caps,rows) if c<64];hi=[r for c,r in zip(caps,rows) if c>=64]
    def rate(gr):
        f=sum(r["failures"] for r in gr);n=sum(r["n"] for r in gr);return f/n
    plo,phi=rate(lo),rate(hi)
    ps=[plo if c<64 else phi for c in caps]
    lls=_ll_binom(rows,ps)
    out["STEP64"]={"k":2,"loglik":lls,"aic":4-2*lls,"p_lt64":plo,"p_ge64":phi}

    llc=0.0
    for r in rows:
        pp=r["failures"]/r["n"] if r["n"] else .5
        llc+=_ll_binom([r],[pp])
    out["CATEGORICAL"]={"k":len(caps),"loglik":llc,"aic":2*len(caps)-2*llc}
    return out

def analyze(spec,trials):
    expected={(b,i) for b in range(spec["runner_blocks"]) for i in range(spec["identities_per_block"])}
    got={(int(t["block"]),int(t["identity"])) for t in trials}
    if got!=expected: raise ValueError("incomplete matrix")
    caps=[int(x) for x in spec["capacities"]]
    valid=[t for t in trials if t["valid"] and t["stratum"]=="LOW"]
    sums={};posts={};blocks={};pre={};lat={}
    for c in caps:
        rr=[t for t in valid if int(t["capacity_pages"])==c]
        ss=_sum(rr);sums[str(c)]=ss;posts[str(c)]=_posterior(ss["failures"],ss["successes"])
        blocks[str(c)]={str(b):_sum([t for t in rr if int(t["block"])==b]) for b in range(spec["runner_blocks"])}
        pre[str(c)]=_dist([t["pre_current_pages"] for t in rr])
        lat[str(c)]=_dist([t["affinity_to_go_us"] for t in rr])
    mods=_models(caps,sums)
    a={k:v["aic"] for k,v in mods.items()}
    low=sum(sums[str(c)]["failures"] for c in caps if c<64)/sum(sums[str(c)]["n"] for c in caps if c<64)
    high=sum(sums[str(c)]["failures"] for c in caps if c>=64)/sum(sums[str(c)]["n"] for c in caps if c>=64)
    label="FLAT_OR_UNRESOLVED"
    if a["STEP64"]<=a["CONSTANT"]-6 and a["STEP64"]<=a["LOGISTIC_LINEAR"]-2 and high-low>=.04:
        label="DISCOVERY_STEP64_CANDIDATE"
    elif a["LOGISTIC_LINEAR"]<=a["CONSTANT"]-6 and a["LOGISTIC_LINEAR"]<=a["STEP64"]+2:
        label="DISCOVERY_SMOOTH_CANDIDATE"
    elif a["CATEGORICAL"]<=a["STEP64"]-6 and a["CATEGORICAL"]<=a["LOGISTIC_LINEAR"]-6:
        label="DISCOVERY_OTHER_SHAPE"
    adjacent={}
    for c1,c2 in zip(caps,caps[1:]):
        s1,s2=sums[str(c1)],sums[str(c2)]
        x=fisher_exact([[s2["failures"],s2["successes"]],[s1["failures"],s1["successes"]]],alternative="two-sided")
        adjacent[f"{c1}->{c2}"]={"odds_ratio":float(x.statistic),"two_sided_p":float(x.pvalue),
          "rate_difference":s2["capture_rate"]-s1["capture_rate"]}
    rng=np.random.default_rng(5007);mc=200000
    samples={str(c):rng.beta(posts[str(c)]["alpha"],posts[str(c)]["beta"],mc) for c in caps}
    adjprob={f"{c1}->{c2}":float(np.mean(samples[str(c2)]>samples[str(c1)])) for c1,c2 in zip(caps,caps[1:])}
    return {"experiment_id":spec["experiment_id"],"discovery_label":label,
      "by_capacity":sums,"posterior":posts,"models":mods,
      "mean_rate_lt64":low,"mean_rate_ge64":high,
      "adjacent_fisher":adjacent,"adjacent_posterior_increase_probability":adjprob,
      "p70_gt_p8":float(np.mean(samples["70"]>samples["8"])),
      "blockwise":blocks,"pre_current_distribution":pre,"latency_us_distribution":lat,
      "cpu_mismatches":sum(not t["cpu_match"] for t in trials),
      "other_delta_failures":sum((t["valid"] and t["stratum"]=="LOW" and not t["q64_pass"] and t["first_touch_delta_pages"]!=0) for t in trials),
      "trials":trials}

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
    r=analyze(spec,trials);out=Path(a.json_out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"label":r["discovery_label"],"by_capacity":r["by_capacity"],
      "models":{k:v["aic"] for k,v in r["models"].items()}},sort_keys=True))
if __name__=="__main__":main()
