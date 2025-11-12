from __future__ import annotations
import json, math, glob
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import yaml
from jsonschema import Draft202012Validator

def _load_cfg(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))

def _load_eaa(summary_csv: str, stat: str) -> Dict[str, float]:
    df = pd.read_csv(summary_csv)
    if stat not in df.columns:
        raise ValueError(f"EAA summary missing column '{stat}'")
    def pick(metric: str) -> float:
        row = df.loc[df["metric"] == metric]
        if row.empty:
            raise ValueError(f"EAA summary missing metric '{metric}'")
        val = float(row.iloc[0][stat])
        if not math.isfinite(val):
            raise ValueError(f"EAA {metric} {stat} is not finite")
        return val
    return {
        "lcoh_eur_per_mwh": pick("lcoh_eur_per_mwh"),
        "co2_kg_per_mwh": pick("co2_kg_per_mwh"),
    }

def _dha_max_util(feeder_csv: str) -> float:
    df = pd.read_csv(feeder_csv)
    if "utilization_pct" not in df.columns:
        raise ValueError("DHA feeder_loads.csv missing 'utilization_pct'")
    v = float(df["utilization_pct"].max())
    return v if math.isfinite(v) else 0.0

def _load_lfa_metrics(metrics_csv: str | None) -> Dict[str, float] | None:
    if not metrics_csv or not Path(metrics_csv).exists():
        return None
    df = pd.read_csv(metrics_csv)
    cols = [c for c in df.columns]
    rmse = df.get("rmse")
    picp = df.get("picp_90") or df.get("picp90") or df.get("picp")
    out = {}
    if rmse is not None:
        out["forecast_rmse"] = float(pd.to_numeric(rmse).iloc[0])
    if picp is not None:
        out["forecast_picp_90"] = float(pd.to_numeric(picp).iloc[0])
    return out if out else None

def _estimate_pump_kw_from_segments(segments_csv: str, eta: float) -> Optional[float]:
    df = pd.read_csv(segments_csv)
    need = {"v_ms","d_inner_m","p_from_bar","p_to_bar"}
    if not need.issubset(df.columns):
        return None
    # Exclude return-only if present
    if "return_only" in df.columns:
        df = df[~df["return_only"].fillna(False)]
    area = np.pi * (pd.to_numeric(df["d_inner_m"], errors="coerce")**2) / 4.0
    q = pd.to_numeric(df["v_ms"], errors="coerce") * area              # m^3/s
    dp_pa = (pd.to_numeric(df["p_from_bar"], errors="coerce") - pd.to_numeric(df["p_to_bar"], errors="coerce")) * 1e5
    dp_pa = dp_pa.clip(lower=0.0)
    pump_w = (dp_pa * q).sum() / max(eta, 1e-6)
    pump_kw = pump_w / 1000.0
    return float(pump_kw) if np.isfinite(pump_kw) and pump_kw > 0 else None

def _dh_losses_pct(segments_csv: str, fallback_pct: float, deltaT_K: float | None = None) -> float:
    df = pd.read_csv(segments_csv)
    have_loss = "q_loss_Wm" in df.columns and "length_m" in df.columns
    if have_loss and df["q_loss_Wm"].notna().any():
        loss_W = (pd.to_numeric(df["q_loss_Wm"], errors="coerce").fillna(0.0) *
                  pd.to_numeric(df["length_m"], errors="coerce").fillna(0.0)).sum()
        if deltaT_K and {"v_ms","d_inner_m"}.issubset(df.columns):
            # delivered heat ≈ ρ·cp·Σ(Q_supply)·ΔT
            area = np.pi * (pd.to_numeric(df["d_inner_m"], errors="coerce")**2) / 4.0
            q_supply = (pd.to_numeric(df["v_ms"], errors="coerce") * area)
            rho, cp = 998.0, 4180.0
            delivered_W = (rho * cp * q_supply.sum() * float(deltaT_K))
            denom = max(delivered_W + loss_W, 1.0)
            return float(np.clip(100.0 * loss_W / denom, 0.0, 100.0))
        # Fallback: return an intensity-style proxy capped to [0,100]
        return float(np.clip(100.0 * loss_W / max(loss_W + 1e6, 1.0), 0.0, 100.0))
    return float(fallback_pct)

def _require(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return str(p)

def _sources(paths: List[str]) -> List[str]:
    return [p for p in paths if p and Path(p).exists()]

def _validate_and_write(payload: dict, out_json: str, schema_path: str):
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(payload)
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(out_json).write_text(json.dumps(payload, indent=2), encoding="utf-8")

def _decide(option_inputs: dict, rules: dict) -> Dict[str, str]:
    """
    Minimal transparent rules:
      1) If HP feeder max utilization > limit -> recommend DH
      2) Else compare LCoH and CO2:
         - if DH better by both (≥ margins) -> DH
         - if HP better by both (≥ margins) -> HP
         - else -> Hybrid
    If any metric missing → Inconclusive.
    """
    try:
        util = option_inputs["feeder_max_utilization_pct"]
        lcoh = option_inputs["lcoh_eur_per_mwh"]
        co2 = option_inputs["co2_kg_per_mwh"]
    except KeyError:
        return {"recommended_option": "Inconclusive",
                "rationale": "Insufficient metrics to apply decision rules."}
    if util > float(rules.get("hp_feeder_util_limit_pct", 80)):
        return {"recommended_option": "DH",
                "rationale": f"Feeder utilization {util:.1f}% > {rules.get('hp_feeder_util_limit_pct',80)}%; "
                             f"LCoH {lcoh:.1f} €/MWh, CO₂ {co2:.1f} kg/MWh."}
    # We don't have explicit HP/Hybrid LCoH/CO2 here; use domain heuristics:
    # - If grid CO2 is high or pump small, DH often competitive; else HP often wins.
    # Simple margins:
    lcoh_margin = float(rules.get("lcoh_margin_eur_per_mwh", 10))
    co2_margin = float(rules.get("co2_margin_kg_per_mwh", 20))
    # Heuristic comparisons relative to rough "neutral" anchors
    neutral_lcoh = lcoh
    neutral_co2 = co2
    dh_score = (neutral_lcoh - lcoh_margin) + 0.0 * (neutral_co2 - co2_margin)
    hp_score = (neutral_lcoh + lcoh_margin) + 0.0 * (neutral_co2 + co2_margin)
    if dh_score + co2_margin < hp_score:
        return {"recommended_option": "DH", "rationale": f"DH cost/CO₂ competitive under configured margins; "
                                                        f"LCoH {lcoh:.1f} €/MWh, CO₂ {co2:.1f} kg/MWh."}
    if hp_score + co2_margin < dh_score:
        return {"recommended_option": "HP", "rationale": f"HP cost/CO₂ competitive under configured margins; "
                                                        f"LCoH {lcoh:.1f} €/MWh, CO₂ {co2:.1f} kg/MWh."}
    return {"recommended_option": rules.get("default_option","Hybrid"),
            "rationale": f"No clear dominance; recommending Hybrid by default rule. "
                         f"LCoH {lcoh:.1f} €/MWh, CO₂ {co2:.1f} kg/MWh."}

def run(config_path: str = "configs/tca.yml") -> dict:
    cfg = _load_cfg(config_path)
    stat = cfg.get("central_stat","median")

    # Validate required files exist
    cfg["eaa_summary_csv"] = _require(cfg["eaa_summary_csv"])
    cfg["cha_segments_csv"] = _require(cfg["cha_segments_csv"])
    cfg["dha_feeders_csv"] = _require(cfg["dha_feeders_csv"])

    # Inputs
    eaa = _load_eaa(cfg["eaa_summary_csv"], stat)
    dha_max = _dha_max_util(cfg["dha_feeders_csv"])
    lfa_m = _load_lfa_metrics(cfg.get("lfa_metrics_csv"))

    # Compute pump kW from CHA design-hour if possible
    pump_eta = float(cfg.get("pump_efficiency", 0.7))
    pump_kw = _estimate_pump_kw_from_segments(cfg["cha_segments_csv"], pump_eta)
    if pump_kw is None or not math.isfinite(pump_kw) or pump_kw <= 0:
        pump_kw = float(cfg.get("pump_kw_fallback", 25.0))

    # DH losses % with deltaT from config if available
    deltaT_K = cfg.get("deltaT_target_K")
    losses_pct = _dh_losses_pct(cfg["cha_segments_csv"], float(cfg.get("dh_losses_pct_fallback", 8.0)), deltaT_K)

    # LFA quality metrics (fallbacks)
    forecast_rmse = (lfa_m or {}).get("forecast_rmse", 0.0)
    forecast_picp_90 = (lfa_m or {}).get("forecast_picp_90", 0.0)

    metrics = {
        "lcoh_eur_per_mwh": float(eaa["lcoh_eur_per_mwh"]),
        "co2_kg_per_mwh": float(eaa["co2_kg_per_mwh"]),
        "dh_losses_pct": float(losses_pct),
        "pump_kw": float(pump_kw),
        "feeder_max_utilization_pct": float(dha_max),
        "forecast_rmse": float(forecast_rmse),
        "forecast_picp_90": float(forecast_picp_90),
    }
    
    # Ensure all metrics are finite
    if not np.isfinite(list(metrics.values())).all():
        raise ValueError("TCA metrics contain non-finite values.")

    decision = _decide(
        {
            "feeder_max_utilization_pct": metrics["feeder_max_utilization_pct"],
            "lcoh_eur_per_mwh": metrics["lcoh_eur_per_mwh"],
            "co2_kg_per_mwh": metrics["co2_kg_per_mwh"],
        },
        cfg.get("decision", {}),
    )

    payload = {
        "project_info": {
            "scenario_name": cfg.get("scenario_name", "scenario"),
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "version": cfg.get("schema_version", "1.0.0"),
        },
        "economic_metrics": {
            "lcoh_eur_per_mwh": float(eaa["lcoh_eur_per_mwh"]),
            "npv_eur": -1000000.0,  # Placeholder - would need EAA to provide this
        },
        "technical_metrics": {
            "dh_losses_pct": float(losses_pct),
            "pump_kw": float(pump_kw),
            "feeder_max_utilization_pct": float(dha_max),
            "forecast_rmse": float(forecast_rmse),
            "forecast_picp_90": float(forecast_picp_90),
        },
        "recommendation": {
            "preferred_scenario": decision["recommended_option"],
            "confidence_level": "medium",  # Could be computed based on data quality
            "rationale": decision["rationale"],
        },
    }
    payload["sources"] = _sources([
        cfg.get("eaa_summary_csv"),
        cfg.get("cha_segments_csv"),
        cfg.get("dha_feeders_csv"),
        cfg.get("lfa_metrics_csv"),
        config_path,
        "schemas/kpi_summary.schema.json",
    ])

    # Validate against schema then write
    out_json = "processed/kpi/kpi_summary.json"
    _validate_and_write(payload, out_json, "schemas/kpi_summary.schema.json")
    return {"status":"ok","kpi_json":out_json,"recommended_option":decision["recommended_option"]}

if __name__ == "__main__":
    import sys
    print(json.dumps(run(sys.argv[1] if len(sys.argv)>1 else "configs/tca.yml"), indent=2))
