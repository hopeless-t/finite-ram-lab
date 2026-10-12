#!/usr/bin/env python3
import argparse,json,math,random,statistics,time
from pathlib import Path
import torch
import torch.nn.functional as F
from peft import LoraConfig,get_peft_model
from transformers import AutoModelForCausalLM,AutoTokenizer

CLASSES=['deterministic','harness','retrieval','tiny_model','larger_model','unknown','ordinary']; LETTERS='ABCDEFG'; C2I={c:i for i,c in enumerate(CLASSES)}
PROMPT='''AuthorityはMVCA側で別判定します。依頼のsemantic intentだけを7分類し、説明せずA〜Gの1文字だけ返してください。\nA 決定論的な計算・構文検査・変換。\nB ローカルPCやrepositoryをHarnessで扱う。\nC 最新・外部情報を検索取得。\nD 短い意味分類・抽出・Canonical IR化。\nE 長い推論・計画・複雑な統合。\nF 情報不足・曖昧なのでUNKNOWN。\nG 普通の質問への説明・会話。'''

def load(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def split(rows):
 by={c:[] for c in CLASSES}
 for r in rows:
  q=r['expected_semantic_outcome']['route']
  if q in by: by[q].append(r)
 tr=[]; ca=[]
 for c in CLASSES:
  if len(by[c])<12: raise RuntimeError((c,len(by[c])))
  tr+=by[c][:10]; ca+=by[c][10:12]
 return tr,ca
def render(tok,t):
 m=[{'role':'system','content':PROMPT},{'role':'user','content':'依頼: '+t+'\n分類:'}]
 return tok.apply_chat_template(m,tokenize=False,add_generation_prompt=True)
def batch(tok,rows): return tok([render(tok,r['input']) for r in rows],padding=True,truncation=True,max_length=384,return_tensors='pt',add_special_tokens=False)
def candids(tok):
 out=[]
 for ch in LETTERS:
  z=tok.encode(ch,add_special_tokens=False)
  if len(z)!=1: raise RuntimeError((ch,z))
  out.append(z[0])
 return out
def logits(model,tok,rows,cand,bs=8):
 z=[]; model.eval()
 with torch.inference_mode():
  for s in range(0,len(rows),bs): z+=model(**batch(tok,rows[s:s+bs])).logits[:,-1,cand].float().cpu().tolist()
 return z
def acc(ls,rows): return sum(max(range(7),key=ls[i].__getitem__)==C2I[r['expected_semantic_outcome']['route']] for i,r in enumerate(rows))/len(rows)
def probs(ls,T):
 out=[]
 for v in ls:
  m=max(v); e=[math.exp((x-m)/T) for x in v]; q=sum(e); out.append([x/q for x in e])
 return out
def nll(pp,rows): return sum(-math.log(max(p[C2I[r['expected_semantic_outcome']['route']]],1e-15)) for p,r in zip(pp,rows))/len(rows)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--source',required=True); ap.add_argument('--out',required=True); ap.add_argument('--checkpoint-dir',required=True); ap.add_argument('--epochs',type=int,default=4); ap.add_argument('--seed',type=int,default=45); a=ap.parse_args()
 random.seed(a.seed); torch.manual_seed(a.seed); rows=load(a.source); train,cal=split(rows)
 model_id='llm-jp/llm-jp-3-150m-instruct3'; rev='5be263e1a3613cd5c163f41ad828c8de6a2aa6ec'
 tok=AutoTokenizer.from_pretrained(model_id,revision=rev); tok.padding_side='left'; tok.pad_token=tok.pad_token or tok.eos_token; cand=candids(tok)
 base=AutoModelForCausalLM.from_pretrained(model_id,revision=rev,dtype=torch.float32); base.config.use_cache=False
 model=get_peft_model(base,LoraConfig(r=4,lora_alpha=8,lora_dropout=0.05,target_modules=['q_proj','v_proj'],bias='none',task_type='CAUSAL_LM'))
 opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=8e-4,weight_decay=.01)
 trainable=sum(p.numel() for p in model.parameters() if p.requires_grad); hist=[]; best=-1; bestn=1e9; beststate=None; patience=0; start=time.perf_counter()
 for ep in range(1,a.epochs+1):
  model.train(); order=list(range(len(train))); random.shuffle(order); losses=[]
  for s in range(0,len(order),8):
   part=[train[i] for i in order[s:s+8]]; enc=batch(tok,part); opt.zero_grad(set_to_none=True); o=model(**enc); c=o.logits[:,-1,cand].float(); y=torch.tensor([C2I[x['expected_semantic_outcome']['route']] for x in part]); loss=F.cross_entropy(c,y); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step(); losses.append(float(loss))
  ca=logits(model,tok,cal,cand); ca_acc=acc(ca,cal); tr_acc=None; raw_nll=nll(probs(ca,1),cal)
  h={'epoch':ep,'loss':statistics.mean(losses),'train_accuracy':tr_acc,'calibration_accuracy':ca_acc,'calibration_nll_raw':raw_nll}; hist.append(h); print(json.dumps(h))
  score=(ca_acc,-raw_nll)
  if ca_acc>best or (ca_acc==best and raw_nll<bestn):
   best=ca_acc; bestn=raw_nll; patience=0; beststate={k:v.detach().cpu().clone() for k,v in model.state_dict().items() if 'lora_' in k}
  else: patience+=1
 if beststate:
  cur=model.state_dict(); cur.update(beststate); model.load_state_dict(cur,strict=False)
 Path(a.checkpoint_dir).mkdir(parents=True,exist_ok=True); model.save_pretrained(a.checkpoint_dir); tok.save_pretrained(a.checkpoint_dir)
 ca=logits(model,tok,cal,cand); grid=[.25,.5,.75,1,1.5,2,3,4,6,8,12,16,24,32]; vals=[(nll(probs(ca,T),cal),T) for T in grid]; cal_nll,T=min(vals)
 result={'run_id':f'semantic7-dev-v1-{int(time.time())}','model_id':model_id,'revision':rev,'source':a.source,'train_rows':len(train),'calibration_rows':len(cal),'seed':a.seed,'history':hist,'epochs_completed':len(hist),'best_calibration_accuracy':best,'temperature':T,'calibration_nll':cal_nll,'trainable_parameters':trainable,'train_wall_seconds':time.perf_counter()-start,'checkpoint_dir':a.checkpoint_dir,'holdout_evaluated':False}
 Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({k:result[k] for k in ['train_rows','calibration_rows','epochs_completed','best_calibration_accuracy','temperature','calibration_nll','trainable_parameters','train_wall_seconds']},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
