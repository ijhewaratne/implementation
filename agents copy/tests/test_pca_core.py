import pandas as pd
from agents import pca

def test_wall_thickness_and_validation_and_dedup(tmp_path, monkeypatch):
    # Fake a "read" by directly calling internal functions on a DataFrame
    data = pd.DataFrame({
        "dn": [25, 25, 32, 40],
        "d_i_mm": [23.0, 23.0, 30.0, 38.0],    # mm -> m
        "d_o_mm": [27.0, 27.0, 34.0, 37.0],    # last row invalid (outer <= inner)
        "u_value": [0.035, 0.035, 0.040, 0.035],
        "heat_loss_W_per_m": [12.5, 12.0, 14.0, 11.0],
        "eur_per_m": [85.0, 80.0, 120.0, 90.0],
    })
    colmap = {
        "dn": {"keywords": ["dn"]},
        "d_inner_m": {"keywords": ["d_i_mm"], "unit": "mm"},
        "d_outer_m": {"keywords": ["d_o_mm"], "unit": "mm"},
        "u_wpermk": {"keywords": ["u_value"], "unit": "W_per_mK"},
        "w_loss_w_per_m": {"keywords": ["heat_loss_W_per_m"]},
        "cost_eur_per_m": {"keywords": ["eur_per_m"], "unit": "EUR_per_m"},
    }
    df_can = pca._process_sheet(data, colmap)
    assert "wall_thickness_m" in df_can.columns
    # Validate + dedup
    df_ok, df_qc = pca._validate_and_qc(df_can)
    # Expect one invalid row (outer<=inner) and one duplicate (dn=25 keep cheaper)
    reasons = set(df_qc["reason"].tolist())
    assert "invalid_diameter" in reasons
    assert "duplicate_dn_higher_cost" in reasons
    # Expect dedup keeps the cheaper dn=25 row (80.0)
    kept_25 = df_ok[df_ok["dn"] == 25]["cost_eur_per_m"].iloc[0]
    assert kept_25 == 80.0
