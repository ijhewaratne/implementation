"""Pandapipes-based district heating simulator for Branitz AI.

This module consolidates the legacy CHA pandapipes workflow from the street
agent prototypes into a reusable function.  It draws on the routing utilities
from ``branitz_energy_decision_ai_street_agents_copy`` and the enhanced
pandapipes helpers from ``Branitz_energy_decision_ai_street_final`` to provide a
single orchestrated entry-point.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points

try:  # pragma: no cover - import check
    import pandapipes as pp
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise ImportError(
        "pandapipes is required to run the CHA simulator."
    ) from exc

from branitz_energy_decision_ai_street_agents_copy.src.routing.dual_pipe import (
    build_dual_pipe_topology,
)
from branitz_energy_decision_ai_street_agents_copy.src.sizing.cha.cha_adapter import (
    run_cha_sizing_from_topology,
)
from branitz_energy_decision_ai_street_final.src.cha_standards_compliance import (
    CHAStandardsComplianceEngine,
)


TARGET_CRS = "EPSG:32633"
SPECIFIC_HEAT_WATER_J_PER_KG_K = 4186.0

DEFAULT_COST_PARAMS = {
    "capex_dh_eur_per_meter": 400.0,
    "opex_factor": 0.02,
    "discount_rate": 0.05,
    "project_lifetime": 30,
    "biomass_price_eur_per_kwh": 0.08,
}


@dataclass
class CHAScenarioConfig:
    """Configuration describing the inputs required to run a CHA simulation."""

    scenario_id: str
    data_root: str
    output_root: str
    supply_temperature: float
    return_temperature: float
    plant_node_id: str
    streets_file: str
    buildings_file: str
    supply_pressure_bar: float = 6.0
    connection_max_distance_m: float = 120.0
    load_column_kw: str = "heating_load_kw"
    annual_demand_column: str = "annual_heat_demand_kwh"
    fallback_design_hours: float = 2500.0
    pipe_cost_eur_per_m: float = 400.0
    opex_fraction_of_capex: float = 0.02
    asset_lifetime_years: int = 30
    discount_rate: float = 0.05
    co2_factor_kg_per_mwh: float = 180.0
    standards_payback_years: float = 12.0
    standards_lifecycle_cost_eur_per_mwh: float = 45.0
    standards_safety_factor: float = 2.5
    plant_coordinates: Optional[Tuple[float, float]] = None


@dataclass
class CHAKPIResult:
    """Summary of the CHA pandapipes run."""

    scenario_id: str
    lcoh_eur_per_mwh: float
    annual_co2_tons: float
    max_velocity_m_per_s: float
    max_pressure_drop_pa_per_m: float
    network_length_m: float
    raw_results: Dict[str, Any]


def run_cha_scenario(config: CHAScenarioConfig) -> CHAKPIResult:
    """Build the DH network, run pandapipes, validate standards, and compute KPIs."""

    buildings, streets = _load_geodata(config)
    plant_point = _determine_plant_location(buildings, config)
    connections_df = _compute_connections_df(buildings, streets, config, plant_point)

    dual_topology = build_dual_pipe_topology(
        buildings_gdf=buildings,
        streets_gdf=streets,
        plant_connection={"plant_x": plant_point.x, "plant_y": plant_point.y},
        supply_temp=config.supply_temperature,
        return_temp=config.return_temperature,
        supply_pressure=config.supply_pressure_bar,
        analysis={"method": "branitz_ai_nearest_street"},
        connections_df=connections_df,
    )

    sizing_outputs = run_cha_sizing_from_topology(
        dual_topology=dual_topology,
        supply_temp_c=config.supply_temperature,
        return_temp_c=config.return_temperature,
    )

    _apply_sizing_to_topology(
        dual_topology,
        sizing_outputs.pipe_sizing,
        sizing_outputs.compliance,
    )
    _update_stats_with_sizing(dual_topology.setdefault("stats", {}), dual_topology)

    compliance_detail, compliance_summary = _evaluate_standards(
        dual_topology,
        config,
    )

    net = _create_network_from_dual_topology(
        dual_topology,
        supply_temp_c=config.supply_temperature,
        return_temp_c=config.return_temperature,
        supply_pressure_bar=config.supply_pressure_bar,
    )

    simulation_results = _run_pandapipes(net)
    kpi_data = _extract_network_kpis(net, dual_topology)

    economics = _compute_economic_metrics(
        buildings,
        dual_topology,
        config,
    )

    max_velocity = _max_velocity_from_sizing(dual_topology)
    max_pressure_drop = _max_pressure_drop_from_sizing(dual_topology)
    network_length_m = _network_length_m(dual_topology)

    raw_results = {
        "simulation": simulation_results,
        "kpis": kpi_data,
        "economics": economics,
        "dual_topology": dual_topology,
        "standards": {
            "per_pipe": [asdict(res) for res in compliance_detail],
            "summary": asdict(compliance_summary),
        },
    }

    return CHAKPIResult(
        scenario_id=config.scenario_id,
        lcoh_eur_per_mwh=economics["lcoh_eur_per_mwh"],
        annual_co2_tons=economics["annual_co2_tons"],
        max_velocity_m_per_s=max_velocity,
        max_pressure_drop_pa_per_m=max_pressure_drop,
        network_length_m=network_length_m,
        raw_results=raw_results,
    )


# ---------------------------------------------------------------------------
# Helper functions (data preparation)
# ---------------------------------------------------------------------------

def _resolve_path(root: str, candidate: str) -> Path:
    path = Path(candidate)
    if not path.is_absolute():
        path = Path(root) / candidate
    return path


def _load_geodata(config: CHAScenarioConfig) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    buildings_path = _resolve_path(config.data_root, config.buildings_file)
    streets_path = _resolve_path(config.data_root, config.streets_file)

    buildings = gpd.read_file(buildings_path)
    streets = gpd.read_file(streets_path)

    if buildings.crs is None:
        buildings.set_crs("EPSG:4326", inplace=True)
    if streets.crs is None:
        streets.set_crs("EPSG:4326", inplace=True)

    if buildings.crs.to_string() != TARGET_CRS:
        buildings = buildings.to_crs(TARGET_CRS)
    if streets.crs.to_string() != TARGET_CRS:
        streets = streets.to_crs(TARGET_CRS)

    load_col = config.load_column_kw
    demand_col = config.annual_demand_column

    if load_col not in buildings.columns:
        if demand_col in buildings.columns:
            annual_kwh = buildings[demand_col].fillna(0.0).astype(float)
            design_hours = max(config.fallback_design_hours, 1.0)
            buildings[load_col] = annual_kwh / design_hours
        else:
            buildings[load_col] = 0.0

    return buildings, streets


def _determine_plant_location(
    buildings: gpd.GeoDataFrame, config: CHAScenarioConfig
) -> Point:
    if config.plant_coordinates is not None:
        x, y = config.plant_coordinates
        return Point(float(x), float(y))

    for column in ("GebaeudeID", "building_id", "id"):
        if column in buildings.columns:
            plant_rows = buildings[buildings[column].astype(str) == str(config.plant_node_id)]
            if not plant_rows.empty:
                centroid = plant_rows.geometry.iloc[0].centroid
                return Point(float(centroid.x), float(centroid.y))

    raise ValueError(
        "Unable to determine plant location. Provide 'plant_coordinates' or ensure the "
        "plant building ID exists in the buildings dataset."
    )


def _compute_connections_df(
    buildings: gpd.GeoDataFrame,
    streets: gpd.GeoDataFrame,
    config: CHAScenarioConfig,
    plant_point: Point,
) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []

    street_geoms = streets.geometry
    for idx, building in buildings.iterrows():
        centroid = building.geometry.centroid
        if centroid.is_empty:
            continue

        distances = street_geoms.distance(centroid)
        if distances.empty:
            continue
        nearest_idx = distances.idxmin()
        nearest_street = streets.loc[nearest_idx]
        street_geom = nearest_street.geometry
        if street_geom.is_empty:
            continue

        _, street_point = nearest_points(centroid, street_geom)
        records.append(
            {
                "building_id": str(
                    building.get("GebaeudeID")
                    or building.get("building_id")
                    or building.get("id")
                    or idx
                ),
                "building_x": float(centroid.x),
                "building_y": float(centroid.y),
                "connection_point_x": float(street_point.x),
                "connection_point_y": float(street_point.y),
                "distance_to_street": float(centroid.distance(street_point)),
                "street_segment_id": str(nearest_street.get("street_id", nearest_idx)),
                "street_name": nearest_street.get("name") or f"Street_{nearest_idx}",
                "highway_type": nearest_street.get("highway", "residential"),
                config.load_column_kw: float(building.get(config.load_column_kw, 0.0) or 0.0),
                "heating_load_kw": float(building.get(config.load_column_kw, 0.0) or 0.0),
            }
        )

    if not records:
        raise ValueError("No building-to-street connections could be generated.")

    connections_df = pd.DataFrame.from_records(records)
    max_distance = config.connection_max_distance_m
    if np.isfinite(max_distance):
        connections_df = connections_df[
            connections_df["distance_to_street"] <= float(max_distance)
        ]
        if connections_df.empty:
            raise ValueError(
                "All building connections exceed the maximum snapping distance."
            )

    return connections_df


# ---------------------------------------------------------------------------
# Helper functions (sizing, standards, pandapipes)
# ---------------------------------------------------------------------------

def _apply_sizing_to_topology(
    topology: Dict[str, Any],
    sizing_lookup: Dict[str, Any],
    compliance_lookup: Dict[str, Any],
) -> None:
    """Inject sizing metadata into the topology structure.

    Adapted from ``energy_tools._apply_sizing_to_topology``.
    """

    def _apply_record(target: Dict[str, Any], pipe_id: str) -> None:
        sizing = sizing_lookup.get(pipe_id)
        if sizing is None:
            return
        target["diameter_m"] = float(getattr(sizing, "diameter_m", 0.0) or 0.0)
        target["diameter_dn"] = getattr(sizing, "diameter_nominal", None)
        target["velocity_ms"] = float(getattr(sizing, "velocity_ms", 0.0) or 0.0)
        target["pressure_drop_pa_per_m"] = float(
            getattr(sizing, "pressure_drop_pa_per_m", 0.0) or 0.0
        )
        target["pressure_drop_bar"] = float(
            getattr(sizing, "pressure_drop_bar", 0.0) or 0.0
        )
        target.setdefault("sizing_source", "CHA")

        compliance = compliance_lookup.get(pipe_id)
        if compliance is not None:
            target["standards_compliant"] = bool(getattr(compliance, "overall_compliant", False))
            target["standards_compliance"] = dict(
                getattr(compliance, "standards_compliance", {})
            )
            target["standards_violations"] = [
                {
                    "standard": v.standard,
                    "violation_type": v.violation_type,
                    "description": v.description,
                    "current_value": v.current_value,
                    "limit_value": v.limit_value,
                    "severity": v.severity,
                    "recommendation": v.recommendation,
                }
                for v in getattr(compliance, "violations", [])
            ]
        else:
            target["standards_compliant"] = None
            target["standards_compliance"] = {}
            target["standards_violations"] = []

    compliance_lookup = compliance_lookup or {}

    for pipe in topology.get("pipes", []):
        pipe_id = str(pipe.get("id"))
        _apply_record(pipe, pipe_id)

    for service in topology.get("service_connections", []):
        building_id = service.get("building_id")
        if building_id is None:
            continue
        service_id = f"service_{building_id}"
        _apply_record(service, service_id)
        if service.get("pipe_type") == "return_service":
            _apply_record(service, service_id)


def _update_stats_with_sizing(stats: Dict[str, float], topology: Dict[str, Any]) -> None:
    """Update topology statistics with sizing aggregates.

    Based on ``energy_tools._update_stats_with_sizing``.
    """

    supply_diameters = [
        pipe.get("diameter_m")
        for pipe in topology.get("pipes", [])
        if pipe.get("type") == "supply" and pipe.get("diameter_m")
    ]
    return_diameters = [
        pipe.get("diameter_m")
        for pipe in topology.get("pipes", [])
        if pipe.get("type") == "return" and pipe.get("diameter_m")
    ]
    service_diameters = [
        svc.get("diameter_m")
        for svc in topology.get("service_connections", [])
        if svc.get("diameter_m")
    ]

    velocities = [
        pipe.get("velocity_ms")
        for pipe in topology.get("pipes", [])
        if pipe.get("velocity_ms") is not None
    ]
    service_velocities = [
        svc.get("velocity_ms")
        for svc in topology.get("service_connections", [])
        if svc.get("velocity_ms") is not None
    ]

    if supply_diameters:
        stats["avg_supply_diameter_mm"] = float(np.mean(supply_diameters) * 1000.0)
        stats["max_supply_diameter_mm"] = float(np.max(supply_diameters) * 1000.0)
    if return_diameters:
        stats["avg_return_diameter_mm"] = float(np.mean(return_diameters) * 1000.0)
        stats["max_return_diameter_mm"] = float(np.max(return_diameters) * 1000.0)
    if service_diameters:
        stats["avg_service_diameter_mm"] = float(np.mean(service_diameters) * 1000.0)

    if velocities:
        stats["max_pipe_velocity_ms"] = float(np.max(velocities))
    if service_velocities:
        stats["max_service_velocity_ms"] = float(np.max(service_velocities))

    non_compliant_supply = sum(
        1
        for pipe in topology.get("pipes", [])
        if pipe.get("type") == "supply" and pipe.get("standards_compliant") is False
    )
    non_compliant_return = sum(
        1
        for pipe in topology.get("pipes", [])
        if pipe.get("type") == "return" and pipe.get("standards_compliant") is False
    )
    non_compliant_service = sum(
        1
        for svc in topology.get("service_connections", [])
        if svc.get("standards_compliant") is False
    )

    total_segments = len(topology.get("pipes", [])) + len(topology.get("service_connections", []))
    total_non_compliant = non_compliant_supply + non_compliant_return + non_compliant_service

    stats["non_compliant_supply"] = int(non_compliant_supply)
    stats["non_compliant_return"] = int(non_compliant_return)
    stats["non_compliant_services"] = int(non_compliant_service)
    stats["non_compliant_segments"] = int(total_non_compliant)
    if total_segments:
        stats["compliance_rate"] = float(1 - (total_non_compliant / total_segments))


def _evaluate_standards(
    topology: Dict[str, Any], config: CHAScenarioConfig
) -> Tuple[List[Any], Any]:
    engine = CHAStandardsComplianceEngine(config={})

    pipe_results = []

    def _validate_segment(record: Dict[str, Any], pipe_id: str, category: str) -> None:
        pipe_data = {
            "pipe_id": pipe_id,
            "velocity_ms": float(record.get("velocity_ms", 0.0) or 0.0),
            "pressure_drop_pa_per_m": float(record.get("pressure_drop_pa_per_m", 0.0) or 0.0),
            "diameter_m": float(record.get("diameter_m", 0.0) or 0.0),
            "pipe_category": category,
            "temperature_supply_c": config.supply_temperature,
            "temperature_return_c": config.return_temperature,
            "pressure_bar": config.supply_pressure_bar,
            "safety_factor": config.standards_safety_factor,
            "payback_period_years": config.standards_payback_years,
            "lifecycle_cost_eur_per_mwh": config.standards_lifecycle_cost_eur_per_mwh,
        }
        result = engine.validate_pipe_compliance(pipe_data)
        pipe_results.append(result)

    for pipe in topology.get("pipes", []):
        pipe_id = str(pipe.get("id"))
        pipe_type = pipe.get("type", "distribution")
        if pipe_type == "return":
            category = "distribution_pipe"
        elif pipe_type == "supply":
            category = "distribution_pipe"
        else:
            category = "main_pipe"
        _validate_segment(pipe, pipe_id, category)

    for service in topology.get("service_connections", []):
        building_id = service.get("building_id")
        if building_id is None:
            continue
        service_id = f"service_{building_id}"
        _validate_segment(service, service_id, "service_connection")

    network_summary = engine.validate_network_compliance(pipe_results)
    return pipe_results, network_summary


def _create_network_from_dual_topology(
    topology: Dict[str, Any],
    supply_temp_c: float,
    return_temp_c: float,
    supply_pressure_bar: float,
) -> pp.pandapipesNet:
    if not topology.get("junctions"):
        raise ValueError("Dual topology does not contain junctions.")

    net = pp.create_empty_network(fluid="water")

    supply_temp_k = supply_temp_c + 273.15
    return_temp_k = return_temp_c + 273.15

    junction_map: Dict[int, Dict[str, Any]] = {}

    for junction in topology.get("junctions", []):
        coords = (junction["x"], junction["y"])
        if junction.get("type") == "plant":
            supply_idx = pp.create_junction(
                net,
                pn_bar=supply_pressure_bar,
                tfluid_k=supply_temp_k,
                geodata=coords,
                name="plant_supply",
            )
            return_idx = pp.create_junction(
                net,
                pn_bar=supply_pressure_bar - 0.5,
                tfluid_k=return_temp_k,
                geodata=coords,
                name="plant_return",
            )
        else:
            supply_idx = pp.create_junction(
                net,
                pn_bar=supply_pressure_bar,
                tfluid_k=supply_temp_k,
                geodata=coords,
                name=f"supply_{junction['id']}",
            )
            return_idx = pp.create_junction(
                net,
                pn_bar=supply_pressure_bar - 0.5,
                tfluid_k=return_temp_k,
                geodata=coords,
                name=f"return_{junction['id']}",
            )

        junction_map[junction["id"]] = {
            "data": junction,
            "supply": supply_idx,
            "return": return_idx,
        }

    plant_supply_idx = junction_map[0]["supply"]
    plant_return_idx = junction_map[0]["return"]

    pp.create_ext_grid(
        net,
        junction=plant_supply_idx,
        p_bar=supply_pressure_bar,
        t_k=supply_temp_k,
        name="plant_ext_grid",
    )

    for pipe in topology.get("pipes", []):
        coords = pipe.get("coords")
        if not coords:
            continue
        line = LineString(coords)
        length_km = max(line.length / 1000.0, 1e-6)

        from_map = junction_map[pipe["from_junction"]]
        to_map = junction_map[pipe["to_junction"]]

        if pipe.get("type") == "return":
            from_idx = from_map["return"]
            to_idx = to_map["return"]
        else:
            from_idx = from_map["supply"]
            to_idx = to_map["supply"]

        diameter_m = float(pipe.get("diameter_m") or 0.065)

        pp.create_pipe_from_parameters(
            net,
            from_junction=from_idx,
            to_junction=to_idx,
            length_km=length_km,
            diameter_m=diameter_m,
            k_mm=0.1,
            name=str(pipe.get("id")),
            geodata=coords,
        )

    total_demand_kw = 0.0
    for consumer in topology.get("consumers", []):
        heat_kw = float(consumer.get("heat_demand_kw", 0.0) or 0.0)
        total_demand_kw += heat_kw
        supply_idx = junction_map[consumer["junction_id"]]["supply"]
        return_idx = junction_map[consumer["junction_id"]]["return"]

        pp.create_heat_exchanger(
            net,
            from_junction=supply_idx,
            to_junction=return_idx,
            diameter_m=0.1,
            qext_w=-heat_kw * 1000.0,
            name=consumer.get("name", f"consumer_{consumer['id']}")
            if consumer.get("id") is not None
            else str(consumer.get("name", "consumer")),
        )

    delta_t_k = max(supply_temp_k - return_temp_k, 1.0)
    total_demand_w = total_demand_kw * 1000.0
    mdot_kg_per_s = total_demand_w / (SPECIFIC_HEAT_WATER_J_PER_KG_K * delta_t_k)

    pp.create_sink(
        net,
        junction=plant_return_idx,
        mdot_kg_per_s=mdot_kg_per_s,
        name="system_sink",
    )

    return net


def _run_pandapipes(net: pp.pandapipesNet) -> Dict[str, Any]:
    pp.pipeflow(net, mode="all")
    return {
        "res_pipe": net.res_pipe.to_dict(orient="records") if hasattr(net, "res_pipe") else [],
        "res_junction": net.res_junction.to_dict(orient="records") if hasattr(net, "res_junction") else [],
        "res_heat_exchanger": (
            net.res_heat_exchanger.to_dict(orient="records")
            if hasattr(net, "res_heat_exchanger")
            else []
        ),
    }


def _extract_network_kpis(
    net: pp.pandapipesNet, topology: Dict[str, Any]
) -> Dict[str, float]:
    kpis: Dict[str, float] = {}

    if hasattr(net, "res_heat_exchanger") and "qext_w" in net.res_heat_exchanger:
        total_heat_w = -net.res_heat_exchanger["qext_w"].sum()
        kpis["total_heat_supplied_mwh"] = total_heat_w / 1e6
        kpis["peak_heat_load_kw"] = -net.res_heat_exchanger["qext_w"].max() / 1000.0
    else:
        kpis["total_heat_supplied_mwh"] = 0.0
        kpis["peak_heat_load_kw"] = 0.0

    if hasattr(net, "res_pipe") and not net.res_pipe.empty:
        pressure_drops = (net.res_pipe.p_from_bar - net.res_pipe.p_to_bar).abs()
        kpis["max_pressure_drop_bar"] = pressure_drops.max()
        kpis["avg_pressure_drop_bar"] = pressure_drops.mean()
    else:
        kpis["max_pressure_drop_bar"] = 0.0
        kpis["avg_pressure_drop_bar"] = 0.0

    total_pipe_length_km = net.pipe.length_km.sum() if hasattr(net, "pipe") else 0.0
    kpis["total_pipe_length_km"] = float(total_pipe_length_km)
    kpis["num_junctions"] = float(len(net.junction)) if hasattr(net, "junction") else 0.0
    kpis["num_pipes"] = float(len(net.pipe)) if hasattr(net, "pipe") else 0.0
    kpis["num_consumers"] = (
        float(len(net.heat_exchanger)) if hasattr(net, "heat_exchanger") else 0.0
    )

    stats = topology.get("stats", {})
    if stats:
        for key in (
            "total_supply_length_m",
            "total_return_length_m",
            "total_service_length_m",
            "total_main_length_km",
            "avg_service_length_m",
        ):
            if key in stats:
                kpis[key] = float(stats[key])

    return kpis


def _compute_economic_metrics(
    buildings: gpd.GeoDataFrame,
    topology: Dict[str, Any],
    config: CHAScenarioConfig,
) -> Dict[str, float]:
    annual_kwh = (
        buildings[config.annual_demand_column].fillna(0.0).astype(float)
        if config.annual_demand_column in buildings.columns
        else pd.Series(0.0, index=buildings.index)
    )
    annual_heat_mwh = float(annual_kwh.sum() / 1000.0)

    network_length_m = _network_length_m(topology)
    total_pipe_cost = network_length_m * config.pipe_cost_eur_per_m

    r = max(config.discount_rate, 1e-6)
    n = max(config.asset_lifetime_years, 1)
    annuity_factor = (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    annualized_capex = total_pipe_cost * annuity_factor
    annual_opex = total_pipe_cost * config.opex_fraction_of_capex

    lcoh = (annualized_capex + annual_opex) / max(annual_heat_mwh, 1e-6)
    annual_co2_tons = annual_heat_mwh * config.co2_factor_kg_per_mwh / 1000.0

    return {
        "annual_heat_mwh": annual_heat_mwh,
        "network_length_m": network_length_m,
        "total_pipe_cost_eur": total_pipe_cost,
        "annualized_capex_eur": annualized_capex,
        "annual_opex_eur": annual_opex,
        "lcoh_eur_per_mwh": lcoh,
        "annual_co2_tons": annual_co2_tons,
    }


def _max_velocity_from_sizing(topology: Dict[str, Any]) -> float:
    velocities: Iterable[float] = [
        float(pipe.get("velocity_ms", 0.0) or 0.0)
        for pipe in topology.get("pipes", [])
    ] + [
        float(service.get("velocity_ms", 0.0) or 0.0)
        for service in topology.get("service_connections", [])
    ]
    return float(max(velocities)) if velocities else 0.0


def _max_pressure_drop_from_sizing(topology: Dict[str, Any]) -> float:
    drops: Iterable[float] = [
        float(pipe.get("pressure_drop_pa_per_m", 0.0) or 0.0)
        for pipe in topology.get("pipes", [])
    ] + [
        float(service.get("pressure_drop_pa_per_m", 0.0) or 0.0)
        for service in topology.get("service_connections", [])
    ]
    return float(max(drops)) if drops else 0.0


def _network_length_m(topology: Dict[str, Any]) -> float:
    stats = topology.get("stats", {})
    if "total_pipe_length_m" in stats:
        return float(stats["total_pipe_length_m"])

    supply = sum(float(pipe.get("length_m", 0.0) or 0.0) for pipe in topology.get("pipes", []))
    services = sum(
        float(service.get("distance_to_street", 0.0) or 0.0)
        for service in topology.get("service_connections", [])
        if service.get("pipe_type") == "supply_service"
    )
    return float(supply + services * 2.0)
