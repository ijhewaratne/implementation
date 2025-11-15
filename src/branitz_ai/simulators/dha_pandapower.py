"""Pandapower-based heat pump and LV grid simulator for Branitz AI.

This module mirrors the CHA pandapipes refactor by consolidating the legacy
heat-pump pandapower workflow into a single orchestration entry-point. The
implementation draws on the historical simulator in
``branitz_energy_decision_ai_street_agents_copy`` as well as the feeder
analysis utilities from ``Branitz_energy_decision_ai_street_final``.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import geopandas as gpd
import pandas as pd
import json
from pyproj import CRS, Transformer
from shapely.geometry import Point

try:  # pragma: no cover - import guarded for optional dependency
    import pandapower as pp
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise ImportError("pandapower is required to run the DHA simulator.") from exc

from ..kpi.core import compute_lcoh


TARGET_CRS = "EPSG:32633"


@dataclass
class DHAScenarioConfig:
    """Configuration describing the inputs required to run a DHA simulation."""

    scenario_id: str
    data_root: str
    output_root: str
    buildings_file: str
    lv_assets_file: Optional[str]
    supply_voltage_kv: float
    medium_voltage_kv: float = 20.0
    hp_cop: float = 3.2
    hp_three_phase: bool = True
    hp_thermal_kw_per_building: Optional[float] = None
    base_electric_load_kw: float = 2.0
    voltage_min_pu: float = 0.90
    voltage_max_pu: float = 1.10
    line_loading_max_pct: float = 100.0
    power_factor: float = 0.98
    heat_column_kw: str = "heating_load_kw"
    annual_heat_demand_column: str = "annual_heat_demand_kwh"
    fallback_design_hours: float = 2500.0
    capex_hp_eur: float = 14000.0
    opex_fraction_of_capex: float = 0.01
    discount_rate: float = 0.04
    project_lifetime_years: int = 20
    electricity_price_eur_per_kwh: float = 0.35
    co2_factor_grid_g_per_kwh: float = 290.0
    hours_to_evaluate: int = 10


@dataclass
class DHAKPIResult:
    """Summary of the DHA pandapower run."""

    scenario_id: str
    lcoh_eur_per_mwh: float
    annual_co2_tons: float
    max_voltage_pu: float
    min_voltage_pu: float
    max_feeder_loading_pu: float
    raw_results: Dict[str, Any]


def run_dha_scenario(config: DHAScenarioConfig) -> DHAKPIResult:
    """Build the LV grid, run pandapower, evaluate constraints, and compute KPIs."""

    buildings = _load_buildings(config)
    lv_assets = _load_lv_assets(config)
    projected_buildings = _project_buildings(buildings)
    hp_loads = _derive_hp_loads(projected_buildings, config)

    net, building_buses, metadata = _create_network(
        projected_buildings,
        lv_assets,
        config,
    )

    loads_metadata = _attach_loads_to_network(
        net,
        projected_buildings,
        building_buses,
        hp_loads,
        config,
    )

    _run_power_flow(net, config)

    voltage_metrics = _extract_voltage_metrics(net, config)
    loading_metrics = _extract_loading_metrics(net)
    economics = _compute_hp_economics(projected_buildings, hp_loads, config)

    raw_results: Dict[str, Any] = {
        "network": net,
        "building_assignments": building_buses,
        "hp_loads_kw": hp_loads,
        "metadata": {**metadata, **loads_metadata},
        "voltages": voltage_metrics,
        "loading": loading_metrics,
        "economics": economics,
    }

    return DHAKPIResult(
        scenario_id=config.scenario_id,
        lcoh_eur_per_mwh=economics["lcoh_eur_per_mwh"],
        annual_co2_tons=economics["annual_co2_tons"],
        max_voltage_pu=voltage_metrics["max_voltage_pu"],
        min_voltage_pu=voltage_metrics["min_voltage_pu"],
        max_feeder_loading_pu=loading_metrics["max_loading_pu"],
        raw_results=raw_results,
    )


def run_dha_simulation(config: DHAScenarioConfig) -> DHAKPIResult:
    """Backward-compatible alias retained for legacy callers."""

    return run_dha_scenario(config)


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------


def _resolve_path(root: str, candidate: Optional[str]) -> Optional[Path]:
    if candidate is None or str(candidate).strip() == "":
        return None
    path = Path(candidate)
    if not path.is_absolute():
        path = Path(root) / candidate
    return path


def _load_buildings(config: DHAScenarioConfig) -> gpd.GeoDataFrame:
    buildings_path = _resolve_path(config.data_root, config.buildings_file)
    if buildings_path is None:
        raise ValueError("'buildings_file' must be provided in the scenario config.")

    buildings = gpd.read_file(buildings_path)
    if buildings.crs is None:
        buildings.set_crs("EPSG:4326", inplace=True)

    if config.heat_column_kw not in buildings.columns:
        if config.annual_heat_demand_column in buildings.columns:
            demand = buildings[config.annual_heat_demand_column].fillna(0.0).astype(float)
            design_hours = max(config.fallback_design_hours, 1.0)
            buildings[config.heat_column_kw] = demand / design_hours
        else:
            buildings[config.heat_column_kw] = 0.0

    if config.annual_heat_demand_column not in buildings.columns:
        design_hours = max(config.fallback_design_hours, 1.0)
        buildings[config.annual_heat_demand_column] = (
            buildings[config.heat_column_kw].fillna(0.0).astype(float) * design_hours
        )

    if "base_electric_load_kw" not in buildings.columns:
        buildings["base_electric_load_kw"] = config.base_electric_load_kw

    id_column = None
    for candidate in ("GebaeudeID", "building_id", "id"):
        if candidate in buildings.columns:
            id_column = candidate
            break

    if id_column is None:
        buildings["building_id"] = [f"B{i}" for i in range(len(buildings))]
    elif id_column != "building_id":
        buildings["building_id"] = buildings[id_column].astype(str)
    else:
        buildings["building_id"] = buildings[id_column].astype(str)

    return buildings


def _load_lv_assets(config: DHAScenarioConfig) -> Optional[Tuple[Dict[int, dict], List[dict]]]:
    assets_path = _resolve_path(config.data_root, config.lv_assets_file)
    if assets_path is None:
        return None

    with Path(assets_path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("LV assets JSON must contain 'nodes' and 'ways' keys.")

    nodes = data.get("nodes", [])
    ways = data.get("ways", [])

    id_to_node: Dict[int, dict] = {}
    for node in nodes:
        try:
            node_id = int(node["id"])
            id_to_node[node_id] = {
                "id": node_id,
                "lat": float(node["lat"]),
                "lon": float(node["lon"]),
                "tags": node.get("tags", {}),
            }
        except (KeyError, TypeError, ValueError):
            continue

    normalized_ways: List[dict] = []
    for way in ways:
        try:
            node_seq = [int(nid) for nid in way.get("nodes", [])]
        except Exception:
            continue
        if len(node_seq) < 2:
            continue
        normalized_ways.append(
            {
                "id": way.get("id"),
                "nodes": node_seq,
                "tags": way.get("tags", {}),
            }
        )

    if not id_to_node:
        return None

    return id_to_node, normalized_ways


# ---------------------------------------------------------------------------
# Network construction helpers
# ---------------------------------------------------------------------------


def _project_buildings(buildings: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if buildings.crs is None:
        raise ValueError("Buildings GeoDataFrame must have a CRS set.")

    if buildings.crs.to_string() == TARGET_CRS:
        return buildings.copy()

    return buildings.to_crs(TARGET_CRS)


def _create_network(
    buildings: gpd.GeoDataFrame,
    lv_assets: Optional[Tuple[Dict[int, dict], List[dict]]],
    config: DHAScenarioConfig,
) -> Tuple[pp.pandapowerNet, Dict[int, int], Dict[str, Any]]:
    if lv_assets:
        return _create_network_from_nodes(buildings, lv_assets, config)
    return _create_star_network(buildings, config)


def _create_star_network(
    buildings: gpd.GeoDataFrame,
    config: DHAScenarioConfig,
) -> Tuple[pp.pandapowerNet, Dict[int, int], Dict[str, Any]]:
    net = pp.create_empty_network()
    mv_bus = pp.create_bus(net, vn_kv=config.medium_voltage_kv, name="MV_bus")
    pp.create_ext_grid(
        net,
        bus=mv_bus,
        vm_pu=1.02,
        name="MV_slack",
        s_sc_max_mva=500.0,
        rx_max=0.1,
    )

    building_buses: Dict[int, int] = {}
    geodata_records: List[Dict[str, float]] = []

    for idx, building in buildings.iterrows():
        centroid: Point = building.geometry.centroid
        bus = pp.create_bus(
            net,
            vn_kv=config.supply_voltage_kv,
            name=f"LV_{building['building_id']}",
        )
        building_buses[idx] = bus
        geodata_records.append({"bus": bus, "x": float(centroid.x), "y": float(centroid.y)})

    if geodata_records:
        net.bus_geodata = pd.DataFrame(geodata_records).set_index("bus")

    centroid = buildings.geometry.unary_union.centroid
    distances = buildings.geometry.centroid.distance(centroid)
    trafo_idx = distances.idxmin()
    trafo_bus = building_buses[trafo_idx]

    pp.create_transformer_from_parameters(
        net,
        hv_bus=mv_bus,
        lv_bus=trafo_bus,
        sn_mva=0.63,
        vn_hv_kv=config.medium_voltage_kv,
        vn_lv_kv=config.supply_voltage_kv,
        vk_percent=6.0,
        vkr_percent=0.5,
        pfe_kw=1.0,
        i0_percent=0.1,
        vector_group="Dyn",
        name="Trafo_1",
    )

    trafo_point = buildings.loc[trafo_idx].geometry.centroid
    for idx, bus in building_buses.items():
        if idx == trafo_idx:
            continue
        target_point = buildings.loc[idx].geometry.centroid
        length_km = max(hypot(target_point.x - trafo_point.x, target_point.y - trafo_point.y) / 1000.0, 0.001)
        pp.create_line_from_parameters(
            net,
            from_bus=trafo_bus,
            to_bus=bus,
            length_km=length_km,
            r_ohm_per_km=0.206,
            x_ohm_per_km=0.080,
            c_nf_per_km=210,
            max_i_ka=0.27,
            r0_ohm_per_km=0.206,
            x0_ohm_per_km=0.080,
            c0_nf_per_km=210,
            name=f"Cable_to_{buildings.loc[idx, 'building_id']}",
        )

    metadata = {
        "network_construction": "star",
        "num_buildings": int(len(buildings)),
        "transformer_bus_index": int(trafo_bus),
        "analysis_hours_requested": config.hours_to_evaluate,
    }

    return net, building_buses, metadata


def _create_network_from_nodes(
    buildings: gpd.GeoDataFrame,
    lv_assets: Tuple[Dict[int, dict], List[dict]],
    config: DHAScenarioConfig,
) -> Tuple[pp.pandapowerNet, Dict[int, int], Dict[str, Any]]:
    id_to_node, ways = lv_assets
    transformer = Transformer.from_crs("EPSG:4326", CRS(TARGET_CRS), always_xy=True)

    node_coords: Dict[int, Tuple[float, float]] = {}
    for node_id, node in id_to_node.items():
        try:
            lon = float(node["lon"])
            lat = float(node["lat"])
        except (KeyError, TypeError, ValueError):
            continue
        x, y = transformer.transform(lon, lat)
        node_coords[node_id] = (x, y)

    if not node_coords:
        raise ValueError("LV assets file does not contain valid node coordinates.")

    net = pp.create_empty_network()
    mv_bus = pp.create_bus(net, vn_kv=config.medium_voltage_kv, name="MV_bus")
    pp.create_ext_grid(
        net,
        bus=mv_bus,
        vm_pu=1.02,
        name="MV_slack",
        s_sc_max_mva=500.0,
        rx_max=0.1,
    )

    node_to_bus: Dict[int, int] = {}
    geodata_records: List[Dict[str, float]] = []
    for node_id, (x, y) in node_coords.items():
        bus = pp.create_bus(net, vn_kv=config.supply_voltage_kv, name=f"node_{node_id}")
        node_to_bus[node_id] = bus
        geodata_records.append({"bus": bus, "x": float(x), "y": float(y)})

    if geodata_records:
        net.bus_geodata = pd.DataFrame(geodata_records).set_index("bus")

    union_geom = buildings.geometry.unary_union
    centroid = union_geom.centroid
    trafo_node = min(
        node_coords,
        key=lambda nid: hypot(node_coords[nid][0] - centroid.x, node_coords[nid][1] - centroid.y),
    )
    trafo_bus = node_to_bus[trafo_node]

    pp.create_transformer_from_parameters(
        net,
        hv_bus=mv_bus,
        lv_bus=trafo_bus,
        sn_mva=0.63,
        vn_hv_kv=config.medium_voltage_kv,
        vn_lv_kv=config.supply_voltage_kv,
        vk_percent=6.0,
        vkr_percent=0.5,
        pfe_kw=1.0,
        i0_percent=0.1,
        vector_group="Dyn",
        name="Trafo_1",
    )

    seen_edges: set[Tuple[int, int]] = set()
    for way in ways:
        tags = way.get("tags", {})
        if tags.get("power") not in {"line", "cable", "minor_line"}:
            continue
        nodes = way.get("nodes", [])
        for u, v in zip(nodes, nodes[1:]):
            if u not in node_to_bus or v not in node_to_bus:
                continue
            edge = tuple(sorted((u, v)))
            if edge in seen_edges:
                continue
            seen_edges.add(edge)
            x1, y1 = node_coords[u]
            x2, y2 = node_coords[v]
            length_km = max(hypot(x2 - x1, y2 - y1) / 1000.0, 0.001)
            pp.create_line_from_parameters(
                net,
                from_bus=node_to_bus[u],
                to_bus=node_to_bus[v],
                length_km=length_km,
                r_ohm_per_km=0.206,
                x_ohm_per_km=0.080,
                c_nf_per_km=210,
                max_i_ka=0.27,
                r0_ohm_per_km=0.206,
                x0_ohm_per_km=0.080,
                c0_nf_per_km=210,
                name=f"edge_{u}_{v}",
            )

    building_buses: Dict[int, int] = {}
    for idx, building in buildings.iterrows():
        centroid: Point = building.geometry.centroid
        best_node = min(
            node_coords,
            key=lambda nid: hypot(node_coords[nid][0] - centroid.x, node_coords[nid][1] - centroid.y),
        )
        building_buses[idx] = node_to_bus[best_node]

    metadata = {
        "network_construction": "branched",
        "num_buildings": int(len(buildings)),
        "transformer_bus_index": int(trafo_bus),
        "nodes_file": str(_resolve_path(config.data_root, config.lv_assets_file)),
        "analysis_hours_requested": config.hours_to_evaluate,
    }

    return net, building_buses, metadata


# ---------------------------------------------------------------------------
# Load assignment and simulation
# ---------------------------------------------------------------------------


def _derive_hp_loads(buildings: gpd.GeoDataFrame, config: DHAScenarioConfig) -> pd.Series:
    if config.hp_cop <= 0:
        raise ValueError("Heat pump COP must be greater than zero.")

    if config.hp_thermal_kw_per_building is not None:
        thermal_kw = pd.Series(
            config.hp_thermal_kw_per_building,
            index=buildings.index,
            dtype=float,
        )
    else:
        load_kw = buildings[config.heat_column_kw].fillna(0.0).astype(float)
        thermal_kw = load_kw.clip(lower=0.0)

    electrical_kw = thermal_kw / config.hp_cop
    return electrical_kw


def _attach_loads_to_network(
    net: pp.pandapowerNet,
    buildings: gpd.GeoDataFrame,
    building_buses: Dict[int, int],
    hp_electrical_kw: pd.Series,
    config: DHAScenarioConfig,
) -> Dict[str, Any]:
    total_load_kw = 0.0
    loads_attached = 0

    for idx, building in buildings.iterrows():
        bus = building_buses.get(idx)
        if bus is None:
            continue

        base_kw = float(building.get("base_electric_load_kw", config.base_electric_load_kw) or 0.0)
        hp_kw = float(hp_electrical_kw.get(idx, 0.0) or 0.0)
        total_kw = base_kw + hp_kw

        if total_kw <= 0.0:
            continue

        loads_attached += 1
        total_load_kw += total_kw

        name = f"Load_{building['building_id']}"

        if config.hp_three_phase:
            pp.create_load(net, bus=bus, p_mw=total_kw / 1000.0, q_mvar=0.0, name=name)
        else:  # unbalanced mode (attach to phase A)
            pp.create_asymmetric_load(
                net,
                bus=bus,
                p_a_mw=total_kw / 1000.0,
                p_b_mw=0.0,
                p_c_mw=0.0,
                q_a_mvar=0.0,
                q_b_mvar=0.0,
                q_c_mvar=0.0,
                name=name,
            )

    return {
        "loads_attached": loads_attached,
        "total_load_kw": total_load_kw,
        "hp_kw_total": float(hp_electrical_kw.sum()),
    }


def _run_power_flow(net: pp.pandapowerNet, config: DHAScenarioConfig) -> None:
    if config.hp_three_phase:
        pp.runpp(net)
    else:
        pp.runpp_3ph(net)


# ---------------------------------------------------------------------------
# KPI extraction
# ---------------------------------------------------------------------------


def _extract_voltage_metrics(net: pp.pandapowerNet, config: DHAScenarioConfig) -> Dict[str, float]:
    if not net.bus.empty and hasattr(net, "res_bus") and not net.res_bus.empty:
        min_pu = float(net.res_bus.vm_pu.min())
        max_pu = float(net.res_bus.vm_pu.max())
    elif hasattr(net, "res_bus_3ph") and not net.res_bus_3ph.empty:
        min_pu = float(
            net.res_bus_3ph[["vm_a_pu", "vm_b_pu", "vm_c_pu"]].min(axis=1).min()
        )
        max_pu = float(
            net.res_bus_3ph[["vm_a_pu", "vm_b_pu", "vm_c_pu"]].max(axis=1).max()
        )
    else:
        min_pu = max_pu = 1.0

    return {
        "min_voltage_pu": min_pu,
        "max_voltage_pu": max_pu,
        "violates_voltage_limits": min_pu < config.voltage_min_pu or max_pu > config.voltage_max_pu,
    }


def _extract_loading_metrics(net: pp.pandapowerNet) -> Dict[str, float]:
    loading_values: List[float] = []
    if hasattr(net, "res_line") and not net.res_line.empty and "loading_percent" in net.res_line.columns:
        loading_values.extend(net.res_line.loading_percent.to_list())
    if hasattr(net, "res_trafo") and not net.res_trafo.empty and "loading_percent" in net.res_trafo.columns:
        loading_values.extend(net.res_trafo.loading_percent.to_list())

    if loading_values:
        max_loading_pct = max(loading_values)
    else:
        max_loading_pct = 0.0

    return {
        "max_loading_pct": float(max_loading_pct),
        "max_loading_pu": float(max_loading_pct) / 100.0,
        "violates_loading": float(max_loading_pct) > 100.0,
    }


def _compute_hp_economics(
    buildings: gpd.GeoDataFrame,
    hp_electrical_kw: pd.Series,
    config: DHAScenarioConfig,
) -> Dict[str, float]:
    annual_heat_kwh = buildings[config.annual_heat_demand_column].fillna(0.0).astype(float)
    total_heat_kwh = float(annual_heat_kwh.sum())
    total_heat_mwh = total_heat_kwh / 1000.0

    hp_electricity_kwh = total_heat_kwh / max(config.hp_cop, 1e-6)

    capex_total = config.capex_hp_eur * len(buildings)
    annual_fixed_opex = capex_total * config.opex_fraction_of_capex
    annual_energy_costs = hp_electricity_kwh * config.electricity_price_eur_per_kwh
    annual_opex = annual_fixed_opex + annual_energy_costs

    lcoh = compute_lcoh(
        capex_total,
        annual_opex,
        total_heat_mwh,
        config.discount_rate,
        config.project_lifetime_years,
    )

    annual_co2_tons = (hp_electricity_kwh * config.co2_factor_grid_g_per_kwh) / 1e6

    return {
        "total_heat_supplied_mwh": total_heat_mwh,
        "hp_electricity_kwh": hp_electricity_kwh,
        "annual_fixed_opex_eur": annual_fixed_opex,
        "annual_energy_costs_eur": annual_energy_costs,
        "annual_opex_eur": annual_opex,
        "lcoh_eur_per_mwh": float(lcoh),
        "annual_co2_tons": float(annual_co2_tons),
    }


__all__ = [
    "DHAScenarioConfig",
    "DHAKPIResult",
    "run_dha_scenario",
    "run_dha_simulation",
]
