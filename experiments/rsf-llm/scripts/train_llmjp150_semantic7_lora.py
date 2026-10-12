#!/usr/bin/env python3
import argparse, json, math, os, random, resource, statistics, time
from pathlib import Path

import torch
import torch.nn.functional as F
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

CLASSES = ['deterministic','harness','retrieval','tiny_model','larger_model','unknown','ordinary']
LETTERS = 'ABCDEFG'
C2I = {c:i for i,c in enumerate(CLASSES)}
PROMPT = '''AuthorityはMVCA側で別判定します。依頼のsemantic intentだけを7分類し、説明せずA〜Gの1文字だけ返してください。
A 決定論的な計算・構文検査・変換。
B ローカルPCやrepositoryをHarnessで扱う。
C 最新・外部情報を検索取得。
D 短い意味分類・抽出・Canonical IR化。
E 長い推論・計画・複雑な統合。
F 情報不足・曖昧なのでUNKNOWN。
G 普通の質問への説明・会話。'''

def load_rows(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]

def split_per_class(rows):
    by={c:[] for c in CLASSES}
    for r in rows:
        route=r['expected_semantic_outcome']['route']
        if route in by: by[route].append(r)
    train=[]; cal=[]
    for c in CLASSES:
        if len(by[c]) < 10: raise RuntimeError(f'{c}: need >=10 rows, got {len(by[c])}')
        train.extend(by[c][:8]); cal.extend(by[c][8:10])
    return train, cal

def render(tok, text):
    msgs=[{'role':'system','content':PROMPT},{'role':'user','content':'依頼: '+text+'\n分類:'}]
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

def make_batch(tok, rows):
    texts=[render(tok,r['input']) for r in rows]
    return tok(texts, padding=True, truncation=True, max_length=384, return_tensors='pt', add_special_tokens=False)

def candidate_ids(tok):
    ids=[]
    for ch in LETTERS:
        z=tok.encode(ch,add_special_tokens=False)
        if len(z)!=1: raise RuntimeError(f'letter {ch} tokenized to {z}')
        ids.append(z[0])
    return ids

def batch_logits(model,tok,rows,cand,batch_size=8):
    out=[]
    model.eval()
    with torch.inference_mode():
        for s in range(0,len(rows),batch_size):
            part=rows[s:s+batch_size]; enc=make_batch(tok,part); o=model(**enc)
            out.extend(o.logits[:,-1,cand].float().cpu().tolist())
    return out

def accuracy(logits,rows):
    return sum(max(range(len(CLASSES)),key=logits[i].__getitem__)==C2I[rows[i]['expected_semantic_outcome']['route']] for i in range(len(rows)))/len(rows)

def probs(logits,T):
    z=[]
    for ls in logits:
        m=max(ls); e=[math.exp((x-m)/T) for x in ls]; s=sum(e); z.append([x/s for x in e])
    return z

def nll(prob,rows):
    v=0.0
    for p,r in zip(prob,rows): v-=math.log(max(p[C2I[r['expected_semantic_outcome']['route']]],1e-15))
    return v/len(rows)

def ece(records):
    n=len(records); out=0.0
    for i in range(10):
        bucket=[r for r in records if i/10 <= r['confidence'] < (i+1)/10 or (i==9 and r['confidence']==1)]
        if bucket:
            a=sum(r['correct'] for r in bucket)/len(bucket); c=sum(r['confidence'] for r in bucket)/len(bucket)
            out += len(bucket)/n*abs(a-c)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',required=True); ap.add_argument('--holdout',required=True); ap.add_argument('--out',required=True); ap.add_argument('--checkpoint-dir',required=True)
    ap.add_argument('--model',default='llm-jp/llm-jp-3-150m-instruct3'); ap.add_argument('--revision',default='5be263e1a3613cd5c163f41ad828c8de6a2aa6ec')
    ap.add_argument('--epochs',type=int,default=12); ap.add_argument('--batch-size',type=int,default=8); ap.add_argument('--lr',type=float,default=8e-4); ap.add_argument('--seed',type=int,default=42)
    a=ap.parse_args(); random.seed(a.seed); torch.manual_seed(a.seed)
    rows=load_rows(a.source); train,cal=split_per_class(rows); holdout=[r for r in load_rows(a.holdout) if r['expected_semantic_outcome']['route'] in CLASSES]
    tok=AutoTokenizer.from_pretrained(a.model,revision=a.revision); tok.padding_side='left'; tok.pad_token=tok.pad_token or tok.eos_token; cand=candidate_ids(tok)
    base=AutoModelForCausalLM.from_pretrained(a.model,revision=a.revision,dtype=torch.float32); base.config.use_cache=False
    cfg=LoraConfig(r=4,lora_alpha=8,lora_dropout=0.05,target_modules=['q_proj','v_proj'],bias='none',task_type='CAUSAL_LM')
    model=get_peft_model(base,cfg); trainable=sum(p.numel() for p in model.parameters() if p.requires_grad); total=sum(p.numel() for p in model.parameters())
    opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=a.lr,weight_decay=0.01)
    history=[]; best=-1.0; best_state=None; patience=0; t_train=time.perf_counter()
    for epoch in range(1,a.epochs+1):
        model.train(); order=list(range(len(train))); random.shuffle(order); losses=[]
        for s in range(0,len(order),a.batch_size):
            part=[train[i] for i in order[s:s+a.batch_size]]; enc=make_batch(tok,part); opt.zero_grad(set_to_none=True)
            o=model(**enc); candidate=o.logits[:,-1,cand].float(); target=torch.tensor([C2I[r['expected_semantic_outcome']['route']] for r in part],dtype=torch.long)
            loss=F.cross_entropy(candidate,target); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step(); losses.append(float(loss.detach()))
        cal_logits=batch_logits(model,tok,cal,cand,a.batch_size); cal_acc=accuracy(cal_logits,cal); train_logits=batch_logits(model,tok,train,cand,a.batch_size); train_acc=accuracy(train_logits,train)
        history.append({'epoch':epoch,'loss':statistics.mean(losses),'train_accuracy':train_acc,'calibration_accuracy':cal_acc})
        print(json.dumps(history[-1]))
        if cal_acc > best:
            best=cal_acc; patience=0; best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items() if 'lora_' in k}
        else:
            patience += 1
        if patience >= 4 and epoch >= 5: break
    train_wall=time.perf_counter()-t_train
    if best_state:
        current=model.state_dict(); current.update(best_state); model.load_state_dict(current,strict=False)
    Path(a.checkpoint_dir).mkdir(parents=True,exist_ok=True); model.save_pretrained(a.checkpoint_dir); tok.save_pretrained(a.checkpoint_dir)
    adapter_bytes=sum(p.stat().st_size for p in Path(a.checkpoint_dir).glob('*') if p.is_file())
    cal_logits=batch_logits(model,tok,cal,cand,a.batch_size)
    grid=[0.25,0.5,0.75,1,1.5,2,3,4,6,8,12,16,24,32]
    vals=[(nll(probs(cal_logits,T),cal),T) for T in grid]; cal_nll,T=min(vals)
    lat=[]; hold_logits=[]; model.eval()
    with torch.inference_mode():
        for r in holdout:
            enc=make_batch(tok,[r]); t0=time.perf_counter(); o=model(**enc); lat.append((time.perf_counter()-t0)*1000); hold_logits.append(o.logits[0,-1,cand].float().cpu().tolist())
    pp=probs(hold_logits,T); records=[]
    for r,p in zip(holdout,pp):
        j=max(range(len(CLASSES)),key=p.__getitem__); exp=r['expected_semantic_outcome']['route']; conf=p[j]
        br=sum((p[k]-(1 if CLASSES[k]==exp else 0))**2 for k in range(len(CLASSES)))/len(CLASSES)
        records.append({'id':r['id'],'expected':exp,'predicted':CLASSES[j],'confidence':conf,'correct':CLASSES[j]==exp,'brier':br})
    coverage={}
    for th in [0.3,0.4,0.5,0.6,0.7,0.8,0.9]:
        z=[r for r in records if r['confidence']>=th]; coverage[str(th)]={'coverage':len(z)/len(records),'selective_accuracy':sum(r['correct'] for r in z)/len(z) if z else None,'escalation_rate':1-len(z)/len(records),'accepted':len(z)}
    result={'run_id':f'llmjp150-semantic7-lora-{int(time.time())}','model_id':a.model,'revision':a.revision,'method':'LoRA next-token semantic-7 projection with authority externalized','lora':{'r':4,'alpha':8,'dropout':0.05,'targets':['q_proj','v_proj']},'seed':a.seed,'train_rows':len(train),'calibration_rows':len(cal),'holdout_rows':len(holdout),'epochs_completed':len(history),'best_calibration_accuracy':best,'history':history,'train_wall_seconds':train_wall,'trainable_parameters':trainable,'total_parameters_with_adapter':total,'adapter_dir':a.checkpoint_dir,'adapter_bytes_local':adapter_bytes,'temperature':T,'calibration_nll':cal_nll,'accuracy':sum(r['correct'] for r in records)/len(records),'brier':statistics.mean(r['brier'] for r in records),'ece':ece(records),'median_latency_ms':statistics.median(lat),'p95_latency_ms':sorted(lat)[math.ceil(.95*len(lat))-1],'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'coverage':coverage,'failures':[r for r in records if not r['correct']]}
    Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['epochs_completed','best_calibration_accuracy','train_wall_seconds','trainable_parameters','adapter_bytes_local','temperature','accuracy','brier','ece','median_latency_ms','p95_latency_ms','peak_rss_bytes']},ensure_ascii=False,indent=2)); print('failures',len(result['failures']))
if __name__=='__main__': main()
