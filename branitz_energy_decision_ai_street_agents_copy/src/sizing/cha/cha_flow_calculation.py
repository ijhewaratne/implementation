"""
Flow-calculation helpers adapted from the CHA tooling.

These utilities convert building heat demand into design mass flows and
aggregate them along a supplied network topology dictionary.  The logic is
intentionally lightweight so it can be reused inside the agent workflow
without pulling the entire legacy CHA stack.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import math


@dataclass
class FlowCalculationResult:
    """Result for a single building."""

    building_id: str
    peak_heat_demand_kw: float
    design_heat_demand_kw: float
    mass_flow_kg_s: float
    volume_flow_m3_s: float


@dataclass
class NetworkFlowResult:
    """Aggregated flow information for a network element (pipe)."""

    pipe_id: str
    aggregated_flow_kg_s: float
    connected_buildings: List[str]
    pipe_category: str


class CHAFlowCalculationEngine:
    """
    Convert heat demand values into district-heating flow rates.

    Parameters are configurable to match scenario settings (supply/return
    temperature, safety factor, etc.).
    """

    def __init__(
        self,
        supply_temperature_c: float = 70.0,
        return_temperature_c: float = 40.0,
        safety_factor: float = 1.1,
        diversity_factor: float = 0.8,
    ) -> None:
        self.supply_temperature_c = supply_temperature_c
        self.return_temperature_c = return_temperature_c
        self.safety_factor = safety_factor
        self.diversity_factor = diversity_factor

        # Water properties around 70°C
        self._water_density_kg_m3 = 977.8
        self._water_specific_heat_j_per_kgk = 4180.0

    # --------------------------------------------------------------------- #
    # Building-level flow calculation
    # --------------------------------------------------------------------- #

    def calculate_building_flows(
        self,
        building_heat_kw: Dict[str, float],
    ) -> Dict[str, FlowCalculationResult]:
        """
        Compute design mass flow for each building.

        Args:
            building_heat_kw: map of building_id -> peak heat demand in kW.

        Returns:
            Dict mapping building_id to FlowCalculationResult.
        """
        results: Dict[str, FlowCalculationResult] = {}

        for building_id, peak_heat_kw in building_heat_kw.items():
            peak_heat_kw = max(0.0, float(peak_heat_kw))
            design_heat_kw = peak_heat_kw * self.safety_factor
            mass_flow = self.heat_kw_to_mass_flow(design_heat_kw)
            volume_flow = mass_flow / self._water_density_kg_m3

            results[building_id] = FlowCalculationResult(
                building_id=building_id,
                peak_heat_demand_kw=peak_heat_kw,
                design_heat_demand_kw=design_heat_kw,
                mass_flow_kg_s=mass_flow,
                volume_flow_m3_s=volume_flow,
            )

        return results

    def heat_kw_to_mass_flow(self, heat_kw: float) -> float:
        """Convert heat demand (kW) to mass flow (kg/s)."""
        if heat_kw <= 0.0:
            return 0.0
        delta_t = max(1.0, self.supply_temperature_c - self.return_temperature_c)
        heat_w = heat_kw * 1000.0
        return heat_w / (self._water_specific_heat_j_per_kgk * delta_t)

    # --------------------------------------------------------------------- #
    # Network aggregation
    # --------------------------------------------------------------------- #

    def aggregate_network_flows(
        self,
        building_flows: Dict[str, FlowCalculationResult],
        pipe_building_map: Dict[str, Iterable[str]],
    ) -> Dict[str, NetworkFlowResult]:
        """
        Aggregate flows for each pipe based on attached buildings.

        Args:
            building_flows: per-building flow results.
            pipe_building_map: mapping of pipe_id -> iterable of building IDs
                whose demand travels through that pipe.  For a tree, this
                usually means all downstream buildings.

        Returns:
            Dict mapping pipe_id -> NetworkFlowResult.
        """
        aggregated: Dict[str, NetworkFlowResult] = {}

        for pipe_id, building_ids in pipe_building_map.items():
            connected = list(building_ids)
            total_mass_flow = sum(
                building_flows[b_id].mass_flow_kg_s
                for b_id in connected
                if b_id in building_flows
            )

            if len(connected) > 1:
                total_mass_flow *= self.diversity_factor

            pipe_category = self._categorize_pipe(total_mass_flow)

            aggregated[pipe_id] = NetworkFlowResult(
                pipe_id=pipe_id,
                aggregated_flow_kg_s=total_mass_flow,
                connected_buildings=connected,
                pipe_category=pipe_category,
            )

        return aggregated

    @staticmethod
    def _categorize_pipe(flow_kg_s: float) -> str:
        """Simple category heuristic based on aggregated flow."""
        if flow_kg_s < 2.0:
            return "service_connection"
        if flow_kg_s < 20.0:
            return "distribution_pipe"
        return "main_pipe"

