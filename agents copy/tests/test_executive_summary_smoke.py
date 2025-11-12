"""
Smoke test for executive summary.
"""

import pytest
from pathlib import Path
from reports.executive_summary import generate_executive_summary


def test_executive_summary_smoke(tmp_path):
    """Call with small dict & tmp_path; assert file exists and contains 'Executive Summary' and 'P10/P50/P90'."""
    # Small test data
    data = {
        "dh": {"npv": -1500000, "lcoh": 45.5},
        "hp": {"npv": -800000, "lcoh": 52.3},
        "econ": {"bands": {"P10": -2000000, "P50": -1500000, "P90": -1000000}},
        "links": {"DH Report": "dh_report.html", "HP Report": "hp_report.html"},
    }

    # Generate report
    out_path = tmp_path / "executive_summary.html"
    result_path = generate_executive_summary(data, str(out_path))

    # Assert file exists
    assert Path(result_path).exists()

    # Read and check content
    with open(result_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Assert key content
    assert "Executive Summary" in content
    assert "P10/P50/P90" in content
    assert "DH NPV" in content
    assert "HP NPV" in content
    assert "DH LCoH" in content
    assert "HP LCoH" in content
    assert "DH Report" in content
    assert "HP Report" in content


def test_executive_summary_minimal_data(tmp_path):
    """Test with minimal data (empty dict)."""
    data = {}

    out_path = tmp_path / "minimal_summary.html"
    result_path = generate_executive_summary(data, str(out_path))

    assert Path(result_path).exists()

    with open(result_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Should still contain basic structure
    assert "Executive Summary" in content
    assert "P10/P50/P90" in content
    assert "DH NPV" in content
    assert "HP NPV" in content


def test_executive_summary_partial_data(tmp_path):
    """Test with partial data."""
    data = {"dh": {"npv": -1000000}, "links": {"Report": "report.html"}}

    out_path = tmp_path / "partial_summary.html"
    result_path = generate_executive_summary(data, str(out_path))

    assert Path(result_path).exists()

    with open(result_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Should handle missing data gracefully
    assert "Executive Summary" in content
    assert "P10/P50/P90" in content
    assert "Report" in content
