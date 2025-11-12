import json
from jsonschema import Draft202012Validator

def test_tca_schema_exact():
    from pathlib import Path
    from src import tca
    
    # Create minimal test data
    import pandas as pd
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create minimal inputs
        pcha = tmp_path/"processed/cha"; pcha.mkdir(parents=True)
        pdha = tmp_path/"processed/dha"; pdha.mkdir(parents=True)
        pte  = tmp_path/"eval/te"; pte.mkdir(parents=True)
        pkpi = tmp_path/"processed/kpi"; pkpi.mkdir(parents=True)
        
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

        # Create EAA summary
        pd.DataFrame({
            "metric": ["lcoh_eur_per_mwh","co2_kg_per_mwh"],
            "mean": [100.0, 0.5],
            "median": [99.0, 0.49],
            "p2_5": [95.0, 0.45],
            "p97_5": [105.0, 0.55],
            "annual_pumping_kwh": [1000.0, 1000.0],
            "annual_heat_mwh": [10000.0, 10000.0]
        }).to_csv(pte/"summary.csv", index=False)

        # Copy schema file to temp directory
        (tmp_path/"schemas").mkdir()
        import shutil
        shutil.copy("schemas/kpi_summary.schema.json", tmp_path/"schemas/kpi_summary.schema.json")

        # Config
        (tmp_path/"configs").mkdir()
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

        # Change to tmpdir to resolve relative paths
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            cfg = str(tmp_path/"configs/tca.yml")
            out = tca.run(cfg)["kpi"]
            obj = json.loads(Path(out).read_text())
            schema = json.loads(Path("schemas/kpi_summary.schema.json").read_text())
            Draft202012Validator(schema).validate(obj)
        finally:
            os.chdir(original_cwd)
