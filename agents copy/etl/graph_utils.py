"""
Graph utilities for network topology analysis.

This module provides functions to load network graphs, snap buildings to nodes,
and compute topology features for the ETL pipeline.
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import networkx as nx
from scipy.spatial.distance import cdist

# Configure logging
logger = logging.getLogger(__name__)


def load_graph(nodes_path: str, edges_path: str) -> nx.Graph:
    """
    Load network graph from nodes and edges CSV files.
    
    Args:
        nodes_path: Path to network nodes CSV
        edges_path: Path to network edges CSV
        
    Returns:
        NetworkX graph with edge attributes
    """
    logger.info(f"Loading network graph from {nodes_path} and {edges_path}")
    
    # Load nodes
    if not Path(nodes_path).exists():
        raise FileNotFoundError(f"Nodes file not found: {nodes_path}")
    
    nodes_df = pd.read_csv(nodes_path)
    logger.info(f"Loaded {len(nodes_df)} nodes")
    
    # Load edges
    if not Path(edges_path).exists():
        raise FileNotFoundError(f"Edges file not found: {edges_path}")
    
    edges_df = pd.read_csv(edges_path)
    logger.info(f"Loaded {len(edges_df)} edges")
    
    # Create graph
    G = nx.Graph()
    
    # Add nodes
    for _, node in nodes_df.iterrows():
        node_attrs = {
            'x': node.get('x', 0.0),
            'y': node.get('y', 0.0),
            'type': node.get('type', 'junction')
        }
        G.add_node(node['id'], **node_attrs)
    
    # Add edges
    for _, edge in edges_df.iterrows():
        edge_attrs = {
            'length_m': edge.get('length_m', 0.0)
        }
        # Add optional pipe U-value if available
        if 'pipe_U' in edge:
            edge_attrs['pipe_U'] = edge['pipe_U']
        
        G.add_edge(edge['u'], edge['v'], **edge_attrs)
    
    logger.info(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G


def snap_buildings_to_graph(df_b: pd.DataFrame, G: nx.Graph, 
                           building_links_path: Optional[str] = None) -> pd.DataFrame:
    """
    Snap buildings to nearest network nodes.
    
    Args:
        df_b: Building DataFrame with coordinates
        G: NetworkX graph
        building_links_path: Optional path to building-node links CSV
        
    Returns:
        DataFrame with 'nearest_node_id' column added
    """
    logger.info("Snapping buildings to network nodes...")
    
    df = df_b.copy()
    
    # Check if we have explicit building-node links
    if building_links_path and Path(building_links_path).exists():
        logger.info(f"Using explicit building-node links from {building_links_path}")
        links_df = pd.read_csv(building_links_path)
        
        # Rename building_id to id to match normalized data
        links_df = links_df.rename(columns={'building_id': 'id'})
        # Merge with building data
        df = df.merge(links_df, on='id', how='left')
        
        # Check for missing links
        missing_links = df['nearest_node_id'].isna().sum()
        if missing_links > 0:
            logger.warning(f"{missing_links} buildings without explicit node links")
    
    # If no explicit links or some missing, snap by nearest distance
    if 'nearest_node_id' not in df.columns or df['nearest_node_id'].isna().any():
        logger.info("Computing nearest nodes by distance...")
        
        # Extract building coordinates (assuming x, y columns exist)
        if 'x' not in df.columns or 'y' not in df.columns:
            logger.warning("Building coordinates (x, y) not found, cannot snap to graph")
            df['nearest_node_id'] = None
            return df
        
        # Get node coordinates
        node_coords = []
        node_ids = []
        for node_id, attrs in G.nodes(data=True):
            if 'x' in attrs and 'y' in attrs:
                node_coords.append([attrs['x'], attrs['y']])
                node_ids.append(node_id)
        
        if not node_coords:
            logger.warning("No nodes with coordinates found in graph")
            df['nearest_node_id'] = None
            return df
        
        node_coords = np.array(node_coords)
        
        # Compute distances for buildings without explicit links
        buildings_to_snap = df['nearest_node_id'].isna() if 'nearest_node_id' in df.columns else pd.Series([True] * len(df))
        
        if buildings_to_snap.any():
            building_coords = df.loc[buildings_to_snap, ['x', 'y']].values
            
            # Compute distances
            distances = cdist(building_coords, node_coords)
            nearest_indices = np.argmin(distances, axis=1)
            
            # Assign nearest node IDs
            if 'nearest_node_id' not in df.columns:
                df['nearest_node_id'] = None
            
            df.loc[buildings_to_snap, 'nearest_node_id'] = [node_ids[i] for i in nearest_indices]
    
    logger.info(f"Snapped {len(df)} buildings to network nodes")
    return df


def compute_topology_features(df_b: pd.DataFrame, G: nx.Graph, 
                            substations: Set[str]) -> pd.DataFrame:
    """
    Compute topology features for buildings.
    
    Args:
        df_b: Building DataFrame with 'nearest_node_id'
        G: NetworkX graph
        substations: Set of substation node IDs
        
    Returns:
        DataFrame with topology features
    """
    logger.info("Computing topology features...")
    
    if 'nearest_node_id' not in df_b.columns:
        logger.warning("No nearest_node_id column found, cannot compute topology features")
        return pd.DataFrame()
    
    # Initialize topology features
    topology_data = []
    
    # Compute graph-wide metrics
    try:
        betweenness = nx.betweenness_centrality(G, normalized=True)
    except:
        logger.warning("Could not compute betweenness centrality")
        betweenness = {node: 0.0 for node in G.nodes()}
    
    for _, building in df_b.iterrows():
        building_id = building['id']
        nearest_node = building.get('nearest_node_id')
        
        if pd.isna(nearest_node) or nearest_node not in G:
            # Fill with NaN for missing data
            topology_data.append({
                'id': building_id,
                'substation_id': None,
                'feeder_id': None,
                'road_distance_m': None,
                'hydraulic_distance_m': None,
                'topo_hops': None,
                'node_degree': None,
                'betweenness_centrality': None,
                'edge_count_to_substation': None
            })
            continue
        
        # Find nearest substation
        substation_id = None
        min_distance = float('inf')
        
        for substation in substations:
            try:
                distance = nx.shortest_path_length(G, nearest_node, substation, weight='length_m')
                if distance < min_distance:
                    min_distance = distance
                    substation_id = substation
            except nx.NetworkXNoPath:
                continue
        
        if substation_id is None:
            logger.warning(f"No path to substation found for building {id}")
            topology_data.append({
                'id': building_id,
                'substation_id': None,
                'feeder_id': None,
                'road_distance_m': None,
                'hydraulic_distance_m': None,
                'topo_hops': None,
                'node_degree': None,
                'betweenness_centrality': None,
                'edge_count_to_substation': None
            })
            continue
        
        # Compute topology features
        try:
            # Shortest path to substation
            shortest_path = nx.shortest_path(G, nearest_node, substation_id, weight='length_m')
            unweighted_path = nx.shortest_path(G, nearest_node, substation_id)
            
            # Hydraulic distance (weighted)
            hydraulic_distance = nx.shortest_path_length(G, nearest_node, substation_id, weight='length_m')
            
            # Topology hops (unweighted)
            topo_hops = len(unweighted_path) - 1
            
            # Edge count
            edge_count = len(shortest_path) - 1
            
            # Node degree
            node_degree = G.degree(nearest_node)
            
            # Betweenness centrality
            centrality = betweenness.get(nearest_node, 0.0)
            
            # Road distance (Euclidean for now, could be enhanced with actual road network)
            if 'x' in building and 'y' in building:
                substation_coords = (G.nodes[substation_id]['x'], G.nodes[substation_id]['y'])
                building_coords = (building['x'], building['y'])
                road_distance = np.sqrt((substation_coords[0] - building_coords[0])**2 + 
                                      (substation_coords[1] - building_coords[1])**2)
            else:
                road_distance = None
            
            # Feeder ID (simplified: use first edge on path or substation-based ID)
            if len(shortest_path) > 1:
                first_edge = (shortest_path[0], shortest_path[1])
                if G.has_edge(*first_edge):
                    feeder_id = f"fd_{first_edge[0]}_{first_edge[1]}"
                else:
                    feeder_id = f"fd_{substation_id}"
            else:
                feeder_id = f"fd_{substation_id}"
            
            topology_data.append({
                'id': building_id,
                'substation_id': substation_id,
                'feeder_id': feeder_id,
                'road_distance_m': road_distance,
                'hydraulic_distance_m': hydraulic_distance,
                'topo_hops': topo_hops,
                'node_degree': node_degree,
                'betweenness_centrality': centrality,
                'edge_count_to_substation': edge_count
            })
            
        except nx.NetworkXNoPath:
            logger.warning(f"No path to substation {substation_id} for building {id}")
            topology_data.append({
                'id': building_id,
                'substation_id': substation_id,
                'feeder_id': None,
                'road_distance_m': None,
                'hydraulic_distance_m': None,
                'topo_hops': None,
                'node_degree': None,
                'betweenness_centrality': None,
                'edge_count_to_substation': None
            })
    
    topology_df = pd.DataFrame(topology_data)
    logger.info(f"Computed topology features for {len(topology_df)} buildings")
    
    return topology_df
