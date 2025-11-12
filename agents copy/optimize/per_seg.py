from __future__ import annotations
import pandas as pd

REQUIRED_COLUMNS = [
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


def build_per_segment_df(segments: list, metrics: dict) -> pd.DataFrame:
    """
    Build a tidy per-segment DataFrame from optimizer inputs + metrics.
    Expects metrics["per_segment"][seg_id] with keys: dn,v,dp,h,heat_loss_W.
    """
    rows = []
    per_seg = metrics.get("per_segment", {}) or {}
    for s in segments:
        m = per_seg.get(s.seg_id, {})
        rows.append(
            dict(
                seg_id=s.seg_id,
                length_m=float(getattr(s, "length_m", 0.0)),
                DN=int(m.get("dn", 0)),
                V_dot_m3s=float(getattr(s, "V_dot_m3s", 0.0)),
                v_mps=float(m.get("v", 0.0)),
                dp_Pa=float(m.get("dp", 0.0)),
                h_m=float(m.get("h", 0.0)),
                heat_loss_W=float(m.get("heat_loss_W", 0.0)),
                path_id=str(getattr(s, "path_id", "")),
                is_supply=bool(getattr(s, "is_supply", False)),
            )
        )
    df = pd.DataFrame(rows)
    # Ensure column order & presence
    for c in REQUIRED_COLUMNS:
        if c not in df.columns:
            df[c] = None
    return df[REQUIRED_COLUMNS]
