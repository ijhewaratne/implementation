"""
Test ETL graph features.

Tests the graph utilities and topology feature computation
with synthetic network data.
"""

import pytest
import pandas as pd
import numpy as np
import networkx as nx
from pathlib import Path
import tempfile
import sys

# Import ETL functions
sys.path.append('..')
from etl.graph_utils import load_graph, snap_buildings_to_graph, compute_topology_features


def create_synthetic_network_data():
    """Create synthetic network data for testing."""
    
    # Create nodes: 2 substations, 5 junctions
    nodes_data = {
        'id': ['S1', 'S2', 'J1', 'J2', 'J3', 'J4', 'J5'],
        'x': [0.0, 100.0, 25.0, 50.0, 75.0, 30.0, 70.0],
        'y': [0.0, 0.0, 25.0, 50.0, 25.0, -25.0, -25.0],
        'type': ['substation', 'substation', 'junction', 'junction', 'junction', 'junction', 'junction']
    }
    nodes_df = pd.DataFrame(nodes_data)
    
    # Create edges connecting the network
    edges_data = {
        'u': ['S1', 'J1', 'J2', 'J3', 'S2', 'J1', 'J2', 'J3'],
        'v': ['J1', 'J2', 'J3', 'S2', 'J3', 'J4', 'J4', 'J5'],
        'length_m': [35.0, 35.0, 35.0, 35.0, 35.0, 50.0, 20.0, 50.0]
    }
    edges_df = pd.DataFrame(edges_data)
    
    return nodes_df, edges_df


def create_synthetic_buildings():
    """Create synthetic building data for testing."""
    
    buildings_data = {
        'building_id': ['B001', 'B002', 'B003', 'B004'],
        'x': [10.0, 40.0, 60.0, 80.0],
        'y': [10.0, 30.0, 40.0, 10.0],
        'floor_area': [80.0, 120.0, 150.0, 200.0],
        'function': ['residential', 'commercial', 'residential', 'commercial']
    }
    buildings_df = pd.DataFrame(buildings_data)
    
    return buildings_df


def test_graph_loading():
    """Test loading network graph from synthetic data."""
    print("🧪 Testing graph loading...")
    
    nodes_df, edges_df = create_synthetic_network_data()
    
    # Save to temporary files
    with tempfile.TemporaryDirectory() as temp_dir:
        nodes_path = Path(temp_dir) / "nodes.csv"
        edges_path = Path(temp_dir) / "edges.csv"
        
        nodes_df.to_csv(nodes_path, index=False)
        edges_df.to_csv(edges_path, index=False)
        
        # Load graph
        G = load_graph(str(nodes_path), str(edges_path))
        
        # Verify graph structure
        assert G.number_of_nodes() == 7, f"Expected 7 nodes, got {G.number_of_nodes()}"
        assert G.number_of_edges() == 8, f"Expected 8 edges, got {G.number_of_edges()}"
        
        # Check node attributes
        for node_id in ['S1', 'S2']:
            assert G.nodes[node_id]['type'] == 'substation', f"Node {node_id} should be substation"
        
        # Check edge attributes
        for u, v, attrs in G.edges(data=True):
            assert 'length_m' in attrs, f"Edge {u}-{v} should have length_m attribute"
            assert attrs['length_m'] > 0, f"Edge {u}-{v} should have positive length"
        
        print("✅ Graph loading test passed")


def test_building_snapping():
    """Test snapping buildings to network nodes."""
    print("\n🏗️ Testing building snapping...")
    
    nodes_df, edges_df = create_synthetic_network_data()
    buildings_df = create_synthetic_buildings()
    
    # Create graph
    G = nx.Graph()
    for _, node in nodes_df.iterrows():
        G.add_node(node['id'], x=node['x'], y=node['y'], type=node['type'])
    for _, edge in edges_df.iterrows():
        G.add_edge(edge['u'], edge['v'], length_m=edge['length_m'])
    
    # Snap buildings to graph
    snapped_df = snap_buildings_to_graph(buildings_df, G)
    
    # Verify results
    assert 'nearest_node_id' in snapped_df.columns, "nearest_node_id column should be added"
    assert not snapped_df['nearest_node_id'].isna().all(), "Some buildings should be snapped to nodes"
    
    # Check that buildings are snapped to valid nodes
    valid_nodes = set(nodes_df['id'])
    for node_id in snapped_df['nearest_node_id'].dropna():
        assert node_id in valid_nodes, f"Building snapped to invalid node: {node_id}"
    
    print("✅ Building snapping test passed")


def test_topology_features():
    """Test topology feature computation."""
    print("\n⚙️ Testing topology feature computation...")
    
    nodes_df, edges_df = create_synthetic_network_data()
    buildings_df = create_synthetic_buildings()
    
    # Create graph
    G = nx.Graph()
    for _, node in nodes_df.iterrows():
        G.add_node(node['id'], x=node['x'], y=node['y'], type=node['type'])
    for _, edge in edges_df.iterrows():
        G.add_edge(edge['u'], edge['v'], length_m=edge['length_m'])
    
    # Snap buildings to graph
    snapped_df = snap_buildings_to_graph(buildings_df, G)
    
    # Get substation nodes
    substations = set(nodes_df[nodes_df['type'] == 'substation']['id'])
    
    # Compute topology features
    topology_df = compute_topology_features(snapped_df, G, substations)
    
    # Verify results
    assert not topology_df.empty, "Topology features should be computed"
    assert len(topology_df) == len(buildings_df), "Should have topology features for all buildings"
    
    # Check required columns
    required_cols = [
        'building_id', 'substation_id', 'feeder_id', 'road_distance_m',
        'hydraulic_distance_m', 'topo_hops', 'node_degree',
        'betweenness_centrality', 'edge_count_to_substation'
    ]
    for col in required_cols:
        assert col in topology_df.columns, f"Missing required column: {col}"
    
    # Check that topology features are reasonable
    if not topology_df['hydraulic_distance_m'].isna().all():
        assert (topology_df['hydraulic_distance_m'].dropna() > 0).all(), "Hydraulic distance should be positive"
    
    if not topology_df['topo_hops'].isna().all():
        assert (topology_df['topo_hops'].dropna() >= 1).all(), "Topology hops should be >= 1"
    
    if not topology_df['node_degree'].isna().all():
        assert (topology_df['node_degree'].dropna() >= 1).all(), "Node degree should be >= 1"
    
    print("✅ Topology feature computation test passed")


def test_end_to_end_graph_processing():
    """Test end-to-end graph processing pipeline."""
    print("\n🔄 Testing end-to-end graph processing...")
    
    nodes_df, edges_df = create_synthetic_network_data()
    buildings_df = create_synthetic_buildings()
    
    # Save to temporary files
    with tempfile.TemporaryDirectory() as temp_dir:
        nodes_path = Path(temp_dir) / "nodes.csv"
        edges_path = Path(temp_dir) / "edges.csv"
        buildings_path = Path(temp_dir) / "buildings.csv"
        
        nodes_df.to_csv(nodes_path, index=False)
        edges_df.to_csv(edges_path, index=False)
        buildings_df.to_csv(buildings_path, index=False)
        
        # Load graph
        G = load_graph(str(nodes_path), str(edges_path))
        
        # Snap buildings
        snapped_df = snap_buildings_to_graph(buildings_df, G)
        
        # Get substations
        substations = set(nodes_df[nodes_df['type'] == 'substation']['id'])
        
        # Compute topology features
        topology_df = compute_topology_features(snapped_df, G, substations)
        
        # Merge with building data
        enriched_df = buildings_df.merge(topology_df, on='building_id', how='left')
        
        # Verify enriched data
        assert len(enriched_df) == len(buildings_df), "Should preserve all buildings"
        
        # Check that topology features are present
        topology_cols = [
            'substation_id', 'feeder_id', 'road_distance_m', 'hydraulic_distance_m',
            'topo_hops', 'node_degree', 'betweenness_centrality', 'edge_count_to_substation'
        ]
        
        present_cols = [col for col in topology_cols if col in enriched_df.columns]
        assert len(present_cols) > 0, "At least some topology features should be present"
        
        print(f"✅ End-to-end test passed with {len(present_cols)} topology features")
    
    print("\n🎉 All graph feature tests passed!")


if __name__ == "__main__":
    test_graph_loading()
    test_building_snapping()
    test_topology_features()
    test_end_to_end_graph_processing()







