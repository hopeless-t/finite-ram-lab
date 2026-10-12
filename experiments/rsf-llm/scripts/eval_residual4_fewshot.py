#!/usr/bin/env python3
import argparse,json,resource,statistics,time
from pathlib import Path
import torch
from transformers import AutoTokenizer,AutoConfig,AutoModelForCausalLM,AutoModelForImageTextToText
C=['tiny_model','larger_model','unknown','ordinary'];L='ABCD'
P='''依頼を4分類し、説明せずA〜Dの1文字だけ返す。 A 短い意味分類・抽出・Canonical IR化。 B 長い推論・計画・複雑な統合。 C 情報不足・曖昧なのでUNKNOWN。 D 普通の質問への説明・会話。 例: 「次の文が質問か命令か分類して」=>A。 「この論文群を読んで反証可能な新仮説を作って」=>B。 「あれを直して」=>C。 「RAMとSSDの違いは？」=>D。'''
def render(t,s):
 m=[{'role':'system','content':P},{'role':'user','content':'依頼: '+s+'\n分類:'}]
 return t.apply_chat_template(m,tokenize=False,add_generation_prompt=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--revision',required=True);p.add_argument('--corpus',required=True);p.add_argument('--out',required=True);p.add_argument('--batch-size',type=int,default=4);a=p.parse_args()
 allrows=[json.loads(x) for x in Path(a.corpus).read_text(encoding='utf-8').splitlines() if x.strip()];rows=[r for r in allrows if r['expected_semantic_outcome']['route'] in C]
 tok=AutoTokenizer.from_pretrained(a.model,revision=a.revision);tok.padding_side='left';tok.pad_token=tok.pad_token or tok.eos_token;cfg=AutoConfig.from_pretrained(a.model,revision=a.revision)
 m=(AutoModelForImageTextToText.from_pretrained(a.model,revision=a.revision,dtype=torch.float32) if cfg.model_type=='qwen3_5' else AutoModelForCausalLM.from_pretrained(a.model,revision=a.revision,dtype=torch.float32));m.eval();ids=[tok.encode(ch,add_special_tokens=False)[0] for ch in L];rec=[];times=[]
 with torch.inference_mode():
  for s in range(0,len(rows),a.batch_size):
   part=rows[s:s+a.batch_size];enc=tok([render(tok,r['input']) for r in part],padding=True,return_tensors='pt',add_special_tokens=False);t=time.perf_counter();o=m(**enc);times.append((time.perf_counter()-t)*1000);pp=torch.softmax(o.logits[:,-1,ids].float(),dim=1).cpu().tolist()
   for row,v in zip(part,pp):
    j=max(range(4),key=v.__getitem__);pred=C[j];exp=row['expected_semantic_outcome']['route'];rec.append({'id':row['id'],'expected':exp,'predicted':pred,'confidence':v[j],'correct':pred==exp})
 out={'model_id':a.model,'revision':a.revision,'experiment':'externalized-residual4-fewshot-v1','attempted':len(rec),'accuracy':sum(r['correct'] for r in rec)/len(rec),'random_floor':0.25,'batch_wall_ms':sum(times),'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'failures':[r for r in rec if not r['correct']]};Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='failures'},ensure_ascii=False,indent=2));print('failures',len(out['failures']))
if __name__=='__main__':main()
