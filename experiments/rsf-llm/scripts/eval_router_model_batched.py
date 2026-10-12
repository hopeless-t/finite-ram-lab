#!/usr/bin/env python3
import argparse,json,math,resource,statistics,time
from pathlib import Path
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM,AutoConfig,AutoModelForImageTextToText
C=['authority','deterministic','harness','retrieval','tiny_model','larger_model','unknown','ordinary'];L='ABCDEFGH'
P_EN='''Choose one category letter only. A authority-boundary. B deterministic calculation or validation. C local harness task. D external retrieval. E small semantic classification. F complex synthesis. G unknown or ambiguous. H ordinary explanation.'''; P_JA='''依頼を8分類のどれか1つに分類し、説明せずA〜Hの1文字だけ返す。 A 権限制約で確認が必要。 B 決定論的な計算・構文検査・変換。 C ローカルPCやrepositoryをHarnessで扱う。 D 最新・外部情報を検索取得。 E 短い意味分類・抽出・Canonical IR化。 F 長い推論・計画・複雑な統合。 G 情報不足・曖昧なのでUNKNOWN。 H 普通の質問への説明・会話。'''; P=P_EN
def render(t,s):
 m=[{'role':'system','content':P},{'role':'user','content':'Request: '+s+'\nAnswer:'}]
 return t.apply_chat_template(m,tokenize=False,add_generation_prompt=True) if getattr(t,'chat_template',None) else P+'\nRequest: '+s+'\nAnswer:'
def calc(r):
 n=len(r);a=sum(x['ok'] for x in r)/n;b=sum(x['brier'] for x in r)/n;e=0
 for i in range(10):
  z=[x for x in r if i/10<=x['conf']<(i+1)/10 or (i==9 and x['conf']==1)]
  if z:e+=len(z)/n*abs(sum(x['ok'] for x in z)/len(z)-sum(x['conf'] for x in z)/len(z))
 return a,b,e
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--revision',required=True);p.add_argument('--corpus',required=True);p.add_argument('--out',required=True);p.add_argument('--batch-size',type=int,default=8);p.add_argument('--prompt',choices=['en','ja'],default='en');a=p.parse_args();global P;P=P_JA if a.prompt=='ja' else P_EN
 rows=[json.loads(x) for x in Path(a.corpus).read_text().splitlines() if x.strip()]
 t0=time.perf_counter();tok=AutoTokenizer.from_pretrained(a.model,revision=a.revision);tls=time.perf_counter()-t0;tok.padding_side='left';tok.pad_token=tok.pad_token or tok.eos_token
 cfg=AutoConfig.from_pretrained(a.model,revision=a.revision);t0=time.perf_counter();m=(AutoModelForImageTextToText.from_pretrained(a.model,revision=a.revision,dtype=torch.float32) if cfg.model_type=='qwen3_5' else AutoModelForCausalLM.from_pretrained(a.model,revision=a.revision,dtype=torch.float32));m.eval();mls=time.perf_counter()-t0
 ids=[]
 for ch in L:
  q=tok.encode(ch,add_special_tokens=False)
  if len(q)!=1:raise RuntimeError((ch,q))
  ids.append(q[0])
 rec=[];bt=[]
 with torch.inference_mode():
  for s in range(0,len(rows),a.batch_size):
   part=rows[s:s+a.batch_size];enc=tok([render(tok,x['input']) for x in part],padding=True,return_tensors='pt',add_special_tokens=False);t0=time.perf_counter();o=m(**enc);dt=(time.perf_counter()-t0)*1000;bt.append(dt)
   pp=torch.softmax(o.logits[:,-1,ids].float(),dim=1).cpu().tolist()
   for row,v in zip(part,pp):
    j=max(range(8),key=v.__getitem__);exp=row['expected_semantic_outcome']['route'];pred=C[j];cf=v[j];br=sum((v[k]-(1 if C[k]==exp else 0))**2 for k in range(8))/8;rec.append({'id':row['id'],'expected':exp,'predicted':pred,'conf':cf,'ok':pred==exp,'brier':br})
 lat=[]
 with torch.inference_mode():
  for row in rows[:10]:
   enc=tok(render(tok,row['input']),return_tensors='pt',add_special_tokens=False);t0=time.perf_counter();m(**enc);lat.append((time.perf_counter()-t0)*1000)
 ac,br,ec=calc(rec);sl=sorted(lat);out={'model_id':a.model,'revision':a.revision,'parameters':sum(x.numel() for x in m.parameters()),'dtype':str(next(m.parameters()).dtype),'attempted':len(rec),'accuracy':ac,'brier':br,'ece':ec,'median_latency_ms':statistics.median(lat),'p95_latency_ms':sl[-1],'throughput_tasks_per_second':len(rec)/(sum(bt)/1000),'batch_size':a.batch_size,'prompt':a.prompt,'evaluator_version':'v2-no-double-special','peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'tokenizer_load_seconds':tls,'model_load_seconds':mls,'failures':[x for x in rec if not x['ok']]};Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='failures'},ensure_ascii=False,indent=2));print('failures',len(out['failures']))
if __name__=='__main__':main()
