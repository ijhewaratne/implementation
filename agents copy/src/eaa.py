from __future__ import annotations
import json, glob
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

# ---------------- Helpers ----------------

def _read_annual_heat_mwh(lfa_glob: str) -> float | None:
    files = sorted(glob.glob(lfa_glob))
    if not files:
        return None
    total_kwh = 0.0
    for p in files:
        j = json.loads(Path(p).read_text(encoding="utf-8"))
        series = j.get("series") or []
        if len(series) != 8760:
            continue
        # series is kW per hour; sum→kWh
        total_kwh += float(np.sum(series))
    return total_kwh / 1000.0  # → MWh

def _annuity_factor(rate: float, years: int) -> float:
    r = float(rate)
    n = int(years)
    if r <= 0: return 1.0 / max(n, 1)
    return r * (1 + r) ** n / ((1 + r) ** n - 1)

def _lognormal_from_mean_rel_sigma(mean: float, rel_sigma: float, size: int, rng: np.random.Generator) -> np.ndarray:
    """
    Draw lognormal with given mean and relative sigma (std/mean).
    We solve for (mu, sigma) in log-space: mean = exp(mu + 0.5*sigma^2), var = (exp(sigma^2)-1)*exp(2mu+sigma^2)
    """
    m = float(mean)
    rs = max(float(rel_sigma), 1e-9)
    var = (rs * m) ** 2
    sigma2 = np.log(1.0 + var / (m ** 2))
    mu = np.log(m) - 0.5 * sigma2
    sigma = np.sqrt(sigma2)
    return rng.lognormal(mean=mu, sigma=sigma, size=size)

# ---------------- Core deterministic model ----------------

def _deterministic_inputs(cfg: dict) -> dict:
    seg = pd.read_csv(cfg["cha_segments"])  # needs length_m; may have pump_kW_contrib but we keep pump intensity from config
    feeders = pd.read_csv(cfg["dha_feeders"])  # feeder_id,hour,p_kw,utilization_pct...

    # total DH trench length (m)
    total_length_m = float(seg["length_m"].sum()) if "length_m" in seg.columns else 0.0

    # annual heat demand (MWh)
    annual_heat_mwh = _read_annual_heat_mwh(cfg.get("lfa_glob", "processed/lfa/*.json"))
    if annual_heat_mwh is None:
        annual_heat_mwh = float(cfg.get("annual_heat_mwh_fallback", 0.0))

    # annual electricity for DH pumping (MWh) with simple intensity (kWh/MWh_heat)
    pump_kwh_per_mwh = float(cfg.get("pump_kwh_per_mwh_heat", 15.0))
    dh_pump_mwh = (annual_heat_mwh * pump_kwh_per_mwh) / 1000.0

    # For HP scenario electric use, if you provide that elsewhere, integrate here. For EAA core we focus on DH KPIs.
    return {
        "total_length_m": total_length_m,
        "annual_heat_mwh": annual_heat_mwh,
        "dh_pump_mwh": dh_pump_mwh,
    }

# ---------------- Monte Carlo engine ----------------

def _run_mc(cfg: dict, det: dict) -> pd.DataFrame:
    n = int(max(cfg.get("mc_samples", 1000), 500))
    seed = int(cfg.get("random_seed", 42))
    rng = np.random.default_rng(seed)

    # Samples
    dh_cost_per_m = _lognormal_from_mean_rel_sigma(
        cfg["dh_cost_per_m_eur_mean"], cfg["dh_cost_per_m_eur_rel_sigma"], n, rng
    )
    elec_price = _lognormal_from_mean_rel_sigma(
        cfg["elec_price_eur_per_mwh_mean"], cfg["elec_price_eur_per_mwh_rel_sigma"], n, rng
    )
    grid_co2 = _lognormal_from_mean_rel_sigma(
        cfg["grid_co2_kg_per_mwh_mean"], cfg["grid_co2_kg_per_mwh_rel_sigma"], n, rng
    )

    # CapEx → annualized via annuity
    A = _annuity_factor(cfg.get("discount_rate", 0.07), int(cfg.get("lifetime_years", 30)))
    capex_dh = dh_cost_per_m * det["total_length_m"]
    annualized_capex = capex_dh * A

    # OpEx (pumping electricity)
    annual_pump_cost = det["dh_pump_mwh"] * elec_price
    annual_pump_co2 = det["dh_pump_mwh"] * grid_co2

    # LCoH (€/MWh) = (annualized capex + pump cost) / annual heat
    # CO2 intensity (kg/MWh) = annual pump CO2 / annual heat
    heat = max(det["annual_heat_mwh"], 1e-9)  # avoid div-by-zero
    lcoh = (annualized_capex + annual_pump_cost) / heat
    co2 = annual_pump_co2 / heat

    out = pd.DataFrame({
        "sample": np.arange(n, dtype=int),
        "dh_cost_per_m": dh_cost_per_m,
        "elec_price_eur_per_mwh": elec_price,
        "grid_co2_kg_per_mwh": grid_co2,
        "annualized_capex_eur": annualized_capex,
        "annual_pump_cost_eur": annual_pump_cost,
        "annual_pump_co2_kg": annual_pump_co2,
        "lcoh_eur_per_mwh": lcoh,
        "co2_kg_per_mwh": co2,
    })
    return out

def _summarize(mc: pd.DataFrame) -> pd.DataFrame:
    q = mc[["lcoh_eur_per_mwh","co2_kg_per_mwh"]]
    summary = pd.DataFrame({
        "metric": ["lcoh_eur_per_mwh","co2_kg_per_mwh"],
        "mean": q.mean().values,
        "median": q.median().values,
        "p2_5": q.quantile(0.025).values,
        "p97_5": q.quantile(0.975).values,
    })
    return summary

# ---------------- Public API ----------------

def run(config_path: str = "configs/eaa.yml") -> dict:
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    out_dir = Path(cfg.get("out_dir", "eval/te")); out_dir.mkdir(parents=True, exist_ok=True)

    det = _deterministic_inputs(cfg)
    mc = _run_mc(cfg, det)

    # Persist artifacts
    mc_path = out_dir / "mc.parquet"
    mc.to_parquet(mc_path, index=False)

    summary = _summarize(mc)
    # Guardrails: finite only
    if not np.isfinite(summary[["mean","median","p2_5","p97_5"]].values).all():
        raise RuntimeError("EAA: summary contains non-finite values.")
    summary_path = out_dir / "summary.csv"
    summary.to_csv(summary_path, index=False)

    return {
        "status": "ok",
        "mc_parquet": str(mc_path),
        "summary_csv": str(summary_path),
        "samples": int(len(mc)),
    }

if __name__ == "__main__":
    import sys
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "configs/eaa.yml"), indent=2))
