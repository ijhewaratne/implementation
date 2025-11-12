"""
Contract tests for LV Feeder Analyzer.
"""

import pytest
import pandas as pd
from src.lv_feeder_analyzer import map_buildings_to_feeders, pick_top10_hours, run_feeder_studies


def test_map_buildings_to_feeders_with_mapping():
    """Test building to feeder mapping when both dataframes have required columns."""
    buildings_df = pd.DataFrame({"building_id": ["B1", "B2", "B3"], "other_col": ["a", "b", "c"]})

    feeders_df = pd.DataFrame(
        {
            "building_id": ["B1", "B2", "B4"],
            "feeder_id": ["F1", "F2", "F3"],
            "other_col": ["x", "y", "z"],
        }
    )

    result = map_buildings_to_feeders(buildings_df, feeders_df)

    # B1 and B2 should be mapped, B3 should default to F0
    assert result == {"B1": "F1", "B2": "F2", "B3": "F0"}


def test_map_buildings_to_feeders_default():
    """Test building to feeder mapping when feeders_df is missing required columns."""
    buildings_df = pd.DataFrame({"building_id": ["B1", "B2", "B3"]})

    feeders_df = pd.DataFrame({"other_col": ["x", "y", "z"]})

    result = map_buildings_to_feeders(buildings_df, feeders_df)

    # All buildings should default to F0
    assert result == {"B1": "F0", "B2": "F0", "B3": "F0"}


def test_pick_top10_hours():
    """Test top-10 hour selection logic."""
    # Create load dataframe with 20 hours
    load_df = pd.DataFrame(
        {
            "total_kw": [
                100,
                200,
                150,
                300,
                250,
                180,
                220,
                280,
                190,
                210,
                110,
                120,
                130,
                140,
                160,
                170,
                240,
                260,
                270,
                290,
            ]
        }
    )

    result = pick_top10_hours(load_df)

    # Should return 10 indices
    assert len(result) == 10

    # Should be sorted in descending order of load
    assert result[0] == 3  # 300 kW
    assert result[1] == 19  # 290 kW (corrected)
    assert result[2] == 7  # 280 kW (corrected)


def test_pick_top10_hours_validation():
    """Test input validation for pick_top10_hours."""
    load_df = pd.DataFrame({"other_col": [100, 200, 150]})

    with pytest.raises(ValueError, match="load_df must contain 'total_kw'"):
        pick_top10_hours(load_df)


def test_run_feeder_studies():
    """Test feeder studies with minimal fake data."""
    # Mock feeders_model (not used in stub)
    feeders_model = None

    # Building to feeder mapping
    building_to_feeder = {"B1": "F1", "B2": "F2", "B3": "F1"}

    # Hourly building kW data
    hourly_building_kw = pd.DataFrame(
        {"0": [10, 15, 20], "1": [12, 18, 22], "2": [8, 14, 16]},  # hour 0  # hour 1  # hour 2
        index=["B1", "B2", "B3"],
    )

    # Top hours to analyze
    hours = [0, 1]

    result = run_feeder_studies(feeders_model, building_to_feeder, hourly_building_kw, hours)

    # Assert shapes and column presence
    assert len(result) == 4  # 2 hours × 2 feeders
    assert "feeder_id" in result.columns
    assert "hour" in result.columns
    assert "utilization_max" in result.columns
    assert "voltage_min" in result.columns
    assert "voltage_max" in result.columns
    assert "violates_util>=0.8" in result.columns
    assert "violates_voltage_outside_±10%" in result.columns

    # Assert boolean flags
    assert all(isinstance(x, bool) for x in result["violates_util>=0.8"])
    assert all(isinstance(x, bool) for x in result["violates_voltage_outside_±10%"])

    # Assert reasonable voltage ranges
    assert all(0.5 <= v <= 1.5 for v in result["voltage_min"])
    assert all(0.5 <= v <= 1.5 for v in result["voltage_max"])
