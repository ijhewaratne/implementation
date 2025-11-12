# src/kpi_calculator.py

import argparse
import json
from pathlib import Path
import pandas as pd

DEFAULT_COST_PARAMS = {
    "heat_pump_cop": 3.5,
    "elec_price_eur_per_kwh": 0.35,
    "biomass_price_eur_per_kwh": 0.07,
    "capex_hp_eur": 14000,
    "capex_dh_eur_per_meter": 800,
    "opex_factor": 0.01,  # O&M as percent of capex per year
    "discount_rate": 0.04,
    "project_lifetime": 20,
}

DEFAULT_EMISSIONS = {
    "grid_electricity_gco2_per_kwh": 290,
    "biomass_gco2_per_kwh": 70,
}


def compute_lcoh(total_costs_eur, total_heat_supplied_mwh, discount_rate, lifetime):
    """
    Simple NPV-based Levelized Cost of Heat (LCoH, €/MWh).
    """
    if total_heat_supplied_mwh == 0:
        return float("inf")
    # Annuitization factor (fixed capital recovery)
    q = 1 + discount_rate
    ann_factor = (q**lifetime * discount_rate) / (q**lifetime - 1)
    annualized_costs = total_costs_eur * ann_factor
    lcoh = annualized_costs / total_heat_supplied_mwh
    return lcoh


def compute_co2_emissions(energy_kwh, fuel_type, emissions_factors):
    """
    Returns emissions in tCO2 (tonnes).
    """
    if fuel_type == "electricity":
        gco2_per_kwh = emissions_factors.get("grid_electricity_gco2_per_kwh", 290)
    elif fuel_type == "biomass":
        gco2_per_kwh = emissions_factors.get("biomass_gco2_per_kwh", 70)
    else:
        gco2_per_kwh = 400  # fallback for fossil
    return (energy_kwh * gco2_per_kwh) / 1e6  # [tCO2]


def compute_kpis(sim_results, cost_params=None, emissions_factors=None):
    """
    Aggregate KPIs for all simulation results.
    
    Updated to handle both old placeholder format and new SimulationResult format
    with detailed KPIs from real pandapipes/pandapower simulations.
    
    Returns a DataFrame of scenario KPIs with economic and environmental metrics.
    """
    cost_params = cost_params or DEFAULT_COST_PARAMS
    emissions_factors = emissions_factors or DEFAULT_EMISSIONS
    kpi_records = []

    for res in sim_results:
        if not res.get("success", False):
            kpi_records.append(
                {
                    "scenario": res.get("scenario", ""),
                    "type": res.get("type", ""),
                    "simulation_mode": res.get("mode", "unknown"),
                    "lcoh_eur_per_mwh": None,
                    "co2_t_per_a": None,
                    "comment": res.get("error", "simulation failed"),
                }
            )
            continue

        if res.get("type") == "DH":
            # District Heating (pandapipes) - Enhanced with new KPIs
            kpi = res.get("kpi", {})
            
            # Heat supply
            heat_supplied_mwh = kpi.get("total_heat_supplied_mwh", 0)
            pump_energy_kwh = kpi.get("pump_energy_kwh", 0)
            
            # Network metrics (use new detailed KPIs if available)
            total_pipe_length_km = kpi.get("total_pipe_length_km", 3.0)
            length_network_m = total_pipe_length_km * 1000
            num_consumers = kpi.get("num_consumers", 50)
            
            # Cost calculation
            capex = length_network_m * cost_params["capex_dh_eur_per_meter"]
            opex = capex * cost_params["opex_factor"] * cost_params["project_lifetime"]
            energy_costs = heat_supplied_mwh * 1000 * cost_params["biomass_price_eur_per_kwh"]
            total_costs = capex + opex + energy_costs
            
            lcoh = compute_lcoh(
                total_costs,
                heat_supplied_mwh,
                cost_params["discount_rate"],
                cost_params["project_lifetime"],
            )
            
            # Emissions
            co2 = compute_co2_emissions(
                heat_supplied_mwh * 1000, "biomass", emissions_factors
            ) + compute_co2_emissions(pump_energy_kwh, "electricity", emissions_factors)
            
            # Build enhanced KPI record with new detailed metrics
            kpi_record = {
                    "scenario": res.get("scenario", ""),
                    "type": "DH",
                "simulation_mode": res.get("mode", "unknown"),
                    "lcoh_eur_per_mwh": round(lcoh, 2),
                    "co2_t_per_a": round(co2, 2),
                
                # Thermal metrics (NEW)
                "total_heat_supplied_mwh": round(heat_supplied_mwh, 2),
                "peak_heat_load_kw": kpi.get("peak_heat_load_kw"),
                "network_heat_loss_kwh": kpi.get("network_heat_loss_kwh"),
                "heat_loss_percentage": kpi.get("heat_loss_percentage"),
                
                # Hydraulic metrics (ENHANCED)
                "max_pressure_drop_bar": kpi.get("max_pressure_drop_bar"),
                "avg_pressure_drop_bar": kpi.get("avg_pressure_drop_bar"),
                    "pump_energy_kwh": pump_energy_kwh,
                
                # Thermal performance (NEW)
                "min_supply_temp_c": kpi.get("min_supply_temp_c"),
                "avg_supply_temp_c": kpi.get("avg_supply_temp_c"),
                
                # Network metrics (ENHANCED)
                "num_junctions": kpi.get("num_junctions"),
                "num_pipes": kpi.get("num_pipes"),
                "num_consumers": num_consumers,
                "total_pipe_length_km": total_pipe_length_km,
                
                    "comment": "",
                }
            kpi_records.append(kpi_record)
            
        elif res.get("type") == "HP":
            # Heat Pump (pandapower) - Enhanced with new KPIs
            kpi = res.get("kpi", {})
            
            # Load metrics (use new detailed KPIs if available)
            total_load_mw = kpi.get("total_load_mw", 0)
            num_loads = kpi.get("num_loads", 50)
            
            # Calculate heat supplied from electrical load
            # HP electrical load is part of total_load_mw
            # Estimate: HP_electric = total - base, HP_thermal = HP_electric * COP
            hp_elec_kwh = total_load_mw * 1000 * 8760  # Annual (rough estimate)
            hp_energy_mwh = (hp_elec_kwh * cost_params["heat_pump_cop"]) / 1000
            
            # Cost calculation
            capex = cost_params["capex_hp_eur"] * num_loads
            opex = capex * cost_params["opex_factor"] * cost_params["project_lifetime"]
            energy_costs = hp_elec_kwh * cost_params["elec_price_eur_per_kwh"]
            total_costs = capex + opex + energy_costs
            
            lcoh = compute_lcoh(
                total_costs,
                hp_energy_mwh,
                cost_params["discount_rate"],
                cost_params["project_lifetime"],
            )
            
            # Emissions
            co2 = compute_co2_emissions(hp_elec_kwh, "electricity", emissions_factors)
            
            # Build enhanced KPI record with new detailed metrics
            kpi_record = {
                    "scenario": res.get("scenario", ""),
                    "type": "HP",
                "simulation_mode": res.get("mode", "unknown"),
                    "lcoh_eur_per_mwh": round(lcoh, 2),
                    "co2_t_per_a": round(co2, 2),
                
                # Voltage metrics (NEW)
                "min_voltage_pu": kpi.get("min_voltage_pu"),
                "max_voltage_pu": kpi.get("max_voltage_pu"),
                "avg_voltage_pu": kpi.get("avg_voltage_pu"),
                "voltage_violations": kpi.get("voltage_violations"),
                
                # Loading metrics (ENHANCED)
                "max_line_loading_pct": kpi.get("max_line_loading_pct"),
                "avg_line_loading_pct": kpi.get("avg_line_loading_pct"),
                "overloaded_lines": kpi.get("overloaded_lines"),
                
                # Transformer metrics (ENHANCED)
                "transformer_loading_pct": kpi.get("transformer_loading_pct"),
                "transformer_overloaded": kpi.get("transformer_overloaded"),
                
                # Load and loss metrics (NEW)
                "total_load_mw": total_load_mw,
                "total_losses_mw": kpi.get("total_losses_mw"),
                "loss_percentage": kpi.get("loss_percentage"),
                
                # Network metrics (NEW)
                "num_buses": kpi.get("num_buses"),
                "num_lines": kpi.get("num_lines"),
                "num_loads": num_loads,
                
                    "comment": "",
                }
            kpi_records.append(kpi_record)
        else:
            kpi_records.append(
                {
                    "scenario": res.get("scenario", ""),
                    "type": res.get("type", ""),
                    "simulation_mode": res.get("mode", "unknown"),
                    "lcoh_eur_per_mwh": None,
                    "co2_t_per_a": None,
                    "comment": "Unknown scenario type",
                }
            )

    return pd.DataFrame(kpi_records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Aggregate and compute KPIs from simulation results."
    )
    parser.add_argument(
        "--results", nargs="+", required=True, help="List of simulation results JSON files"
    )
    parser.add_argument("--cost_params", default=None, help="Cost params JSON (optional)")
    parser.add_argument(
        "--emissions_factors", default=None, help="Emissions factors JSON (optional)"
    )
    parser.add_argument(
        "--output_csv", default="results/scenario_kpis.csv", help="Summary output CSV"
    )
    parser.add_argument(
        "--output_json", default="results/scenario_kpis.json", help="Summary output JSON"
    )
    args = parser.parse_args()

    # Load simulation results
    sim_results = []
    for rf in args.results:
        with open(rf, "r", encoding="utf-8") as f:
            sim_results.append(json.load(f))

    # Load params if provided
    cost_params = DEFAULT_COST_PARAMS
    emissions_factors = DEFAULT_EMISSIONS
    if args.cost_params:
        with open(args.cost_params, "r", encoding="utf-8") as f:
            cost_params = json.load(f)
    if args.emissions_factors:
        with open(args.emissions_factors, "r", encoding="utf-8") as f:
            emissions_factors = json.load(f)

    # Compute KPIs and save
    kpi_df = compute_kpis(sim_results, cost_params, emissions_factors)
    Path("results").mkdir(exist_ok=True)
    kpi_df.to_csv(args.output_csv, index=False)
    kpi_df.to_json(args.output_json, orient="records", indent=2)
    print(f"KPI table written to {args.output_csv} and {args.output_json}")
