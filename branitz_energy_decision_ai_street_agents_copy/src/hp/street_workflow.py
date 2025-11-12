"""
Street-level heat pump workflow orchestrator.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import geopandas as gpd

from src.simulation_runner import (
    load_configuration,
    _resolve_path,
    _load_buildings_geodata,
    _load_load_profiles,
)
from src.hp.nodes_ways import load_nodes_ways
from src.simulators import HeatPumpElectricalSimulator
from src.hp.street_selection import (
    DEFAULT_OSM_PATH,
    load_streets,
    list_available_streets,
    select_street_interactive,
    filter_buildings_for_street,
)
from src.visualization import InteractiveMapGenerator

CONFIG = load_configuration()
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STREET_OUTPUT_ROOT = PROJECT_ROOT / "street_analysis_outputs"


def _slugify(value: str) -> str:
    return value.strip().replace("/", "_").replace(" ", "-") or "Unnamed"


def _load_scenario(scenario_name: str) -> Dict:
    scenario_path = PROJECT_ROOT / "scenarios" / f"{scenario_name}.json"
    if not scenario_path.exists():
        scenario_path = PROJECT_ROOT / "scenarios" / f"{scenario_name}_scenario.json"
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario not found: {scenario_path}")
    with scenario_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _attach_base_loads(
    buildings_gdf: gpd.GeoDataFrame,
    load_profiles: Dict[str, Dict[str, float]],
    profile_name: str,
    default_base_kw: float,
) -> gpd.GeoDataFrame:
    if not load_profiles:
        if "base_electric_load_kw" not in buildings_gdf.columns:
            buildings_gdf["base_electric_load_kw"] = default_base_kw
        return buildings_gdf

    import statistics

    sample_values = []
    for profile in list(load_profiles.values())[:500]:
        if isinstance(profile, dict):
            try:
                sample_values.append(abs(float(profile.get(profile_name, 0.0))))
            except (TypeError, ValueError):
                continue
    median_value = statistics.median(sample_values) if sample_values else 0.0
    unit_scale = 1000.0 if median_value < 0.1 else 1.0

    loads = []
    id_column = "GebaeudeID" if "GebaeudeID" in buildings_gdf.columns else "building_id"
    for idx, row in buildings_gdf.iterrows():
        building_id = str(row.get(id_column, idx))
        profile = load_profiles.get(building_id, {})
        try:
            base_kw = float(profile.get(profile_name, default_base_kw)) * unit_scale
        except (TypeError, ValueError):
            base_kw = default_base_kw
        loads.append(base_kw)
    buildings_gdf["base_electric_load_kw"] = loads
    return buildings_gdf


def _prepare_street_buildings(
    scenario: Dict,
    street_name: str,
    buffer_m: float,
    osm_path: Optional[Path] = None,
) -> Tuple[gpd.GeoDataFrame, Dict]:
    osm_path = osm_path or DEFAULT_OSM_PATH
    building_path = _resolve_path(scenario.get("building_file"))

    buildings_gdf = _load_buildings_geodata(building_path)

    streets = load_streets(osm_path)
    if street_name not in streets:
        raise ValueError(f"Street '{street_name}' not found in OSM: {osm_path}")

    filtered_gdf, metadata = filter_buildings_for_street(
        buildings_gdf, streets[street_name], buffer_m
    )

    return filtered_gdf, metadata


def _ensure_required_columns(
    buildings_gdf: gpd.GeoDataFrame,
    scenario_params: Dict[str, float],
) -> gpd.GeoDataFrame:
    if "GebaeudeID" not in buildings_gdf.columns:
        buildings_gdf["GebaeudeID"] = [f"B{idx}" for idx in range(len(buildings_gdf))]
    if "heating_load_kw" not in buildings_gdf.columns:
        default_heat = scenario_params.get("default_heating_load_kw", 10.0)
        buildings_gdf["heating_load_kw"] = default_heat
    return buildings_gdf


def _simulation_output_dir(street_name: str, scenario_slug: str) -> Path:
    street_slug = _slugify(street_name)
    return STREET_OUTPUT_ROOT / street_slug / "hp" / scenario_slug


def run_hp_street_analysis(
    scenario_name: str,
    street_name: str,
    buffer_m: float = 40.0,
    force: bool = False,
    osm_path: Optional[Path] = None,
) -> Dict:
    scenario = _load_scenario(scenario_name)
    scenario_slug = _slugify(scenario_name)
    street_slug = _slugify(street_name)
    output_dir = _simulation_output_dir(street_name, scenario_slug)
    summary_path = output_dir / f"{scenario_slug}_{street_slug}_summary.json"

    if summary_path.exists() and not force:
        with summary_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    output_dir.mkdir(parents=True, exist_ok=True)

    filtered_buildings, filter_metadata = _prepare_street_buildings(
        scenario, street_name, buffer_m, osm_path=osm_path
    )

    nodes_file = scenario.get("nodes_file")
    nodes_path = _resolve_path(nodes_file) if nodes_file else None
    nodes_data = load_nodes_ways(nodes_path) if nodes_path else None

    if filtered_buildings.empty:
        raise ValueError(
            f"No buildings found within {buffer_m} m of street '{street_name}'."
        )

    filtered_buildings = _ensure_required_columns(
        filtered_buildings, scenario.get("params", {})
    )

    load_profile_file = scenario.get("load_profile_file")
    load_profiles = (
        _load_load_profiles(_resolve_path(load_profile_file))
        if load_profile_file
        else {}
    )
    profile_name = scenario.get("params", {}).get(
        "load_profile_name", "winter_werktag_abendspitze"
    )
    default_base_kw = scenario.get("params", {}).get("base_load_default_kw", 2.0)

    filtered_buildings = _attach_base_loads(
        filtered_buildings, load_profiles, profile_name, default_base_kw
    )

    hp_params = {**CONFIG["hp"], **scenario.get("params", {})}
    hp_params["scenario_name"] = f"{scenario_name}_{street_slug}"

    simulator = HeatPumpElectricalSimulator(hp_params)
    simulator.validate_inputs(filtered_buildings)
    net = simulator.create_network(
        filtered_buildings,
        nodes_data=nodes_data,
        nodes_ways_path=nodes_path,
    )
    result = simulator.run_simulation()

    exported = {}
    interactive_map_path = None
    if result.success:
        kpi = result.kpi if hasattr(result, "kpi") else result.metadata.get("kpi", {})
        exported = simulator.export_results(
            output_dir,
            prefix=street_name,
            kpi_summary={
                key: kpi.get(key)
                for key in (
                    "min_voltage_pu",
                    "max_voltage_pu",
                    "voltage_violations",
                    "max_line_loading_pct",
                    "avg_line_loading_pct",
                    "overloaded_lines",
                    "transformer_loading_pct",
                    "transformer_overloaded",
                )
                if kpi and key in kpi
            },
        )
        map_generator = InteractiveMapGenerator(output_dir=output_dir)
        interactive_map_path = map_generator.create_hp_interactive_map(
            scenario_name=f"{street_slug}_hp_lv",
            buildings_gdf=filtered_buildings,
            kpi=kpi,
            buses_data=exported.get("buses_results"),
            lines_data=exported.get("lines_results"),
            violations_data=exported.get("violations"),
            metadata=result.metadata if hasattr(result, "metadata") else {},
            output_path=output_dir / f"{street_name}_hp_lv_map.html",
        )
        exported["interactive_map"] = Path(interactive_map_path)

    result_dict = result.to_dict()
    result_dict["metadata"].update(filter_metadata)
    result_dict["metadata"]["street_name"] = street_name
    result_dict["metadata"]["scenario"] = scenario_name
    result_dict["metadata"]["buffer_m"] = buffer_m

    results_path = output_dir / f"{scenario_slug}_{street_slug}_results.json"
    with results_path.open("w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2)

    filtered_geojson = output_dir / f"{scenario_slug}_{street_slug}_buildings.geojson"
    filtered_buildings.to_file(filtered_geojson, driver="GeoJSON")

    summary = {
        "street": street_name,
        "scenario": scenario_name,
        "buffer_m": buffer_m,
        "num_buildings": len(filtered_buildings),
        "metadata": filter_metadata,
        "result": result_dict,
        "exported_files": {k: str(v) for k, v in exported.items()},
        "buildings_geojson": str(filtered_geojson),
        "results_file": str(results_path),
        "output_dir": str(output_dir),
        "nodes_file": nodes_file,
    }
    if interactive_map_path:
        summary["interactive_map"] = str(interactive_map_path)

    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


def run_hp_street_batch(
    scenario_name: str,
    street_names: Iterable[str],
    buffer_m: float = 40.0,
    force: bool = False,
    osm_path: Optional[Path] = None,
) -> List[Dict]:
    results = []
    for street in street_names:
        try:
            results.append(
                run_hp_street_analysis(
                    scenario_name,
                    street,
                    buffer_m=buffer_m,
                    force=force,
                    osm_path=osm_path,
                )
            )
        except Exception as exc:
            results.append(
                {
                    "street": street,
                    "scenario": scenario_name,
                    "buffer_m": buffer_m,
                    "error": str(exc),
                    "success": False,
                }
            )
    return results


__all__ = [
    "run_hp_street_analysis",
    "run_hp_street_batch",
    "list_available_streets",
    "select_street_interactive",
]


