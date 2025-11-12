from pathlib import Path
import json
import pandas as pd
import numpy as np

from src.eaa import run, _lognormal_from_mean_rel_sigma

def _fake_upstreams(tmp: Path):
    # CHA segments (length)
    seg = pd.DataFrame({"pipe_id":[0,1], "length_m":[100.0, 150.0]})
    pcha = tmp/"processed/cha"; pcha.mkdir(parents=True, exist_ok=True)
    seg.to_csv(pcha/"segments.csv", index=False)

    # DHA feeders (not directly used except path check; still create minimal frame)
    fd = pd.DataFrame({"feeder_id":["F1"], "hour":[0], "p_kw":[0.0], "utilization_pct":[0.0]})
    pdha = tmp/"processed/dha"; pdha.mkdir(parents=True, exist_ok=True)
    fd.to_csv(pdha/"feeder_loads.csv", index=False)

    # LFA annual heat: make one building with 8760 x 1 kW → 8.76 MWh
    plfa = tmp/"processed/lfa"; plfa.mkdir(parents=True, exist_ok=True)
    series = [1.0]*8760
    (plfa/"B1.json").write_text(json.dumps({"building_id":"B1","series":series,"q10":series,"q90":series}))

def _cfg(tmp: Path) -> str:
    y = tmp/"configs"; y.mkdir(parents=True, exist_ok=True)
    (y/"eaa.yml").write_text(
        "cha_segments: "+str(tmp/"processed/cha/segments.csv")+"\n"+
        "dha_feeders: "+str(tmp/"processed/dha/feeder_loads.csv")+"\n"+
        "lfa_glob: "+str(tmp/"processed/lfa/*.json")+"\n"+
        "out_dir: "+str(tmp/"eval/te")+"\n"+
        "mc_samples: 600\n"+
        "random_seed: 123\n"+
        "dh_cost_per_m_eur_mean: 600\n"+
        "dh_cost_per_m_eur_rel_sigma: 0.20\n"+
        "elec_price_eur_per_mwh_mean: 150\n"+
        "elec_price_eur_per_mwh_rel_sigma: 0.25\n"+
        "grid_co2_kg_per_mwh_mean: 250\n"+
        "grid_co2_kg_per_mwh_rel_sigma: 0.30\n"+
        "discount_rate: 0.07\n"+
        "lifetime_years: 30\n"+
        "pump_kwh_per_mwh_heat: 15\n"
    )
    return str(y/"eaa.yml")

def test_eaa_runs_and_writes(tmp_path: Path):
    _fake_upstreams(tmp_path)
    cfg = _cfg(tmp_path)
    res = run(cfg)
    assert res["status"] == "ok"
    mc = pd.read_parquet(res["mc_parquet"])
    summ = pd.read_csv(res["summary_csv"])
    assert len(mc) >= 600
    assert np.isfinite(summ[["mean","median","p2_5","p97_5"]].values).all()

def test_lognormal_builder_stats_reasonable():
    import numpy as np
    rng = np.random.default_rng(0)
    x = _lognormal_from_mean_rel_sigma(100.0, 0.2, 100000, rng)
    # sample mean close to 100 within a tolerance
    assert abs(x.mean() - 100.0) / 100.0 < 0.03
