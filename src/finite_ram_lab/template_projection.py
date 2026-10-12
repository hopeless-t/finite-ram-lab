from __future__ import annotations

import argparse, hashlib, json, os, random, resource, statistics, subprocess, sys, time
from pathlib import Path
from typing import Any

from .fast_reinstall_epoch import make_epoch, verify_epoch
from .fast_reinstall_loop import run_measured
from .fast_reinstall_loop_v2 import build_wheel_isolated

WORK_BODY=r'''
REQUEST_COUNTER=0
def work(seed):
    global REQUEST_COUNTER
    REQUEST_COUNTER += 1
    rng=random.Random(seed)
    trace=generate_trace("shifting_hotset",rng,12000,257,41)
    core={"seed":seed,"trace_sha256":hashlib.sha256(bytes((x%256 for x in trace))).hexdigest(),"lru_faults":lru_faults(trace,41),"opt_faults":opt_faults(trace,41),"trace_len":len(trace)}
    core["semantic_sha256"]=hashlib.sha256(json.dumps(core,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    core["request_counter"]=REQUEST_COUNTER
    core["ru_maxrss_kib"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return core
'''.strip()

PREFIX="import hashlib,json,random,resource,sys,os\nfrom finite_ram_lab.sim import generate_trace,lru_faults,opt_faults\n"+WORK_BODY+"\n"
COLD_CODE=PREFIX+'print(json.dumps(work(int(sys.argv[1])),sort_keys=True))\n'
WARM_CODE=PREFIX+r'''
print(json.dumps({"ready":True,"rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}),flush=True)
for line in sys.stdin:
    line=line.strip()
    if line=="STOP": break
    if line: print(json.dumps(work(int(line)),sort_keys=True),flush=True)
'''
FORK_CODE=PREFIX+r'''
print(json.dumps({"ready":True,"rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}),flush=True)
for line in sys.stdin:
    line=line.strip()
    if line=="STOP": break
    if not line: continue
    seed=int(line); r,w=os.pipe(); pid=os.fork()
    if pid==0:
        try:
            os.close(r); data=(json.dumps(work(seed),sort_keys=True)+"\n").encode(); os.write(w,data)
        finally:
            try: os.close(w)
            except OSError: pass
        os._exit(0)
    os.close(w); parts=[]
    while True:
        chunk=os.read(r,65536)
        if not chunk: break
        parts.append(chunk)
    os.close(r); os.waitpid(pid,0); sys.stdout.write(b"".join(parts).decode()); sys.stdout.flush()
'''

def rss_kib(pid:int)->int:
    try:
        for line in Path(f'/proc/{pid}/status').read_text().splitlines():
            if line.startswith('VmRSS:'): return int(line.split()[1])
    except (OSError,ValueError,IndexError): pass
    return 0

def pct(xs:list[float],q:float)->float:
    ys=sorted(xs); return float(ys[max(0,min(len(ys)-1,int(len(ys)*q)-1))])

def start_server(code:str,repo:Path,env:dict[str,str])->tuple[subprocess.Popen[str],float,dict[str,Any]]:
    t=time.perf_counter_ns(); p=subprocess.Popen([sys.executable,'-u','-c',code],cwd=repo,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    assert p.stdout is not None; line=p.stdout.readline(); elapsed=(time.perf_counter_ns()-t)/1e6
    if not line:
        err=p.stderr.read() if p.stderr else ''; raise RuntimeError(err[-2000:])
    return p,elapsed,json.loads(line)

def server_call(p:subprocess.Popen[str],wheel:Path,epoch:dict[str,Any],seed:int)->dict[str,Any]:
    assert p.stdin is not None and p.stdout is not None
    t=time.perf_counter_ns();
    if not verify_epoch(wheel,epoch): raise RuntimeError('artifact epoch changed')
    p.stdin.write(f'{seed}\n'); p.stdin.flush(); line=p.stdout.readline(); elapsed=time.perf_counter_ns()-t
    if not line: raise RuntimeError('server died')
    return {'elapsed_ns':elapsed,'parent_rss_kib':rss_kib(p.pid),'payload':json.loads(line)}
def cold_call(repo:Path,wheel:Path,epoch:dict[str,Any],seed:int)->dict[str,Any]:
    env=dict(os.environ); env['PYTHONPATH']=str(wheel); env.pop('PYTHONDONTWRITEBYTECODE',None)
    t=time.perf_counter_ns();
    if not verify_epoch(wheel,epoch): raise RuntimeError('artifact epoch changed')
    r=run_measured([sys.executable,'-c',COLD_CODE,str(seed)],cwd=repo,env=env,poll_s=.001); elapsed=time.perf_counter_ns()-t
    if r['returncode']!=0: raise RuntimeError(r['stderr'][-2000:])
    return {'elapsed_ns':elapsed,'peak_rss_kib':r['peak_rss_kib'],'payload':json.loads(r['stdout'].splitlines()[-1])}
def stop(p:subprocess.Popen[str]):
    if p.poll() is None and p.stdin is not None:
        p.stdin.write('STOP\n'); p.stdin.flush(); p.wait(timeout=5)

def run(repo:Path,out:Path,*,blocks:int,seed:int)->dict[str,Any]:
    out.mkdir(parents=True,exist_ok=True); wheel,build=build_wheel_isolated(repo,out/'artifacts'); epoch=make_epoch(wheel)
    env=dict(os.environ); env['PYTHONPATH']=str(wheel); env.pop('PYTHONDONTWRITEBYTECODE',None)
    warm,warm_start,warm_ready=start_server(WARM_CODE,repo,env); fork,fork_start,fork_ready=start_server(FORK_CODE,repo,env)
    warm_idle=rss_kib(warm.pid); fork_idle=rss_kib(fork.pid); rows=[]
    try:
        for block in range(blocks):
            s=seed+block; arms=['cold_exec','warm_persistent','fork_template']; random.Random(seed+block*4001).shuffle(arms); hashes={}
            for order,arm in enumerate(arms):
                if arm=='cold_exec': r=cold_call(repo,wheel,epoch,s)
                elif arm=='warm_persistent': r=server_call(warm,wheel,epoch,s)
                else: r=server_call(fork,wheel,epoch,s)
                hashes[arm]=r['payload']['semantic_sha256']; rows.append({'block':block,'order':order,'arm':arm,'seed':s,**r})
            if len(set(hashes.values()))!=1: raise RuntimeError(f'semantic mismatch {block}')
    finally:
        stop(warm); stop(fork)
    arms_out={}
    for arm in ['cold_exec','warm_persistent','fork_template']:
        g=[r for r in rows if r['arm']==arm]; ms=[r['elapsed_ns']/1e6 for r in g]
        d={'n':len(g),'median_ms':float(statistics.median(ms)),'p95_ms':pct(ms,.95),'min_ms':float(min(ms)),'max_ms':float(max(ms)),'counter_unique':sorted(set(r['payload']['request_counter'] for r in g))[:10]}
        if arm=='cold_exec': d['median_peak_rss_kib']=float(statistics.median(r['peak_rss_kib'] for r in g))
        else:
            d['median_parent_rss_kib']=float(statistics.median(r['parent_rss_kib'] for r in g)); d['median_execution_ru_maxrss_kib']=float(statistics.median(r['payload']['ru_maxrss_kib'] for r in g))
        arms_out[arm]=d
    base=arms_out['cold_exec']['median_ms']
    for arm in ['warm_persistent','fork_template']: arms_out[arm]['speedup_vs_cold']=base/arms_out[arm]['median_ms']
    result={'experiment_id':'FRL-REINSTALL-005-TEMPLATE-PROJECTION-v1','blocks':blocks,'semantic_triplets_match':True,'canonical_build_residue_delta_bytes':build['canonical_residue_delta_bytes'],'warm_startup_ms':warm_start,'fork_template_startup_ms':fork_start,'warm_idle_rss_kib':warm_idle,'fork_template_idle_rss_kib':fork_idle,'warm_ready':warm_ready,'fork_ready':fork_ready,'arms':arms_out,'state_isolation_probe':{'cold_counter_all_one':arms_out['cold_exec']['counter_unique']==[1],'fork_counter_all_one':arms_out['fork_template']['counter_unique']==[1],'warm_counter_advances':len(arms_out['warm_persistent']['counter_unique'])>1}}
    (out/'trials.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows)); (out/'summary.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); return result

def main():
    p=argparse.ArgumentParser(); p.add_argument('--repo',default='.'); p.add_argument('--out',required=True); p.add_argument('--blocks',type=int,default=60); p.add_argument('--seed',type=int,default=20261012); a=p.parse_args(); print(json.dumps(run(Path(a.repo).resolve(),Path(a.out).resolve(),blocks=a.blocks,seed=a.seed),indent=2,sort_keys=True))
if __name__=='__main__': main()
