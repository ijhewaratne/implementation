"""
High-level orchestrator combining flow calculation, pipe sizing, and
standards compliance.

This module wires together the trimmed CHA components so the agent
workflow can invoke a single entry-point when pipe sizing is required.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional

from .cha_flow_calculation import (
    CHAFlowCalculationEngine,
    FlowCalculationResult,
    NetworkFlowResult,
)
from .cha_network_hierarchy import CHANetworkHierarchyManager, NetworkPipeDescription
from .cha_pipe_sizing import CHAPipeSizingEngine, PipeSizingResult
from .cha_standards_compliance import CHAStandardsComplianceEngine, ComplianceResult


@dataclass
class SizingOutputs:
    """Container returned by ``CHAIntelligentSizing.run``."""

    building_flows: Dict[str, FlowCalculationResult]
    network_flows: Dict[str, NetworkFlowResult]
    pipe_sizing: Dict[str, PipeSizingResult]
    compliance: Dict[str, ComplianceResult]


class CHAIntelligentSizing:
    """
    Glue layer that mirrors the behaviour of the CHA intelligent sizing
    pipeline but with a simplified interface.
    """

    def __init__(
        self,
        flow_engine: Optional[CHAFlowCalculationEngine] = None,
        sizing_engine: Optional[CHAPipeSizingEngine] = None,
        compliance_engine: Optional[CHAStandardsComplianceEngine] = None,
    ) -> None:
        self.flow_engine = flow_engine or CHAFlowCalculationEngine()
        self.sizing_engine = sizing_engine or CHAPipeSizingEngine()
        self.compliance_engine = compliance_engine or CHAStandardsComplianceEngine()
        self.network_manager = CHANetworkHierarchyManager()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def run(
        self,
        building_heat_kw: Dict[str, float],
        pipes: Iterable[NetworkPipeDescription],
        pipe_building_map: Optional[Mapping[str, Iterable[str]]] = None,
    ) -> SizingOutputs:
        """
        Execute the complete sizing workflow.

        Args:
            building_heat_kw: map of building ID -> peak heat demand (kW).
            pipes: iterable describing the pipes that form the network.
            pipe_building_map: optional mapping of pipe -> downstream building
                IDs.  If omitted, the manager uses the data bundled inside
                ``pipes``.
        """
        self.network_manager.clear()
        self.network_manager.bulk_register(pipes)

        # ------------------------------------------------------------------
        # Step 1: per-building flows
        # ------------------------------------------------------------------
        building_flows = self.flow_engine.calculate_building_flows(building_heat_kw)

        # ------------------------------------------------------------------
        # Step 2: aggregated flows per pipe
        # ------------------------------------------------------------------
        if pipe_building_map is None:
            map_for_aggregation = self.network_manager.pipe_building_map()
        else:
            map_for_aggregation = {
                pipe_id: list(building_ids)
                for pipe_id, building_ids in pipe_building_map.items()
            }
            # Update registered pipes with any additional associations
            for pipe_id, building_ids in map_for_aggregation.items():
                if pipe_id in self.network_manager.pipes:
                    self.network_manager.pipes[pipe_id].connected_buildings.update(
                        str(b) for b in building_ids
                    )

        network_flows = self.flow_engine.aggregate_network_flows(
            building_flows,
            map_for_aggregation,
        )

        # ------------------------------------------------------------------
        # Step 3: pipe sizing + compliance
        # ------------------------------------------------------------------
        pipe_results: Dict[str, PipeSizingResult] = {}
        compliance_results: Dict[str, ComplianceResult] = {}

        for pipe_id, flow_result in network_flows.items():
            descriptor = self.network_manager.pipes.get(pipe_id)
            length_m = descriptor.length_m if descriptor else 1.0
            pipe_type = descriptor.pipe_type if descriptor else "supply"

            sizing_result = self.sizing_engine.size_pipe(
                pipe_id=pipe_id,
                flow_rate_kg_s=flow_result.aggregated_flow_kg_s,
                length_m=length_m,
                pipe_category=flow_result.pipe_category,
            )
            pipe_results[pipe_id] = sizing_result

            compliance = self.compliance_engine.validate_pipe(
                pipe_id=pipe_id,
                pipe_category=flow_result.pipe_category,
                velocity_ms=sizing_result.velocity_ms,
                pressure_drop_pa_per_m=sizing_result.pressure_drop_pa_per_m,
            )
            compliance_results[pipe_id] = compliance

        return SizingOutputs(
            building_flows=building_flows,
            network_flows=network_flows,
            pipe_sizing=pipe_results,
            compliance=compliance_results,
        )

