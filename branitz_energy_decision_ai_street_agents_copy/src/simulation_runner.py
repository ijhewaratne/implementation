# src/simulation_runner.py

"""
Enhanced Simulation Runner with Real Physics Simulations.

This module replaces the placeholder implementation with real pandapipes
and pandapower simulations while maintaining backward compatibility.

Features:
- Smart routing between real and placeholder simulators
- Configuration-driven behavior (feature flags)
- Graceful fallback on errors
- Full integration with existing pipeline
"""

import json
import os
from pathlib import Path
import traceback
from typing import Dict, Any, List, Optional

import geopandas as gpd
import yaml
from shapely.geometry import Point

# Import simulators
try:
    from .simulators import (
        DistrictHeatingSimulator,
        HeatPumpElectricalSimulator,
        PlaceholderDHSimulator,
        PlaceholderHPSimulator,
        SimulationResult,
        SimulationType,
        SimulationMode,
    )
    SIMULATORS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import simulators: {e}")
    SIMULATORS_AVAILABLE = False

# Import enhancements
try:
    from .orchestration import SimulationCache, ProgressTracker
    ENHANCEMENTS_AVAILABLE = True
except ImportError:
    ENHANCEMENTS_AVAILABLE = False
    SimulationCache = None
    ProgressTracker = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "simulation_outputs"
RESULTS_DIR.mkdir(exist_ok=True)


def _resolve_path(path_str: str) -> Path:
    """Resolve a path relative to project root if not absolute."""
    path = Path(path_str)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _parse_buildings_from_json(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract building records with coordinates from generic Branitz JSON."""

    def _find_lat_lon(obj: Any) -> Optional[tuple]:
        if not isinstance(obj, dict):
            return None
        keys = {k.lower(): k for k in obj.keys()}
        lat_key = next((keys[k] for k in keys if k in ("lat", "latitude", "y", "lat_wgs84")), None)
        lon_key = next((keys[k] for k in keys if k in ("lon", "lng", "longitude", "x", "lon_wgs84")), None)
        if lat_key and lon_key:
            try:
                return float(obj[lat_key]), float(obj[lon_key])
            except Exception:
                return None
        if "geometry" in obj and isinstance(obj["geometry"], dict):
            geom = obj["geometry"]
            if geom.get("type") == "Point" and isinstance(geom.get("coordinates"), (list, tuple)):
                lon, lat = geom["coordinates"][:2]
                return float(lat), float(lon)
        return None

    def _find_id(obj: Any) -> Optional[str]:
        if not isinstance(obj, dict):
            return None
        for key in ("GebaeudeID", "building_id", "id", "Id", "ID"):
            if key in obj:
                return str(obj[key])
        return None

    def _centroid_from_gebaeudeteile(obj: Any) -> Optional[tuple]:
        if not isinstance(obj, dict):
            return None
        parts = obj.get("Gebaeudeteile")
        if isinstance(parts, list) and parts:
            coords = parts[0].get("Koordinaten")
            if isinstance(coords, list) and coords:
                lats = [float(c.get("latitude")) for c in coords if "latitude" in c]
                lons = [float(c.get("longitude")) for c in coords if "longitude" in c]
                if lats and lons:
                    return sum(lats) / len(lats), sum(lons) / len(lons)
        return None

    records: List[Dict[str, Any]] = []

    if isinstance(data, dict) and isinstance(data.get("buildings"), list):
        for rec in data["buildings"]:
            latlon = _find_lat_lon(rec)
            building_id = _find_id(rec)
            if latlon and building_id:
                records.append({"GebaeudeID": building_id, "lat": latlon[0], "lon": latlon[1], **rec})
        if records:
            return records

    if isinstance(data, dict) and isinstance(data.get("features"), list):
        for feat in data["features"]:
            props = feat.get("properties", {})
            building_id = _find_id(props) or _find_id(feat)
            latlon = _find_lat_lon(feat) or _find_lat_lon(props)
            if latlon and building_id:
                records.append({"GebaeudeID": building_id, "lat": latlon[0], "lon": latlon[1], **props})
        if records:
            return records

    if isinstance(data, dict):
        for key, value in data.items():
            building_id = _find_id(value) or str(key)
            latlon = _find_lat_lon(value) or _centroid_from_gebaeudeteile(value)
            if latlon:
                record = {"GebaeudeID": building_id, "lat": latlon[0], "lon": latlon[1]}
                if isinstance(value, dict):
                    record.update(value)
                records.append(record)

    return records


def _load_buildings_geodata(building_path: Path) -> gpd.GeoDataFrame:
    """Load buildings into a GeoDataFrame, supporting GeoJSON and Branitz JSON formats."""
    try:
        gdf = gpd.read_file(building_path)
        if not gdf.empty:
            return gdf
    except Exception:
        pass

    with building_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    records = _parse_buildings_from_json(data)
    if not records:
        raise ValueError(f"Unable to parse building coordinates from {building_path}")

    df = gpd.GeoDataFrame(
        records,
        geometry=gpd.points_from_xy([rec["lon"] for rec in records], [rec["lat"] for rec in records]),
        crs="EPSG:4326",
    )
    return df


def _load_load_profiles(load_path: Optional[Path]) -> Dict[str, Dict[str, float]]:
    """Load Branitz load profiles mapping building ID -> scenario -> value."""
    if load_path is None or not load_path.exists():
        return {}
    with load_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {}
    return {str(k): v for k, v in data.items() if isinstance(v, dict)}


def load_configuration() -> Dict[str, Any]:
    """
    Load configuration from YAML files.
    
    Loads both feature flags and simulation parameters.
    Falls back to defaults if files not found.
    
    Returns:
        Dictionary with merged configuration
    """
    config = {
        # Default feature flags
        "use_real_simulations": False,  # Safe default
        "use_real_dh": True,
        "use_real_hp": False,  # Not fully tested yet
        "fallback_on_error": True,
        "enable_caching": False,  # Not implemented yet
        "auto_generate_visualizations": False,  # Auto-create interactive maps
        
        # Default simulation parameters
        "dh": {
            "supply_temp_c": 85.0,
            "return_temp_c": 55.0,
            "default_diameter_m": 0.065,
            "pipe_roughness_mm": 0.1,
            "supply_pressure_bar": 6.0,
        },
        "hp": {
            "hp_thermal_kw": 6.0,
            "hp_cop": 2.8,
            "hp_three_phase": True,
            "lv_voltage_kv": 0.4,
            "mv_voltage_kv": 20.0,
            "voltage_min_pu": 0.90,
            "voltage_max_pu": 1.10,
        }
    }
    
    # Try to load feature flags
    feature_flags_path = Path("config/feature_flags.yaml")
    if feature_flags_path.exists():
        try:
            with open(feature_flags_path, 'r') as f:
                flags = yaml.safe_load(f)
                if flags and "features" in flags:
                    config.update(flags["features"])
                    print(f"  Loaded feature flags from {feature_flags_path}")
        except Exception as e:
            print(f"  Warning: Could not load feature flags: {e}")
    
    # Try to load simulation config
    sim_config_path = Path("config/simulation_config.yaml")
    if sim_config_path.exists():
        try:
            with open(sim_config_path, 'r') as f:
                sim_config = yaml.safe_load(f)
                if sim_config:
                    if "district_heating" in sim_config:
                        config["dh"].update(sim_config["district_heating"])
                    if "heat_pump" in sim_config:
                        config["hp"].update(sim_config["heat_pump"])
                    print(f"  Loaded simulation config from {sim_config_path}")
        except Exception as e:
            print(f"  Warning: Could not load simulation config: {e}")
    
    return config


# Global config (loaded once)
CONFIG = load_configuration()

# Global cache (if enabled)
CACHE = None
if CONFIG.get("enable_caching", False) and ENHANCEMENTS_AVAILABLE and SimulationCache:
    try:
        CACHE = SimulationCache(
            cache_dir=Path(CONFIG.get("cache_directory", "simulation_cache")),
            ttl_hours=CONFIG.get("cache_ttl_hours", 24)
        )
        print("  💾 Cache enabled")
    except Exception as e:
        print(f"  ⚠️  Could not enable cache: {e}")
        CACHE = None


def run_pandapipes_simulation(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run district heating simulation using real pandapipes or placeholder.
    
    This function:
    1. Checks configuration to decide real vs placeholder
    2. Loads building data from scenario
    3. Creates and runs appropriate simulator
    4. Returns results in standardized format
    
    Args:
        scenario: Dictionary with keys:
            - name: Scenario identifier
            - building_file: Path to buildings GeoJSON
            - params: Optional simulation parameters
            - type: "DH" for district heating
    
    Returns:
        Dictionary with simulation results:
            - scenario: Name
            - type: "DH"
            - success: Boolean
            - kpi: Dictionary of KPIs
            - simulation_type: "real_pandapipes" or "placeholder"
            - error: Error message if failed
    """
    scenario_name = scenario.get("name", "DH_scenario")
    print(f"\n{'='*60}")
    print(f"Running DH simulation: {scenario_name}")
    print(f"{'='*60}")
    
    try:
        # Determine if we should use real simulation
        use_real = (
            SIMULATORS_AVAILABLE and
            CONFIG.get("use_real_simulations", False) and
            CONFIG.get("use_real_dh", True)
        )
        
        if use_real:
            print("  → Using REAL pandapipes simulation")
            result = _run_real_dh_simulation(scenario)
        else:
            print("  → Using PLACEHOLDER simulation")
            result = _run_placeholder_dh_simulation(scenario)
        
        # Convert SimulationResult to dict if needed
        if hasattr(result, 'to_dict'):
            result_dict = result.to_dict()
        else:
            result_dict = result
        
        # Save results
        _save_simulation_results(scenario_name, result_dict)
        
        # Auto-generate visualizations if enabled
        if CONFIG.get("auto_generate_visualizations", False) and result_dict.get('success', False):
            try:
                from visualization import InteractiveMapGenerator
                map_gen = InteractiveMapGenerator()
                
                # Generate interactive map
                html_file = map_gen.create_hp_interactive_map(
                    scenario_name=scenario_name,
                    buildings_gdf=None,
                    kpi=result_dict.get('kpi', {})
                )
                print(f"  ✨ Auto-generated interactive map: {html_file}")
                result_dict['visualization_files'] = result_dict.get('visualization_files', {})
                result_dict['visualization_files']['interactive_map'] = html_file
            except Exception as viz_error:
                print(f"  ⚠️  Could not auto-generate visualization: {viz_error}")
        
        return result_dict
        
    except Exception as e:
        # Error occurred
        print(f"  ❌ Simulation failed: {e}")
        traceback.print_exc()
        
        # Try fallback if enabled
        if CONFIG.get("fallback_on_error", True) and use_real:
            print("  → Falling back to PLACEHOLDER simulation")
            try:
                result = _run_placeholder_dh_simulation(scenario)
                if hasattr(result, 'to_dict'):
                    return result.to_dict()
                return result
            except Exception as fallback_error:
                print(f"  ❌ Fallback also failed: {fallback_error}")
        
        # Return error result
        return {
            "scenario": scenario_name,
            "type": "DH",
            "success": False,
            "error": str(e),
            "simulation_type": "failed"
        }


def _run_real_dh_simulation(scenario: Dict[str, Any]) -> SimulationResult:
    """
    Run real pandapipes DH simulation with caching support.
    
    Args:
        scenario: Scenario configuration
    
    Returns:
        SimulationResult from real simulator (or cache)
    """
    # Load buildings
    building_file = scenario.get("building_file")
    if not building_file or not Path(building_file).exists():
        raise FileNotFoundError(f"Building file not found: {building_file}")
    
    print(f"  Loading buildings from: {building_file}")
    buildings_gdf = gpd.read_file(building_file)
    
    # Ensure heating_load_kw column exists
    if "heating_load_kw" not in buildings_gdf.columns:
        print("  Warning: 'heating_load_kw' not found, using default 10 kW")
        buildings_gdf["heating_load_kw"] = 10.0
    
    print(f"  Loaded {len(buildings_gdf)} buildings")
    
    # Merge scenario params with defaults
    params = {**CONFIG["dh"], **scenario.get("params", {})}
    params["scenario_name"] = scenario.get("name", "DH_scenario")
    
    # Check cache first
    if CACHE:
        cached_result = CACHE.get("DH", buildings_gdf, params)
        if cached_result:
            print("  💾 Using cached result (skipping simulation)")
            return cached_result
    
    print(f"  Supply temp: {params['supply_temp_c']}°C, "
          f"Return temp: {params['return_temp_c']}°C")
    
    # Create simulator
    simulator = DistrictHeatingSimulator(params)
    
    # Validate inputs
    print("  Validating inputs...")
    simulator.validate_inputs(buildings_gdf)
    
    # Create network
    print("  Creating network...")
    simulator.create_network(buildings_gdf)
    
    # Run simulation
    print("  Running simulation...")
    result = simulator.run_simulation()
    
    # Export results
    if result.success:
        print("  Exporting results...")
        exported_files = simulator.export_results(RESULTS_DIR)
        result.metadata["exported_files"] = {k: str(v) for k, v in exported_files.items()}
    
    print(f"  ✅ Simulation complete: {result.execution_time_s:.1f}s")
    
    return result


def _run_placeholder_dh_simulation(scenario: Dict[str, Any]) -> SimulationResult:
    """
    Run placeholder DH simulation (dummy data).
    
    Args:
        scenario: Scenario configuration
    
    Returns:
        SimulationResult from placeholder simulator
    """
    # Load buildings (needed for estimates)
    building_file = scenario.get("building_file")
    if building_file and Path(building_file).exists():
        buildings_gdf = gpd.read_file(building_file)
        if "heating_load_kw" not in buildings_gdf.columns:
            buildings_gdf["heating_load_kw"] = 10.0
    else:
        # Create dummy buildings
        from shapely.geometry import Point
        buildings_gdf = gpd.GeoDataFrame({
            'GebaeudeID': ['B1', 'B2', 'B3'],
            'heating_load_kw': [50.0, 75.0, 30.0],
            'geometry': [Point(0, 0), Point(100, 0), Point(50, 100)]
        }, crs='EPSG:25833')
    
    # Create placeholder simulator
    params = {**CONFIG["dh"], **scenario.get("params", {})}
    params["scenario_name"] = scenario.get("name", "DH_placeholder")
    
    simulator = PlaceholderDHSimulator(params)
    simulator.validate_inputs(buildings_gdf)
    simulator.create_network(buildings_gdf)
    result = simulator.run_simulation()
    
    return result


def run_pandapower_simulation(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run heat pump electrical simulation using real pandapower or placeholder.
    
    Args:
        scenario: Dictionary with keys:
            - name: Scenario identifier
            - building_file: Path to buildings GeoJSON
            - params: Optional simulation parameters
            - type: "HP" for heat pump
    
    Returns:
        Dictionary with simulation results
    """
    scenario_name = scenario.get("name", "HP_scenario")
    print(f"\n{'='*60}")
    print(f"Running HP simulation: {scenario_name}")
    print(f"{'='*60}")
    
    try:
        # Determine if we should use real simulation
        use_real = (
            SIMULATORS_AVAILABLE and
            CONFIG.get("use_real_simulations", False) and
            CONFIG.get("use_real_hp", False)
        )

        # Scenario-level overrides
        scenario_params = scenario.get("params", {})
        if "use_real_simulation" in scenario_params:
            use_real = bool(scenario_params["use_real_simulation"])
        if scenario_params.get("use_placeholder_simulation", False):
            use_real = False

        # CLI / environment override
        env_mode = os.getenv("HP_SIM_MODE")
        if env_mode:
            env_mode = env_mode.strip().lower()
            if env_mode in ("real", "true", "1"):
                use_real = True
            elif env_mode in ("placeholder", "fake", "0"):
                use_real = False
        
        if use_real:
            print("  → Using REAL pandapower simulation")
            result = _run_real_hp_simulation(scenario)
        else:
            print("  → Using PLACEHOLDER simulation")
            result = _run_placeholder_hp_simulation(scenario)
        
        # Convert to dict
        if hasattr(result, 'to_dict'):
            result_dict = result.to_dict()
        else:
            result_dict = result
        
        # Save results
        _save_simulation_results(scenario_name, result_dict)
        
        return result_dict
        
    except Exception as e:
        print(f"  ❌ Simulation failed: {e}")
        traceback.print_exc()
        
        # Try fallback if enabled
        if CONFIG.get("fallback_on_error", True) and use_real:
            print("  → Falling back to PLACEHOLDER simulation")
            try:
                result = _run_placeholder_hp_simulation(scenario)
                if hasattr(result, 'to_dict'):
                    return result.to_dict()
                return result
            except Exception as fallback_error:
                print(f"  ❌ Fallback also failed: {fallback_error}")
        
        # Return error result
        return {
            "scenario": scenario_name,
            "type": "HP",
            "success": False,
            "error": str(e),
            "simulation_type": "failed"
        }


def _run_real_hp_simulation(scenario: Dict[str, Any]) -> SimulationResult:
    """
    Run real pandapower HP simulation.
    
    Args:
        scenario: Scenario configuration
    
    Returns:
        SimulationResult from real simulator
    """
    # Load buildings
    building_file = scenario.get("building_file")
    if not building_file:
        raise FileNotFoundError("Scenario must specify 'building_file'")

    building_path = _resolve_path(building_file)
    if not building_path.exists():
        raise FileNotFoundError(f"Building file not found: {building_path}")

    print(f"  Loading buildings from: {building_path}")
    buildings_gdf = _load_buildings_geodata(building_path)
    if buildings_gdf.empty:
        raise ValueError("No buildings found in building dataset.")

    print(f"  Loaded {len(buildings_gdf)} buildings")

    # Ensure CRS is defined
    if buildings_gdf.crs is None:
        buildings_gdf.set_crs("EPSG:4326", inplace=True)

    # Identify building identifier column
    building_id_col = None
    for candidate in ("GebaeudeID", "building_id", "id", "ID"):
        if candidate in buildings_gdf.columns:
            building_id_col = candidate
            break
    if building_id_col is None:
        building_id_col = "GebaeudeID"
        buildings_gdf[building_id_col] = [f"B{idx}" for idx in range(len(buildings_gdf))]

    # Ensure heating load column exists
    if "heating_load_kw" not in buildings_gdf.columns:
        default_heat_kw = scenario.get("params", {}).get("default_heating_load_kw", 10.0)
        buildings_gdf["heating_load_kw"] = default_heat_kw

    # Load base load profiles if provided
    load_profile_file = scenario.get("load_profile_file")
    load_profile_name = scenario.get("params", {}).get("load_profile_name", "winter_werktag_abendspitze")
    base_load_default_kw = scenario.get("params", {}).get("base_load_default_kw", 2.0)
    load_profiles = _load_load_profiles(_resolve_path(load_profile_file)) if load_profile_file else {}

    if load_profiles:
        import statistics

        sample_values = []
        for profile in list(load_profiles.values())[:500]:
            if isinstance(profile, dict):
                try:
                    sample_values.append(abs(float(profile.get(load_profile_name, 0.0))))
                except (TypeError, ValueError):
                    continue
        median_value = statistics.median(sample_values) if sample_values else 0.0
        unit_scale = 1000.0 if median_value < 0.1 else 1.0

        base_loads = []
        for idx, row in buildings_gdf.iterrows():
            building_id = str(row.get(building_id_col, idx))
            profile = load_profiles.get(building_id, {})
            try:
                base_kw = float(profile.get(load_profile_name, base_load_default_kw)) * unit_scale
            except (TypeError, ValueError):
                base_kw = base_load_default_kw
            base_loads.append(base_kw)
        buildings_gdf["base_electric_load_kw"] = base_loads
    elif "base_electric_load_kw" not in buildings_gdf.columns:
        buildings_gdf["base_electric_load_kw"] = base_load_default_kw
    
    # Merge params
    params = {**CONFIG["hp"], **scenario.get("params", {})}
    params["scenario_name"] = scenario.get("name", "HP_scenario")
    
    print(f"  HP: {params['hp_thermal_kw']} kW thermal, "
          f"COP: {params['hp_cop']}, "
          f"3-phase: {params['hp_three_phase']}")
    
    # Create simulator
    simulator = HeatPumpElectricalSimulator(params)
    
    # Validate inputs
    print("  Validating inputs...")
    simulator.validate_inputs(buildings_gdf)
    
    # Create network
    print("  Creating network...")
    simulator.create_network(buildings_gdf)
    
    # Run simulation
    print("  Running simulation...")
    result = simulator.run_simulation()
    
    # Export results
    if result.success:
        print("  Exporting results...")
        exported_files = simulator.export_results(RESULTS_DIR)
        result.metadata["exported_files"] = {k: str(v) for k, v in exported_files.items()}

    # Attach data source metadata
    result.metadata.setdefault("data_sources", {})
    nodes_file = scenario.get("nodes_file")
    result.metadata["data_sources"].update(
        {
            "building_file": str(building_path),
            "load_profile_file": str(_resolve_path(load_profile_file))
            if load_profile_file
            else None,
            "nodes_file": str(_resolve_path(nodes_file)) if nodes_file else None,
            "load_profile_name": load_profile_name,
        }
    )
    
    print(f"  ✅ Simulation complete: {result.execution_time_s:.1f}s")
    
    return result


def _run_placeholder_hp_simulation(scenario: Dict[str, Any]) -> SimulationResult:
    """
    Run placeholder HP simulation (dummy data).
    
    Args:
        scenario: Scenario configuration
    
    Returns:
        SimulationResult from placeholder simulator
    """
    # Load buildings
    building_file = scenario.get("building_file")
    if building_file and Path(building_file).exists():
        buildings_gdf = gpd.read_file(building_file)
        if "heating_load_kw" not in buildings_gdf.columns:
            buildings_gdf["heating_load_kw"] = 10.0
    else:
        # Create dummy buildings
        from shapely.geometry import Point
        buildings_gdf = gpd.GeoDataFrame({
            'GebaeudeID': ['B1', 'B2', 'B3'],
            'heating_load_kw': [50.0, 75.0, 30.0],
            'geometry': [Point(0, 0), Point(100, 0), Point(50, 100)]
        }, crs='EPSG:25833')
    
    # Create placeholder simulator
    params = {**CONFIG["hp"], **scenario.get("params", {})}
    params["scenario_name"] = scenario.get("name", "HP_placeholder")
    
    simulator = PlaceholderHPSimulator(params)
    simulator.validate_inputs(buildings_gdf)
    simulator.create_network(buildings_gdf)
    result = simulator.run_simulation()
    
    return result


def _save_simulation_results(scenario_name: str, results: Dict[str, Any]) -> None:
    """
    Save simulation results to JSON file.
    
    Args:
        scenario_name: Name of scenario
        results: Results dictionary
    """
    output_file = RESULTS_DIR / f"{scenario_name}_results.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"  Results saved: {output_file}")
    except Exception as e:
        print(f"  Warning: Could not save results: {e}")


def run_scenario(scenario_file: str) -> Dict[str, Any]:
    """
    Load scenario JSON, call the correct simulation function, and save results.
    
    Args:
        scenario_file: Path to scenario JSON file
    
    Returns:
        Dictionary with simulation results
    """
    try:
        with open(scenario_file, "r", encoding="utf-8") as f:
            scenario = json.load(f)
        
        scenario_type = scenario.get("type", "DH").upper()
        
        if scenario_type == "DH":
            results = run_pandapipes_simulation(scenario)
        elif scenario_type == "HP":
            results = run_pandapower_simulation(scenario)
        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")
        
        return results
        
    except Exception as e:
        traceback.print_exc()
        return {
            "scenario_file": scenario_file,
            "success": False,
            "error": str(e)
        }


def run_simulation_scenarios(scenario_files: List[str], parallel: bool = False) -> List[Dict[str, Any]]:
    """
    Batch run all scenario files.
    
    Args:
        scenario_files: List of paths to scenario JSON files
        parallel: Whether to run in parallel (not yet implemented)
    
    Returns:
        List of result dictionaries
    """
    print(f"\n{'='*60}")
    print(f"Running {len(scenario_files)} simulation scenarios")
    print(f"{'='*60}")
    
    # Note: Parallel execution not yet implemented
    # Would need multiprocessing or async
    if parallel:
        print("  Warning: Parallel execution not yet implemented, running sequentially")
    
    results = []
    for i, scenario_file in enumerate(scenario_files, 1):
        print(f"\n[Scenario {i}/{len(scenario_files)}]")
        result = run_scenario(scenario_file)
        results.append(result)
    
    print(f"\n{'='*60}")
    print(f"All simulations complete")
    print(f"{'='*60}")
    
    # Summary
    successful = sum(1 for r in results if r.get("success", False))
    failed = len(results) - successful
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    
    return results


if __name__ == "__main__":
    """
    Command-line interface for running simulations.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run energy network simulations for scenario files."
    )
    parser.add_argument(
        "--scenarios", nargs="+", required=True,
        help="List of scenario JSON files to run"
    )
    parser.add_argument(
        "--no_parallel", action="store_true",
        help="Disable multiprocessing (currently always disabled)"
    )
    
    args = parser.parse_args()

    run_simulation_scenarios(args.scenarios, parallel=not args.no_parallel)
