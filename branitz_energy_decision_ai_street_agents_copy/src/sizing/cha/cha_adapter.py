"""
Adapter utilities that turn the agent dual-topology into CHA sizing inputs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

from shapely.geometry import LineString

from .cha_flow_calculation import CHAFlowCalculationEngine
from .cha_intelligent_sizing import CHAIntelligentSizing, SizingOutputs
from .cha_network_hierarchy import NetworkPipeDescription


def run_cha_sizing_from_topology(
    dual_topology: Dict,
    supply_temp_c: float,
    return_temp_c: float,
) -> SizingOutputs:
    """
    Execute CHA sizing using the agent dual-topology structure.

    Returns:
        SizingOutputs with building flows, aggregated network flows,
        sizing, and compliance data.
    """
    building_heat = _extract_building_heat(dual_topology)
    supply_info, return_info = _compute_pipe_building_sets(dual_topology)
    service_info = _collect_service_info(dual_topology)

    pipe_descriptions: List[NetworkPipeDescription] = []
    for pipe_id, info in supply_info.items():
        pipe_descriptions.append(
            NetworkPipeDescription(
                pipe_id=pipe_id,
                length_m=info.length_m,
                pipe_type="supply",
                street_id=info.street_id,
                connected_buildings=info.buildings.copy(),
            )
        )
    for pipe_id, info in return_info.items():
        pipe_descriptions.append(
            NetworkPipeDescription(
                pipe_id=pipe_id,
                length_m=info.length_m,
                pipe_type="return",
                street_id=info.street_id,
                connected_buildings=info.buildings.copy(),
            )
        )
    for pipe_id, info in service_info.items():
        pipe_descriptions.append(
            NetworkPipeDescription(
                pipe_id=pipe_id,
                length_m=info.length_m,
                pipe_type="service",
                street_id=info.street_id,
                connected_buildings=info.buildings.copy(),
            )
        )

    sizing = CHAIntelligentSizing(
        flow_engine=CHAFlowCalculationEngine(
            supply_temperature_c=supply_temp_c,
            return_temperature_c=return_temp_c,
        )
    )
    return sizing.run(
        building_heat_kw=building_heat,
        pipes=pipe_descriptions,
    )


def sizing_outputs_to_serializable(outputs: SizingOutputs) -> Dict:
    """Convert SizingOutputs into JSON-friendly dictionaries."""
    return {
        "building_flows": {
            building_id: asdict(result) for building_id, result in outputs.building_flows.items()
        },
        "network_flows": {
            pipe_id: asdict(result) for pipe_id, result in outputs.network_flows.items()
        },
        "pipe_sizing": {
            pipe_id: asdict(result) for pipe_id, result in outputs.pipe_sizing.items()
        },
        "compliance": {
            pipe_id: {
                "overall_compliant": result.overall_compliant,
                "standards_compliance": result.standards_compliance,
                "violations": [asdict(v) for v in result.violations],
            }
            for pipe_id, result in outputs.compliance.items()
        },
    }


# --------------------------------------------------------------------------- #
# internal helpers
# --------------------------------------------------------------------------- #

def _extract_building_heat(dual_topology: Dict) -> Dict[str, float]:
    building_heat: Dict[str, float] = {}
    for consumer in dual_topology.get("consumers", []):
        building_id = str(consumer.get("id"))
        heat_kw = float(consumer.get("heat_demand_kw", 0.0) or 0.0)
        building_heat[building_id] = heat_kw
    return building_heat


@dataclass
class _PipeAggregate:
    length_m: float
    street_id: Optional[str]
    buildings: Set[str]


def _compute_pipe_building_sets(dual_topology: Dict) -> Tuple[Dict[str, _PipeAggregate], Dict[str, _PipeAggregate]]:
    """
    Determine downstream building sets for each supply/return pipe.

    The current dual_topology structure represents each pipe segment as part
    of a per-building route (as opposed to a merged tree).  This means each
    segment already corresponds to a single building's demand, so we can map
    pipes to that building directly.
    """
    supply_aggregates: Dict[str, _PipeAggregate] = {}
    return_aggregates: Dict[str, _PipeAggregate] = {}

    for pipe in dual_topology.get("pipes", []):
        pipe_id = str(pipe.get("id"))
        building_id = pipe.get("building_id")
        pipe_type = pipe.get("type")
        length = float(pipe.get("length_m") or _line_length(pipe.get("coords")))
        street_id = pipe.get("street_id")
        buildings = {str(building_id)} if building_id is not None else set()

        aggregate = _PipeAggregate(
            length_m=length,
            street_id=street_id,
            buildings=buildings,
        )

        if pipe_type == "supply":
            supply_aggregates[pipe_id] = aggregate
        elif pipe_type == "return":
            return_aggregates[pipe_id] = aggregate

    return supply_aggregates, return_aggregates


def _collect_service_info(dual_topology: Dict) -> Dict[str, _PipeAggregate]:
    aggregates: Dict[str, _PipeAggregate] = {}
    for service in dual_topology.get("service_connections", []):
        if service.get("pipe_type") != "supply_service":
            continue
        building_id = str(service.get("building_id"))
        length = float(service.get("distance_to_street", 0.0) or 0.0)
        street_id = service.get("street_segment_id")
        aggregates[f"service_{building_id}"] = _PipeAggregate(
            length_m=max(length, 0.1),
            street_id=str(street_id) if street_id is not None else None,
            buildings={building_id},
        )
    return aggregates


def _line_length(coords: Optional[Iterable]) -> float:
    if not coords:
        return 0.0
    try:
        return LineString(coords).length
    except Exception:
        return 0.0

