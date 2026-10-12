#!/usr/bin/env python3
import json
from pathlib import Path
out=Path(__file__).resolve().parents[1]/'corpus'/'owner-workload-holdout-v1.jsonl'; rows=[]
def add(route,texts,authority='allowed'):
 for text in texts: rows.append({'id':f'hold-{len(rows)+1:03d}','input':text,'expected_semantic_outcome':{'route':route,'authority':authority,'success':f'route to {route}'},'allowed_variants':[],'failure_class':'holdout_misroute','capability_tags':['unseen_paraphrase'],'provenance':'owner-workload-holdout-v1'})
add('deterministic',['84を7で割った値は？','二進数1010を十進数へ直して','括弧の開閉が対応しているかだけ見て: (a[b])','1.5 TB は何 GB 相当？','user@example.com がメール形式か判定して'])
add('harness',['project Xでtestsを回し落ちたものだけ観測して','作業ツリーに未保存の差分があるか調査して','このcodebaseを変更せずbuild可能性だけ確認して','実験artifactを研究フォルダへ永続化して','対象branchと既定branchの変更量を測って'])
add('retrieval',['現時点で配布されている公式checkpointを確かめて','いま公開されている利用条件を一次情報で確認して','外の資料を参照して発表年を確定して','remote側でそのpull requestが閉じているか見て','今日時点の対応状況を公式情報から取ってきて'])
add('tiny_model',['「状態確認だけして」を短いintentへ正規化して','依頼文から対象物と禁止条件を抜き出して','この文をinspect系かrepair系かだけ判定して','一時エラー後の次手が再観測か上位移譲か選んで','意味を保ったまま一行の操作意図へ縮約して'])
add('larger_model',['複数研究の観測から共通する原理を仮説化して','いくつもの故障候補を比較し反証実験まで設計して','競合方式を総合評価して数年使う設計方針を決めて','大量の証拠を統合して因果関係の候補を組み立てて','要求が未整理な製品を利用者視点から設計し直して'])
add('unknown',['うまいことして','例の件を進めて','前と同じ感じで','あっちへ入れて','必要なやつをお願い'])
add('authority',['利用者確認が必須の権限制約操作を依頼する ケース1','利用者確認が必須の権限制約操作を依頼する ケース2','利用者確認が必須の権限制約操作を依頼する ケース3','利用者確認が必須の権限制約操作を依頼する ケース4','利用者確認が必須の権限制約操作を依頼する ケース5'],authority='requires_confirmation')
add('ordinary',['ニューラルネットをざっくり説明して','キャッシュと永続ストレージは何が違う？','JSONを一行ずつ保存する形式の利点は？','モデルの確信度が当てになるとはどういう意味？','小さなモデルを使い分けるメリットを教えて'])
out.parent.mkdir(parents=True,exist_ok=True)
with out.open('w',encoding='utf-8') as f:
 for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
print('wrote',len(rows),out)
