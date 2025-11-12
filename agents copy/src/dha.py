from __future__ import annotations
import yaml
from pathlib import Path
import pandas as pd

from .dha_adapter import load_lfa_series, load_weather_opt, heat_to_electric_kw
from .dha_heuristic import aggregate_feeder_loads, write_outputs
try:
    from .dha_pandapower import run_loadflow_for_hours
except Exception:
    run_loadflow_for_hours = None  # optional

def top_n_peak_hours(total_system_kw: pd.Series, n: int) -> list[int]:
    return list(total_system_kw.nlargest(n).index.astype(int))

def run(config_path: str = "configs/dha.yml") -> dict:
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    lfa_glob        = cfg.get("lfa_glob")
    topo_path       = cfg.get("feeder_topology")
    weather_path    = cfg.get("weather_parquet")
    bins            = cfg.get("cop_bins", [])
    cop_default     = float(cfg.get("cop_default", 3.0))
    util_thr        = float(cfg.get("utilization_threshold", 0.8))
    v_min_pu        = float(cfg.get("v_min_pu", 0.90))
    v_max_pu        = float(cfg.get("v_max_pu", 1.10))
    out_dir         = cfg.get("out_dir", "processed/dha")
    eval_dir        = cfg.get("eval_dir", "eval/dha")
    pp_enabled      = bool(cfg.get("pandapower_enabled", False))
    top_n           = int(cfg.get("top_n_hours", 10))

    # 1) Inputs
    lfa = load_lfa_series(lfa_glob)
    weather = load_weather_opt(weather_path)
    lfa_el = heat_to_electric_kw(lfa, weather, bins, cop_default)  # building_id,hour,p_kw,cop
    topo = pd.read_parquet(topo_path)  # building_id, feeder_id, feeder_rating_kw

    # 2) Aggregate per feeder & select top-N hours
    agg = aggregate_feeder_loads(lfa_el, topo)                     # feeder_id,hour,p_kw,utilization_pct
    hours = top_n_peak_hours(agg.groupby("hour")["p_kw"].sum(), top_n)
    agg = agg[agg["hour"].isin(hours)].copy()

    # 3) Optional pandapower voltage calc
    if pp_enabled and run_loadflow_for_hours is not None:
        agg = run_loadflow_for_hours(agg, (v_min_pu, v_max_pu))

    # 4) Outputs & violations
    feeder_csv, viol_csv = write_outputs(agg, out_dir, eval_dir, util_thr, v_min_pu, v_max_pu)

    return {
        "status": "ok",
        "hours": hours,
        "feeder_loads": feeder_csv,
        "violations": viol_csv,
        "pandapower": bool(pp_enabled and run_loadflow_for_hours is not None),
    }

if __name__ == "__main__":
    import json, sys
    cfg = sys.argv[1] if len(sys.argv) > 1 else "configs/dha.yml"
    print(json.dumps(run(cfg), indent=2))
