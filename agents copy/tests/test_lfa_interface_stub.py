"""
Smoke test for Load Forecasting Agent interface.
"""

import pytest
import pandas as pd
from lfa.interface import forecast_8760


def test_forecast_8760_basic():
    """Test basic functionality with minimal buildings dataframe."""
    # Build tiny buildings df (3 ids)
    buildings = pd.DataFrame({"building_id": ["B1", "B2", "B3"], "scale_kw": [10.0, 15.0, 8.0]})

    # Call forecast_8760
    result = forecast_8760(buildings, seed=42)

    # Assert keys
    assert "per_building" in result
    assert "metrics" in result

    # Assert per_building structure
    per_building = result["per_building"]
    assert "B1" in per_building
    assert "B2" in per_building
    assert "B3" in per_building

    # Assert arrays of length 8760
    for bid in ["B1", "B2", "B3"]:
        building_data = per_building[bid]
        assert "P10" in building_data
        assert "P50" in building_data
        assert "P90" in building_data
        assert len(building_data["P10"]) == 8760
        assert len(building_data["P50"]) == 8760
        assert len(building_data["P90"]) == 8760

    # Assert metrics keys present
    metrics = result["metrics"]
    assert "MAE" in metrics
    assert "RMSE" in metrics
    assert "MAPE" in metrics
    assert "PICP80" in metrics
    assert "PICP90" in metrics

    # Assert metric values are reasonable
    assert 0 <= metrics["MAE"] <= 100
    assert 0 <= metrics["RMSE"] <= 100
    assert 0 <= metrics["MAPE"] <= 100
    assert 0 <= metrics["PICP80"] <= 1
    assert 0 <= metrics["PICP90"] <= 1


def test_forecast_8760_determinism():
    """Test determinism with fixed seed."""
    buildings = pd.DataFrame({"building_id": ["B1", "B2"], "scale_kw": [10.0, 15.0]})

    # Run twice with same seed
    result1 = forecast_8760(buildings, seed=42)
    result2 = forecast_8760(buildings, seed=42)

    # Results should be identical
    assert result1["per_building"]["B1"]["P50"][0] == result2["per_building"]["B1"]["P50"][0]
    assert result1["metrics"]["MAE"] == result2["metrics"]["MAE"]


def test_forecast_8760_default_scale():
    """Test default scale_kw behavior."""
    buildings = pd.DataFrame(
        {
            "building_id": ["B1", "B2"]
            # No scale_kw column
        }
    )

    result = forecast_8760(buildings, seed=42)

    # Should work with default scale_kw=10.0
    assert "B1" in result["per_building"]
    assert "B2" in result["per_building"]


def test_forecast_8760_validation():
    """Test input validation."""
    # Missing building_id column
    buildings = pd.DataFrame({"name": ["Building 1", "Building 2"]})

    with pytest.raises(ValueError, match="buildings must contain 'building_id'"):
        forecast_8760(buildings, seed=42)
