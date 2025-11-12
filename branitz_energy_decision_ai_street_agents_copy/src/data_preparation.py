import geopandas as gpd
import pandas as pd
import json
import os


def load_buildings(buildings_file, selected_buildings=None):
    """
    Load building geometries from GeoJSON, JSON, or CSV.
    Optionally filter to a subset of building IDs.
    """
    ext = os.path.splitext(buildings_file)[-1].lower()
    if ext in [".geojson", ".json"]:
        try:
            gdf = gpd.read_file(buildings_file)
        except Exception as e:
            raise RuntimeError(f"Could not load {buildings_file} as GeoDataFrame: {e}")
    elif ext == ".csv":
        df = pd.read_csv(buildings_file)
        # Try to convert to GeoDataFrame if 'geometry' column is present
        if "geometry" in df.columns:
            gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkt(df["geometry"]))
        else:
            raise ValueError("CSV file must contain a 'geometry' column in WKT format.")
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

    # Optional: Filter to only selected buildings
    if selected_buildings:
        if "GebaeudeID" in gdf.columns:
            gdf = gdf[gdf["GebaeudeID"].isin(selected_buildings)]
        elif "building_id" in gdf.columns:
            gdf = gdf[gdf["building_id"].isin(selected_buildings)]
        else:
            raise ValueError("No suitable building ID column found for subsetting.")
    return gdf


def load_osm_streets(osm_file):
    """
    Load street network from OSM file.
    Returns a tuple: (NetworkX graph, edges GeoDataFrame, nodes GeoDataFrame)
    """
    try:
        import osmnx as ox

        G = ox.graph_from_xml(osm_file)
        edges = ox.graph_to_gdfs(G, nodes=False)
        nodes = ox.graph_to_gdfs(G, edges=False)
        return G, edges, nodes
    except ImportError:
        # Fallback: Use geopandas to read OSM if osmnx is not available
        print("osmnx not installed, trying geopandas to load OSM (may be incomplete)...")
        gdf = gpd.read_file(osm_file)
        # For a real project, you might want to extract edges/nodes from the tags yourself
        return None, gdf, None


def preprocess_building_geometries(gdf):
    """
    Clean, fix, or process geometries for building footprints.
    Example: Remove empty/invalid geometries, fix multi-polygons.
    """
    gdf = gdf[~gdf["geometry"].is_empty]
    gdf = gdf[gdf["geometry"].notnull()]
    # Fix invalid geometries if needed
    gdf["geometry"] = gdf["geometry"].buffer(0)
    return gdf


def prepare_buildings_with_snapping(
    buildings_file, 
    streets_file, 
    plant_location=None,
    max_snapping_distance=100,
    output_dir="results_test"
):
    """
    Prepare buildings with precise street snapping.
    
    Uses advanced snapping algorithms from street_final_copy_3 (Phase 8.2).
    
    Args:
        buildings_file: Path to buildings GeoJSON
        streets_file: Path to streets GeoJSON  
        plant_location: Optional plant location (x, y) tuple
        max_snapping_distance: Maximum distance for snapping (meters)
        output_dir: Output directory for results
        
    Returns:
        Tuple of (buildings_gdf, streets_gdf, connections_df, plant_connection)
    """
    try:
        from .routing import (
            BuildingStreetSnapper,
            snap_plant_to_network_node,
            save_snapping_results
        )
        
        print("📍 Preparing buildings with advanced street snapping...")
        
        # Create snapper
        snapper = BuildingStreetSnapper()
        
        # Load data
        snapper.load_data(buildings_file, streets_file, plant_location)
        
        # Create street network
        snapper.create_street_network()
        
        # Snap buildings to streets
        connections_df = snapper.snap_buildings_to_streets(max_distance=max_snapping_distance)
        
        # Snap plant to network
        plant_conn = snapper.snap_plant_to_network()
        
        # Save connections
        snapper.save_connections(output_dir)
        
        print(f"✅ Buildings prepared with precise street snapping")
        print(f"  • {len(connections_df)} buildings snapped")
        print(f"  • Plant snapped to network")
        print(f"  • Results saved to {output_dir}/")
        
        return snapper.buildings_gdf, snapper.streets_gdf, connections_df, plant_conn
        
    except ImportError:
        print("⚠️  Advanced snapping not available. Using basic preparation.")
        # Fall back to basic loading
        buildings_gdf = load_buildings(buildings_file)
        streets_gdf = gpd.read_file(streets_file)
        return buildings_gdf, streets_gdf, None, None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Prepare and filter building and street data.")
    parser.add_argument(
        "--buildings", required=True, help="Path to building file (.geojson, .json, .csv)"
    )
    parser.add_argument("--osm", required=True, help="Path to OSM file")
    parser.add_argument(
        "--output",
        default="results/buildings_prepared.geojson",
        help="Output GeoJSON file for buildings",
    )
    parser.add_argument("--subset", nargs="*", help="Subset of building IDs to process (optional)")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    bldg_gdf = load_buildings(args.buildings, selected_buildings=args.subset)
    bldg_gdf = preprocess_building_geometries(bldg_gdf)
    bldg_gdf.to_file(args.output, driver="GeoJSON")

    G, edges, nodes = load_osm_streets(args.osm)
    if edges is not None:
        edges.to_file("results/streets.geojson", driver="GeoJSON")
    if nodes is not None:
        nodes.to_file("results/nodes.geojson", driver="GeoJSON")
    print(f"Finished! Saved prepared buildings to {args.output}")
