#!/usr/bin/env python3
# Deterministic 0B semantic router benchmark. No external actions are performed.
import argparse, json, math, re, resource, statistics, time
from pathlib import Path

CLASSES = ['authority','deterministic','harness','retrieval','tiny_model','larger_model','unknown','ordinary']

RULES = {
    'authority': ['PROTECTED_ACTION:'],
    'deterministic': ['計算','妥当か検査','日後','SHA256','構文だけ検査','変換して','拡張子','割り切れる','英数字'],
    'retrieval': ['今日の','最新の','公開日','GitHub上','最近の','現在の','外部文献','最新リリース','公開repo','benchmark結果'],
    'harness': ['failing tests','GAYA-CENTRAL','作業ブランチ','ディスク使用量','git status','対象repo','ローカルでbuild','failed run','指定ディレクトリ','branchのdiff'],
    'larger_model': ['22repo','複数仮説','長期アーキテクチャ','論文群','コードベース全体','長い会話履歴','未知ドメイン','複数の性能指標','製品仕様','failure biopsy'],
    'tiny_model': ['canonical intent','どれか分類','意図を一語','target と constraint','retry / reobserve / escalate','read-only intent','semantic IR','制約として抽出','質問か命令','研究判定intent'],
    'ordinary': ['LLMって何','分かりやすく言い換え','listとtuple','RAMとSSD','小さいモデル','JSONL','confidence calibration','Pareto frontier','retrievalを外部化','UNKNOWNと言える'],
}
UNKNOWN_TEXT = {'いい感じにやって','あれを直して','前のやつと同じにして','それ消していい？','例のモデルを使って','いつもの場所へ移して','適当に最適化して','なんか変だから見て','これ実行して','必要ならやっといて'}

def predict(text):
    for label in ['authority','deterministic','retrieval','harness','larger_model','tiny_model','ordinary']:
        hits = sum(token.lower() in text.lower() for token in RULES[label])
        if hits:
            return label, min(0.995, 0.84 + 0.04 * hits), f'{label}:{hits}'
    if text in UNKNOWN_TEXT:
        return 'unknown', 0.93, 'explicit_underspecification'
    return 'unknown', 0.58, 'no_rule_hit'

def distribution(pred, confidence):
    other = (1.0-confidence)/(len(CLASSES)-1)
    return {c: confidence if c == pred else other for c in CLASSES}

def score_brier(prob, expected):
    return sum((prob[c] - (1.0 if c == expected else 0.0))**2 for c in CLASSES)/len(CLASSES)

def score_ece(records, bins=10):
    total = len(records); out = 0.0
    for i in range(bins):
        lo, hi = i/bins, (i+1)/bins
        bucket = [r for r in records if lo <= r['confidence'] < hi or (i == bins-1 and r['confidence'] == 1.0)]
        if bucket:
            observed = sum(r['correct'] for r in bucket)/len(bucket)
            claimed = sum(r['confidence'] for r in bucket)/len(bucket)
            out += len(bucket)/total * abs(observed-claimed)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('corpus'); ap.add_argument('--out', required=True); ap.add_argument('--repeats', type=int, default=100)
    a = ap.parse_args()
    rows = [json.loads(line) for line in Path(a.corpus).read_text(encoding='utf-8').splitlines() if line.strip()]
    records = []
    for row in rows:
        expected = row['expected_semantic_outcome']['route']
        pred, conf, reason = predict(row['input'])
        prob = distribution(pred, conf)
        expected_auth = row['expected_semantic_outcome']['authority']
        predicted_auth = 'requires_confirmation' if pred == 'authority' else 'allowed'
        records.append({'id':row['id'],'expected':expected,'predicted':pred,'confidence':conf,'correct':pred==expected,'authority_correct':predicted_auth==expected_auth,'reason':reason,'brier':score_brier(prob, expected)})
    timings=[]
    for _ in range(a.repeats):
        for row in rows:
            start=time.perf_counter_ns(); predict(row['input']); timings.append((time.perf_counter_ns()-start)/1e6)
    timings.sort()
    p95=timings[math.ceil(0.95*len(timings))-1]
    coverage={}
    for threshold in [0.6,0.7,0.8,0.9,0.95]:
        accepted=[r for r in records if r['confidence'] >= threshold]
        coverage[str(threshold)]={'coverage':len(accepted)/len(records),'selective_accuracy':sum(r['correct'] for r in accepted)/len(accepted) if accepted else None,'escalation_rate':1-len(accepted)/len(records)}
    result={
        'run_id':f'0b-{int(time.time())}','system':'regex_fsm_router_v0','attempted':len(records),
        'accuracy':sum(r['correct'] for r in records)/len(records),
        'authority_accuracy':sum(r['authority_correct'] for r in records)/len(records),
        'brier':statistics.mean(r['brier'] for r in records),'ece':score_ece(records),
        'median_latency_ms':statistics.median(timings),'p95_latency_ms':p95,
        'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        'coverage':coverage,'failures':[r for r in records if not r['correct'] or not r['authority_correct']]
    }
    Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['run_id','attempted','accuracy','authority_accuracy','brier','ece','median_latency_ms','p95_latency_ms','peak_rss_bytes']}, ensure_ascii=False, indent=2))
    print('failures=',len(result['failures']))

if __name__ == '__main__':
    main()
