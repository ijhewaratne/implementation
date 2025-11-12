from pathlib import Path
import json
import pandas as pd

def _fake_minimal_repo(tmp: Path):
    # Makefile with no-ops
    (tmp/"Makefile").write_text(".PHONY: run-branitz\nrun-branitz:\n\t@echo running\n", encoding="utf-8")
    # validator that returns 0
    (tmp/"scripts").mkdir(parents=True, exist_ok=True)
    (tmp/"scripts/validate_json.py").write_text("import sys; print('ok'); sys.exit(0)", encoding="utf-8")
    # artifacts
    (tmp/"processed/kpi").mkdir(parents=True, exist_ok=True)
    (tmp/"eval/te").mkdir(parents=True, exist_ok=True)
    (tmp/"processed/cha").mkdir(parents=True, exist_ok=True)
    (tmp/"processed/dha").mkdir(parents=True, exist_ok=True)
    (tmp/"eval/cha").mkdir(parents=True, exist_ok=True)
    (tmp/"eval/dha").mkdir(parents=True, exist_ok=True)
    (tmp/"eval/apa").mkdir(parents=True, exist_ok=True)
    (tmp/"MIGRATIONS.md").write_text("# migrations\n", encoding="utf-8")
    (tmp/"schemas").mkdir(parents=True, exist_ok=True)
    (tmp/"schemas/kpi_summary.schema.json").write_text("{}", encoding="utf-8")
    (tmp/"processed/kpi/kpi_summary.json").write_text("{}", encoding="utf-8")
    pd.DataFrame({"x":[1]}).to_csv(tmp/"eval/te/summary.csv", index=False)
    pd.DataFrame({"x":[1]}).to_parquet(tmp/"eval/te/mc.parquet")
    pd.DataFrame({"x":[1]}).to_csv(tmp/"processed/cha/segments.csv", index=False)
    pd.DataFrame({"x":[1]}).to_csv(tmp/"eval/cha/hydraulics_check.csv", index=False)
    pd.DataFrame({"x":[1]}).to_csv(tmp/"processed/dha/feeder_loads.csv", index=False)
    pd.DataFrame({"x":[1]}).to_csv(tmp/"eval/dha/violations.csv", index=False)
    pd.DataFrame({"x":[1]}).to_csv(tmp/"eval/apa/sensitivity.csv", index=False)

def _cfg(tmp: Path) -> str:
    (tmp/"configs").mkdir(parents=True, exist_ok=True)
    (tmp/"configs/caa.yml").write_text(
        "scenario_name: test\nfast: true\nuse_make_run_branitz: true\n"
        "out_zip: "+str(tmp/"eval/caa/diagnostics.zip")+"\n"
        "artifacts:\n"
        "  - processed/kpi/kpi_summary.json\n"
        "  - eval/te/summary.csv\n"
        "  - eval/te/mc.parquet\n"
        "  - processed/cha/segments.csv\n"
        "  - eval/cha/hydraulics_check.csv\n"
        "  - processed/dha/feeder_loads.csv\n"
        "  - eval/dha/violations.csv\n"
        "  - eval/apa/sensitivity.csv\n"
        "  - MIGRATIONS.md\n"
        "  - schemas/kpi_summary.schema.json\n"
        "  - scripts/validate_json.py\n"
        "  - Makefile\n",
        encoding="utf-8"
    )
    return str(tmp/"configs/caa.yml")

def test_caa_zip_created(tmp_path: Path, monkeypatch):
    _fake_minimal_repo(tmp_path)
    cfg = _cfg(tmp_path)
    import sys; sys.path.insert(0, str(tmp_path))
    from src.caa import run
    res = run(cfg)
    assert res["status"] == "ok"
    assert (tmp_path/"eval/caa/diagnostics.zip").exists()

def test_caa_fails_when_artifact_missing(tmp_path: Path, monkeypatch):
    _fake_minimal_repo(tmp_path)
    # remove a required file to provoke DoD failure
    (tmp_path/"processed/kpi/kpi_summary.json").unlink()
    cfg = _cfg(tmp_path)
    import sys; sys.path.insert(0, str(tmp_path))
    from src.caa import run
    try:
        run(cfg)
        assert False, "CAA should have raised on DoD failure"
    except RuntimeError as e:
        assert "missing artifacts" in str(e)





