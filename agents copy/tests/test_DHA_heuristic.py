import json
from pathlib import Path
import pandas as pd

from src.dha import run

def _fake_lfa(tmp: Path):
    d = tmp/"processed"/"lfa"; d.mkdir(parents=True, exist_ok=True)
    series = [0.0]*8760; series[100] = 60.0  # 60 kW spike
    (d/"B1.json").write_text(json.dumps({"building_id":"B1","series":series,"q10":series,"q90":series}))
    (d/"B2.json").write_text(json.dumps({"building_id":"B2","series":series,"q10":series,"q90":series}))

def _fake_topology(tmp: Path):
    df = pd.DataFrame({
        "building_id":["B1","B2"],
        "feeder_id":["F1","F1"],
        "feeder_rating_kw":[100.0, 100.0],
    })
    p = tmp/"data"/"processed"; p.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p/"feeder_topology.parquet")

def _cfg(tmp: Path):
    y = tmp/"configs"; y.mkdir(parents=True, exist_ok=True)
    (y/"dha.yml").write_text(
        "lfa_glob: "+str(tmp/"processed/lfa/*.json")+"\n"+
        "feeder_topology: "+str(tmp/"data/processed/feeder_topology.parquet")+"\n"+
        "out_dir: "+str(tmp/"processed/dha")+"\n"+
        "eval_dir: "+str(tmp/"eval/dha")+"\n"+
        "cop_default: 3.0\n"+
        "top_n_hours: 1\n"+
        "pandapower_enabled: false\n"
    )
    return str(y/"dha.yml")

def test_dha_heuristic(tmp_path: Path):
    _fake_lfa(tmp_path); _fake_topology(tmp_path)
    cfg = _cfg(tmp_path)
    res = run(cfg)
    assert res["status"] == "ok"
    loads = pd.read_csv(tmp_path/"processed/dha/feeder_loads.csv")
    assert not loads.empty and "utilization_pct" in loads.columns
