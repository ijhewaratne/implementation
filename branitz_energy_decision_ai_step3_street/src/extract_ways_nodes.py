import geopandas as gpd
import osmnx as ox
import logging
from pathlib import Path

def extract_ways_nodes(osm_file, output_edges=None, output_nodes=None):
    """
    Extract road network (edges/ways and nodes) from an OSM .osm or .pbf file.
    Returns: (edges_gdf, nodes_gdf) as GeoDataFrames.
    Optionally saves each to GeoJSON.
    """
    logging.info(f"Extracting street network from {osm_file} ...")
    try:
        # Load the OSM file as a street graph
        G = ox.graph_from_xml(osm_file)  # 'drive' or 'all'
        edges = ox.graph_to_gdfs(G, nodes=False, edges=True)
        nodes = ox.graph_to_gdfs(G, nodes=True, edges=False)
        # Save if needed
        if output_edges:
            Path(output_edges).parent.mkdir(exist_ok=True, parents=True)
            edges.to_file(output_edges, driver="GeoJSON")
            logging.info(f"Saved street edges to {output_edges}")
        if output_nodes:
            Path(output_nodes).parent.mkdir(exist_ok=True, parents=True)
            nodes.to_file(output_nodes, driver="GeoJSON")
            logging.info(f"Saved street nodes to {output_nodes}")
        return edges, nodes
    except Exception as e:
        logging.error(f"Failed to extract ways/nodes: {e}")
        raise

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract ways/nodes from OSM file.")
    parser.add_argument("osm_file", help="Input OSM .osm/.pbf file")
    parser.add_argument("--edges", help="Output edges GeoJSON")
    parser.add_argument("--nodes", help="Output nodes GeoJSON")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    extract_ways_nodes(args.osm_file, args.edges, args.nodes)
