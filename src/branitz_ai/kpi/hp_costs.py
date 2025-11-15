"""Heat pump and LV reinforcement cost modelling utilities.

The functions in this module consolidate cost logic previously scattered across
``branitz_energy_decision_ai_street_final/src/dha.py``,
``branitz_energy_decision_ai_street_final/src/lv_feeder_analyzer.py`` and the
Google ADK simulator fork. The new API mirrors the DH cost helpers so the
planner can swap between pathways with consistent KPI assumptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .core import (
    annualize_capex,
    compute_lcoh,
    present_value_of_annuity,
)


@dataclass
class HPSystemCostInputs:
    """Inputs describing a heat-pump + LV reinforcement investment scenario."""

    annual_heat_kwh: float
    annual_el_kwh: float
    hp_capex_eur: float
    lv_reinforcement_capex_eur: float
    electricity_price_eur_per_kwh: float
    lifetime_years: int
    discount_rate: float


@dataclass
class HPSystemCostResult:
    """Aggregated KPIs for a heat-pump pathway."""

    lcoh_eur_per_mwh: float
    npv_total_cost_eur: float
    annualized_cost_eur_per_year: float
    details: Dict[str, Any]


def compute_hp_system_cost(inputs: HPSystemCostInputs) -> HPSystemCostResult:
    """Return LCoH and NPV metrics for a HP + LV reinforcement setup.

    The total CAPEX is treated as an upfront cost (heat pump hardware, service
    connections, and LV reinforcements such as cable or transformer upgrades),
    while electricity costs remain an annual OPEX stream. Any finer-grained unit
    costs (e.g. €/kW heat pump, €/m feeder upgrade, €/transformer step) should
    be aggregated prior to calling this function—typically by reading external
    configuration tables or scenario JSON files.

    Example
    -------
    >>> result = compute_hp_system_cost(
    ...     HPSystemCostInputs(
    ...         annual_heat_kwh=180_000,
    ...         annual_el_kwh=60_000,
    ...         hp_capex_eur=250_000,
    ...         lv_reinforcement_capex_eur=120_000,
    ...         electricity_price_eur_per_kwh=0.32,
    ...         lifetime_years=20,
    ...         discount_rate=0.04,
    ...     )
    ... )
    >>> round(result.lcoh_eur_per_mwh, 1)
    132.3
    """

    annual_heat_mwh = inputs.annual_heat_kwh / 1000.0
    total_capex = max(inputs.hp_capex_eur, 0.0) + max(inputs.lv_reinforcement_capex_eur, 0.0)
    annual_opex = max(inputs.annual_el_kwh, 0.0) * max(inputs.electricity_price_eur_per_kwh, 0.0)

    annualized_capex = annualize_capex(total_capex, inputs.discount_rate, inputs.lifetime_years)
    annual_total_cost = annualized_capex + annual_opex

    lcoh = compute_lcoh(
        total_capex,
        annual_opex,
        annual_heat_mwh,
        inputs.discount_rate,
        inputs.lifetime_years,
    )

    npv_opex = present_value_of_annuity(annual_opex, inputs.discount_rate, inputs.lifetime_years)
    npv_total_cost = total_capex + npv_opex

    details: Dict[str, Any] = {
        "annual_heat_mwh": annual_heat_mwh,
        "total_capex_eur": total_capex,
        "annual_opex_eur": annual_opex,
        "annualized_capex_eur": annualized_capex,
        "annualized_total_cost_eur": annual_total_cost,
        "npv_opex_eur": npv_opex,
    }

    return HPSystemCostResult(
        lcoh_eur_per_mwh=float(lcoh),
        npv_total_cost_eur=float(npv_total_cost),
        annualized_cost_eur_per_year=float(annual_total_cost),
        details=details,
    )


__all__ = [
    "HPSystemCostInputs",
    "HPSystemCostResult",
    "compute_hp_system_cost",
]
