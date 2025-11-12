import pandas as pd
from optimize.reporting import write_compliance_report
from optimize.per_seg import build_per_segment_df


class _Seg:  # simple stand-in for Segment
    def __init__(self, seg_id, L, V, path, is_supply):
        self.seg_id = seg_id
        self.length_m = L
        self.V_dot_m3s = V
        self.path_id = path
        self.is_supply = is_supply


def test_perseg_and_report(tmp_path):
    segments = [_Seg("S1", 100.0, 0.01, "P1", True)]
    metrics = {
        "per_segment": {"S1": {"dn": 80, "v": 1.1, "dp": 50000.0, "h": 5.1, "heat_loss_W": 200.0}},
        "npv_eur": -1.0,
        "capex_eur": 1000,
        "opex_eur_per_a": 100,
        "pump_MWh": 1.0,
        "heat_loss_MWh": 0.6,
        "v_max": 1.1,
        "head_required_m": 5.1,
        "velocity_ok": True,
        "deltaT_ok": True,
    }
    df = build_per_segment_df(segments, metrics)
    assert list(df.columns) == [
        "seg_id",
        "length_m",
        "DN",
        "V_dot_m3s",
        "v_mps",
        "dp_Pa",
        "h_m",
        "heat_loss_W",
        "path_id",
        "is_supply",
    ]
    out = tmp_path / "report_dir"
    path = write_compliance_report("Test", df, dict(**metrics, deltaT_design_k=30.0), str(out))
    assert "compliance_report" in path
