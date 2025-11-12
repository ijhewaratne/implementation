import json
from pathlib import Path
import pytest

def test_tool_direct(tmp_path: Path):
    """Test the KPI analysis tool directly without ADK dependency."""
    p = tmp_path / "kpi.json"
    p.write_text(json.dumps({
        "economic_metrics": {"lcoh_eur_per_mwh": 95.2},
        "technical_metrics": {"feeder_max_utilization_pct": 72.5},
        "recommendation": {"preferred_scenario": "Hybrid"},
    }), encoding="utf-8")
    
    from src.enhanced_tools import analyze_kpi_report
    out = analyze_kpi_report(str(p))
    assert "lcoh_eur_per_mwh" in out
    assert "Hybrid" in out

@pytest.mark.skipif(
    pytest.importorskip("adk", reason="ADK optional") is None, 
    reason="ADK missing"
)
def test_egpt_via_adk(tmp_path: Path):
    """Test EnergyGPT via ADK when available."""
    p = tmp_path / "kpi.json"
    p.write_text(json.dumps({"metrics":{"lcoh_eur_per_mwh": 88}}), encoding="utf-8")
    
    from src.enhanced_agents import EnergyGPT
    from src.enhanced_agent_runner import run_agent_once
    
    out = run_agent_once(EnergyGPT, f"analyze_kpi_report(kpi_report_path='{p}')")
    assert "lcoh_eur_per_mwh" in out

def test_energygpt_parses_kpi(tmp_path: Path):
    """Legacy test name for backward compatibility."""
    test_tool_direct(tmp_path)
