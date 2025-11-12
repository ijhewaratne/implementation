from __future__ import annotations
import json, glob
from pathlib import Path
import pandas as pd

CP_WATER = 4180.0  # J/(kg·K)

def load_lfa_series(lfa_glob: str = "processed/lfa/*.json") -> pd.DataFrame:
    """
    Load 8760-hour mean series per building.
    Returns long DF: columns [building_id, hour, q_kw].
    """
    rows = []
    for p in glob.glob(lfa_glob):
        j = json.loads(Path(p).read_text(encoding="utf-8"))
        bid = str(j.get("building_id") or Path(p).stem)
        series = j.get("series") or []
        if len(series) != 8760:
            raise ValueError(f"{p}: series length {len(series)} != 8760")
        rows += ({"building_id": bid, "hour": h, "q_kw": float(q)} for h, q in enumerate(series))
    if not rows:
        raise FileNotFoundError(f"No LFA JSONs found at {lfa_glob}")
    return pd.DataFrame(rows)

def qkw_to_mdot_kg_s(df: pd.DataFrame, t_supply_c: float, t_return_c: float) -> pd.DataFrame:
    """
    m_dot = Q_W / (cp * ΔT); enforce ΔT ≥ 30 K.
    Adds columns [mdot_kg_s, deltaT_K].
    """
    deltaT = max(30.0, float(t_supply_c) - float(t_return_c))
    out = df.copy()
    out["mdot_kg_s"] = (out["q_kw"] * 1000.0) / (CP_WATER * deltaT)
    out["deltaT_K"] = deltaT
    return out
