"""
Monte Carlo Economics

Provides Monte Carlo simulation for NPV/LCoH distributions with deterministic seeding.
Now includes CO₂ sampling and P10/P50/P90 summaries.
"""

import math
import random
import pandas as pd
from typing import Dict, List, Tuple, Union
from optimize.cost_models import npv


def run_monte_carlo(
    assignment: Dict[str, int],
    segments_df: pd.DataFrame,
    design: Dict,
    econ: Dict,
    catalog_df: pd.DataFrame,
    n: int = 500,
    capex_sigma: float = 0.2,
    el_price_sigma: float = 0.25,
    # CO2 settings (means in tCO2/MWh, sigmas are lognormal std-devs)
    grid_co2_mean_t_per_MWh: float = 0.35,
    grid_co2_sigma: float = 0.15,
    heat_co2_mean_t_per_MWh: float = 0.20,
    heat_co2_sigma: float = 0.10,
    seed: int = 42,
) -> Dict:
    """
    Return dict with lists for npv, lcoh, pump_mwh, heat_loss_mwh, co2_tons and a 'summary'
    containing p10/p50/p90 for NPV and CO2.

    Deterministic seeding, lognormal perturbations around mean costs and emission factors.

    Args:
        assignment: seg_id -> DN chosen (only used here to map DN->costs).
        segments_df: contains per-segment data; if columns 'pump_MWh' or 'heat_loss_MWh'
                     exist they are used for base annual energy terms (else 0).
        design: (unused here, kept for API compatibility).
        econ: contains price_el [€/kWh el], cost_heat_prod [€/MWh th], years, r.
        catalog_df: at least columns ['dn', 'cost_eur_per_m'].
        n: number of Monte-Carlo trials (default 500).
        capex_sigma/el_price_sigma: lognormal sigmas for CapEx and electricity price.
        grid_co2_mean_t_per_MWh/heat_co2_mean_t_per_MWh: mean emission factors for electricity and heat.
        grid_co2_sigma/heat_co2_sigma: lognormal sigmas for emission factors.
        seed: deterministic seed.

    Returns:
        {
          "npv": List[float],
          "lcoh": List[float],
          "pump_mwh": List[float],         # repeated constant if derived from segments_df
          "heat_loss_mwh": List[float],    # repeated constant if derived from segments_df
          "co2_tons": List[float],
          "summary": {
             "npv_p10": float, "npv_p50": float, "npv_p90": float,
             "co2_p10": float, "co2_p50": float, "co2_p90": float
          }
        }
    """
    rnd = random.Random(seed)

    # derive base CapEx from catalog costs
    cost_map = {
        int(r["dn"]): float(r.get("cost_eur_per_m", 0.0))
        for _, r in catalog_df.iterrows() if "dn" in r
    }
    capex_base = 0.0
    for _, r in segments_df.iterrows():
        length = float(r.get("length_m", 0.0))
        dn = int(r.get("DN", 0))
        capex_base += length * float(cost_map.get(dn, 0.0))

    # base annual opex energy terms if provided
    pump_mwh = float(segments_df.get("pump_MWh", pd.Series([0.0])).sum())
    loss_mwh = float(segments_df.get("heat_loss_MWh", pd.Series([0.0])).sum())

    mean_el = float(econ.get("price_el", 0.25))         # €/kWh_el
    heat_cost = float(econ.get("cost_heat_prod", 55.0)) # €/MWh_th
    years = int(econ.get("years", 30))
    r = float(econ.get("r", 0.04))

    samples = []
    for i in range(n):
        # stochastic CapEx and electricity price
        capex = capex_base * rnd.lognormvariate(0.0, capex_sigma)
        el_price = mean_el * rnd.lognormvariate(0.0, el_price_sigma)

        # annual operating cost (energy + simple O&M as 1% CapEx)
        annual_cost = (pump_mwh * 1000.0 * el_price) + (loss_mwh * heat_cost) + 0.01 * capex

        pv = npv(capex, annual_cost, years, r)

        # rough LCoH proxy: €/MWh_tot over project lifetime
        denom = max(1.0, years * (pump_mwh + loss_mwh))
        lcoh = (pv / denom)

        # emission factors (lognormal positives)
        grid_factor = grid_co2_mean_t_per_MWh * rnd.lognormvariate(0.0, grid_co2_sigma)
        heat_factor = heat_co2_mean_t_per_MWh * rnd.lognormvariate(0.0, heat_co2_sigma)

        co2_tons = pump_mwh * grid_factor + loss_mwh * heat_factor

        samples.append({
            "trial": i,
            "npv": pv,
            "lcoh": lcoh,
            "pump_mwh": pump_mwh,
            "heat_loss_mwh": loss_mwh,
            "co2_tons": co2_tons,
        })

    df = pd.DataFrame(samples)

    # summaries
    npv_p10 = df["npv"].quantile(0.10)
    npv_p50 = df["npv"].quantile(0.50)
    npv_p90 = df["npv"].quantile(0.90)
    co2_p10 = df["co2_tons"].quantile(0.10)
    co2_p50 = df["co2_tons"].quantile(0.50)
    co2_p90 = df["co2_tons"].quantile(0.90)

    return {
        "npv": df["npv"].tolist(),
        "lcoh": df["lcoh"].tolist(),
        "pump_mwh": df["pump_mwh"].tolist(),
        "heat_loss_mwh": df["heat_loss_mwh"].tolist(),
        "co2_tons": df["co2_tons"].tolist(),
        "summary": {
            "npv_p10": npv_p10, "npv_p50": npv_p50, "npv_p90": npv_p90,
            "co2_p10": co2_p10, "co2_p50": co2_p50, "co2_p90": co2_p90,
        },
    } 