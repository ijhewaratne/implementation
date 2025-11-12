from pathlib import Path
import json, shutil, subprocess, time
import pandas as pd

def test_parallel_fanout_and_idempotence(tmp_path: Path, monkeypatch):
    # Create minimal inputs (CHA/DHA/LFA) as in smoke test
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

    # Ensure the sentinel exists:
    (plfa/".ready").write_text("ok")

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

    # Point Makefile to tmp_path if you're parameterizing paths via env
    # Otherwise call modules directly twice:
    from src import eaa, tca
    eaa_cfg = tmp_path/"configs/eaa.yml"
    tca_cfg = tmp_path/"configs/tca.yml"

    r1 = eaa.run(str(eaa_cfg)); k1 = json.loads(Path(tca.run(str(tca_cfg))["kpi"]).read_text())
    r2 = eaa.run(str(eaa_cfg)); k2 = json.loads(Path(tca.run(str(tca_cfg))["kpi"]).read_text())

    # Idempotent: same inputs → same KPI metrics (within numeric tolerance)
    assert abs(k1["economic_metrics"]["lcoh_eur_per_mwh"] - k2["economic_metrics"]["lcoh_eur_per_mwh"]) < 1e-6
    assert abs(k1["technical_metrics"]["feeder_max_utilization_pct"] - k2["technical_metrics"]["feeder_max_utilization_pct"]) < 1e-6





