# src/data_preparation.py

import argparse
import json
from pathlib import Path
import geopandas as gpd

def load_buildings(buildings_file):
    """
    Load buildings from GeoJSON, JSON, or CSV.
    Returns a GeoDataFrame (preferred).
    """
    ext = Path(buildings_file).suffix.lower()
    if ext == ".geojson":
        print(f"Reading GeoJSON: {buildings_file}")
        return gpd.read_file(buildings_file)
    elif ext == ".json":
        # Try to parse as GeoJSON first, fallback to properties-only JSON
        try:
            print(f"Trying as GeoJSON: {buildings_file}")
            return gpd.read_file(buildings_file)
        except Exception:
            print(f"Parsing as plain JSON: {buildings_file}")
            with open(buildings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Check for a list of features
            if isinstance(data, list):
                return gpd.GeoDataFrame(data)
            elif isinstance(data, dict):
                if "features" in data:  # GeoJSON format
                    return gpd.GeoDataFrame.from_features(data["features"])
                else:
                    # Flat dict: each key is an object
                    records = [v for v in data.values()]
                    return gpd.GeoDataFrame(records)
            else:
                raise ValueError("Unrecognized JSON structure for buildings")
    elif ext == ".csv":
        import pandas as pd
        print(f"Reading CSV: {buildings_file}")
        df = pd.read_csv(buildings_file)
        # Try to build geometries from lon/lat columns, if present
        for geom_cols in (("lon", "lat"), ("longitude", "latitude"), ("x", "y")):
            if all(col in df.columns for col in geom_cols):
                gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[geom_cols[0]], df[geom_cols[1]]))
                gdf.set_crs(epsg=4326, inplace=True)
                return gdf
        # Otherwise just return DataFrame, will error if geometry needed
        return df
    else:
        raise ValueError(f"Unsupported filetype: {ext}")

def load_osm_streets(osm_file):
    """
    Parse OSM file for street network using osmnx.
    Returns a NetworkX MultiDiGraph and GeoDataFrames for edges/nodes.
    """
    import osmnx as ox
    print(f"Parsing OSM street network with osmnx: {osm_file}")
    # ox can read from OSM xml or .pbf, and extract drivable/footway graphs
    # If osm_file is an .osm extract, specify the bounding box or polygon for context
    try:
        # You may want to buffer your area of interest, or get bounding box from buildings
        G = ox.graph_from_xml(osm_file)
        edges = ox.graph_to_gdfs(G, nodes=False)
        nodes = ox.graph_to_gdfs(G, edges=False)
        return G, edges, nodes
    except Exception as e:
        print(f"Error with osmnx.graph_from_file: {e}")
        raise

def preprocess_building_geometries(buildings_gdf):
    """
    Clean, repair, and buffer building geometries.
    - Fix invalid polygons
    - Optionally buffer (e.g., shrink by 0.1m for 'realistic' walls)
    """
    import shapely
    from shapely.errors import TopologicalError
    def fix_geom(geom):
        try:
            if not geom.is_valid:
                geom = geom.buffer(0)
            return geom
        except TopologicalError:
            return None
    
    # Check CRS and reproject if necessary
    if buildings_gdf.crs is None:
        # Default to WGS84 if not set
        buildings_gdf = buildings_gdf.set_crs("EPSG:4326")
    if buildings_gdf.crs.is_geographic:
        print("Reprojecting to UTM (EPSG:25833) for geometry operations...")
        buildings_gdf = buildings_gdf.to_crs(epsg=25833)  # UTM zone 33N
    
    

    # Fix invalid geometries
    print("Repairing building geometries...")
    buildings_gdf["geometry"] = buildings_gdf["geometry"].apply(fix_geom)
    # Drop any null geometries
    buildings_gdf = buildings_gdf[~buildings_gdf["geometry"].isnull()].copy()
    # (Optional) Apply a small negative buffer to ensure no overlaps
    buildings_gdf["geometry"] = buildings_gdf["geometry"].buffer(-0.05)
    # Remove empty geometries after buffering
    buildings_gdf = buildings_gdf[~buildings_gdf["geometry"].is_empty].copy()
    print(f"Final building count after cleaning: {len(buildings_gdf)}")
    return buildings_gdf

    buildings_gdf = buildings_gdf.to_crs("EPSG:4326")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load and preprocess building and street network data.")
    parser.add_argument("--buildings", required=True, help="Building footprints file (.geojson/.json/.csv)")
    parser.add_argument("--osm", required=True, help="OSM file for street network (.osm/.pbf)")
    parser.add_argument("--output", default="results/buildings_prepared.geojson", help="Output cleaned buildings GeoJSON")
    parser.add_argument("--output_streets", default="results/streets.geojson", help="Output street network edges GeoJSON")
    parser.add_argument("--output_nodes", default="results/nodes.geojson", help="Output street network nodes GeoJSON")
    args = parser.parse_args()

    # Step 1: Load buildings
    buildings = load_buildings(args.buildings)

    # Step 2: Load OSM street network
    G, edges, nodes = load_osm_streets(args.osm)

    # Step 3: Clean building geometries
    buildings_clean = preprocess_building_geometries(buildings)

    # Step 4: Save outputs
    Path("results").mkdir(exist_ok=True)
    print(f"Saving cleaned buildings to {args.output}")
    buildings_clean.to_file(args.output, driver="GeoJSON")
    print(f"Saving streets to {args.output_streets}")
    edges.to_file(args.output_streets, driver="GeoJSON")
    print(f"Saving nodes to {args.output_nodes}")
    nodes.to_file(args.output_nodes, driver="GeoJSON")

    print("Data preparation complete!")
