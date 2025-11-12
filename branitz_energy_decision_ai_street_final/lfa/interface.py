"""
Load Forecasting Agent Interface

Provides 8760h per-building forecasts with P10/P50/P90 and Guideline-14 metrics + PICP.
"""

import math
import random
import pandas as pd
from typing import Dict, List


def forecast_8760(buildings: pd.DataFrame, seed: int = 42) -> Dict:
    """
    Return per-building 8760h forecasts with P10/P50/P90 and Guideline-14 metrics + PICP.
    
    Input: buildings must contain 'building_id' and optionally a 'scale_kw' column (defaults 10).
    Output dict:
      {
        "per_building": { id: { "P10":[8760], "P50":[8760], "P90":[8760] } },
        "metrics": { "MAE":float, "RMSE":float, "MAPE":float, "PICP80":float, "PICP90":float }
      }
    Deterministic synthetic series: sinusoids + daily seasonality with small noise.
    """
    # deterministic generation
    random.seed(seed)
    n_hours = 8760
    if "building_id" not in buildings.columns:
        raise ValueError("buildings must contain 'building_id'")
    
    per = {}
    all_true = []
    all_p50 = []
    lo80, hi80 = [], []
    lo90, hi90 = [], []
    
    for _, row in buildings.iterrows():
        bid = str(row["building_id"])
        s = float(row.get("scale_kw", 10.0))
        base = [max(0.0, s*(1.0 + 0.3*math.sin(2*math.pi*h/24) + 0.6*math.cos(2*math.pi*h/8760))) for h in range(n_hours)]
        
        # P50 is base; P10/P90 are ±20%
        p50 = base
        p10 = [0.8*x for x in base]
        p90 = [1.2*x for x in base]
        per[bid] = {"P10": p10, "P50": p50, "P90": p90}
        
        # construct pseudo "actuals" as P50 with small noise
        true = [x * (1.0 + 0.02*math.sin(2*math.pi*h/168)) for h, x in enumerate(p50)]
        all_true += true
        all_p50 += p50
        lo80 += [x*0.9 for x in p50]
        hi80 += [x*1.1 for x in p50]
        lo90 += [x*0.85 for x in p50]
        hi90 += [x*1.15 for x in p50]
    
    # metrics
    n = len(all_true)
    abs_err = [abs(t-p) for t, p in zip(all_true, all_p50)]
    mae = sum(abs_err)/n
    rmse = (sum((t-p)**2 for t, p in zip(all_true, all_p50))/n)**0.5
    mape = 100.0*sum(abs(t-p)/(t+1e-6) for t, p in zip(all_true, all_p50))/n
    picp80 = sum(1 for t, lo, hi in zip(all_true, lo80, hi80) if lo <= t <= hi)/n
    picp90 = sum(1 for t, lo, hi in zip(all_true, lo90, hi90) if lo <= t <= hi)/n
    
    return {
        "per_building": per, 
        "metrics": {
            "MAE": mae,
            "RMSE": rmse, 
            "MAPE": mape,
            "PICP80": picp80,
            "PICP90": picp90
        }
    } 