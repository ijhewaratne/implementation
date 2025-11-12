"""
Threshold tests for LV Feeder Analyzer.

Verifies that:
- utilization flag trips at >= 0.80 pu of nameplate (1 MW in the stub),
- voltage flag trips when vmin < 0.90 pu or vmax > 1.10 pu.
"""

import pandas as pd
from src.lv_feeder_analyzer import run_feeder_studies

def _mk_hourly_df(values_by_building):
    # values_by_building: dict building_id -> kW at hour '0'
    return pd.DataFrame({"0": list(values_by_building.values())},
                        index=list(values_by_building.keys()))

def test_utilization_flag_off_below_80_percent():
    # Map two buildings to feeder F1, total = 650 kW -> util = 0.65 -> below 0.80
    building_to_feeder = {"B1": "F1", "B2": "F1"}
    hourly = _mk_hourly_df({"B1": 300.0, "B2": 350.0})
    df = run_feeder_studies(feeders_model=None,
                            building_to_feeder=building_to_feeder,
                            hourly_building_kw=hourly,
                            hours=[0])
    row = df[(df.feeder_id == "F1") & (df.hour == 0)].iloc[0]
    assert row["utilization_max"] == 0.65
    assert row["violates_util>=0.8"] == False
    # voltage: vmin = 1 - 0.15*0.65 = 0.9025 (inside ±10%)
    assert row["violates_voltage_outside_±10%"] == False

def test_utilization_flag_on_at_exact_80_percent():
    # Total = 800 kW -> util = 0.80 -> flag should be True (>= 0.8)
    building_to_feeder = {"B1": "F1", "B2": "F1"}
    hourly = _mk_hourly_df({"B1": 500.0, "B2": 300.0})
    df = run_feeder_studies(None, building_to_feeder, hourly, hours=[0])
    row = df[(df.feeder_id == "F1") & (df.hour == 0)].iloc[0]
    assert abs(row["utilization_max"] - 0.80) < 1e-9
    assert row["violates_util>=0.8"] == True
    # vmin = 1 - 0.15*0.8 = 0.88 -> < 0.90 → voltage flag True as well
    assert row["violates_voltage_outside_±10%"] == True

def test_voltage_flag_on_when_vmin_below_0p90():
    # util = 0.85 -> vmin = 1 - 0.1275 = 0.8725 < 0.9 → voltage violation
    building_to_feeder = {"B1": "F1", "B2": "F1"}
    hourly = _mk_hourly_df({"B1": 600.0, "B2": 250.0})  # 850 kW
    df = run_feeder_studies(None, building_to_feeder, hourly, hours=[0])
    row = df[(df.feeder_id == "F1") & (df.hour == 0)].iloc[0]
    assert row["violates_voltage_outside_±10%"] == True

def test_voltage_flag_on_when_vmax_above_1p10():
    # need util > 2.0 (since vmax = 1 + 0.05*util) -> 2.1 MW
    building_to_feeder = {"B1": "F1", "B2": "F1", "B3": "F1"}
    hourly = _mk_hourly_df({"B1": 900.0, "B2": 700.0, "B3": 600.0})  # 2200 kW = 2.2 pu
    df = run_feeder_studies(None, building_to_feeder, hourly, hours=[0])
    row = df[(df.feeder_id == "F1") & (df.hour == 0)].iloc[0]
    assert row["utilization_max"] == 2.2
    # vmax = 1 + 0.05*2.2 = 1.11 -> > 1.10 → violation
    assert row["violates_voltage_outside_±10%"] == True

def test_configurable_feeder_ratings():
    # Test with custom feeder ratings
    building_to_feeder = {"B1": "F1", "B2": "F2"}
    hourly = _mk_hourly_df({"B1": 400.0, "B2": 600.0})
    
    # Test scalar rating (500 kW for all feeders)
    df_scalar = run_feeder_studies(None, building_to_feeder, hourly, hours=[0], feeder_ratings_kw=500.0)
    row_f1 = df_scalar[(df_scalar.feeder_id == "F1") & (df_scalar.hour == 0)].iloc[0]
    row_f2 = df_scalar[(df_scalar.feeder_id == "F2") & (df_scalar.hour == 0)].iloc[0]
    assert row_f1["utilization_max"] == 0.8  # 400/500
    assert row_f2["utilization_max"] == 1.2  # 600/500
    
    # Test dict ratings (different for each feeder)
    ratings = {"F1": 400.0, "F2": 800.0}
    df_dict = run_feeder_studies(None, building_to_feeder, hourly, hours=[0], feeder_ratings_kw=ratings)
    row_f1 = df_dict[(df_dict.feeder_id == "F1") & (df_dict.hour == 0)].iloc[0]
    row_f2 = df_dict[(df_dict.feeder_id == "F2") & (df_dict.hour == 0)].iloc[0]
    assert row_f1["utilization_max"] == 1.0  # 400/400
    assert row_f2["utilization_max"] == 0.75  # 600/800 