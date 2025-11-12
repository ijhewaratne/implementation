import geopandas as gpd
import pandas as pd
import json
import logging
from pathlib import Path

import pandas as pd
import geopandas as gpd
import json

def add_demographics(buildings_gdf, demographics_file, merge_key='GebaeudeID', output_file=None, test_mode=False, selected_buildings=None):
    """
    Merge building GeoDataFrame with demographics from JSON.
    
    Args:
        buildings_gdf (GeoDataFrame): The geodataframe of buildings.
        demographics_file (str): Path to JSON file with population, households, etc.
        merge_key (str): The column name to use as join key (e.g., 'GebaeudeID' or 'Gebaeudecode').
        output_file (str): If set, will write the merged GeoDataFrame to this file.
        test_mode (bool): If True, restricts to selected_buildings.
        selected_buildings (list): List of IDs to use if test_mode is True.

    Returns:
        GeoDataFrame: Merged geodataframe.
    """
    # --- Load demographics JSON as DataFrame, use top-level key as ID ---
    with open(demographics_file) as f:
        demo_data = json.load(f)
    demo_df = pd.DataFrame.from_dict(demo_data, orient="index")
    demo_df.reset_index(inplace=True)
    
    # Try to determine best column name for merge
    if merge_key not in buildings_gdf.columns:
        print(f"[WARN] Merge key {merge_key} not found in buildings_gdf, available columns: {list(buildings_gdf.columns)}")
        raise ValueError(f"Merge key {merge_key} not found in buildings_gdf!")
    # Guess the right name for demo_df
    if merge_key not in demo_df.columns:
        # Try common alternatives: 'GebaeudeID', 'Gebaeudecode'
        for alt in ['GebaeudeID', 'Gebaeudecode']:
            if alt in buildings_gdf.columns:
                demo_df.rename(columns={'index': alt}, inplace=True)
                merge_key = alt
                break
        if merge_key not in demo_df.columns:
            # Use 'index' as fallback
            demo_df.rename(columns={'index': merge_key}, inplace=True)

    # --- Optionally subset for test_mode ---
    if test_mode and selected_buildings is not None and len(selected_buildings) > 0:
        buildings_gdf = buildings_gdf[buildings_gdf[merge_key].isin(selected_buildings)]
        demo_df = demo_df[demo_df[merge_key].isin(selected_buildings)]
    
    # --- Merge ---
    merged = buildings_gdf.merge(
        demo_df,
        how="left",
        left_on=merge_key,
        right_on=merge_key,
        suffixes=("", "_demo")
    )
    print(f"[INFO] Merged {len(merged)} buildings with demographics.")

    # --- Optionally write to file ---
    if output_file:
        merged.to_file(output_file, driver="GeoJSON")
        print(f"[INFO] Saved merged file to {output_file}")

    return merged


if __name__ == "__main__":
    import argparse
    import sys
    import yaml

    parser = argparse.ArgumentParser(description="Merge building polygons with demographic/census data.")
    parser.add_argument("--config", help="YAML config file (preferred).")
    parser.add_argument("--buildings_file", help="GeoJSON or shapefile with building polygons.")
    parser.add_argument("--demographics_file", help="JSON/CSV with census/household data.")
    parser.add_argument("--output_file", help="Output file (GeoJSON/CSV).")
    parser.add_argument("--merge_key", default="GebaeudeID", help="Join field (default: GebaeudeID).")
    parser.add_argument("--test_mode", action="store_true", help="Process only selected_buildings.")
    parser.add_argument("--selected_buildings", nargs="*", help="List of IDs to keep (if test_mode).")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    # Load from config if provided
    if args.config:
        with open(args.config, "r") as f:
            config = yaml.safe_load(f)
        buildings_file = config.get("buildings_file")
        demographics_file = config.get("demographics_file")
        output_file = config.get("output_dir", "results/") + "buildings_with_demographics.geojson"
        merge_key = config.get("merge_key", "GebaeudeID")
        test_mode = config.get("test_mode", False)
        selected_buildings = config.get("selected_buildings", [])
    else:
        buildings_file = args.buildings_file
        demographics_file = args.demographics_file
        output_file = args.output_file
        merge_key = args.merge_key
        test_mode = args.test_mode
        selected_buildings = args.selected_buildings

    if not buildings_file or not demographics_file:
        print("Both buildings_file and demographics_file must be specified (either as args or in config).")
        sys.exit(1)

    # Load building polygons
    b_gdf = gpd.read_file(buildings_file)
    add_demographics(
        b_gdf,
        demographics_file,
        merge_key=merge_key,
        output_file=output_file,
        test_mode=test_mode,
        selected_buildings=selected_buildings
    )
