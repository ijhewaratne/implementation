"""District heating cost modelling utilities for Branitz AI."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Any, Dict

from .core import annualize_capex, present_value_of_annuity


def _load_default_cost_params() -> Dict[str, Any]:
    """Return the default DH cost parameters, falling back if imports fail."""

    try:  # pragma: no cover - optional import guarded to avoid pandapipes dependency
        from branitz_ai.simulators.cha_pandapipes import (  # type: ignore
            DEFAULT_COST_PARAMS as CHA_DEFAULT_COST_PARAMS,
        )

        return dict(CHA_DEFAULT_COST_PARAMS)
    except Exception:  # pragma: no cover - fallback when simulator deps unavailable
        return {
            "capex_dh_eur_per_meter": 400.0,
            "opex_factor": 0.02,
            "discount_rate": 0.05,
            "project_lifetime": 30,
            "biomass_price_eur_per_kwh": 0.08,
        }


def compute_dh_costs(kpi: Mapping[str, object]) -> MutableMapping[str, float]:
    """Derive DH economic indicators from a CHA KPI payload."""

    if not isinstance(kpi, Mapping):
        raise TypeError("kpi must be a mapping of KPI values.")

    raw_results = kpi.get("raw_results")
    economics = {}
    if isinstance(raw_results, Mapping):
        econ_candidate = raw_results.get("economics")
        if isinstance(econ_candidate, Mapping):
            economics = dict(econ_candidate)

    network_length_m = kpi.get("network_length_m")
    if network_length_m is None:
        network_length_m = economics.get("network_length_m")
    total_heat_mwh = kpi.get("total_heat_mwh")
    if total_heat_mwh is None:
        total_heat_mwh = economics.get("annual_heat_mwh")

    network_length_m = float(network_length_m or 0.0)
    total_heat_mwh = float(total_heat_mwh or 0.0)

    cost_params_input = {}
    provided_params = kpi.get("cost_params")
    if isinstance(provided_params, Mapping):
        cost_params_input = dict(provided_params)

    cost_params = _load_default_cost_params()
    cost_params.update(cost_params_input)

    capex_per_meter = float(cost_params.get("capex_dh_eur_per_meter", 0.0))
    opex_factor = float(cost_params.get("opex_factor", 0.0))
    discount_rate = float(cost_params.get("discount_rate", 0.0))
    lifetime_years = int(cost_params.get("project_lifetime", 0) or 0)
    biomass_price = float(cost_params.get("biomass_price_eur_per_kwh", 0.0))

    capex_eur = network_length_m * capex_per_meter
    annual_opex_eur = capex_eur * opex_factor
    annual_heat_kwh = total_heat_mwh * 1000.0
    annual_energy_costs_eur = annual_heat_kwh * biomass_price

    if lifetime_years > 0:
        annualized_capex_eur = annualize_capex(capex_eur, discount_rate, lifetime_years)
        annualized_total_cost_eur = (
            annualized_capex_eur + annual_opex_eur + annual_energy_costs_eur
        )
        npv_total_cost_eur = present_value_of_annuity(
            annualized_total_cost_eur, discount_rate, lifetime_years
        )
    else:
        annualized_capex_eur = 0.0
        annualized_total_cost_eur = capex_eur + annual_opex_eur + annual_energy_costs_eur
        npv_total_cost_eur = annualized_total_cost_eur

    lcoh_eur_per_mwh = (
        annualized_total_cost_eur / max(total_heat_mwh, 1e-6)
        if total_heat_mwh > 0.0
        else float("inf")
    )

    return {
        "capex_eur": capex_eur,
        "annual_opex_eur": annual_opex_eur,
        "annual_energy_costs_eur": annual_energy_costs_eur,
        "annualized_capex_eur": annualized_capex_eur,
        "annualized_total_cost_eur": annualized_total_cost_eur,
        "lcoh_eur_per_mwh": lcoh_eur_per_mwh,
        "npv_total_cost_eur": npv_total_cost_eur,
        "cost_params_used": cost_params,
    }


__all__ = ["compute_dh_costs"]

