from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json

def load_building_links(links_file: str = "data_16122024/building_links.csv") -> Dict[str, int]:
    """
    Load building-to-node mapping from CSV file.
    Expected format: building_id, node_id
    """
    try:
        df = pd.read_csv(links_file)
        if 'building_id' in df.columns and 'node_id' in df.columns:
            return dict(zip(df['building_id'].astype(str), df['node_id'].astype(int)))
        else:
            print(f"Warning: {links_file} missing required columns 'building_id' and 'node_id'")
            return {}
    except FileNotFoundError:
        print(f"Warning: Building links file {links_file} not found")
        return {}

def create_building_to_junction_mapping(
    buildings_gdf: gpd.GeoDataFrame,
    network_nodes: pd.DataFrame,
    building_links_file: Optional[str] = None
) -> Dict[str, int]:
    """
    Create building_id to junction index mapping.
    
    Args:
        buildings_gdf: GeoDataFrame with building geometries and IDs
        network_nodes: DataFrame with network node coordinates
        building_links_file: Optional CSV with explicit building-to-node links
    
    Returns:
        Dict mapping building_id to junction index
    """
    building_to_junction = {}
    
    # Try explicit links first
    if building_links_file:
        building_to_junction = load_building_links(building_links_file)
        if building_to_junction:
            print(f"Loaded {len(building_to_junction)} building-to-node mappings from {building_links_file}")
            return building_to_junction
    
    # Fallback: nearest node mapping
    print("Creating nearest-node mapping for buildings...")
    
    # Get building centroids
    building_centroids = buildings_gdf.geometry.centroid
    building_ids = buildings_gdf.get('building_id', buildings_gdf.get('id', buildings_gdf.index.astype(str)))
    
    # Create points for network nodes
    node_points = [Point(x, y) for x, y in zip(network_nodes['x'], network_nodes['y'])]
    
    # Find nearest node for each building
    for i, (building_id, centroid) in enumerate(zip(building_ids, building_centroids)):
        distances = [centroid.distance(node_point) for node_point in node_points]
        nearest_node_idx = distances.index(min(distances))
        building_to_junction[str(building_id)] = nearest_node_idx
    
    print(f"Created nearest-node mapping for {len(building_to_junction)} buildings")
    return building_to_junction

def create_simple_mapping_for_test(building_ids: list, num_junctions: int) -> Dict[str, int]:
    """
    Create a simple sequential mapping for testing purposes.
    Maps buildings to junctions in order, cycling if needed.
    """
    mapping = {}
    for i, building_id in enumerate(building_ids):
        junction_idx = (i + 1) % num_junctions  # Skip junction 0 (usually the source)
        if junction_idx == 0:
            junction_idx = 1  # Avoid mapping to source junction
        mapping[str(building_id)] = junction_idx
    return mapping
