#!/usr/bin/env python3
import argparse,ast,hashlib,json,os,re,subprocess,time,uuid
from pathlib import Path
from shoal_runtime import ShoalRouter, DEFAULT_ADAPTER
from finite_ram_control import BoundedControlState, ByteBudgetGovernor, GIB, resource_snapshot

ROOT=Path(__file__).resolve().parents[3]
SURFACE_VERSION='catfood-shoal/reinstall-loop-v4'
CAPABILITIES=['core_text','0b_calculator','readonly_harness','semantic_handoff','authority_guard','finite_ram_governor','bounded_control_state','shared_prefix_kv','version_surface','capability_introspection','health_surface','self_doctor','self_reinstall','footprint_introspection']
EVENTS=ROOT/'.work'/'rsf-llm'/'runtime-events.jsonl'
CONTROL=ROOT/'.work'/'rsf-llm'/'control-state.json'
JOURNAL=BoundedControlState(EVENTS,CONTROL,budget_bytes=4096)
ALLOWED_BIN={ast.Add:lambda a,b:a+b,ast.Sub:lambda a,b:a-b,ast.Mult:lambda a,b:a*b,ast.Div:lambda a,b:a/b,ast.FloorDiv:lambda a,b:a//b,ast.Mod:lambda a,b:a%b}
ALLOWED_UNARY={ast.UAdd:lambda a:+a,ast.USub:lambda a:-a}

def safe_eval(node):
    if isinstance(node,ast.Expression): return safe_eval(node.body)
    if isinstance(node,ast.Constant) and isinstance(node.value,(int,float)): return node.value
    if isinstance(node,ast.BinOp) and type(node.op) in ALLOWED_BIN: return ALLOWED_BIN[type(node.op)](safe_eval(node.left),safe_eval(node.right))
    if isinstance(node,ast.UnaryOp) and type(node.op) in ALLOWED_UNARY: return ALLOWED_UNARY[type(node.op)](safe_eval(node.operand))
    raise ValueError('unsupported arithmetic')

def arithmetic(text):
    norm=text.translate(str.maketrans('０１２３４５６７８９×÷','0123456789*/'))
    candidates=re.findall(r'[0-9.()+*/%\-\s]{3,}',norm)
    for c in sorted(candidates,key=len,reverse=True):
        expr=c.strip()
        if not re.search(r'\d\s*[+*/-]\s*\d|\([^)]*[+*/-][^)]*\)',expr): continue
        try:
            value=safe_eval(ast.parse(expr,mode='eval'))
            if isinstance(value,float) and value.is_integer(): value=int(value)
            return {'kind':'arithmetic','expression':expr,'value':value}
        except Exception: pass
    m=re.search(r'(\d+(?:\.\d+)?)\s*分.*?(?:何|いくつ).*?秒',norm)
    if m: return {'kind':'unit_time','expression':m.group(0),'value':float(m.group(1))*60,'unit':'秒'}
    m=re.search(r'(\d+(?:\.\d+)?)\s*時間.*?(?:何|いくつ).*?分',norm)
    if m: return {'kind':'unit_time','expression':m.group(0),'value':float(m.group(1))*60,'unit':'分'}
    return None

def run(argv,cwd):
    p=subprocess.run(argv,cwd=cwd,text=True,capture_output=True,timeout=10,check=False)
    return {'argv':argv,'exit_code':p.returncode,'stdout':p.stdout[-12000:],'stderr':p.stderr[-4000:]}

def explicit_path(text,cwd):
    for token in re.findall(r'([A-Za-z0-9_./-]+\.(?:md|txt|json|jsonl|py|sh|yaml|yml|toml|csv|log))',text,re.I):
        p=(Path(cwd)/token).resolve() if not Path(token).is_absolute() else Path(token).resolve()
        base=Path(cwd).resolve()
        try: p.relative_to(base)
        except ValueError: continue
        if p.exists() and p.is_file(): return p
    return None

def harness_readonly(text,cwd):
    if re.search(r'git\s+status',text,re.I): return {'kind':'git_status',**run(['git','status','--short','--branch'],cwd)}
    if re.search(r'pwd|現在(?:の)?directory|カレントディレクトリ',text,re.I): return {'kind':'pwd',**run(['pwd'],cwd)}
    if re.search(r'HEAD',text,re.I): return {'kind':'git_head',**run(['git','rev-parse','HEAD'],cwd)}
    if re.search(r'diff(?:量|統計|stat)|差分.*(?:量|統計)',text,re.I): return {'kind':'git_diff_stat',**run(['git','diff','--stat'],cwd)}
    if re.search(r'branch一覧|ブランチ一覧',text,re.I): return {'kind':'git_branch_list',**run(['git','branch','--format=%(refname:short)'],cwd)}
    p=explicit_path(text,cwd)
    if p and re.search(r'byte|バイト|サイズ|更新日時',text,re.I):
        st=p.stat(); return {'kind':'file_stat','path':str(p),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
    return None

def log_event(text,decision,out,elapsed_ms,pre_snapshot,post_work_snapshot):
    rec={'ts_unix':time.time(),'trace_id':out['trace_id'],'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'route':decision.route,'source':decision.source,'handoff':decision.handoff,'authority':decision.authority,'status':out['status'],'elapsed_ms':elapsed_ms,'resource_pre':pre_snapshot,'resource_post_work_pre_record':post_work_snapshot}
    return JOURNAL.append(rec)

def execute(text,router,cwd):
    pre_snapshot=resource_snapshot(); t0=time.perf_counter(); d=router.route(text); trace=uuid.uuid4().hex[:12]
    base={'trace_id':trace,'surface':'ordinary_llm','authority':d.authority,'route':d.route,'handoff':d.handoff,'source':d.source}
    if d.authority!='allowed': out={**base,'status':'confirmation_required'}
    elif d.route=='deterministic':
        z=arithmetic(text); out={**base,'status':'completed','specialist':'0b_calculator','result':z} if z is not None else {**base,'status':'handoff','specialist':d.handoff}
    elif d.route=='harness':
        z=harness_readonly(text,cwd); out={**base,'status':'completed','specialist':'readonly_harness','result':z} if z is not None else {**base,'status':'handoff','specialist':d.handoff}
    else: out={**base,'status':'handoff','specialist':d.handoff}
    post_work_snapshot=resource_snapshot(); resident=log_event(text,d,out,(time.perf_counter()-t0)*1000,pre_snapshot,post_work_snapshot); out['control_state']=resident; return out


def health_report():
    state={}
    gov=ROOT/'.work'/'rsf-llm'/'resource-governor-state.json'
    if gov.exists():
        try: state=json.loads(gov.read_text())
        except Exception: state={'status':'unreadable'}
    return {'surface':SURFACE_VERSION,'resource':resource_snapshot(),'adapter_exists':Path(DEFAULT_ADAPTER).exists(),'governor_state':state.get('state','unknown'),'control_state_bytes':CONTROL.stat().st_size if CONTROL.exists() else 0}

def doctor_report():
    checks={}
    z=arithmetic('(12+8)*5の値は？'); checks['calculator']=(z or {}).get('value')==100
    def snap(gib,psi=0.0): return {'mem_available_bytes':int(gib*GIB),'psi_memory_some_avg10':psi}
    g=ByteBudgetGovernor(model_estimated_bytes=1*GIB,enter_reserve_bytes=3*GIB,exit_reserve_bytes=5*GIB,enter_psi=.10,exit_psi=.02)
    seq=[g.decide(snap(10)).admit,g.decide(snap(3.5)).admit,g.decide(snap(5.5)).admit,g.decide(snap(6.2)).admit]
    checks['finite_ram_hysteresis']=seq==[True,False,False,True]
    checks['adapter_present']=Path(DEFAULT_ADAPTER).exists()
    return {'surface':SURFACE_VERSION,'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks}


def footprint_report():
    scripts=[ROOT/'experiments'/'rsf-llm'/'scripts'/name for name in ('shoal_workcell.py','shoal_runtime.py','finite_ram_control.py')]
    adapter=Path(DEFAULT_ADAPTER)
    adapter_bytes=sum(x.stat().st_size for x in adapter.rglob('*') if x.is_file()) if adapter.exists() else 0
    launcher=Path.home()/'.local'/'bin'/'catfood-shoal'
    return {'surface':SURFACE_VERSION,'canonical_runtime_code_bytes':sum(x.stat().st_size for x in scripts if x.exists()),'canonical_launcher_bytes':launcher.stat().st_size if launcher.exists() else 0,'adapter_checkpoint_bytes':adapter_bytes,'adapter_model_safetensors_bytes':(adapter/'adapter_model.safetensors').stat().st_size if (adapter/'adapter_model.safetensors').exists() else 0,'note':'base-model/venv/shared-library bytes are shared substrate and intentionally not counted as install-delta'}

def reinstall_projection(dest):
    dest=Path(dest).expanduser().resolve()
    src=Path.home()/'.local'/'bin'/'catfood-shoal'
    if dest.exists() or dest.is_symlink(): raise FileExistsError(f'refuse overwrite: {dest}')
    dest.parent.mkdir(parents=True,exist_ok=True)
    try:
        os.link(src,dest)
        mode='hardlink'; exclusive=0
    except OSError:
        dest.symlink_to(src)
        mode='symlink'; exclusive=dest.lstat().st_size
    dest.chmod(src.stat().st_mode) if mode=='hardlink' else None
    return {'surface':SURFACE_VERSION,'destination':str(dest),'mode':mode,'logical_path_bytes':dest.stat().st_size if mode=='hardlink' else dest.lstat().st_size,'exclusive_content_bytes':exclusive}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('text',nargs='?'); ap.add_argument('--cwd',default='.'); ap.add_argument('--debug',action='store_true'); ap.add_argument('--version',action='store_true'); ap.add_argument('--capabilities',action='store_true'); ap.add_argument('--health',action='store_true'); ap.add_argument('--doctor',action='store_true'); ap.add_argument('--footprint',action='store_true'); ap.add_argument('--reinstall',metavar='DEST'); a=ap.parse_args()
    if a.version:
        print(SURFACE_VERSION); return
    if a.capabilities:
        print(json.dumps({'surface':SURFACE_VERSION,'capabilities':CAPABILITIES},ensure_ascii=False)); return
    if a.health:
        print(json.dumps(health_report(),ensure_ascii=False)); return
    if a.doctor:
        print(json.dumps(doctor_report(),ensure_ascii=False)); return
    if a.footprint:
        print(json.dumps(footprint_report(),ensure_ascii=False)); return
    if a.reinstall:
        print(json.dumps(reinstall_projection(a.reinstall),ensure_ascii=False)); return
    if not a.text: raise SystemExit('text required')
    cwd=str(Path(a.cwd).resolve()); router=ShoalRouter(str(DEFAULT_ADAPTER),temperature=.5,min_confidence=.8)
    out=execute(a.text,router,cwd)
    if not a.debug:
        out.pop('route',None); out.pop('source',None)
    print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__': main()
