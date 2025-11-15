"""Core KPI aggregation utilities.

This module now hosts common financial helpers used by both CHA and DHA
pipelines. The functions mirror the annuity-style cost modelling found in the
legacy cost calculators (see
``Branitz_energy_decision_ai_street_final/src/cha_cost_benefit_analyzer.py`` and
``DH_New/branitz_dh/dh_core/costs.py``).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, MutableMapping
from typing import Any, Dict, List, Optional


def aggregate(simulation_results: Iterable[Mapping[str, object]]) -> MutableMapping[str, object]:
    """Aggregate per-scenario KPI payloads into a consolidated summary."""

    scenarios: List[Dict[str, Any]] = []
    best_lcoh_value: Optional[float] = None
    best_lcoh_id: Optional[str] = None
    best_co2_value: Optional[float] = None
    best_co2_id: Optional[str] = None
    lcoh_values: List[float] = []
    co2_values: List[float] = []

    for index, result in enumerate(simulation_results):
        if not isinstance(result, Mapping):
            continue

        payload = dict(result)
        scenario_id = payload.get("scenario_id")
        if not scenario_id:
            scenario_id = f"scenario_{index}"

        metrics = {key: value for key, value in payload.items() if key != "scenario_id"}
        scenarios.append({"scenario_id": scenario_id, "metrics": metrics})

        lcoh = metrics.get("lcoh_eur_per_mwh")
        if isinstance(lcoh, (int, float)):
            lcoh_float = float(lcoh)
            lcoh_values.append(lcoh_float)
            if best_lcoh_value is None or lcoh_float < best_lcoh_value:
                best_lcoh_value = lcoh_float
                best_lcoh_id = scenario_id

        co2 = metrics.get("annual_co2_tons")
        if isinstance(co2, (int, float)):
            co2_float = float(co2)
            co2_values.append(co2_float)
            if best_co2_value is None or co2_float < best_co2_value:
                best_co2_value = co2_float
                best_co2_id = scenario_id

    summary: Dict[str, Any] = {"num_scenarios": len(scenarios)}
    if lcoh_values:
        summary["min_lcoh_eur_per_mwh"] = min(lcoh_values)
        summary["max_lcoh_eur_per_mwh"] = max(lcoh_values)
    if co2_values:
        summary["min_annual_co2_tons"] = min(co2_values)
        summary["max_annual_co2_tons"] = max(co2_values)

    return {
        "scenarios": scenarios,
        "best_lcoh_scenario_id": best_lcoh_id,
        "best_co2_scenario_id": best_co2_id,
        "summary": summary,
    }


def summarize_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Return a placeholder KPI summary for the given simulation results."""

    # TODO: Aggregate KPIs once migration is complete.
    return {"status": "pending"}


def annuity_factor(discount_rate: float, lifetime_years: int) -> float:
    """Return the annuity factor for a cash flow over ``lifetime_years`` years.

    The implementation follows the standard discounted annuity formula and
    matches the approach historically used across the Branitz DH and HP
    calculators. A zero discount rate falls back to a straight-line average.
    """

    if lifetime_years <= 0:
        raise ValueError("lifetime_years must be positive.")
    if discount_rate <= -1.0:
        raise ValueError("discount_rate must be greater than -1.0.")

    if abs(discount_rate) < 1e-9:
        return 1.0 / float(lifetime_years)

    growth = 1.0 + discount_rate
    numerator = growth**lifetime_years * discount_rate
    denominator = growth**lifetime_years - 1.0
    return numerator / denominator


def annualize_capex(total_capex_eur: float, discount_rate: float, lifetime_years: int) -> float:
    """Convert an upfront CAPEX into an equivalent annual payment."""

    if total_capex_eur < 0.0:
        raise ValueError("total_capex_eur must be non-negative.")
    factor = annuity_factor(discount_rate, lifetime_years)
    return total_capex_eur * factor


def present_value_of_annuity(annual_cost_eur: float, discount_rate: float, lifetime_years: int) -> float:
    """Return the present value of an annual cost repeated over the project life."""

    if lifetime_years <= 0:
        raise ValueError("lifetime_years must be positive.")

    if abs(discount_rate) < 1e-9:
        return annual_cost_eur * float(lifetime_years)

    growth = 1.0 + discount_rate
    factor = (1.0 - growth**(-lifetime_years)) / discount_rate
    return annual_cost_eur * factor


def compute_lcoh(
    total_capex_eur: float,
    annual_opex_eur: float,
    annual_heat_supplied_mwh: float,
    discount_rate: float,
    lifetime_years: int,
) -> float:
    """Compute a levelized cost of heat (€/MWh) using an annuity formulation."""

    if annual_heat_supplied_mwh <= 0.0:
        return float("inf")

    annualized_capex = annualize_capex(total_capex_eur, discount_rate, lifetime_years)
    annual_total_cost = annualized_capex + max(annual_opex_eur, 0.0)
    return annual_total_cost / annual_heat_supplied_mwh


__all__ = [
    "aggregate",
    "summarize_results",
    "annuity_factor",
    "annualize_capex",
    "present_value_of_annuity",
    "compute_lcoh",
]
