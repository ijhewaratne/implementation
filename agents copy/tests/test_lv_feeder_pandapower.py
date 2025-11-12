"""
Contract tests for LV Feeder Analyzer with pandapower backend.

Verifies that pandapower backend produces realistic results and
thresholds trigger correctly with actual power flow calculations.
"""

import pytest
import pandas as pd

pytest.importorskip("pandapower")  # skip on CI without PP

from src.lv_feeder_analyzer import run_feeder_studies


# Import the factory function directly
def build_simple_lv_feeder():
    """Build a simple LV feeder network for testing."""
    import pandapower as pp

    net = pp.create_empty_network(sn_mva=0.4)  # LV base

    # Create buses
    bus_hv = pp.create_bus(net, vn_kv=20.0, name="MV")
    bus_lv = pp.create_bus(net, vn_kv=0.4, name="LV")
    bus_l1 = pp.create_bus(net, vn_kv=0.4, name="L1")

    # Create external grid (slack bus)
    pp.create_ext_grid(net, bus=bus_hv)

    # Create transformer
    pp.create_transformer_from_parameters(
        net,
        hv_bus=bus_hv,
        lv_bus=bus_lv,
        sn_mva=0.4,
        vn_hv_kv=20.0,
        vn_lv_kv=0.4,
        vk_percent=6.0,
        vkr_percent=0.8,
        pfe_kw=0.5,
        i0_percent=0.2,
    )

    # Create LV line
    pp.create_line_from_parameters(
        net,
        from_bus=bus_lv,
        to_bus=bus_l1,
        length_km=0.05,
        r_ohm_per_km=0.4,
        x_ohm_per_km=0.08,
        c_nf_per_km=220,
        max_i_ka=0.6,
    )

    return dict(net=net, lv_bus=bus_l1, rating_mva=0.4)


def test_flags_trigger_with_pandapower():
    """Test that utilization and voltage flags trigger correctly with pandapower."""
    fm = build_simple_lv_feeder()
    feeders_model = {"F1": fm}

    # 3 buildings on same feeder; two hours (light + heavy)
    hourly_kw = pd.DataFrame(
        {
            "0": [50.0, 60.0, 40.0],  # 150 kW total
            "1": [
                250.0,
                300.0,
                250.0,
            ],  # 800 kW total -> near 0.8 pu for 1 MVA equiv, but our trafo is 0.4 MVA so loading will exceed 80%
        },
        index=["B1", "B2", "B3"],
    )

    b2f = {"B1": "F1", "B2": "F1", "B3": "F1"}
    hours = [0, 1]

    df = run_feeder_studies(
        feeders_model,
        b2f,
        hourly_kw,
        hours,
        backend="pandapower",
        util_threshold=0.8,
        v_limits=(0.90, 1.10),
        power_factor=0.98,
    )

    # Two rows (one per hour) for F1
    assert set(df["hour"]) == {0, 1}

    # Light hour: likely no violations
    row0 = df[df["hour"] == 0].iloc[0]
    assert row0["utilization_max"] >= 0.0
    assert row0["voltage_min"] <= row0["voltage_max"]

    # Heavy hour: expect at least one threshold to trip (loading or voltage)
    row1 = df[df["hour"] == 1].iloc[0]
    assert (row1["violates_util>=0.8"] or row1["violates_voltage_outside_±10%"]) == True


def test_pandapower_vs_heuristic_consistency():
    """Test that pandapower and heuristic backends produce consistent structure."""
    fm = build_simple_lv_feeder()
    feeders_model = {"F1": fm}

    hourly_kw = pd.DataFrame(
        {
            "0": [100.0, 150.0],  # 250 kW total
        },
        index=["B1", "B2"],
    )

    b2f = {"B1": "F1", "B2": "F1"}
    hours = [0]

    # Run both backends
    df_pp = run_feeder_studies(feeders_model, b2f, hourly_kw, hours, backend="pandapower")
    df_heuristic = run_feeder_studies(feeders_model, b2f, hourly_kw, hours, backend="heuristic")

    # Same structure
    assert list(df_pp.columns) == list(df_heuristic.columns)
    assert len(df_pp) == len(df_heuristic)

    # Same feeder and hour
    assert df_pp.iloc[0]["feeder_id"] == df_heuristic.iloc[0]["feeder_id"]
    assert df_pp.iloc[0]["hour"] == df_heuristic.iloc[0]["hour"]


def test_pandapower_realistic_values():
    """Test that pandapower produces realistic voltage and utilization values."""
    fm = build_simple_lv_feeder()
    feeders_model = {"F1": fm}

    hourly_kw = pd.DataFrame(
        {
            "0": [200.0],  # 200 kW load
        },
        index=["B1"],
    )

    b2f = {"B1": "F1"}
    hours = [0]

    df = run_feeder_studies(feeders_model, b2f, hourly_kw, hours, backend="pandapower")
    row = df.iloc[0]

    # Realistic voltage range (0.9-1.1 pu)
    assert 0.9 <= row["voltage_min"] <= 1.1
    assert 0.9 <= row["voltage_max"] <= 1.1
    assert row["voltage_min"] <= row["voltage_max"]

    # Realistic utilization (0-2 pu)
    assert 0.0 <= row["utilization_max"] <= 2.0

    # Boolean flags
    assert row["violates_util>=0.8"] in [True, False]
    assert row["violates_voltage_outside_±10%"] in [True, False]


def test_unknown_feeder_handling():
    """Test that unknown feeders are handled gracefully."""
    fm = build_simple_lv_feeder()
    feeders_model = {"F1": fm}  # Only F1 defined

    hourly_kw = pd.DataFrame(
        {
            "0": [100.0, 200.0],  # Two buildings
        },
        index=["B1", "B2"],
    )

    b2f = {"B1": "F1", "B2": "F2"}  # B2 maps to unknown F2
    hours = [0]

    df = run_feeder_studies(feeders_model, b2f, hourly_kw, hours, backend="pandapower")

    # Should have 2 rows (F1 and F2)
    assert len(df) == 2
    assert set(df["feeder_id"]) == {"F1", "F2"}

    # F1 should have valid results
    row_f1 = df[df["feeder_id"] == "F1"].iloc[0]
    assert not pd.isna(row_f1["utilization_max"])

    # F2 should have NaN results (unknown feeder)
    row_f2 = df[df["feeder_id"] == "F2"].iloc[0]
    assert pd.isna(row_f2["utilization_max"])
    assert pd.isna(row_f2["voltage_min"])
    assert pd.isna(row_f2["voltage_max"])
    assert row_f2["violates_util>=0.8"] == False
    assert row_f2["violates_voltage_outside_±10%"] == False
