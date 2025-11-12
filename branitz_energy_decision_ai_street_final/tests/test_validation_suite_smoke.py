"""
Smoke test for validation suite.
"""

import pytest
import pandas as pd
from pathlib import Path
from validation.validation_suite import build_validation_suite


def test_validation_suite_smoke(tmp_path):
    """Call with simple dicts; assert file created and contains section headings and 'PASS/FAIL'."""
    # Simple test data
    lfa = {'MAE': 0.15, 'RMSE': 0.22, 'MAPE': 12.5}
    en13941 = {'velocity_ok': True, 'deltaT_ok': False}
    feeder_df = pd.DataFrame({
        'violates_util>=0.8': [False, True, False],
        'violates_voltage_outside_±10%': [False, False, True]
    })
    econ_bench = {'npv_range': [-2000000, -1000000], 'lcoh_range': [40, 60]}
    
    # Generate validation suite
    out_path = tmp_path / "validation_suite.html"
    result_path = build_validation_suite(str(out_path), lfa, en13941, feeder_df, econ_bench)
    
    # Assert file exists
    assert Path(result_path).exists()
    
    # Read and check content
    with open(result_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Assert key content
    assert "Validation Suite" in content
    assert "Guideline-14" in content
    assert "EN 13941" in content
    assert "VDE/FNN" in content
    assert "Economics" in content
    assert "PASS" in content
    assert "FAIL" in content
    assert "ASHRAE" in content
    assert "AGFW" in content
    assert "FfE" in content


def test_validation_suite_partial_data(tmp_path):
    """Test with partial data."""
    # Only LFA data
    lfa = {'MAE': 0.12}
    
    out_path = tmp_path / "partial_validation.html"
    result_path = build_validation_suite(str(out_path), lfa=lfa)
    
    assert Path(result_path).exists()
    
    with open(result_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Should only contain LFA section
    assert "Validation Suite" in content
    assert "Guideline-14" in content
    assert "MAE=0.12" in content
    assert "PASS" in content


def test_validation_suite_no_data(tmp_path):
    """Test with no data."""
    out_path = tmp_path / "empty_validation.html"
    result_path = build_validation_suite(str(out_path))
    
    assert Path(result_path).exists()
    
    with open(result_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Should still contain basic structure
    assert "Validation Suite" in content
    assert "<html>" in content
    assert "</body></html>" in content


def test_validation_suite_en13941_only(tmp_path):
    """Test with only EN 13941 data."""
    en13941 = {'velocity_ok': True, 'deltaT_ok': True}
    
    out_path = tmp_path / "en13941_validation.html"
    result_path = build_validation_suite(str(out_path), en13941=en13941)
    
    assert Path(result_path).exists()
    
    with open(result_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Should contain EN 13941 section with PASS badges
    assert "EN 13941" in content
    assert "velocity" in content
    assert "ΔT" in content
    assert "PASS" in content 