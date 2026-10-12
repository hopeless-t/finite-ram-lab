#!/usr/bin/env python3
import argparse,json,math,random,resource,statistics,time
from pathlib import Path
import torch
import torch.nn.functional as F
from peft import LoraConfig,get_peft_model
from transformers import AutoTokenizer,AutoModelForCausalLM

CLASSES=['tiny_model','larger_model','unknown','ordinary']; LETTERS='ABCD'; C2I={c:i for i,c in enumerate(CLASSES)}
PROMPT='''外部Harnessが authority・deterministic calculation・repository操作・retrieval を先に処理済みです。残った依頼だけを4分類し、説明せずA〜Dの1文字だけ返してください。
A 短い意味分類・抽出・Canonical IR化。
B 長い推論・計画・複雑な統合。
C 情報不足・曖昧なのでUNKNOWN。
D 普通の質問への説明・会話。'''

def rows(path): return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]
def filtered(rs): return [r for r in rs if r['expected_semantic_outcome']['route'] in CLASSES]
def split(rs):
 by={c:[] for c in CLASSES}
 for r in filtered(rs): by[r['expected_semantic_outcome']['route']].append(r)
 tr=[];cal=[]
 for c in CLASSES: tr+=by[c][:8];cal+=by[c][8:10]
 return tr,cal
def render(tok,text):
 msgs=[{'role':'system','content':PROMPT},{'role':'user','content':'依頼: '+text+'\n分類:'}]
 return tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True) if getattr(tok,'chat_template',None) else PROMPT+'\n依頼: '+text+'\n分類:'
def batch(tok,rs): return tok([render(tok,r['input']) for r in rs],padding=True,truncation=True,max_length=384,return_tensors='pt',add_special_tokens=False)
def cids(tok):
 out=[]
 for c in LETTERS:
  z=tok.encode(c,add_special_tokens=False)
  if len(z)!=1: raise RuntimeError((c,z))
  out.append(z[0])
 return out
def logits(model,tok,rs,cand,bs):
 out=[];model.eval()
 with torch.inference_mode():
  for s in range(0,len(rs),bs): out.extend(model(**batch(tok,rs[s:s+bs])).logits[:,-1,cand].float().cpu().tolist())
 return out
def acc(ls,rs): return sum(max(range(4),key=ls[i].__getitem__)==C2I[rs[i]['expected_semantic_outcome']['route']] for i in range(len(rs)))/len(rs)
def probs(ls,T):
 out=[]
 for row in ls:
  m=max(row);e=[math.exp((x-m)/T) for x in row];z=sum(e);out.append([x/z for x in e])
 return out
def nll(pp,rs): return sum(-math.log(max(p[C2I[r['expected_semantic_outcome']['route']]],1e-15)) for p,r in zip(pp,rs))/len(rs)
def ece(rec):
 n=len(rec);v=0
 for i in range(10):
  b=[r for r in rec if i/10<=r['confidence']<(i+1)/10 or (i==9 and r['confidence']==1)]
  if b:v+=len(b)/n*abs(sum(r['correct'] for r in b)/len(b)-sum(r['confidence'] for r in b)/len(b))
 return v

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--holdout',required=True);ap.add_argument('--out',required=True);ap.add_argument('--checkpoint-dir',required=True);ap.add_argument('--model',default='llm-jp/llm-jp-3-150m-instruct3');ap.add_argument('--revision',default='5be263e1a3613cd5c163f41ad828c8de6a2aa6ec');ap.add_argument('--epochs',type=int,default=16);ap.add_argument('--batch-size',type=int,default=4);ap.add_argument('--lr',type=float,default=8e-4);ap.add_argument('--seed',type=int,default=43);a=ap.parse_args();random.seed(a.seed);torch.manual_seed(a.seed)
 tr,cal=split(rows(a.source));ho=filtered(rows(a.holdout));tok=AutoTokenizer.from_pretrained(a.model,revision=a.revision);tok.padding_side='left';tok.pad_token=tok.pad_token or tok.eos_token;cand=cids(tok)
 base=AutoModelForCausalLM.from_pretrained(a.model,revision=a.revision,dtype=torch.float32);base.config.use_cache=False;model=get_peft_model(base,LoraConfig(r=4,lora_alpha=8,lora_dropout=0.05,target_modules=['q_proj','v_proj'],bias='none',task_type='CAUSAL_LM'));opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=a.lr,weight_decay=.01);trainable=sum(p.numel() for p in model.parameters() if p.requires_grad)
 best=-1;best_state=None;pat=0;hist=[];ttrain=time.perf_counter()
 for epoch in range(1,a.epochs+1):
  order=list(range(len(tr)));random.shuffle(order);model.train();losses=[]
  for s in range(0,len(order),a.batch_size):
   part=[tr[i] for i in order[s:s+a.batch_size]];enc=batch(tok,part);opt.zero_grad(set_to_none=True);o=model(**enc);candidate=o.logits[:,-1,cand].float();target=torch.tensor([C2I[r['expected_semantic_outcome']['route']] for r in part]);loss=F.cross_entropy(candidate,target);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);opt.step();losses.append(float(loss.detach()))
  ca=logits(model,tok,cal,cand,a.batch_size);ta=logits(model,tok,tr,cand,a.batch_size);row={'epoch':epoch,'loss':statistics.mean(losses),'train_accuracy':acc(ta,tr),'calibration_accuracy':acc(ca,cal)};hist.append(row);print(json.dumps(row))
  if row['calibration_accuracy']>best:best=row['calibration_accuracy'];pat=0;best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items() if 'lora_' in k}
  else:pat+=1
  if pat>=4 and epoch>=5:break
 train_wall=time.perf_counter()-ttrain
 if best_state:
  st=model.state_dict();st.update(best_state);model.load_state_dict(st,strict=False)
 Path(a.checkpoint_dir).mkdir(parents=True,exist_ok=True);model.save_pretrained(a.checkpoint_dir);tok.save_pretrained(a.checkpoint_dir);local_bytes=sum(p.stat().st_size for p in Path(a.checkpoint_dir).glob('*') if p.is_file())
 cal_ls=logits(model,tok,cal,cand,a.batch_size);grid=[.25,.5,.75,1,1.5,2,3,4,6,8,12,16,24,32];T=min((nll(probs(cal_ls,t),cal),t) for t in grid)[1]
 lat=[];hl=[];model.eval()
 with torch.inference_mode():
  for r in ho:
   enc=batch(tok,[r]);t=time.perf_counter();o=model(**enc);lat.append((time.perf_counter()-t)*1000);hl.append(o.logits[0,-1,cand].float().cpu().tolist())
 pp=probs(hl,T);rec=[]
 for r,p in zip(ho,pp):
  j=max(range(4),key=p.__getitem__);exp=r['expected_semantic_outcome']['route'];br=sum((p[k]-(1 if CLASSES[k]==exp else 0))**2 for k in range(4))/4;rec.append({'id':r['id'],'expected':exp,'predicted':CLASSES[j],'confidence':p[j],'correct':CLASSES[j]==exp,'brier':br})
 cov={}
 for th in [.4,.5,.6,.7,.8,.9]:
  z=[r for r in rec if r['confidence']>=th];cov[str(th)]={'coverage':len(z)/len(rec),'selective_accuracy':sum(r['correct'] for r in z)/len(z) if z else None,'escalation_rate':1-len(z)/len(rec),'accepted':len(z)}
 res={'run_id':f'llmjp150-residual4-{int(time.time())}','model_id':a.model,'revision':a.revision,'method':'LoRA residual-4 after externalization','externalized':['authority','deterministic','harness','retrieval'],'seed':a.seed,'train_rows':len(tr),'calibration_rows':len(cal),'holdout_rows':len(ho),'epochs_completed':len(hist),'best_calibration_accuracy':best,'history':hist,'train_wall_seconds':train_wall,'trainable_parameters':trainable,'adapter_bytes_local':local_bytes,'temperature':T,'accuracy':sum(r['correct'] for r in rec)/len(rec),'brier':statistics.mean(r['brier'] for r in rec),'ece':ece(rec),'median_latency_ms':statistics.median(lat),'p95_latency_ms':sorted(lat)[math.ceil(.95*len(lat))-1],'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'coverage':cov,'failures':[r for r in rec if not r['correct']]};Path(a.out).write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:res[k] for k in ['epochs_completed','best_calibration_accuracy','train_wall_seconds','trainable_parameters','adapter_bytes_local','temperature','accuracy','brier','ece','median_latency_ms','p95_latency_ms','peak_rss_bytes']},ensure_ascii=False,indent=2));print('failures',len(res['failures']))
if __name__=='__main__':main()
