from __future__ import annotations

import argparse, csv, json, random, re, statistics
from pathlib import Path
from typing import Any

ARMS = ("buffered", "dontneed_48m", "dontneed_64m", "dontneed_80m", "dontneed_96m")
RELEASE = {"buffered": None, "dontneed_48m": 48, "dontneed_64m": 64, "dontneed_80m": 80, "dontneed_96m": 96}
FILE_RE = re.compile(r"trial-(?P<order>\\d+)-(?P<arm>buffered|dontneed_48m|dontneed_64m|dontneed_80m|dontneed_96m)\\.json$")

def load_spec(path: str|Path)->dict[str,Any]:
    return json.loads(Path(path).read_text())

def schedule_rows(spec:dict[str,Any], pressure:int, block:int)->list[dict[str,Any]]:
    if pressure not in [int(x) for x in spec["memory_high_mib"]]:
        raise ValueError("pressure outside frozen design")
    rows=[{"arm":a} for a in spec["arms"]]
    random.Random(int(spec["base_schedule_seed"])+pressure*1009+block*9176).shuffle(rows)
    return [{"order":i,**r} for i,r in enumerate(rows)]

def write_schedule(spec:dict[str,Any],pressure:int,block:int,out:str|Path)->None:
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["order","arm"],lineterminator="\n"); w.writeheader(); w.writerows(schedule_rows(spec,pressure,block))

def summarize(spec:dict[str,Any], root:Path)->dict[str,Any]:
    trials=[]
    for p in sorted(root.rglob("trial-*.json")):
        m=FILE_RE.search(p.name)
        if not m: continue
        z=json.loads(p.read_text())
        high=int(z["parameters"]["expected_high_bytes"])
        rel=z["parameters"]["release_interval_mib"]
        trials.append({
            "status":z["status"], "arm":z["arm"], "high_mib":high/(1024*1024),
            "release_mib":rel, "events":int(z["scan_deltas"]["memory_high_events"]),
            "peak_mib":int(z["scan_deltas"]["max_memory_current"])/(1024*1024),
            "scan_ms":int(z["scan"]["elapsed_ns"])/1e6,
            "file_post":float(z["file"]["post_scan_residency"]["resident_fraction"]),
        })
    if len(trials)!=int(spec["expected_trials"]): raise ValueError(f"expected {spec['expected_trials']} trials, got {len(trials)}")
    if any(x["status"]!="PASS" for x in trials): raise ValueError("all trials must PASS")
    cells={}
    for high in [int(x) for x in spec["memory_high_mib"]]:
        for arm in spec["arms"]:
            g=[x for x in trials if x["high_mib"]==high and x["arm"]==arm]
            if len(g)!=int(spec["runner_blocks_per_pressure"]): raise ValueError(f"incomplete cell {high}/{arm}")
            rel=RELEASE[arm]
            cells[f"{high}/{arm}"]={
                "trials":len(g),
                "median_memory_high_events":statistics.median(x["events"] for x in g),
                "median_peak_mib":statistics.median(x["peak_mib"] for x in g),
                "median_scan_ms":statistics.median(x["scan_ms"] for x in g),
                "median_file_post_fraction":statistics.median(x["file_post"] for x in g),
                "release_fraction_of_high":None if rel is None else rel/high,
                "peak_fraction_of_high":statistics.median(x["peak_mib"]/high for x in g),
                "headroom_over_hot_mib":high-int(spec["hot_anon_mib"]),
            }
    return {"experiment_id":spec["experiment_id"],"execution_status":"PASS","trial_count":len(trials),"cells":cells,
      "inference_boundary":"Cross-pressure directional screen only; no controller formula or OSS default authorized."}

def main()->None:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    s=sub.add_parser("schedule"); s.add_argument("--spec",required=True); s.add_argument("--pressure",type=int,required=True); s.add_argument("--block",type=int,required=True); s.add_argument("--out",required=True)
    a=sub.add_parser("aggregate"); a.add_argument("--spec",required=True); a.add_argument("--input-root",required=True); a.add_argument("--out",required=True)
    x=p.parse_args(); spec=load_spec(x.spec)
    if x.cmd=="schedule": write_schedule(spec,x.pressure,x.block,x.out); return
    result=summarize(spec,Path(x.input_root)); out=Path(x.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__": main()
