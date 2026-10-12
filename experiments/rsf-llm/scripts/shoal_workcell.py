#!/usr/bin/env python3
import argparse,ast,hashlib,json,os,re,subprocess,time,uuid
from pathlib import Path
from shoal_runtime import ShoalRouter, DEFAULT_ADAPTER
from finite_ram_control import BoundedControlState, ByteBudgetGovernor, GIB, resource_snapshot

ROOT=Path(__file__).resolve().parents[3]
SURFACE_VERSION='catfood-shoal/reinstall-loop-v23'
CAPABILITIES=['core_text','0b_calculator','readonly_harness','semantic_handoff','authority_guard','finite_ram_governor','bounded_control_state','shared_prefix_kv','version_surface','capability_introspection','health_surface','self_doctor','self_reinstall','footprint_introspection','install_verification','idempotent_ensure','install_planning','safe_install_repair','safe_projection_uninstall','install_attestation']
EVENTS=ROOT/'.work'/'rsf-llm'/'runtime-events.jsonl'
CONTROL=ROOT/'.work'/'rsf-llm'/'control-state.json'
LAUNCHER=Path.home()/'.local'/'bin'/'catfood-shoal'
ADAPTER=Path(DEFAULT_ADAPTER)
RUNTIME_FILES=tuple(ROOT/'experiments'/'rsf-llm'/'scripts'/n for n in ('shoal_workcell.py','shoal_runtime.py','finite_ram_control.py'))
JOURNAL=BoundedControlState(EVENTS,CONTROL,budget_bytes=4096)
ALLOWED_BIN={ast.Add:lambda a,b:a+b,ast.Sub:lambda a,b:a-b,ast.Mult:lambda a,b:a*b,ast.Div:lambda a,b:a/b,ast.FloorDiv:lambda a,b:a//b,ast.Mod:lambda a,b:a%b}
ALLOWED_UNARY={ast.UAdd:lambda a:+a,ast.USub:lambda a:-a}

def surfaced(**x): return {'surface':SURFACE_VERSION,**x}
def timed(t0,**x): return surfaced(operation_ns=time.perf_counter_ns()-t0,**x)
def inspected(dest):
    t=time.perf_counter_ns(); d=_dest_path(dest); return t,d,projection_state(d)

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
    return surfaced(resource=resource_snapshot(),adapter_exists=ADAPTER.exists(),governor_state=state.get('state','unknown'),control_state_bytes=CONTROL.stat().st_size if CONTROL.exists() else 0)

def doctor_report():
    checks={}
    z=arithmetic('(12+8)*5の値は？'); checks['calculator']=(z or {}).get('value')==100
    def snap(gib,psi=0.0): return {'mem_available_bytes':int(gib*GIB),'psi_memory_some_avg10':psi}
    g=ByteBudgetGovernor(model_estimated_bytes=1*GIB,enter_reserve_bytes=3*GIB,exit_reserve_bytes=5*GIB,enter_psi=.10,exit_psi=.02)
    seq=[g.decide(snap(10)).admit,g.decide(snap(3.5)).admit,g.decide(snap(5.5)).admit,g.decide(snap(6.2)).admit]
    checks['finite_ram_hysteresis']=seq==[True,False,False,True]
    checks['adapter_present']=ADAPTER.exists()
    return surfaced(status='PASS' if all(checks.values()) else 'FAIL',checks=checks)



def sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def attest_install():
    launcher=LAUNCHER
    adapter=ADAPTER/'adapter_model.safetensors'
    return surfaced(launcher_sha256=sha256_file(launcher),adapter_sha256=sha256_file(adapter),runtime_source_sha256={x.name:sha256_file(x) for x in RUNTIME_FILES})

def footprint_report():
    adapter=ADAPTER
    adapter_bytes=sum(x.stat().st_size for x in adapter.rglob('*') if x.is_file()) if adapter.exists() else 0
    launcher=LAUNCHER
    return surfaced(canonical_runtime_code_bytes=sum(x.stat().st_size for x in RUNTIME_FILES if x.exists()),canonical_launcher_bytes=launcher.stat().st_size if launcher.exists() else 0,adapter_checkpoint_bytes=adapter_bytes,adapter_model_safetensors_bytes=(adapter/'adapter_model.safetensors').stat().st_size if (adapter/'adapter_model.safetensors').exists() else 0,note='base-model/venv/shared-library bytes are shared substrate and intentionally not counted as install-delta')

def _dest_path(dest): return Path(os.path.abspath(os.path.expanduser(dest)))

def projection_state(dest):
    dest=_dest_path(dest); src=LAUNCHER
    if not dest.exists() and not dest.is_symlink(): return {'state':'missing','healthy':False,'destination':str(dest)}
    if dest.is_symlink():
        try: target=dest.resolve(strict=True)
        except FileNotFoundError: return {'state':'broken_symlink','healthy':False,'destination':str(dest)}
        healthy=(target==src.resolve())
        return {'state':'symlink_canonical' if healthy else 'foreign_symlink','healthy':healthy,'destination':str(dest)}
    st,ss=dest.stat(),src.stat(); same=(st.st_dev,st.st_ino)==(ss.st_dev,ss.st_ino)
    if same: return {'state':'hardlink_canonical','healthy':True,'destination':str(dest)}
    try: duplicate=(st.st_size==ss.st_size and hashlib.sha256(dest.read_bytes()).digest()==hashlib.sha256(src.read_bytes()).digest())
    except OSError: duplicate=False
    return {'state':'duplicate_copy' if duplicate else 'foreign_file','healthy':False,'destination':str(dest)}

def reinstall_projection(dest):
    dest=_dest_path(dest); src=LAUNCHER
    if dest.exists() or dest.is_symlink(): raise FileExistsError(f'refuse overwrite: {dest}')
    dest.parent.mkdir(parents=True,exist_ok=True)
    try: os.link(src,dest); mode='hardlink'; exclusive=0
    except OSError: dest.symlink_to(src); mode='symlink'; exclusive=dest.lstat().st_size
    return surfaced(destination=str(dest),mode=mode,logical_path_bytes=dest.stat().st_size if mode=='hardlink' else dest.lstat().st_size,exclusive_content_bytes=exclusive)


def install_plan(dest):
    t0,dest,st=inspected(dest)
    if st['healthy']: action='noop'
    elif st['state']!='missing': action='refuse_foreign_or_broken'
    else:
        parent=dest.parent
        while not parent.exists() and parent!=parent.parent: parent=parent.parent
        src=LAUNCHER
        action='hardlink' if parent.stat().st_dev==src.stat().st_dev else 'symlink'
    return timed(t0,planned_action=action,**st)


def repair_projection(dest):
    t0,dest,st=inspected(dest)
    if st['healthy']: return timed(t0,action='noop',**st)
    if st['state']!='duplicate_copy': return timed(t0,action='refuse_unowned',**st)
    tmp=dest.with_name(dest.name+f'.reinstall-{os.getpid()}')
    try:
        out=reinstall_projection(tmp); os.replace(tmp,dest)
    finally:
        if tmp.exists() or tmp.is_symlink(): tmp.unlink()
    out.update({'destination':str(dest),'action':'atomic_repair_duplicate_to_projection','operation_ns':time.perf_counter_ns()-t0}); return out


def uninstall_projection(dest):
    t0,dest,st=inspected(dest)
    if st['state']=='missing': return timed(t0,action='noop_missing',**st)
    if st['state'] not in ('hardlink_canonical','symlink_canonical','duplicate_copy'):
        return timed(t0,action='refuse_unowned',**st)
    dest.unlink(); return timed(t0,action='removed_owned_projection',destination=str(dest),state_before=st['state'])

def ensure_projection(dest):
    t0=time.perf_counter_ns(); st=projection_state(dest)
    if st['healthy']:
        return timed(t0,action='noop',**st)
    if st['state']!='missing':
        return timed(t0,action='refuse_foreign_or_broken',**st)
    out=reinstall_projection(dest); out.update({'action':'created','operation_ns':time.perf_counter_ns()-t0}); return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('text',nargs='?'); ap.add_argument('--cwd',default='.'); ap.add_argument('--debug',action='store_true')
    for name in ('version','capabilities','health','doctor','footprint','attest'): ap.add_argument('--'+name.replace('_','-'),dest=name,action='store_true')
    for name in ('reinstall','verify_install','ensure_installed','install_plan','repair_install','uninstall_projection'): ap.add_argument('--'+name.replace('_','-'),dest=name,metavar='DEST')
    a=ap.parse_args()
    if a.version: print(SURFACE_VERSION); return
    if a.capabilities: print(json.dumps(surfaced(capabilities=CAPABILITIES),ensure_ascii=False)); return
    for name,fn in (('health',health_report),('doctor',doctor_report),('footprint',footprint_report),('attest',attest_install)):
        if getattr(a,name): print(json.dumps(fn(),ensure_ascii=False)); return
    for name,fn in (('reinstall',reinstall_projection),('verify_install',projection_state),('ensure_installed',ensure_projection),('install_plan',install_plan),('repair_install',repair_projection),('uninstall_projection',uninstall_projection)):
        value=getattr(a,name)
        if value:
            out=fn(value)
            if name=='verify_install': out=surfaced(**out)
            print(json.dumps(out,ensure_ascii=False)); return
    if not a.text: raise SystemExit('text required')
    cwd=str(Path(a.cwd).resolve()); router=ShoalRouter(str(DEFAULT_ADAPTER),temperature=.5,min_confidence=.8); out=execute(a.text,router,cwd)
    if not a.debug: out.pop('route',None); out.pop('source',None)
    print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__': main()
