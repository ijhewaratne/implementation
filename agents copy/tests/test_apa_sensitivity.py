from pathlib import Path
import pandas as pd
import numpy as np
import yaml

def _fake_segments(tmp: Path):
    (tmp/"processed/cha").mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([
        # forward supply segments (lower dp)
        {"pipe_id":0,"length_m":100.0,"d_inner_m":0.05,"d_outer_m":0.06,"v_ms":0.8,"q_loss_Wm":np.nan,"return_only":False},
        {"pipe_id":1,"length_m":80.0, "d_inner_m":0.05,"d_outer_m":0.06,"v_ms":0.7,"q_loss_Wm":np.nan,"return_only":False},
        # return-only segment with much larger dp that must be excluded from worst-path
        {"pipe_id":2,"length_m":500.0,"d_inner_m":0.03,"d_outer_m":0.04,"v_ms":1.5,"q_loss_Wm":np.nan,"return_only":True},
    ])
    df.to_csv(tmp/"processed/cha/segments.csv", index=False)

def _cfg(tmp: Path) -> str:
    (tmp/"configs").mkdir(parents=True, exist_ok=True)
    cfg = {
        "roughness_k_mm": 0.1,
        "soil_temp_c": 10,
        "insulation_u_w_per_mk": 0.035,
        "deltaT_target_K": 30,
        "segments_csv": str(tmp/"processed/cha/segments.csv"),
        "out_csv": str(tmp/"eval/apa/sensitivity.csv"),
        "exclude_return_only": True,
        "sweeps": {
            "roughness_k_mm_rel": [-0.05, 0.0, 0.05],
            "soil_temp_c_abs": [-2, 0, 2],
            "insulation_u_w_per_mk_rel": [-0.05, 0.0, 0.05],
            "deltaT_target_K_abs": [-2, 0, 2]
        }
    }
    p = tmp/"configs/apa.yml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return str(p)

def test_apa_runs_and_writes(tmp_path: Path, monkeypatch):
    from importlib import import_module
    _fake_segments(tmp_path)
    cfg_path = _cfg(tmp_path)
    (tmp_path/"eval/apa").mkdir(parents=True, exist_ok=True)
    # import after writing to let module read files
    import sys
    sys.path.insert(0, str(tmp_path))
    apa = import_module("src.apa")
    res = apa.run(cfg_path)
    assert res["status"] == "ok"
    out = pd.read_csv(res["sensitivity_csv"])
    # has required columns and rows
    for c in ["param","delta","metric","baseline_metric","value","delta_value","pct_change"]:
        assert c in out.columns
    assert len(out) > 0

def test_return_only_exclusion_affects_worst_path(tmp_path: Path, monkeypatch):
    # Build two cases: with return-only excluded vs included, worst-path should shrink when excluded
    from importlib import import_module
    _fake_segments(tmp_path)
    base_cfg = {
        "roughness_k_mm": 0.1, "soil_temp_c": 10, "insulation_u_w_per_mk": 0.035, "deltaT_target_K": 30,
        "segments_csv": str(tmp_path/"processed/cha/segments.csv"),
        "sweeps": {"roughness_k_mm_rel":[0.0],"soil_temp_c_abs":[0],"insulation_u_w_per_mk_rel":[0.0],"deltaT_target_K_abs":[0]}
    }
    (tmp_path/"configs").mkdir(parents=True, exist_ok=True)
    import yaml, pandas as pd
    # Case A: exclude_return_only = True
    a = dict(base_cfg); a["exclude_return_only"] = True; a["out_csv"] = str(tmp_path/"eval/apa/sensitivityA.csv")
    (tmp_path/"configs/apaA.yml").write_text(yaml.safe_dump(a), encoding="utf-8")
    # Case B: exclude_return_only = False
    b = dict(base_cfg); b["exclude_return_only"] = False; b["out_csv"] = str(tmp_path/"eval/apa/sensitivityB.csv")
    (tmp_path/"configs/apaB.yml").write_text(yaml.safe_dump(b), encoding="utf-8")

    import sys; sys.path.insert(0, str(tmp_path))
    apa = import_module("src.apa")

    # Run both and read single-row metrics
    ra = apa.run(str(tmp_path/"configs/apaA.yml"))
    rb = apa.run(str(tmp_path/"configs/apaB.yml"))
    A = pd.read_csv(ra["sensitivity_csv"])
    B = pd.read_csv(rb["sensitivity_csv"])
    
    # Extract worst-path rows
    Aw = float(A.loc[A["metric"]=="worst_path_headloss_bar","value"].iloc[0])
    Bw = float(B.loc[B["metric"]=="worst_path_headloss_bar","value"].iloc[0])
    
    assert Aw < Bw   # excluding return-only should reduce worst-path headloss
