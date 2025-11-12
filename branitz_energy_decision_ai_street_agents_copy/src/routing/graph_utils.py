"""
Graph Utilities for Network Construction

Migrated from street_final_copy_3/graph.py and graph2.py

Provides:
- Minimum spanning tree construction
- Service connection calculation
- Graph visualization utilities
"""

import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
from scipy.spatial import distance_matrix
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points
import numpy as np


def create_mst_network_from_buildings(buildings_gdf, target_crs="EPSG:32633"):
    """
    Create a minimum spanning tree network from building centroids.
    
    Migrated from graph.py
    
    Args:
        buildings_gdf: GeoDataFrame with building geometries
        target_crs: Target CRS for projections
        
    Returns:
        NetworkX graph (MST), position dictionary
    """
    # Ensure projected CRS
    utm_crs = buildings_gdf.estimate_utm_crs() if target_crs is None else target_crs
    nodes_proj = buildings_gdf.to_crs(utm_crs)
    nodes_proj["centroid"] = nodes_proj.geometry.centroid

    # Create the position dictionary using the unique building ID
    if "GebaeudeID" in nodes_proj.columns:
        pos = {row["GebaeudeID"]: (row.centroid.x, row.centroid.y) for _, row in nodes_proj.iterrows()}
    else:
        pos = {i: (row.centroid.x, row.centroid.y) for i, (_, row) in enumerate(nodes_proj.iterrows())}

    # Create complete graph with all-to-all connections
    building_ids = list(pos.keys())
    coordinates = list(pos.values())
    complete_graph = nx.Graph()
    dist_matrix = distance_matrix(coordinates, coordinates)

    for i in range(len(building_ids)):
        for j in range(i + 1, len(building_ids)):
            id1 = building_ids[i]
            id2 = building_ids[j]
            dist = dist_matrix[i, j]
            complete_graph.add_edge(id1, id2, weight=dist)

    # Create minimum spanning tree
    mst_graph = nx.minimum_spanning_tree(complete_graph)
    
    print(
        f"Created MST network with {mst_graph.number_of_nodes()} nodes and {mst_graph.number_of_edges()} edges."
    )

    return mst_graph, pos


def calculate_service_connections(buildings_gdf, streets_gdf, target_crs="EPSG:32633"):
    """
    Calculate service line connections from buildings to street network.
    
    Migrated from graph2.py
    
    Args:
        buildings_gdf: GeoDataFrame with building geometries
        streets_gdf: GeoDataFrame with street geometries
        target_crs: Target CRS for projections
        
    Returns:
        GeoDataFrame with service connection LineStrings
    """
    # Project both layers to the same projected CRS for accuracy
    print(f"Projecting layers to a suitable local CRS...")
    utm_crs = buildings_gdf.estimate_utm_crs() if target_crs is None else target_crs
    buildings_proj = buildings_gdf.to_crs(utm_crs)
    streets_proj = streets_gdf.to_crs(utm_crs)
    print(f"Layers projected to: {utm_crs}")

    # Combine all street segments into one continuous line for calculations
    street_line = streets_proj.geometry.union_all()

    # Calculate the service line connections
    connection_lines = []
    for _, building in buildings_proj.iterrows():
        building_polygon = building.geometry

        # Find the two nearest points between the building edge and the street line
        p_building, p_street = nearest_points(building_polygon, street_line)

        # Create a line connecting these two points
        connection_lines.append(LineString([p_building, p_street]))

    # Create a new GeoDataFrame for the connection lines
    connections_gdf = gpd.GeoDataFrame(geometry=connection_lines, crs=utm_crs)
    print(f"Successfully calculated {len(connections_gdf)} service connections.")

    return connections_gdf, buildings_proj, streets_proj


def plot_mst_network(mst_graph, pos, buildings_proj, figsize=(12, 12), save_path=None):
    """
    Plot minimum spanning tree network.
    
    Migrated from graph.py
    
    Args:
        mst_graph: NetworkX MST graph
        pos: Position dictionary for nodes
        buildings_proj: Projected buildings GeoDataFrame
        figsize: Figure size
        save_path: Path to save plot
        
    Returns:
        fig, ax
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Plot background building footprints
    buildings_proj.plot(ax=ax, color="lightgrey", edgecolor="black", alpha=0.7, zorder=0)

    # Draw the edges
    edge_artists = nx.draw_networkx_edges(mst_graph, pos, ax=ax, edge_color="#0066ff", width=1.5)
    if isinstance(edge_artists, list):
        for artist in edge_artists:
            artist.set_zorder(1)
    else:
        edge_artists.set_zorder(1)

    # Draw the nodes
    node_artists = nx.draw_networkx_nodes(
        mst_graph, pos, ax=ax, node_size=60, node_color="red", edgecolors="black"
    )
    node_artists.set_zorder(2)

    ax.set_title("Minimum Spanning Tree Network of Buildings")
    ax.set_axis_off()
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"✅ MST plot saved to {save_path}")

    return fig, ax


def plot_service_connections(buildings_proj, streets_proj, connections_gdf, 
                             figsize=(12, 12), save_path=None):
    """
    Plot service connections from buildings to streets.
    
    Migrated from graph2.py
    
    Args:
        buildings_proj: Projected buildings GeoDataFrame
        streets_proj: Projected streets GeoDataFrame
        connections_gdf: Service connections GeoDataFrame
        figsize: Figure size
        save_path: Path to save plot
        
    Returns:
        fig, ax
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Plot layers from bottom to top
    streets_proj.plot(ax=ax, color="black", linewidth=3, label="Main Street")
    buildings_proj.plot(ax=ax, color="lightgrey", edgecolor="black")
    connections_gdf.plot(ax=ax, color="red", linewidth=1.5, label="Service Connections")

    ax.set_title("Network Connections from Buildings to Street")
    ax.set_axis_off()
    ax.set_aspect("equal", adjustable="box")
    plt.legend()
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"✅ Service connections plot saved to {save_path}")

    return fig, ax


def save_service_connections(connections_gdf, buildings_proj, streets_proj, output_dir="results_test"):
    """
    Save service connection network files.
    
    Migrated from graph2.py
    
    Args:
        connections_gdf: Service connections GeoDataFrame
        buildings_proj: Projected buildings GeoDataFrame
        streets_proj: Projected streets GeoDataFrame
        output_dir: Output directory
    """
    os.makedirs(output_dir, exist_ok=True)

    # Export the calculated connection lines
    connections_gdf.to_file(
        os.path.join(output_dir, "service_connections.geojson"), 
        driver="GeoJSON"
    )

    # Also export the projected buildings and street for context
    buildings_proj.to_file(
        os.path.join(output_dir, "buildings_projected.geojson"), 
        driver="GeoJSON"
    )
    streets_proj.to_file(
        os.path.join(output_dir, "street_projected.geojson"), 
        driver="GeoJSON"
    )

    print(f"\n✅ Service connection files saved to {output_dir}:")
    print(f"   - service_connections.geojson")
    print(f"   - buildings_projected.geojson")
    print(f"   - street_projected.geojson")

