from __future__ import annotations
import math, json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

# ---- Try to reuse PMA helpers if they exist; otherwise safe fallbacks ----
try:
    # Example: adapt these names to your optimize/physics_models.py if available
    from optimize.physics_models import friction_factor_swamee_jain as _ff_swamee
except Exception:
    _ff_swamee = None

RHO_WATER = 998.0     # kg/m^3
MU_WATER = 0.0010     # Pa·s

@dataclass
class APAConfig:
    roughness_k_mm: float
    soil_temp_c: float
    insulation_u_w_per_mk: float
    deltaT_target_K: float
    segments_csv: str
    network_gpkg: Optional[str] = None
    source_node_id: int = 0
    out_csv: str = "eval/apa/sensitivity.csv"
    exclude_return_only: bool = True
    # cache_baseline: bool = True  # Not implemented yet
    # sweeps
    roughness_k_mm_rel: List[float] = None
    soil_temp_c_abs: List[float] = None
    insulation_u_w_per_mk_rel: List[float] = None
    deltaT_target_K_abs: List[float] = None

def _load_cfg(path: str) -> APAConfig:
    y = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    S = y.get("sweeps", {})
    return APAConfig(
        roughness_k_mm=float(y["roughness_k_mm"]),
        soil_temp_c=float(y["soil_temp_c"]),
        insulation_u_w_per_mk=float(y["insulation_u_w_per_mk"]),
        deltaT_target_K=float(y["deltaT_target_K"]),
        segments_csv=y["segments_csv"],
        network_gpkg=y.get("network_gpkg"),
        source_node_id=int(y.get("source_node_id", 0)),
        out_csv=y.get("out_csv", "eval/apa/sensitivity.csv"),
        exclude_return_only=bool(y.get("exclude_return_only", True)),
        # cache_baseline=bool(y.get("cache_baseline", True)),  # Not implemented yet
        roughness_k_mm_rel=list(S.get("roughness_k_mm_rel", [-0.1, -0.05, 0.0, 0.05, 0.1])),
        soil_temp_c_abs=list(S.get("soil_temp_c_abs", [-5, -2, 0, 2, 5])),
        insulation_u_w_per_mk_rel=list(S.get("insulation_u_w_per_mk_rel", [-0.1, -0.05, 0.0, 0.05, 0.1])),
        deltaT_target_K_abs=list(S.get("deltaT_target_K_abs", [-5, -2, 0, 2, 5])),
    )

# ---------- Physics helpers (vectorized) ----------
def _reynolds(v_ms: np.ndarray, d_m: np.ndarray) -> np.ndarray:
    return (RHO_WATER * v_ms * d_m) / MU_WATER

def _friction_factor(v_ms: np.ndarray, d_m: np.ndarray, k_mm: float) -> np.ndarray:
    Re = _reynolds(v_ms, d_m)
    rel_rough = (k_mm / 1000.0) / np.maximum(d_m, 1e-9)

    if _ff_swamee is not None:
        # Prefer project's shared helper if signature matches (adjust if needed)
        try:
            return _ff_swamee(Re=Re, rel_rough=rel_rough)
        except TypeError:
            pass  # fall through to local model

    f = np.empty_like(Re, dtype=float)
    lam = Re < 2300.0
    f[lam] = 64.0 / np.maximum(Re[lam], 1.0)  # laminar
    tur = ~lam
    f[tur] = 0.25 / (np.log10(rel_rough[tur]/3.7 + 5.74/(np.maximum(Re[tur],1.0)**0.9))**2)  # Swamee–Jain
    return f

def _dp_fric_Pa(f: np.ndarray, L_m: np.ndarray, d_m: np.ndarray, v_ms: np.ndarray) -> np.ndarray:
    return f * (np.maximum(L_m, 0.0) / np.maximum(d_m, 1e-9)) * (RHO_WATER * v_ms**2 / 2.0)

def _linear_heat_loss_Wm(U: float, d_outer_m: np.ndarray, t_supply_c: float, t_soil_c: float) -> np.ndarray:
    # Simple linear model per unit length: q' = U * ΔT ; treat U as already linearized W/mK
    deltaT = np.maximum(t_supply_c - t_soil_c, 0.0)
    return U * deltaT * np.ones_like(d_outer_m)

# ---------- Worst-path (exclude return-only segments) ----------
def _worst_path_headloss_bar(df: pd.DataFrame, exclude_return_only: bool) -> float:
    """
    If a real graph is available, Cursor can wire a proper Dijkstra over mains/branches.
    Here, fall back to max cumulative headloss along connected chains, while
    excluding segments flagged as return-only when requested.
    Expected columns in df: ['pipe_id','dp_bar','return_only'?].
    """
    x = df.copy()
    if exclude_return_only and "return_only" in x.columns:
        x = x[~x["return_only"].fillna(False)]
    if "dp_bar" not in x.columns or x.empty:
        return 0.0
    # Fallback heuristic: sum of the largest K headlosses as a proxy (since topology may be absent)
    # K = int(sqrt(N)) bounds
    K = max(1, int(len(x)**0.5))
    return float(x["dp_bar"].nlargest(K).sum())

# ---------- Baseline & sweep engine ----------
def _load_segments(segments_csv: str) -> pd.DataFrame:
    df = pd.read_csv(segments_csv)
    need = {"length_m","d_inner_m","d_outer_m","v_ms"}
    missing = need - set(df.columns)
    if missing:
        raise FileNotFoundError(f"{segments_csv} missing columns: {sorted(missing)}")
    # Optional columns
    for c in ["q_loss_Wm","return_only"]:
        if c not in df.columns:
            df[c] = np.nan if c == "q_loss_Wm" else False
    if "pipe_id" not in df.columns:
        df["pipe_id"] = np.arange(len(df))
    return df

def _metrics_from_params(df: pd.DataFrame, k_mm: float, U_w_per_mk: float, soil_c: float, t_supply_c: float, exclude_return_only: bool = True) -> Dict[str, float]:
    # Robust numeric parsing with fallbacks
    v = pd.to_numeric(df["v_ms"], errors="coerce").fillna(0).to_numpy(dtype=float)
    d_in = pd.to_numeric(df["d_inner_m"], errors="coerce").fillna(1e-6).to_numpy(dtype=float)
    L = pd.to_numeric(df["length_m"], errors="coerce").fillna(0).to_numpy(dtype=float)
    
    f = _friction_factor(v, d_in, k_mm)
    dp_Pa = _dp_fric_Pa(f, L, d_in, v)               # Pa
    dp_bar = dp_Pa / 1e5
    # Heat loss: use provided q_loss_Wm if present; otherwise linear model
    if df["q_loss_Wm"].notna().any():
        q_Wm = df["q_loss_Wm"].fillna(0.0).to_numpy(dtype=float)
    else:
        q_Wm = _linear_heat_loss_Wm(U_w_per_mk, df["d_outer_m"].to_numpy(dtype=float), t_supply_c, soil_c)
    q_W = q_Wm * L
    res = pd.DataFrame({"pipe_id": df["pipe_id"], "dp_bar": dp_bar, "q_W": q_W, "return_only": df["return_only"]})
    total_headloss_bar = float(dp_bar.sum())
    total_heat_loss_kW = float(q_W.sum() / 1000.0)
    worst_path_bar = _worst_path_headloss_bar(res, exclude_return_only=exclude_return_only)
    return {
        "total_headloss_bar": total_headloss_bar,
        "total_heat_loss_kW": total_heat_loss_kW,
        "worst_path_headloss_bar": worst_path_bar
    }

def _sweep(df: pd.DataFrame, cfg: APAConfig) -> pd.DataFrame:
    rows = []

    # Baseline metrics (cached optionally)
    base = _metrics_from_params(
        df,
        k_mm=cfg.roughness_k_mm,
        U_w_per_mk=cfg.insulation_u_w_per_mk,
        soil_c=cfg.soil_temp_c,
        t_supply_c=cfg.deltaT_target_K + 40.0,  # nominal supply ~ return + ΔT; constant offset for sensitivity
        exclude_return_only=cfg.exclude_return_only,
    )

    def _emit(param: str, baseline_value: float, delta_label: float, metrics: Dict[str,float]):
        for m_name, m_val in metrics.items():
            base_val = base[m_name]
            delta_val = m_val - base_val
            pct = 0.0 if base_val == 0 else (delta_val / abs(base_val)) * 100.0
            rows.append({
                "param": param,
                "baseline_value": baseline_value,
                "delta": delta_label,
                "metric": m_name,
                "baseline_metric": base_val,
                "value": m_val,
                "delta_value": delta_val,
                "pct_change": pct,
            })

    # 1) roughness rel deltas
    for r in cfg.roughness_k_mm_rel:
        k = cfg.roughness_k_mm * (1.0 + r)
        met = _metrics_from_params(df, k_mm=k, U_w_per_mk=cfg.insulation_u_w_per_mk,
                                   soil_c=cfg.soil_temp_c, t_supply_c=cfg.deltaT_target_K + 40.0,
                                   exclude_return_only=cfg.exclude_return_only)
        _emit("roughness_k_mm", cfg.roughness_k_mm, r, met)

    # 2) soil temp absolute deltas (affects loss only)
    for dT in cfg.soil_temp_c_abs:
        soil = cfg.soil_temp_c + dT
        met = _metrics_from_params(df, k_mm=cfg.roughness_k_mm, U_w_per_mk=cfg.insulation_u_w_per_mk,
                                   soil_c=soil, t_supply_c=cfg.deltaT_target_K + 40.0,
                                   exclude_return_only=cfg.exclude_return_only)
        _emit("soil_temp_c", cfg.soil_temp_c, dT, met)

    # 3) insulation U rel deltas
    for r in cfg.insulation_u_w_per_mk_rel:
        U = cfg.insulation_u_w_per_mk * (1.0 + r)
        met = _metrics_from_params(df, k_mm=cfg.roughness_k_mm, U_w_per_mk=U,
                                   soil_c=cfg.soil_temp_c, t_supply_c=cfg.deltaT_target_K + 40.0,
                                   exclude_return_only=cfg.exclude_return_only)
        _emit("insulation_u_w_per_mk", cfg.insulation_u_w_per_mk, r, met)

    # 4) ΔT target absolute deltas (approximated through supply temperature for loss sensitivity)
    for d in cfg.deltaT_target_K_abs:
        t_supply = cfg.deltaT_target_K + d + 40.0
        met = _metrics_from_params(df, k_mm=cfg.roughness_k_mm, U_w_per_mk=cfg.insulation_u_w_per_mk,
                                   soil_c=cfg.soil_temp_c, t_supply_c=t_supply,
                                   exclude_return_only=cfg.exclude_return_only)
        _emit("deltaT_target_K", cfg.deltaT_target_K, d, met)

    return pd.DataFrame(rows)

def run(config_path: str = "configs/apa.yml") -> dict:
    cfg = _load_cfg(config_path)
    df = _load_segments(cfg.segments_csv)
    out = _sweep(df, cfg)
    outp = Path(cfg.out_csv); outp.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(outp, index=False)
    return {"status":"ok","sensitivity_csv":str(outp),"rows":int(len(out))}

if __name__ == "__main__":
    import sys
    print(json.dumps(run(sys.argv[1] if len(sys.argv)>1 else "configs/apa.yml"), indent=2))
