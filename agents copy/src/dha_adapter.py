from __future__ import annotations
import json, glob
from pathlib import Path
import pandas as pd

def load_lfa_series(lfa_glob: str) -> pd.DataFrame:
    rows = []
    for p in glob.glob(lfa_glob):
        j = json.loads(Path(p).read_text(encoding="utf-8"))
        bid = str(j.get("building_id") or Path(p).stem)
        series = j.get("series") or []
        if len(series) != 8760:
            raise ValueError(f"{p}: series length {len(series)} != 8760")
        rows += ({"building_id": bid, "hour": h, "q_kw": float(q)} for h, q in enumerate(series))
    if not rows:
        raise FileNotFoundError(f"No LFA JSONs at {lfa_glob}")
    return pd.DataFrame(rows)

def load_weather_opt(path: str | None) -> pd.DataFrame | None:
    if not path or not Path(path).exists(): return None
    df = pd.read_parquet(path)
    if "hour" in df and "T_out_c" in df: return df[["hour","T_out_c"]].copy()
    return None

def cop_from_bins(T: pd.Series, bins: list[dict], default_cop: float) -> pd.Series:
    cop = pd.Series(default_cop, index=T.index, dtype="float64")
    for b in bins or []:
        mask = (T >= b["t_min"]) & (T <= b["t_max"])
        cop.loc[mask] = float(b["cop"])
    cop = cop.clip(lower=0.1)  # safety
    return cop

def heat_to_electric_kw(lfa_df: pd.DataFrame, weather: pd.DataFrame | None,
                        bins: list[dict], cop_default: float) -> pd.DataFrame:
    df = lfa_df.copy()
    if weather is not None:
        df = df.merge(weather, on="hour", how="left")
        df["T_out_c"] = df["T_out_c"].fillna(method="ffill").fillna(method="bfill").fillna(5.0)
        df["cop"] = cop_from_bins(df["T_out_c"], bins, cop_default)
    else:
        df["cop"] = cop_default
    df["cop"] = df["cop"].clip(lower=0.1)
    df["p_kw"] = df["q_kw"] / df["cop"]              # P_el = Q_th / COP
    return df[["building_id","hour","p_kw","cop"]]
