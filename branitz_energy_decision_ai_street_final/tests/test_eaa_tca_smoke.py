import json
from pathlib import Path
import pandas as pd
from src import eaa, tca

def test_eaa_and_tca(tmp_path: Path):
    # Minimal CHA & DHA inputs
    pcha = tmp_path/"processed/cha"; pcha.mkdir(parents=True)
    pdha = tmp_path/"processed/dha"; pdha.mkdir(parents=True)
    pte  = tmp_path/"eval/te"; pte.mkdir(parents=True)
    pkpi = tmp_path/"processed/kpi"; pkpi.mkdir(parents=True)
    plfa = tmp_path/"processed/lfa"; plfa.mkdir(parents=True)

    # CHA segments
    pd.DataFrame({
        "pipe_id":[1,2],
        "length_m":[100.0,150.0],
        "d_inner_m":[0.10,0.15],
        "v_ms":[0.8,0.6],
        "dp_bar":[0.02,0.03]
    }).to_csv(pcha/"segments.csv", index=False)

    # DHA feeders
    pd.DataFrame({"feeder":["F1","F2"],"utilization_pct":[65.0,78.0]}).to_csv(pdha/"feeder_loads.csv", index=False)

    # LFA for annual heat (one tiny file)
    (plfa/"B1.json").write_text(json.dumps({"series":[5.0]*8760}))

    # Configs
    (tmp_path/"configs").mkdir()
    (tmp_path/"configs/eaa.yml").write_text(f"""
paths:
  cha_segments: {pcha/'segments.csv'}
  dha_feeders: {pdha/'feeder_loads.csv'}
  lfa_dir: {plfa}
  out_mc: {pte/'mc.parquet'}
  out_summary: {pte/'summary.csv'}
n_samples: 256
seed: 7
""")
    (tmp_path/"configs/tca.yml").write_text(f"""
scenario_name: testcase
paths:
  eaa_summary: {pte/'summary.csv'}
  cha_segments: {pcha/'segments.csv'}
  dha_feeders: {pdha/'feeder_loads.csv'}
  kpi_out: {pkpi/'kpi_summary.json'}
kpi_schema: schemas/kpi_summary.schema.json
kpi_schema_version: "1.0.0"
thresholds:
  feeder_utilization_warn_pct: 80
  lcoh_hp_advantage_eur_per_mwh: 10
forecast_rmse: 0.1
forecast_picp_90: 0.9
""")

    # Run
    res_eaa = eaa.run(str(tmp_path/"configs/eaa.yml"))
    assert Path(res_eaa["out_summary"]).exists()
    res_tca = tca.run(str(tmp_path/"configs/tca.yml"))
    out = Path(res_tca["kpi"])
    assert out.exists()
    obj = json.loads(out.read_text())
    # basic schema-like checks
    assert "economic_metrics" in obj and "technical_metrics" in obj and "recommendation" in obj
    assert obj["technical_metrics"]["feeder_max_utilization_pct"] >= 0.0
    assert obj["recommendation"]["preferred_scenario"] in ["DH", "HP", "Hybrid", "Inconclusive"]
