from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

def aggregate_feeder_loads(lfa_el: pd.DataFrame, topo: pd.DataFrame) -> pd.DataFrame:
    df = lfa_el.merge(topo[["building_id","feeder_id","feeder_rating_kw"]], on="building_id", how="inner")
    agg = (df.groupby(["feeder_id","hour"], as_index=False)
             .agg(p_kw=("p_kw","sum"), feeder_rating_kw=("feeder_rating_kw","first")))
    agg["utilization_pct"] = (agg["p_kw"] / agg["feeder_rating_kw"]).replace([np.inf, -np.inf], np.nan) * 100.0
    return agg

def heuristic_voltage_bounds(util_pct: pd.Series, v_min_pu=0.90, v_max_pu=1.10) -> tuple[pd.Series,pd.Series]:
    # simple proxy: linear drop up to 10% at 100% utilization
    drop = (util_pct / 100.0) * 0.10
    vmin = (1.0 - drop).clip(lower=0.80)
    vmax = pd.Series(1.0 + 0.02, index=util_pct.index).clip(upper=v_max_pu)  # small headroom
    vmin = vmin.clip(upper=v_max_pu)
    return vmin, vmax

def write_outputs(agg: pd.DataFrame, out_dir: str, eval_dir: str,
                  util_thr: float, v_min_pu: float, v_max_pu: float) -> tuple[str,str]:
    outp = Path(out_dir); outp.mkdir(parents=True, exist_ok=True)
    evalp = Path(eval_dir); evalp.mkdir(parents=True, exist_ok=True)
    vmin, vmax = heuristic_voltage_bounds(agg["utilization_pct"], v_min_pu, v_max_pu)
    feeder_loads = agg.copy()
    feeder_loads["v_min_pu"] = vmin
    feeder_loads["v_max_pu"] = vmax
    feeder_loads.to_csv(outp / "feeder_loads.csv", index=False)
    # violations
    viol = []
    over = feeder_loads[feeder_loads["utilization_pct"] > (util_thr*100.0)]
    for _, r in over.iterrows():
        viol.append({"feeder_id": r["feeder_id"], "hour": int(r["hour"]),
                     "violation_reason": f"utilization>{int(util_thr*100)}%", "value": float(r["utilization_pct"])})
    under_v = feeder_loads[feeder_loads["v_min_pu"] < v_min_pu]
    for _, r in under_v.iterrows():
        viol.append({"feeder_id": r["feeder_id"], "hour": int(r["hour"]),
                     "violation_reason": f"v_min<{v_min_pu}pu", "value": float(r["v_min_pu"])})
    pd.DataFrame(viol).to_csv(evalp / "violations.csv", index=False)
    return str(outp / "feeder_loads.csv"), str(evalp / "violations.csv")
