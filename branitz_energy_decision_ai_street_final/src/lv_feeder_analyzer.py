"""
LV Feeder Analyzer

Two backends:
- "heuristic" (fast stub, current behavior)
- "pandapower" (full AC power-flow per feeder & hour)
"""

from typing import Dict, List, Optional
import pandas as pd

# ---------- Existing helpers (keep) ----------

def map_buildings_to_feeders(buildings_df: pd.DataFrame, feeders_df: pd.DataFrame) -> Dict[str, str]:
    if ("building_id" in buildings_df.columns and 
        "building_id" in feeders_df.columns and 
        "feeder_id" in feeders_df.columns):
        m = dict(pd.merge(
            buildings_df[["building_id"]], 
            feeders_df[["building_id", "feeder_id"]], 
            on="building_id", how="left"
        ).fillna({"feeder_id": "F0"}).set_index("building_id")["feeder_id"])
        return {str(k): str(v) for k, v in m.items()}
    return {str(b): "F0" for b in buildings_df["building_id"].astype(str)}


def pick_top10_hours(load_df: pd.DataFrame) -> List[int]:
    """load_df: index 0..8759, column 'total_kw' -> return top-10 hour indices."""
    if "total_kw" not in load_df.columns:
        raise ValueError("load_df must contain 'total_kw'")
    return list(load_df["total_kw"].nlargest(10).index.astype(int))


# ---------- New: pandapower backend ----------

def _ensure_pp():
    try:
        import pandapower as pp  # noqa: F401
    except Exception as e:
        raise ImportError("pandapower backend requires pandapower") from e


def _run_hour_for_feeder_pp(net, lv_bus: int, p_kw: float, q_kvar: float = 0.0) -> Dict[str, float]:
    """
    Update/insert a single aggregated SLoad at lv_bus, runpp, and return KPIs.
    """
    import pandapower as pp
    import numpy as np

    # create or update an aggregated sgen (P,Q at LV bus). Using sgen (PQ) is simple/robust.
    p_mw = max(0.0, float(p_kw)) / 1000.0
    q_mvar = float(q_kvar) / 1000.0 if q_kvar else 0.0

    if "agg_sgen_idx" not in net:
        net["agg_sgen_idx"] = {}
    idx = net["agg_sgen_idx"].get(lv_bus)
    if idx is None:
        idx = pp.create_sgen(net, bus=lv_bus, p_mw=p_mw, q_mvar=q_mvar, name=f"agg_load_bus{lv_bus}")
        net["agg_sgen_idx"][lv_bus] = idx
    else:
        net.sgen.at[idx, "p_mw"] = p_mw
        net.sgen.at[idx, "q_mvar"] = q_mvar

    # run power flow
    pp.runpp(net, algorithm="nr", max_iteration=20, numba=False)

    # utilization proxy = max of trafo & line loading
    loading = []
    if not net.trafo.empty and "loading_percent" in net.res_trafo.columns:
        loading += list(net.res_trafo.loading_percent.values)
    if not net.line.empty and "loading_percent" in net.res_line.columns:
        loading += list(net.res_line.loading_percent.values)
    util_max = (max(loading) / 100.0) if loading else 0.0

    # voltage extrema
    vmin = float(net.res_bus.vm_pu.min())
    vmax = float(net.res_bus.vm_pu.max())

    # counts for context
    over_80 = sum(1 for x in loading if x >= 80.0)
    over_100 = sum(1 for x in loading if x >= 100.0)

    return dict(utilization_max=util_max, voltage_min=vmin, voltage_max=vmax,
                n_over80=over_80, n_over100=over_100)


def run_feeder_studies(
    feeders_model: Dict[str, dict],
    building_to_feeder: Dict[str, str],
    hourly_building_kw: pd.DataFrame,
    hours: List[int],
    backend: str = "pandapower",
    util_threshold: float = 0.8,
    v_limits: tuple = (0.90, 1.10),
    power_factor: float = 0.98,
) -> pd.DataFrame:
    """
    Return a tidy DataFrame with:
      feeder_id, hour, utilization_max, voltage_min, voltage_max,
      violates_util>=0.8, violates_voltage_outside_±10%
    """
    rows = []

    if backend == "heuristic":
        # Preserve your current stub behavior as fallback
        for h in hours:
            col = str(h) if str(h) in hourly_building_kw.columns else h
            feeder_sum = hourly_building_kw.groupby(building_to_feeder).sum(numeric_only=True)[col]
            for fid, kw in feeder_sum.items():
                util = float(kw)/1000.0  # assume 1 MW base rating
                vmin = 1.0 - 0.15 * util
                vmax = 1.0 + 0.05 * util
                rows.append(dict(
                    feeder_id=fid, hour=int(h),
                    utilization_max=util, voltage_min=vmin, voltage_max=vmax,
                    **{"violates_util>=0.8": util >= util_threshold,
                       "violates_voltage_outside_±10%": (vmin < v_limits[0] or vmax > v_limits[1])}
                ))
        return pd.DataFrame(rows)

    # pandapower backend
    _ensure_pp()
    import math

    # pre-aggregate by feeder for each hour
    for h in hours:
        col = str(h) if str(h) in hourly_building_kw.columns else h
        feeder_kw = hourly_building_kw.groupby(building_to_feeder).sum(numeric_only=True)[col]

        for fid, p_kw in feeder_kw.items():
            fm = feeders_model.get(fid)
            if not fm:
                # unknown feeder; mark as NA row
                rows.append(dict(
                    feeder_id=fid, hour=int(h),
                    utilization_max=float("nan"), voltage_min=float("nan"), voltage_max=float("nan"),
                    **{"violates_util>=0.8": False, "violates_voltage_outside_±10%": False}
                ))
                continue

            net = fm["net"]
            lv_bus = int(fm["lv_bus"])
            # derive Q from PF (approx); Q = P * tan(arccos(pf))
            q_kvar = p_kw * math.tan(math.acos(power_factor)) if power_factor < 1.0 else 0.0

            kpis = _run_hour_for_feeder_pp(net, lv_bus, float(p_kw), float(q_kvar))
            rows.append(dict(
                feeder_id=fid, hour=int(h), **kpis,
                **{"violates_util>=0.8": kpis["utilization_max"] >= util_threshold,
                   "violates_voltage_outside_±10%": (kpis["voltage_min"] < v_limits[0] or kpis["voltage_max"] > v_limits[1])}
            ))

    return pd.DataFrame(rows)


# ---------- CLI shim ----------

if __name__ == "__main__":
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="pandapower", choices=["pandapower","heuristic"])
    parser.add_argument("--hours", type=int, nargs="+", default=[0,1])
    parser.add_argument("--util-threshold", type=float, default=0.8)
    parser.add_argument("--vmin", type=float, default=0.90)
    parser.add_argument("--vmax", type=float, default=1.10)
    args = parser.parse_args()
    print("This CLI is a stub. Import and call run_feeder_studies() from your pipeline.") 