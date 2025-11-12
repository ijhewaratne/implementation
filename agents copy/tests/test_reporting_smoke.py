"""
Smoke tests for reporting module.

This module contains comprehensive smoke tests for the reporting utilities
including HTML compliance report generation and GeoJSON export functionality.
"""

import pytest
import pandas as pd
from pathlib import Path
from optimize.reporting import write_compliance_report, export_geojson_with_dn


def test_write_compliance_report_smoke(tmp_path):
    """Test HTML compliance report generation with synthetic data."""

    # Create synthetic per-segment DataFrame
    per_seg_data = {
        "seg_id": ["S1", "S2", "S3"],
        "length_m": [120.0, 80.0, 150.0],
        "DN": [125, 80, 100],
        "V_dot_m3s": [0.012, 0.006, 0.008],
        "v_mps": [1.2, 1.55, 1.1],  # One segment fails velocity limit
        "dp_Pa": [5000, 3000, 4000],
        "h_m": [0.52, 0.31, 0.41],
        "heat_loss_W": [1200, 800, 1000],
        "path_id": ["P1", "P1", "P2"],
        "is_supply": [True, True, False],
    }

    per_seg_df = pd.DataFrame(per_seg_data)

    # Create summary dict
    summary = {
        "npv_eur": 181052.0,
        "capex_eur": 45000.0,
        "opex_eur_per_a": 8500.0,
        "pump_MWh": 1.3,
        "heat_loss_MWh": 46.6,
        "v_max": 1.55,  # Max velocity (from failing segment)
        "head_required_m": 12.5,
        "deltaT_design_k": 30.0,
        "velocity_ok": True,  # Overall system passes but one segment fails
        "deltaT_ok": True,
    }

    # Generate report
    out_dir = str(tmp_path / "reports")
    report_path = write_compliance_report(
        street="Test Street",
        per_seg_df=per_seg_df,
        summary=summary,
        out_dir=out_dir,
        v_limit=1.5,
        deltaT_min=30.0,
    )

    # Assertions
    assert Path(report_path).exists()

    # Read HTML content
    with open(report_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Check for required content
    assert "EN 13941" in html_content
    assert "Net Present Value" in html_content
    assert "Pump Energy" in html_content
    assert "Design ΔT" in html_content
    assert "badge pass" in html_content or "badge fail" in html_content

    # Check table headers
    assert "Segment ID" in html_content
    assert "Length (m)" in html_content
    assert "DN" in html_content
    assert "Velocity (m/s)" in html_content

    # Check specific values
    assert "€ 181,052" in html_content  # NPV formatting
    assert "1.6 m/s" in html_content  # Max velocity
    assert "30.0 K" in html_content  # Design ΔT

    # Check velocity compliance (2 pass, 1 fail)
    assert "2 of 3 segments pass" in html_content

    print(f"✅ HTML compliance report test passed!")
    print(f"   Report generated: {report_path}")


def test_write_compliance_report_validation():
    """Test input validation for compliance report."""

    # Test missing columns
    invalid_df = pd.DataFrame({"seg_id": ["S1"], "length_m": [100]})  # Missing required columns
    summary = {
        "npv_eur": 100000,
        "capex_eur": 50000,
        "opex_eur_per_a": 5000,
        "pump_MWh": 1.0,
        "heat_loss_MWh": 10.0,
        "v_max": 1.2,
        "head_required_m": 10.0,
        "deltaT_design_k": 30.0,
        "velocity_ok": True,
        "deltaT_ok": True,
    }

    with pytest.raises(ValueError, match="Missing required columns"):
        write_compliance_report("Test", invalid_df, summary, "/tmp")

    # Test missing summary keys
    valid_df = pd.DataFrame(
        {
            "seg_id": ["S1"],
            "length_m": [100],
            "DN": [80],
            "V_dot_m3s": [0.01],
            "v_mps": [1.0],
            "dp_Pa": [1000],
            "h_m": [0.1],
            "heat_loss_W": [100],
            "path_id": ["P1"],
            "is_supply": [True],
        }
    )
    invalid_summary = {"npv_eur": 100000}  # Missing required keys

    with pytest.raises(ValueError, match="Missing required keys"):
        write_compliance_report("Test", valid_df, invalid_summary, "/tmp")


def test_write_compliance_report_large_table(tmp_path):
    """Test report generation with large table (truncation)."""

    # Create large DataFrame (250 rows)
    large_data = {
        "seg_id": [f"S{i}" for i in range(250)],
        "length_m": [100.0] * 250,
        "DN": [80] * 250,
        "V_dot_m3s": [0.01] * 250,
        "v_mps": [1.0] * 250,
        "dp_Pa": [0.1] * 250,
        "h_m": [0.1] * 250,
        "heat_loss_W": [100] * 250,
        "path_id": ["P1"] * 250,
        "is_supply": [True] * 250,
    }

    large_df = pd.DataFrame(large_data)
    summary = {
        "npv_eur": 100000,
        "capex_eur": 50000,
        "opex_eur_per_a": 5000,
        "pump_MWh": 1.0,
        "heat_loss_MWh": 10.0,
        "v_max": 1.0,
        "head_required_m": 10.0,
        "deltaT_design_k": 30.0,
        "velocity_ok": True,
        "deltaT_ok": True,
    }

    report_path = write_compliance_report("Large Test", large_df, summary, str(tmp_path))

    with open(report_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Check for truncation note
    assert "Showing first 200 of 250 rows" in html_content

    print(f"✅ Large table truncation test passed!")


def test_export_geojson_with_dn_smoke(tmp_path):
    """Test GeoJSON export with synthetic data."""

    # Skip if geopandas not available
    try:
        import geopandas
        from shapely.geometry import LineString

        has_geopandas = True
    except ImportError:
        has_geopandas = False
        pytest.skip("geopandas not available")

    # Create synthetic GeoDataFrame
    lines_data = {
        "seg_id": ["S1", "S2"],
        "geometry": [LineString([(0, 0), (1, 1)]), LineString([(1, 1), (2, 2)])],
    }

    gdf = geopandas.GeoDataFrame(lines_data, crs="EPSG:3857")

    # Assignment
    assignment = {"S1": 80, "S2": 100}

    # Export
    out_path = str(tmp_path / "optimized.geojson")
    exported_path = export_geojson_with_dn(gdf, assignment, out_path)

    # Assertions
    assert Path(exported_path).exists()

    # Read back and verify
    result_gdf = geopandas.read_file(exported_path)
    assert "DN" in result_gdf.columns
    assert result_gdf["DN"].tolist() == [80, 100]

    print(f"✅ GeoJSON export test passed!")
    print(f"   Exported: {exported_path}")


def test_export_geojson_validation():
    """Test input validation for GeoJSON export."""

    # Test missing geopandas
    try:
        import geopandas

        has_geopandas = True
    except ImportError:
        has_geopandas = False

    if not has_geopandas:
        # Mock GeoDataFrame for testing
        class MockGeoDataFrame:
            def __init__(self):
                self.columns = ["geometry"]  # Missing seg_id

        mock_gdf = MockGeoDataFrame()

        with pytest.raises(ImportError, match="GeoJSON export requires geopandas"):
            export_geojson_with_dn(mock_gdf, {"S1": 80}, "/tmp/test.geojson")

    # Test empty assignment
    if has_geopandas:
        geopandas = pytest.importorskip("geopandas")
        from shapely.geometry import LineString

        gdf = geopandas.GeoDataFrame({"seg_id": ["S1"], "geometry": [LineString([(0, 0), (1, 1)])]})

        with pytest.raises(ValueError, match="Assignment dictionary cannot be empty"):
            export_geojson_with_dn(gdf, {}, "/tmp/test.geojson")


def test_export_geojson_missing_segments(tmp_path):
    """Test GeoJSON export with missing segments (should log warning)."""

    try:
        import geopandas
        from shapely.geometry import LineString

        has_geopandas = True
    except ImportError:
        has_geopandas = False
        pytest.skip("geopandas not available")

    # Create GeoDataFrame with only one segment
    gdf = geopandas.GeoDataFrame(
        {"seg_id": ["S1"], "geometry": [LineString([(0, 0), (1, 1)])]}, crs="EPSG:3857"
    )

    # Assignment with extra segment
    assignment = {"S1": 80, "S2": 100}  # S2 not in GeoDataFrame

    # Export (should log warning but not fail)
    out_path = str(tmp_path / "missing_segments.geojson")
    exported_path = export_geojson_with_dn(gdf, assignment, out_path)

    # Verify file was created
    assert Path(exported_path).exists()

    # Read back and verify
    result_gdf = geopandas.read_file(exported_path)
    assert result_gdf["DN"].iloc[0] == 80  # S1 should have DN=80
    assert result_gdf["DN"].isna().sum() == 0  # No NaN values (S2 not in GDF)

    print(f"✅ Missing segments test passed!")


if __name__ == "__main__":
    pytest.main([__file__])
