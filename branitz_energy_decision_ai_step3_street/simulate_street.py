#!/usr/bin/env python3

import argparse
import yaml
import os
import geopandas as gpd
import pandas as pd
import osmnx as ox
import networkx as nx
import json
from shapely.geometry import Point, LineString


from src.data_preparation import load_buildings
from src.building_attributes import add_demographics
from src.envelope_and_uvalue import assign_renovation_state, calculate_uvalues, compute_building_envelope
from src.profile_generation import generate_electric_load_profiles
from src.network_construction import create_network_graph
from src.scenario_manager import generate_scenarios
from src.simulation_runner import run_simulation_scenarios
from src.kpi_calculator import compute_kpis

def main():
    parser = argparse.ArgumentParser(description="Run a full simulation pipeline for a single street in Branitz.")
    parser.add_argument("--config", type=str, default="run_all.yaml", help="Pipeline config file (YAML)")
    parser.add_argument("--street-name", type=str, required=True, help="Target street name for simulation (e.g. 'Heinrich-Zille-Straße')")
    parser.add_argument("--output-dir", type=str, default="results/street_sim", help="Where to save outputs")
    args = parser.parse_args()

    # Load pipeline config
    with open(args.config) as f:
        config = yaml.safe_load(f)

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Loading buildings from {config['building_adddress_file']} ...")
    buildings = load_buildings(config['building_adddress_file'])

    # Filter buildings by street
    # After loading buildings as a GeoDataFrame called 'buildings'
    if 'adressen' in buildings.columns:
        # Extract street name from the nested structure into a new column
        def extract_street(adressen):
            if isinstance(adressen, list) and len(adressen) > 0 and 'str' in adressen[0]:
                return adressen[0]['str']
            return None
        buildings['strasse'] = buildings['adressen'].apply(extract_street)
    else:
        raise ValueError("No 'adressen' field found in building data.")
    
    buildings_street = buildings[
        buildings['strasse'].str.lower().str.strip() == args.street_name.lower().strip()
    ]

    # Merge in demographics (if required)
    # --- Extract 'GebaeudeID' from nested 'gebaeude' field if needed ---
    if 'GebaeudeID' not in buildings_street.columns:
        if 'gebaeude' in buildings_street.columns:
            def extract_oi(gebaeude):
                if isinstance(gebaeude, dict):
                    return gebaeude.get('oi')
                return None
            buildings_street['GebaeudeID'] = buildings_street['gebaeude'].apply(extract_oi)
            print("Extracted 'GebaeudeID' from 'gebaeude.oi'.")
        else:
            raise ValueError("No 'GebaeudeID' or 'gebaeude' field found in building data.")

    # Now merge as before
    buildings_street = add_demographics(buildings_street, config["demographics_file"])

    # Calculate renovation state, U-values, envelopes
    print("Calculating renovation state, U-values, and envelope...")
    buildings_street = assign_renovation_state(buildings_street)
    buildings_street = calculate_uvalues(buildings_street)
    buildings_street = compute_building_envelope(buildings_street)

    # Generate load profiles
    print("Generating load profiles...")
    
    #profile_type = config.get('profile_type', 'H0')
    manifest_path = os.path.join(f"{config.get('output_dir')}/profile_manifest.csv")
    generate_electric_load_profiles(buildings_street, 'H0')

    print(f"Electric load profiles saved to {manifest_path}")
    # Build the network for this street
    
    print("Creating network graph for the street...")
    

    def extract_nodes_edges_from_json(json_file, street_name):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        node_records = []
        edge_records = []
        # Loop over buildings
        for b_id, b in data.items():
            # Check each building for the correct street name
            if 'Adressen' in b and b['Adressen']:
                addr = b['Adressen'][0]  # Take first address
                if addr and addr.get('strasse', '').strip() == street_name.strip():
                    # For each building part
                    for teil in b.get('Gebaeudeteile', []):
                        coords = teil.get('Koordinaten', [])
                        # Collect nodes (as points)
                        for i, coord in enumerate(coords):
                            node_records.append({
                                "GebaeudeID": b_id,
                                "GebaeudeteilID": teil.get('GebaeudeteilID'),
                                "point_idx": i,
                                "geometry": Point(coord['longitude'], coord['latitude']),
                                "height": coord.get('height')
                            })
                        # Collect edge (as a LineString through the coordinates)
                        if len(coords) > 1:
                            line = LineString([(c['longitude'], c['latitude']) for c in coords])
                            edge_records.append({
                                "GebaeudeID": b_id,
                                "GebaeudeteilID": teil.get('GebaeudeteilID'),
                                "geometry": line
                            })
        
        # Convert to GeoDataFrames
        nodes_gdf = gpd.GeoDataFrame(node_records, geometry="geometry", crs="EPSG:4326")
        edges_gdf = gpd.GeoDataFrame(edge_records, geometry="geometry", crs="EPSG:4326")

        print(f"Extracted {len(nodes_gdf)} nodes and {len(edges_gdf)} edges for street '{street_name}'.")
        return nodes_gdf, edges_gdf
    

    json_file = "data/json/output_branitzer_siedlungV11.json"
    street_name = "Heinrich-Zille-Straße"
    nodes_gdf, edges_gdf = extract_nodes_edges_from_json(json_file, street_name)
    # Save to file if needed
    nodes_gdf.to_file("results/nodes_zille.geojson", driver="GeoJSON")
    edges_gdf.to_file("results/edges_zille.geojson", driver="GeoJSON")
   
        # Optionally save the networkx graph
    


    # Prepare a scenario and run simulation
    print("Preparing simulation scenario and running simulation...")
    scenario = generate_scenarios(buildings_street, network, config, output_dir=args.output_dir)
    sim_results = run_simulation_scenarios(scenario, output_dir=args.output_dir)

    # Calculate and print KPIs
    print("Computing KPIs...")
    kpis = compute_kpis(sim_results, config.get("cost_params", {}), config.get("emissions_factors", {}))
    print("KPIs for street:", args.street_name)
    print(pd.DataFrame([kpis]))

    # Save outputs
    buildings_street.to_file(os.path.join(args.output_dir, "buildings_street.geojson"), driver="GeoJSON")
    pd.DataFrame([kpis]).to_csv(os.path.join(args.output_dir, "street_kpis.csv"), index=False)
    print(f"Results saved in {args.output_dir}")

if __name__ == "__main__":
    main()
