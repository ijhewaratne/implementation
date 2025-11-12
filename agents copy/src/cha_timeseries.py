from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import pandapipes as pp

from lfa_adapter import load_lfa_series, qkw_to_mdot_kg_s

def attach_building_sinks(net: pp.pandapipesNet, building_to_junction: Dict[str, int]) -> Dict[str, int]:
    """Create one sink per building at its mapped junction."""
    b2sink: Dict[str, int] = {}
    for bid, jidx in building_to_junction.items():
        sidx = pp.create_sink(net, junction=int(jidx), mdot_kg_per_s=0.0, name=str(bid))
        b2sink[str(bid)] = sidx
    return b2sink

def select_peak_hours(total_q_kw_by_hour: pd.Series, top_n: int) -> List[int]:
    """Return top-N system peak hours."""
    return list(total_q_kw_by_hour.nlargest(top_n).index.astype(int))

def run_timeseries(
    net: pp.pandapipesNet,
    building_to_junction: Dict[str, int],
    *,
    lfa_glob: str = "processed/lfa/*.json",
    t_supply_c: float = 80.0,
    t_return_c: float = 50.0,
    top_n: int = 10,
    out_dir: str = "processed/cha",
    v_max_ms: float = 1.5,
    save_hourly: bool = True,
) -> Dict:
    """
    Feed LFA 8760h heat into pandapipes as per-building sink mass flows,
    simulate top-N peak hours, and emit CHA artifacts.
    """
    outp = Path(out_dir); outp.mkdir(parents=True, exist_ok=True)
    evalp = Path("eval/cha"); evalp.mkdir(parents=True, exist_ok=True)

    # 1) LFA -> mdot
    lfa = qkw_to_mdot_kg_s(load_lfa_series(lfa_glob), t_supply_c, t_return_c)

    # 2) Sinks
    b2sink = attach_building_sinks(net, building_to_junction)

    # 3) Hours to simulate
    hours = select_peak_hours(lfa.groupby("hour")["q_kw"].sum(), top_n)

    # 4) Run hydraulics per hour
    rows = []
    for h in hours:
        # Reset network results by clearing result tables
        net.res_pipe = None
        net.res_junction = None
        net.sink["mdot_kg_per_s"] = 0.0
        sub = lfa.loc[lfa["hour"] == h, ["building_id", "mdot_kg_s"]]
        for _, r in sub.iterrows():
            sidx = b2sink.get(str(r["building_id"]))
            if sidx is not None:
                net.sink.at[sidx, "mdot_kg_per_s"] = float(r["mdot_kg_s"])
        pp.pipeflow(net)
        rp = net.res_pipe
        vcol = "v_mean_m_per_s" if "v_mean_m_per_s" in rp.columns else "v_m_per_s"
        for i in rp.index:
            rows.append({
                "hour": int(h),
                "pipe_idx": int(i),
                "v_ms": float(rp.at[i, vcol]),
                "p_from_bar": float(rp.get("p_from_bar", pd.Series([np.nan], index=[i]))[i]),
                "p_to_bar": float(rp.get("p_to_bar", pd.Series([np.nan], index=[i]))[i]),
            })

    hourly = pd.DataFrame(rows)
    if save_hourly:
        hourly.to_parquet(outp / "results_hourly.parquet", index=False)

    # 5) Design-hour segments.csv
    h0 = int(hours[0])
    design = hourly[hourly["hour"] == h0].sort_values("pipe_idx")
    static = net.pipe[["length_km", "diameter_m"]].copy()
    static["length_m"] = static["length_km"] * 1000.0
    static["d_inner_m"] = static["diameter_m"]
    static["d_outer_m"] = static["diameter_m"] * 1.1  # fallback if not stored
    seg = (pd.DataFrame({
        "pipe_id": net.res_pipe.index.astype(int),
        "v_ms": design["v_ms"].to_list(),
        "p_from_bar": design["p_from_bar"].to_list(),
        "p_to_bar": design["p_to_bar"].to_list(),
    })
      .set_index("pipe_id").join(static, how="left").reset_index())
    seg["deltaT_K"] = max(30.0, t_supply_c - t_return_c)
    seg["q_loss_Wm"] = np.nan
    seg["pump_kW_contrib"] = np.nan
    seg = seg[["pipe_id","length_m","d_inner_m","d_outer_m","v_ms","p_from_bar","p_to_bar","q_loss_Wm","deltaT_K","pump_kW_contrib"]]
    seg.to_csv(outp / "segments.csv", index=False)

    # 6) Compliance
    viol = seg.loc[seg["v_ms"] > v_max_ms, ["pipe_id","v_ms"]].copy()
    viol["violation_reason"] = f"velocity>{v_max_ms} m/s"
    viol = viol.rename(columns={"v_ms":"value"})[["pipe_id","violation_reason","value"]]
    viol.to_csv("eval/cha/hydraulics_check.csv", index=False)

    return {
        "status": "ok",
        "hours": hours,
        "segments_csv": str(outp / "segments.csv"),
        "hourly_parquet": (str(outp / "results_hourly.parquet") if save_hourly else None),
        "violations_csv": "eval/cha/hydraulics_check.csv",
    }
