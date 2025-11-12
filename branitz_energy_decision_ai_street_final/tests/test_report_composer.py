from pathlib import Path
import json
import pandas as pd

def _fake_kpi(tmp: Path):
    (tmp/"processed/kpi").mkdir(parents=True, exist_ok=True)
    kpi = {
        "x-version": "1.0.0",
        "scenario_name": "ut_scenario",
        "created_utc": "2025-01-01T00:00:00Z",
        "metrics": {
            "lcoh_eur_per_mwh": 55.5,
            "co2_kg_per_mwh": 210.0,
            "dh_losses_pct": 8.0,
            "pump_kw": 22.0,
            "feeder_max_utilization_pct": 72.0,
            "forecast_rmse": 0.9,
            "forecast_picp_90": 0.92
        },
        "decision": {"recommended_option": "Hybrid", "rationale": "Test rationale"},
        "sources": ["eval/te/summary.csv"]
    }
    (tmp/"processed/kpi/kpi_summary.json").write_text(json.dumps(kpi), encoding="utf-8")

def _fake_eaa(tmp: Path):
    (tmp/"eval/te").mkdir(parents=True, exist_ok=True)
    pd.DataFrame([
        {"metric":"lcoh_eur_per_mwh","mean":60,"median":58,"p2_5":40,"p97_5":90},
        {"metric":"co2_kg_per_mwh","mean":220,"median":200,"p2_5":150,"p97_5":350},
    ]).to_csv(tmp/"eval/te/summary.csv", index=False)

def _fake_tables(tmp: Path):
    (tmp/"processed/cha").mkdir(parents=True, exist_ok=True)
    (tmp/"processed/dha").mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"pipe_id":0,"length_m":100,"d_inner_m":0.05,"v_ms":0.8,"p_from_bar":6.0,"p_to_bar":5.8}]).to_csv(tmp/"processed/cha/segments.csv", index=False)
    pd.DataFrame([{"feeder_id":"F1","hour":100,"p_kw":40.0,"utilization_pct":70.0}]).to_csv(tmp/"processed/dha/feeder_loads.csv", index=False)

def _template(tmp: Path):
    (tmp/"templates").mkdir(parents=True, exist_ok=True)
    (tmp/"templates/report.md.j2").write_text("# Report\n**{{ kpi.decision.recommended_option }}**\n", encoding="utf-8")

def _cfg(tmp: Path, include_artifacts: bool = True) -> str:
    (tmp/"configs").mkdir(parents=True, exist_ok=True)
    arts = ""
    if include_artifacts:
        arts = "artifacts:\n  - eval/te/missing_file.csv\n"
    cfg = (
        "scenario_name: test\n"
        f"kpi_json: {tmp/'processed/kpi/kpi_summary.json'}\n"
        f"eaa_summary_csv: {tmp/'eval/te/summary.csv'}\n"
        f"cha_segments_csv: {tmp/'processed/cha/segments.csv'}\n"
        f"dha_feeders_csv: {tmp/'processed/dha/feeder_loads.csv'}\n"
        f"template_md: {tmp/'templates/report.md.j2'}\n"
        f"out_html: {tmp/'docs/branitz_recommendation.html'}\n"
        + arts
    )
    (tmp/"configs/report.yml").write_text(cfg, encoding="utf-8")
    return str(tmp/"configs/report.yml")

def test_report_writes_html(tmp_path: Path, monkeypatch):
    _fake_kpi(tmp_path); _fake_eaa(tmp_path); _fake_tables(tmp_path); _template(tmp_path)
    import sys; sys.path.insert(0, str(tmp_path))
    from src.report_composer import run
    cfg = _cfg(tmp_path, include_artifacts=True)
    res = run(cfg)
    assert (tmp_path/"docs/branitz_recommendation.html").exists()
    assert res["status"] == "ok"

def test_report_fails_on_missing_artifact(tmp_path: Path, monkeypatch):
    _fake_kpi(tmp_path); _template(tmp_path)
    # Intentionally do NOT create EAA file; config declares it as artifact
    import sys; sys.path.insert(0, str(tmp_path))
    from src.report_composer import run
    cfg = _cfg(tmp_path, include_artifacts=True)
    try:
        run(cfg)
        assert False, "Expected failure for missing artifacts"
    except FileNotFoundError as e:
        assert "declared artifacts missing" in str(e)
