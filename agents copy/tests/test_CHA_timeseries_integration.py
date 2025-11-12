import json
from pathlib import Path
import pandas as pd
import pandapipes as pp
import pytest

import sys
sys.path.append('src')
from cha_timeseries import run_timeseries

def _fake_lfa(tmp: Path):
    d = tmp/"processed"/"lfa"; d.mkdir(parents=True, exist_ok=True)
    series = [0.0]*8760; series[123] = 50.0  # 50 kW spike at one hour
    (d/"B1.json").write_text(json.dumps({"building_id":"B1","series":series,"q10":series,"q90":series}))

def _tiny_net():
    net = pp.create_empty_network("test_network")
    pp.create_fluid_from_lib(net, "water")
    j0 = pp.create_junction(net, pn_bar=6.0, tfluid_k=273.15+80)
    j1 = pp.create_junction(net, pn_bar=6.0, tfluid_k=273.15+80)
    pp.create_ext_grid(net, junction=j0, p_bar=6.0, t_k=273.15+80)
    pp.create_pipe_from_parameters(net, j0, j1, length_km=0.05, diameter_m=0.05, k_mm=0.1)
    return net, {"B1": j1}

def test_cha_timeseries(tmp_path: Path, monkeypatch):
    _fake_lfa(tmp_path)
    net, bmap = _tiny_net()
    res = run_timeseries(
        net, bmap,
        lfa_glob=str(tmp_path/"processed/lfa/*.json"),
        t_supply_c=80, t_return_c=50, top_n=1,
        out_dir=str(tmp_path/"processed/cha"),
        v_max_ms=1.5, save_hourly=False,
    )
    assert res["status"] == "ok"
    seg = pd.read_csv(tmp_path/"processed/cha/segments.csv")
    assert "v_ms" in seg.columns and len(seg) >= 1
