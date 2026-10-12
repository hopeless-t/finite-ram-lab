#!/usr/bin/env python3
import argparse,ast,hashlib,json,re,subprocess,time,uuid
from pathlib import Path
from shoal_runtime import ShoalRouter

ROOT=Path(__file__).resolve().parents[3]
EVENTS=ROOT/'.work'/'rsf-llm'/'runtime-events.jsonl'
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

def log_event(text,decision,out,elapsed_ms):
    EVENTS.parent.mkdir(parents=True,exist_ok=True)
    rec={'ts_unix':time.time(),'trace_id':out['trace_id'],'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'route':decision.route,'source':decision.source,'handoff':decision.handoff,'authority':decision.authority,'status':out['status'],'elapsed_ms':elapsed_ms}
    with EVENTS.open('a',encoding='utf-8') as f: f.write(json.dumps(rec,ensure_ascii=False,separators=(',',':'))+'\n')

def execute(text,router,cwd):
    t0=time.perf_counter(); d=router.route(text); trace=uuid.uuid4().hex[:12]
    base={'trace_id':trace,'surface':'ordinary_llm','authority':d.authority,'route':d.route,'handoff':d.handoff,'source':d.source}
    if d.authority!='allowed': out={**base,'status':'confirmation_required'}
    elif d.route=='deterministic':
        z=arithmetic(text); out={**base,'status':'completed','specialist':'0b_calculator','result':z} if z is not None else {**base,'status':'handoff','specialist':d.handoff}
    elif d.route=='harness':
        z=harness_readonly(text,cwd); out={**base,'status':'completed','specialist':'readonly_harness','result':z} if z is not None else {**base,'status':'handoff','specialist':d.handoff}
    else: out={**base,'status':'handoff','specialist':d.handoff}
    log_event(text,d,out,(time.perf_counter()-t0)*1000); return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('text'); ap.add_argument('--cwd',default='.'); ap.add_argument('--debug',action='store_true'); a=ap.parse_args()
    cwd=str(Path(a.cwd).resolve()); router=ShoalRouter('.work/rsf-llm/llm-jp-150m-semantic7-lora-v1',temperature=.5,min_confidence=.8)
    out=execute(a.text,router,cwd)
    if not a.debug:
        out.pop('route',None); out.pop('source',None)
    print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__': main()
