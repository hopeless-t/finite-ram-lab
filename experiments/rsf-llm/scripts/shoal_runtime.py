#!/usr/bin/env python3
import argparse, json, math, re, time
from dataclasses import dataclass
from pathlib import Path
from finite_ram_control import ByteBudgetGovernor, resource_snapshot


MODEL='llm-jp/llm-jp-3-150m-instruct3'
REV='5be263e1a3613cd5c163f41ad828c8de6a2aa6ec'
REPO_ROOT=Path(__file__).resolve().parents[3]
DEFAULT_ADAPTER=REPO_ROOT/'.work'/'rsf-llm'/'llm-jp-150m-semantic7-lora-v1'
DEFAULT_GOV_STATE=REPO_ROOT/'.work'/'rsf-llm'/'resource-governor-state.json'
CLASSES=['deterministic','harness','retrieval','tiny_model','larger_model','unknown','ordinary']
LETTERS='ABCDEFG'
PROMPT='''AuthorityはMVCA側で別判定します。依頼のsemantic intentだけを7分類し、説明せずA〜Gの1文字だけ返してください。\nA 決定論的な計算・構文検査・変換。\nB ローカルPCやrepositoryをHarnessで扱う。\nC 最新・外部情報を検索取得。\nD 短い意味分類・抽出・Canonical IR化。\nE 長い推論・計画・複雑な統合。\nF 情報不足・曖昧なのでUNKNOWN。\nG 普通の質問への説明・会話。'''

AUTHORITY=[
    r'送金',r'振込',r'資金移動',r'借入',r'投資(?:注文|を|へ|$)',r'秘密(?:鍵|情報)',r'認証(?:情報|トークン)',
    r'なりすま',r'なり代わ',r'本人として',r'金融取引',r'株(?:式)?(?:注文|を買|を購入)',r'契約(?:へ|を|同意)',r'有料契約',r'第三者へ(?:送|渡)',r'公開(?:チャネル|repository).*秘密',r'(?:秘密|private).*?(?:API.?key|APIキー|credential|token|トークン)',r'(?:API.?key|APIキー|credential|token|トークン).*?(?:公開|外へ|送|貼)',r'有料購入'
]
SIGNALS={
'deterministic':[r'計算',r'換算',r'変換',r'構文',r'parse',r'正規表現',r'括弧',r'昇順',r'二進',r'十進',r'16進',r'SHA-?256',r'base64',r'列数',r'(?:秒|分|時間).*?(?:秒|分|時間)'],
'harness':[r'ローカル',r'手元.*git status',r'git\s+status.*(?:取得|確認|見て|観測)',r'pwd.*(?:確認|取得|観測)',r'HEAD.*(?:SHA|取得|確認|観測|取って)',r'[A-Za-z0-9_./-]+\.(?:md|txt|json|jsonl|py|sh|yaml|yml|toml|csv|log).*(?:byte|バイト|サイズ|更新日時)',r'GAYA',r'repositor',r'\brepo\b',r'worktree',r'(?:branch|HEAD).*(?:確認|差分|変更|名|取得)',r'checkpoint.*(?:一覧|サイズ|確認|取得)',r'build',r'test',r'lint',r'script.*実行',r'フォルダ.*(?:容量|使用量)',r'directory.*容量',r'repo内'],
'retrieval':[r'今日',r'最新',r'一次情報',r'現在の公式',r'support matrix',r'公式(?:サイト|ドキュメント|発表|情報|status|リリース)',r'remote',r'現在公開',r'配布元',r'価格',r'利用規約',r'ライセンス',r'発表年',r'サポート終了',r'API仕様'],
'tiny_model':[r'分類して',r'抽出して',r'抜き出して',r'正規化',r'canonical',r'二値',r'二択',r'だけ判定',r'判定して',r'返して',r'だけ抜いて',r'対象名',r'だけ構造化',r'動詞と対象',r'severity'],
'larger_model':[r'統合して',r'総合比較',r'研究方針',r'ロードマップ',r'反証',r'設計し直',r'新仮説',r'因果仮説',r'長期運用',r'優先順位',r'共通設計原理',r'研究プログラム',r'総括して',r'再利用可能な原理',r'複数repo.*成果'],
'ordinary':[r'とは(?:何|どう)',r'って何',r'違い(?:を|は)',r'説明して',r'教えて',r'なぜ',r'長所と短所',r'ざっくり',r'何が変わる',r'使い分け',r'初心者向け']}

@dataclass
class Decision:
    route:str
    confidence:float
    source:str
    handoff:str
    authority:str='allowed'
    signals:tuple=()

class ShoalRouter:
    def __init__(self, adapter_dir, temperature=1.5, min_confidence=0.80, governor=None):
        self.temperature=temperature; self.min_confidence=min_confidence; self.adapter_dir=adapter_dir
        state=DEFAULT_GOV_STATE
        self.governor=governor or ByteBudgetGovernor(state_path=state)
        self.last_admission=None
        self.tok=None; self.model=None; self.cand=None; self.prefix_ids=None; self.prefix_cache=None
    def _authority(self,text):
        return any(re.search(p,text,re.I) for p in AUTHORITY)
    def _signals(self,text):
        found=[k for k,patterns in SIGNALS.items() if any(re.search(p,text,re.I) for p in patterns)]
        norm=text.translate(str.maketrans('０１２３４５６７８９×÷','0123456789*/'))
        if re.search(r'(?<![A-Za-z0-9_])(?:\(?\s*)?\d+(?:\.\d+)?\s*[+*/-]\s*\d+(?:\.\d+)?',norm) and 'deterministic' not in found:
            found.append('deterministic')
        return tuple(found)
    def _ensure_model(self):
        if self.model is not None: return
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tok=AutoTokenizer.from_pretrained(MODEL,revision=REV); tok.padding_side='left'; tok.pad_token=tok.pad_token or tok.eos_token
        base=AutoModelForCausalLM.from_pretrained(MODEL,revision=REV,dtype=torch.float32)
        model=PeftModel.from_pretrained(base,self.adapter_dir); model.eval()
        self.tok=tok; self.model=model; self.cand=[tok.encode(x,add_special_tokens=False)[0] for x in LETTERS]
        # Finite-RAM shared-prefix residency: discover only the token prefix that is
        # provably identical across varied user texts, then cache its KV state.
        probes=['A','ZZZZZZZZZZZZZZ','前の続きやって','CPUとGPUはどう使い分ける？']
        seqs=[]
        for q in probes:
            msgs=[{'role':'system','content':PROMPT},{'role':'user','content':'依頼: '+q+'\n分類:'}]
            rendered=tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
            seqs.append(tok(rendered,return_tensors='pt',add_special_tokens=False).input_ids[0].tolist())
        cp=0
        for i in range(min(map(len,seqs))):
            if len({row[i] for row in seqs}) != 1: break
            cp += 1
        if cp > 0:
            import torch
            prefix=torch.tensor([seqs[0][:cp]],dtype=torch.long)
            with torch.inference_mode(): self.prefix_cache=model(input_ids=prefix,use_cache=True).past_key_values
            self.prefix_ids=seqs[0][:cp]
    def _model(self,text):
        self._ensure_model()
        import torch
        msgs=[{'role':'system','content':PROMPT},{'role':'user','content':'依頼: '+text+'\n分類:'}]
        rendered=self.tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
        enc=self.tok(rendered,return_tensors='pt',add_special_tokens=False,truncation=True,max_length=384)
        t0=time.perf_counter()
        with torch.inference_mode():
            use_prefix=(self.prefix_ids is not None and enc.input_ids.shape[1]>len(self.prefix_ids) and enc.input_ids[0,:len(self.prefix_ids)].tolist()==self.prefix_ids)
            if use_prefix:
                import copy
                cache=copy.copy(self.prefix_cache); cache.layers=[copy.copy(layer) for layer in self.prefix_cache.layers]
                logits=self.model(input_ids=enc.input_ids[:,len(self.prefix_ids):],past_key_values=cache,use_cache=False).logits[0,-1,self.cand].float()
            else:
                logits=self.model(**enc).logits[0,-1,self.cand].float()
        p=torch.softmax(logits/self.temperature,dim=-1)
        j=int(torch.argmax(p)); return CLASSES[j],float(p[j]),(time.perf_counter()-t0)*1000
    @staticmethod
    def _handoff(route):
        return {'deterministic':'deterministic_tool','harness':'local_harness','retrieval':'retrieval_surface','tiny_model':'tiny_semantic_specialist','larger_model':'larger_reasoner','unknown':'clarify_or_observe','ordinary':'ordinary_qa_specialist'}.get(route,'larger_reasoner')
    def route(self,text):
        if self._authority(text):
            return Decision('authority',1.0,'policy_guard','require_user_confirmation','requires_confirmation',())
        signals=self._signals(text)
        if len(signals)==1:
            r=signals[0]
            return Decision(r,0.99,'0b_single_signal',self._handoff(r),'allowed',signals)
        admission=self.governor.decide(resource_snapshot())
        self.last_admission=admission
        if not admission.admit:
            return Decision('unknown',1.0,'resource_pressure_handoff','larger_reasoner','allowed',signals)
        pred,conf,_lat=self._model(text)
        if len(signals)>1 and pred not in signals:
            return Decision('unknown',conf,'signal_model_conflict','clarify_or_larger_reasoner','allowed',signals)
        if len(signals)>1 and pred in signals and conf >= 0.55:
            return Decision(pred,conf,'signal_model_agreement',self._handoff(pred),'allowed',signals)
        if conf < self.min_confidence and pred not in ('larger_model','unknown'):
            return Decision('unknown',conf,'low_confidence_handoff','larger_reasoner','allowed',signals)
        return Decision(pred,conf,'semantic7_model',self._handoff(pred),'allowed',signals)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('text',nargs='?'); ap.add_argument('--adapter',default=str(DEFAULT_ADAPTER)); ap.add_argument('--temperature',type=float,default=0.5); ap.add_argument('--debug',action='store_true'); a=ap.parse_args()
    if not a.text: raise SystemExit('text required')
    r=ShoalRouter(a.adapter,temperature=a.temperature).route(a.text)
    out={'surface':'ordinary_llm','handoff':r.handoff,'authority':r.authority}
    if a.debug: out.update({'route':r.route,'confidence':r.confidence,'source':r.source,'signals':r.signals})
    print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__': main()
