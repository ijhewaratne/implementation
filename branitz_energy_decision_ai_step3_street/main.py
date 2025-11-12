# main.py

import argparse
import json
import os
from pathlib import Path
from src.building_attributes import add_demographics
from src.flurstuecke_osm_geojson import extract_building_geoms_osmium
from src.extract_ways_nodes import extract_ways_nodes
from src.utils import standardize_id_column
from src.utils import clean_building_geoms
import geopandas as gpd
import logging


try:
    import yaml
except ImportError:
    yaml = None

from src import (
    data_preparation,
    building_attributes,
    envelope_and_uvalue,
    demand_calculation,
    profile_generation,
    network_construction,
    scenario_manager,
    simulation_runner,
    kpi_calculator,
    llm_reporter
)

def load_config(config_file):
    ext = Path(config_file).suffix.lower()
    with open(config_file, "r", encoding="utf-8") as f:
        if ext in [".yaml", ".yml"]:
            if not yaml:
                raise ImportError("pyyaml is required for YAML configs. Install with `pip install pyyaml`.")
            return yaml.safe_load(f)
        else:
            return json.load(f)

def filter_buildings_for_test_mode(bldg_gdf, config):
    if config.get("test_mode", False):
        selected = config.get("selected_buildings", [])
        if selected:
            if "GebaeudeID" in bldg_gdf.columns:
                bldg_gdf = bldg_gdf[bldg_gdf['GebaeudeID'].isin(selected)]
            elif "building_id" in bldg_gdf.columns:
                bldg_gdf = bldg_gdf[bldg_gdf['building_id'].isin(selected)]
            else:
                raise ValueError("No suitable building ID column found for filtering in test mode.")
    return bldg_gdf

def run_pipeline(config_file):
    config = load_config(config_file)
    

    # 1. Building geometry extraction
    buildings_gdf = gpd.read_file(config["buildings_file"])

    # Ensure the geometry column is active
    if "geometry" in buildings_gdf.columns:
        buildings_gdf = buildings_gdf.set_geometry("geometry")
    else:
        # If your geometry column is named differently, adjust here
        geom_cols = [col for col in buildings_gdf.columns if buildings_gdf[col].dtype.name.startswith("geometry")]
        if geom_cols:
            buildings_gdf = buildings_gdf.set_geometry(geom_cols[0])
        else:
            raise ValueError("No geometry column found in buildings GeoDataFrame!")

    # Print for quality control
    print("\n[Step 1] Building Geometry Extraction")
    print(f"Loaded buildings GeoDataFrame with {len(buildings_gdf)} rows")
    print(f"Geometry type: {buildings_gdf.geometry.geom_type.unique()}")
    print(f"Columns: {buildings_gdf.columns.tolist()}")
    print(buildings_gdf.head())

    # Call with correct path and merge key
    merged = add_demographics(
        buildings_gdf,
        demographics_file=config['demographics_file'],
        merge_key=config.get('merge_key', 'GebaeudeID'),
        output_file=f"{config['output_dir']}/buildings_with_demographics.geojson",
        test_mode=config.get('test_mode', False),
        selected_buildings=config.get('selected_buildings', [])
    )
    # *** CLEANING AND QC ***
    buildings_gdf = clean_building_geoms(buildings_gdf, id_col=config.get("merge_key", "Gebaeudecode"))
    # *** STANDARDIZE ID COLUMN ***
    buildings_gdf = standardize_id_column(buildings_gdf, canonical_id=config.get("merge_key", "Gebaeudecode"))
    # 2. Street network extraction (ways/nodes)
    if config.get("run_network_construction", True):
        edges_gdf, nodes_gdf = extract_ways_nodes(
            config["osm_file"],
            output_edges=f"{config.get('output_dir')}/edges.geojson",
            output_nodes=f"{config.get('output_dir')}/nodes.geojson"
        )

    # --- 1. Data Preparation ---
    if config.get("run_data_preparation", True):
        print("\n[Step 1] Data Preparation")
        bldg_gdf = data_preparation.load_buildings(config["buildings_file"])
        bldg_gdf = filter_buildings_for_test_mode(bldg_gdf, config)
        G, edges, nodes = data_preparation.load_osm_streets(config["osm_file"])
        bldg_gdf = data_preparation.preprocess_building_geometries(bldg_gdf)
        bldg_prep_file = os.path.join(f"{config.get('output_dir')}/buildings_prepared.geojson")
        edges_file = os.path.join(f"{config.get('output_dir')}/streets.geojson")
        nodes_file = os.path.join(f"{config.get('output_dir')}/nodes.geojson")
        bldg_gdf.to_file(bldg_prep_file, driver="GeoJSON")
        edges.to_file(edges_file, driver="GeoJSON")
        nodes.to_file(nodes_file, driver="GeoJSON") 
    else:
        bldg_prep_file = os.path.join('output_dir', "buildings_prepared.geojson")
        edges_file = os.path.join('output_dir', "streets.geojson")
        nodes_file = os.path.join('output_dir', "nodes.geojson")

    
    # --- 3. Envelope/U-value ---
    if config.get("run_envelope_and_uvalue", True):
        print("\n[Step 3] Calculate U-values/Envelope")
        #import geopandas as gpd
        bldg_gdf = gpd.read_file(config['bldg_attr_file'])
        bldg_gdf = filter_buildings_for_test_mode(bldg_gdf, config)
        bldg_gdf = envelope_and_uvalue.assign_renovation_state(bldg_gdf)
        bldg_gdf = envelope_and_uvalue.calculate_uvalues(bldg_gdf)
        bldg_gdf = envelope_and_uvalue.compute_building_envelope(bldg_gdf)
        bldg_env_file = os.path.join(f"{config.get('output_dir')}/buildings_with_envelope.geojson")
        bldg_gdf.to_file(bldg_env_file, driver="GeoJSON")
    else:
        bldg_env_file = os.path.join('output_dir', "buildings_with_envelope.geojson")

    # --- 4. Demand Calculation ---
    if config.get("run_demand_calculation", True):
        print("\n[Step 4] Heating Demand Calculation")
        #import geopandas as gpd
        bldg_gdf = gpd.read_file(bldg_env_file)
        bldg_gdf = filter_buildings_for_test_mode(bldg_gdf, config)
        bldg_gdf = demand_calculation.calculate_heating_load(bldg_gdf)
        bldg_gdf = demand_calculation.calculate_annual_heat_demand(bldg_gdf)
        bldg_demand_file = os.path.join(f"{config.get('output_dir')}/buildings_with_demand.geojson")
        bldg_gdf.to_file(bldg_demand_file, driver="GeoJSON")
    else:
        bldg_demand_file = os.path.join('output_dir', "buildings_with_demand.geojson")

    # --- 5. Load Profile Generation ---
    if config.get("run_profile_generation", True):
        print("\n[Step 5] Load Profile Generation")
        #import geopandas as gpd
        bldg_gdf = gpd.read_file(bldg_demand_file)
        bldg_gdf = filter_buildings_for_test_mode(bldg_gdf, config)
        profile_type = config.get("profile_type", "H0")
        profiles = profile_generation.generate_electric_load_profiles(bldg_gdf, profile_type)
        output_profiles_file = os.path.join(f"{config.get('output_dir')}/building_load_profiles.json")
        with open(output_profiles_file, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2)
    else:
        output_profiles_file = os.path.join('output_dir', "building_load_profiles.json")

    # --- 6. Network Construction ---
    if config.get("run_network_construction", True):
        
        print("\n[Step 6] Network Construction")
        #import geopandas as gpd
        bldg_gdf = gpd.read_file(bldg_demand_file)
        bldg_gdf = filter_buildings_for_test_mode(bldg_gdf, config)
        edges = gpd.read_file(edges_file)
        nodes = gpd.read_file(nodes_file)
        graphml_file = os.path.join(f"{config.get('output_dir')}/branitz_network.graphml")
        gpickle_file = os.path.join(f"{config.get('output_dir')}/branitz_network.gpickle")
        G = network_construction.create_network_graph(bldg_gdf, edges, nodes, output_graphml=graphml_file)
        import pickle
        with open(gpickle_file, "wb") as f:
            pickle.dump(G, f)
    else:
        graphml_file = os.path.join('output_dir', "branitz_network.graphml")
        gpickle_file = os.path.join('output_dir', "branitz_network.gpickle")

    # --- 7. Scenario Generation ---
    if config.get("run_scenario_manager", True):
        print("\n[Step 7] Scenario Manager")
        #import geopandas as gpd
        bldg_gdf = gpd.read_file(bldg_demand_file)
        bldg_gdf = filter_buildings_for_test_mode(bldg_gdf, config)
        scenario_config_file = config["scenario_config_file"]
        scenario_files = scenario_manager.generate_scenarios(
            buildings=bldg_gdf,
            network=graphml_file,
            config=load_config(scenario_config_file)
        )
    else:
        scenario_files = config.get("scenario_files", [])

    # --- 8. Simulation Runner ---
    if config.get("run_simulation_runner", True):
        print("\n[Step 8] Simulation Runner")
        results = simulation_runner.run_simulation_scenarios(scenario_files)
    else:
        results = []
        for rf in config.get("simulation_results_files", []):
            with open(rf, "r", encoding="utf-8") as f:
                results.append(json.load(f))

    # --- 9. KPI Calculator ---
    if config.get("run_kpi_calculator", True):
        print("\n[Step 9] KPI Calculator")
        kpi_output_csv = os.path.join(f"{config.get('output_dir')}/scenario_kpis.csv")
        kpi_output_json = os.path.join(f"{config.get('output_dir')}/scenario_kpis.json")
        kpi_df = kpi_calculator.compute_kpis(
            sim_results=results,
            cost_params=config.get("cost_params"),
            emissions_factors=config.get("emissions_factors"),
        )
        kpi_df.to_csv(kpi_output_csv, index=False)
        kpi_df.to_json(kpi_output_json, orient="records", indent=2)
    else:
        kpi_output_csv = os.path.join('output_dir', "scenario_kpis.csv")
        kpi_output_json = os.path.join('output_dir', "scenario_kpis.json")

    # --- 10. LLM Reporter ---
    if config.get("run_llm_reporter", True):
        print("\n[Step 10] LLM Reporter")
        scenarios_file = config.get("scenario_config_file", "")
        output_report = os.path.join(f"{config.get('output_dir')}/llm_report.md")
        llm_model = config.get("llm_model", "gpt-4o")
        api_key = config.get("openai_api_key") or os.environ.get("OPENAI_API_KEY")
        llm_reporter.main([
            "--kpis", kpi_output_csv,
            "--scenarios", scenarios_file,
            "--output", output_report,
            "--model", llm_model,
            "--api_key", api_key or "",
        ])

    print("\nPipeline complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the full Branitz energy decision AI pipeline.")
    parser.add_argument("--config", required=True, help="YAML or JSON config file for the full pipeline")
    args = parser.parse_args()
    run_pipeline(args.config)
