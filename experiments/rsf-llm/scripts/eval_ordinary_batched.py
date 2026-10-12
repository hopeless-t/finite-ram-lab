#!/usr/bin/env python3
import argparse,json,resource,statistics,time
from pathlib import Path
import torch
from transformers import AutoTokenizer,AutoConfig,AutoModelForCausalLM,AutoModelForImageTextToText

def score_output(row,text):
 low=text.lower(); hits=[]
 for group in row['must_any']:
  hits.append(any(str(k).lower() in low for k in group))
 return hits,sum(hits)/len(hits)

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--revision',required=True);p.add_argument('--corpus',required=True);p.add_argument('--out',required=True);p.add_argument('--max-new',type=int,default=40);p.add_argument('--batch-size',type=int,default=4);a=p.parse_args()
 rows=[json.loads(x) for x in Path(a.corpus).read_text(encoding='utf-8').splitlines() if x.strip()]
 tok=AutoTokenizer.from_pretrained(a.model,revision=a.revision);tok.padding_side='left';tok.pad_token=tok.pad_token or tok.eos_token
 cfg=AutoConfig.from_pretrained(a.model,revision=a.revision)
 m=(AutoModelForImageTextToText.from_pretrained(a.model,revision=a.revision,dtype=torch.float32) if cfg.model_type=='qwen3_5' else AutoModelForCausalLM.from_pretrained(a.model,revision=a.revision,dtype=torch.float32));m.eval();records=[];batch_times=[]
 for start in range(0,len(rows),a.batch_size):
  part=rows[start:start+a.batch_size]; rendered=[]
  for row in part:
   msgs=[{'role':'system','content':'日本語で、質問に短く普通に役立つ回答をしてください。知らないことは断定しないでください。'},{'role':'user','content':row['input']}]
   rendered.append(tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True))
  enc=tok(rendered,padding=True,return_tensors='pt',add_special_tokens=False);t0=time.perf_counter()
  with torch.inference_mode(): out=m.generate(**enc,max_new_tokens=a.max_new,do_sample=False,pad_token_id=tok.pad_token_id)
  batch_times.append((time.perf_counter()-t0)*1000)
  for i,row in enumerate(part):
   prompt_len=enc['input_ids'].shape[1]; text=tok.decode(out[i][prompt_len:],skip_special_tokens=True).strip();hits,sc=score_output(row,text)
   records.append({'id':row['id'],'input':row['input'],'output':text,'group_hits':hits,'score':sc})
 result={'model_id':a.model,'revision':a.revision,'attempted':len(records),'ordinary_concept_score':sum(r['score'] for r in records)/len(records),'fully_satisfied_rate':sum(all(r['group_hits']) for r in records)/len(records),'batch_size':a.batch_size,'max_new_tokens':a.max_new,'generation_wall_ms':sum(batch_times),'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'records':records}
 Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='records'},ensure_ascii=False,indent=2));print('outputs:');
 for r in records: print(r['id'],r['score'],repr(r['output'][:160]))
if __name__=='__main__':main()
