import geopandas as gpd
import pandas as pd
import json
import os
from . import crs_utils


def load_buildings(buildings_file, selected_buildings=None, ensure_projected=True):
    """
    Load building geometries from GeoJSON, JSON, or CSV.
    Optionally filter to a subset of building IDs.

    Args:
        buildings_file: Path to buildings file
        selected_buildings: Optional list of building IDs to filter
        ensure_projected: If True, ensure the data is in a projected CRS
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

    # Ensure projected CRS if requested
    if ensure_projected:
        gdf = crs_utils.ensure_projected_crs(gdf, name="Buildings")

    return gdf


def load_osm_streets(osm_file, ensure_projected=True):
    """
    Load street network from OSM file.
    Returns a tuple: (NetworkX graph, edges GeoDataFrame, nodes GeoDataFrame)

    Args:
        osm_file: Path to OSM file
        ensure_projected: If True, ensure the data is in a projected CRS
    """
    try:
        import osmnx as ox

        G = ox.graph_from_xml(osm_file)
        edges = ox.graph_to_gdfs(G, nodes=False)
        nodes = ox.graph_to_gdfs(G, edges=False)

        # Ensure projected CRS if requested
        if ensure_projected:
            edges = crs_utils.ensure_projected_crs(edges, name="Street Edges")
            if nodes is not None:
                nodes = crs_utils.ensure_projected_crs(nodes, name="Street Nodes")

        return G, edges, nodes
    except ImportError:
        # Fallback: Use geopandas to read OSM if osmnx is not available
        print("osmnx not installed, trying geopandas to load OSM (may be incomplete)...")
        try:
            # Try to load as lines layer first
            gdf = gpd.read_file(osm_file, layer="lines")
        except:
            # Fallback to default layer
            gdf = gpd.read_file(osm_file)

        # Ensure projected CRS if requested
        if ensure_projected:
            gdf = crs_utils.ensure_projected_crs(gdf, name="Streets")

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


def load_and_prepare_data(
    buildings_file, osm_file, output_dir="results", selected_buildings=None, ensure_projected=True
):
    """
    Load and prepare both buildings and streets data with proper CRS handling.

    Args:
        buildings_file: Path to buildings file
        osm_file: Path to OSM file
        output_dir: Output directory for processed files
        selected_buildings: Optional list of building IDs to filter
        ensure_projected: If True, ensure all data is in projected CRS

    Returns:
        Tuple of (buildings_gdf, edges_gdf, nodes_gdf, graph)
    """
    os.makedirs(output_dir, exist_ok=True)

    # Load buildings
    print("Loading buildings...")
    buildings_gdf = load_buildings(buildings_file, selected_buildings, ensure_projected)
    buildings_gdf = preprocess_building_geometries(buildings_gdf)

    # Load streets
    print("Loading streets...")
    graph, edges_gdf, nodes_gdf = load_osm_streets(osm_file, ensure_projected)

    # Ensure both datasets use the same CRS if both are projected
    if ensure_projected and edges_gdf is not None:
        buildings_gdf, edges_gdf = crs_utils.ensure_same_crs(buildings_gdf, edges_gdf)
        if nodes_gdf is not None:
            _, nodes_gdf = crs_utils.ensure_same_crs(buildings_gdf, nodes_gdf)

    # Save processed files
    buildings_output = os.path.join(output_dir, "buildings_prepared.geojson")
    edges_output = os.path.join(output_dir, "streets.geojson")
    nodes_output = os.path.join(output_dir, "nodes.geojson")

    crs_utils.save_with_crs(buildings_gdf, buildings_output)
    if edges_gdf is not None:
        crs_utils.save_with_crs(edges_gdf, edges_output)
    if nodes_gdf is not None:
        crs_utils.save_with_crs(nodes_gdf, nodes_output)

    print(f"Processed data saved to {output_dir}")
    print(f"Buildings CRS: {buildings_gdf.crs}")
    if edges_gdf is not None:
        print(f"Streets CRS: {edges_gdf.crs}")

    return buildings_gdf, edges_gdf, nodes_gdf, graph


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
    parser.add_argument("--no-crs-fix", action="store_true", help="Skip CRS conversion")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # Use the new integrated function
    buildings_gdf, edges_gdf, nodes_gdf, graph = load_and_prepare_data(
        args.buildings,
        args.osm,
        os.path.dirname(args.output),
        args.subset,
        ensure_projected=not args.no_crs_fix,
    )

    print(f"Finished! Saved prepared buildings to {args.output}")
