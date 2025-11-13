#!/usr/bin/env python3
"""
Simple Street Network Example

This script shows how to build NetworkX graphs from street data with different approaches
and granularity control.
"""

import geopandas as gpd
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from scipy.spatial import distance_matrix
from src import crs_utils
import os


def build_network_from_streets_simple(streets_gdf, max_length=None, intersection_tolerance=2.0):
    """
    Simple function to build NetworkX graph from streets GeoDataFrame.

    Args:
        streets_gdf: GeoDataFrame with street geometries
        max_length: Maximum edge length in meters (for granularity control)
        intersection_tolerance: Distance to merge nearby nodes (meters)

    Returns:
        NetworkX graph, nodes GeoDataFrame, edges GeoDataFrame
    """
    print(f"Building network with max_length={max_length}m, tolerance={intersection_tolerance}m")

    # Ensure projected CRS for accurate distance calculations
    streets_proj = crs_utils.ensure_projected_crs(streets_gdf, "EPSG:32633", "Streets")

    # Create NetworkX graph
    G = nx.Graph()
    nodes_data = []
    edges_data = []

    # Process each street segment
    for street_idx, street in streets_proj.iterrows():
        geometry = street.geometry

        if geometry.geom_type == "LineString":
            coords = list(geometry.coords)

            # Split long edges if requested
            if max_length:
                coords = split_line_at_intervals(coords, max_length)

            # Add nodes and edges for this street
            for i in range(len(coords) - 1):
                # Create nodes
                node1_coords = coords[i]
                node2_coords = coords[i + 1]

                node1_id = f"street_{street_idx}_node_{i}"
                node2_id = f"street_{street_idx}_node_{i+1}"

                # Add nodes to graph
                G.add_node(node1_id, x=node1_coords[0], y=node1_coords[1])
                G.add_node(node2_id, x=node2_coords[0], y=node2_coords[1])

                # Calculate edge length
                edge_length = np.sqrt(
                    (node2_coords[0] - node1_coords[0]) ** 2
                    + (node2_coords[1] - node1_coords[1]) ** 2
                )

                # Add edge
                G.add_edge(node1_id, node2_id, length=edge_length, street_id=street_idx)

                # Store data for GeoDataFrames
                nodes_data.extend(
                    [
                        {"node_id": node1_id, "x": node1_coords[0], "y": node1_coords[1]},
                        {"node_id": node2_id, "x": node2_coords[0], "y": node2_coords[1]},
                    ]
                )

                edges_data.append(
                    {"u": node1_id, "v": node2_id, "length": edge_length, "street_id": street_idx}
                )

    # Merge nearby nodes (intersections)
    G = merge_nearby_nodes(G, intersection_tolerance)

    # Create GeoDataFrames
    nodes_gdf = create_nodes_gdf(G, streets_proj.crs)
    edges_gdf = create_edges_gdf(G, edges_data, streets_proj.crs)

    print(f"✅ Network built: {len(nodes_gdf)} nodes, {len(edges_gdf)} edges")
    return G, nodes_gdf, edges_gdf


def split_line_at_intervals(coords, max_length):
    """Split a line at regular intervals."""
    if len(coords) < 2:
        return coords

    result = [coords[0]]

    for i in range(len(coords) - 1):
        start = coords[i]
        end = coords[i + 1]

        # Calculate segment length
        segment_length = np.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)

        if segment_length > max_length:
            # Split segment
            num_splits = int(segment_length / max_length) + 1
            for j in range(1, num_splits):
                t = j / num_splits
                x = start[0] + t * (end[0] - start[0])
                y = start[1] + t * (end[1] - start[1])
                result.append((x, y))

        result.append(end)

    return result


def merge_nearby_nodes(G, tolerance):
    """Merge nodes that are very close to each other."""
    print(f"Merging nodes within {tolerance}m...")

    # Get node coordinates
    nodes = list(G.nodes())
    coords = np.array([(G.nodes[node]["x"], G.nodes[node]["y"]) for node in nodes])

    # Find nearby nodes
    distances = distance_matrix(coords, coords)
    np.fill_diagonal(distances, np.inf)

    # Group nearby nodes
    node_groups = []
    used_nodes = set()

    for i, node in enumerate(nodes):
        if node in used_nodes:
            continue

        group = [node]
        used_nodes.add(node)

        for j, other_node in enumerate(nodes):
            if other_node not in used_nodes and distances[i, j] <= tolerance:
                group.append(other_node)
                used_nodes.add(other_node)

        if len(group) > 1:
            node_groups.append(group)

    # Merge nodes in each group
    for group in node_groups:
        representative = group[0]

        for node in group[1:]:
            # Move all edges from this node to the representative
            for neighbor in list(G.neighbors(node)):
                if neighbor not in group:  # Don't create self-loops
                    if not G.has_edge(representative, neighbor):
                        G.add_edge(representative, neighbor, **G.edges[node, neighbor])
            G.remove_node(node)

    print(f"Merged {sum(len(g) - 1 for g in node_groups)} nodes")
    return G


def create_nodes_gdf(G, crs):
    """Create GeoDataFrame from NetworkX nodes."""
    nodes_data = []
    for node, data in G.nodes(data=True):
        if "x" in data and "y" in data:
            point = Point(data["x"], data["y"])
            nodes_data.append(
                {
                    "node_id": node,
                    "x": data["x"],
                    "y": data["y"],
                    "degree": G.degree(node),
                    "geometry": point,
                }
            )

    if nodes_data:
        return gpd.GeoDataFrame(nodes_data, crs=crs)
    else:
        return gpd.GeoDataFrame(crs=crs)


def create_edges_gdf(G, edges_data, crs):
    """Create GeoDataFrame from NetworkX edges."""
    if edges_data:
        # Create LineString geometries for edges
        for edge in edges_data:
            u_coords = (G.nodes[edge["u"]]["x"], G.nodes[edge["u"]]["y"])
            v_coords = (G.nodes[edge["v"]]["x"], G.nodes[edge["v"]]["y"])
            edge["geometry"] = LineString([u_coords, v_coords])

        return gpd.GeoDataFrame(edges_data, crs=crs)
    else:
        return gpd.GeoDataFrame(crs=crs)


def plot_network_comparison(networks, titles, figsize=(15, 5)):
    """Plot multiple networks for comparison."""
    fig, axes = plt.subplots(1, len(networks), figsize=figsize)
    if len(networks) == 1:
        axes = [axes]

    for i, (G, nodes_gdf, edges_gdf) in enumerate(networks):
        ax = axes[i]

        # Plot edges
        if not edges_gdf.empty:
            edges_gdf.plot(ax=ax, color="blue", linewidth=1, alpha=0.7)

        # Plot nodes
        if not nodes_gdf.empty:
            nodes_gdf.plot(ax=ax, color="red", markersize=20, alpha=0.8)

            # Label high-degree nodes (intersections)
            for idx, row in nodes_gdf.iterrows():
                if row["degree"] > 2:
                    ax.annotate(
                        f"{row['degree']}",
                        (row["x"], row["y"]),
                        fontsize=8,
                        ha="center",
                        va="bottom",
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7),
                    )

        ax.set_title(f"{titles[i]}\n{nodes_gdf.shape[0]} nodes, {edges_gdf.shape[0]} edges")
        ax.set_aspect("equal")

    plt.tight_layout()
    return fig


def analyze_network(G):
    """Analyze network properties."""
    analysis = {
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "is_connected": nx.is_connected(G),
        "num_components": nx.number_connected_components(G),
        "density": nx.density(G),
        "average_degree": (
            sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0
        ),
    }

    return analysis


def main():
    """Run the simple network example."""
    print("🏗️  Simple Street Network Example")
    print("=" * 50)

    # Load street data
    streets_file = "results_test/streets.geojson"
    if not os.path.exists(streets_file):
        print(f"❌ Streets file not found: {streets_file}")
        print("Run the data preparation pipeline first:")
        print("python main.py --config config_interactive_run.yaml")
        return

    streets_gdf = gpd.read_file(streets_file)
    print(f"Loaded {len(streets_gdf)} street segments")

    # Build networks with different granularity levels
    networks = []
    titles = []

    # No splitting (original)
    print("\n1. Building network without splitting...")
    G1, nodes1, edges1 = build_network_from_streets_simple(streets_gdf, max_length=None)
    networks.append((G1, nodes1, edges1))
    titles.append("Original (No Splitting)")

    # Medium granularity
    print("\n2. Building network with medium granularity...")
    G2, nodes2, edges2 = build_network_from_streets_simple(streets_gdf, max_length=200)
    networks.append((G2, nodes2, edges2))
    titles.append("Medium Granularity (200m)")

    # High granularity
    print("\n3. Building network with high granularity...")
    G3, nodes3, edges3 = build_network_from_streets_simple(streets_gdf, max_length=100)
    networks.append((G3, nodes3, edges3))
    titles.append("High Granularity (100m)")

    # Print comparison
    print("\n" + "=" * 50)
    print("NETWORK COMPARISON")
    print("=" * 50)
    print(f"{'Granularity':<20} {'Nodes':<8} {'Edges':<8} {'Avg Degree':<12} {'Density':<10}")
    print("-" * 60)

    for i, (G, nodes, edges) in enumerate(networks):
        analysis = analyze_network(G)
        print(
            f"{titles[i]:<20} "
            f"{analysis['num_nodes']:<8} "
            f"{analysis['num_edges']:<8} "
            f"{analysis['average_degree']:<12.2f} "
            f"{analysis['density']:<10.4f}"
        )

    # Plot comparison
    print("\nGenerating comparison plot...")
    fig = plot_network_comparison(networks, titles)
    plt.savefig("results_test/network_granularity_comparison.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Save networks
    print("\nSaving networks...")
    for i, (G, nodes, edges) in enumerate(networks):
        output_dir = f"results_test/network_{i+1}"
        os.makedirs(output_dir, exist_ok=True)

        nodes.to_file(f"{output_dir}/nodes.geojson", driver="GeoJSON")
        edges.to_file(f"{output_dir}/edges.geojson", driver="GeoJSON")

        # Save as GraphML
        nx.write_graphml(G, f"{output_dir}/network.graphml")

    print("\n" + "=" * 50)
    print("✅ Example completed!")
    print("=" * 50)
    print("\nGenerated files:")
    print("- results_test/network_granularity_comparison.png - Comparison plot")
    print("- results_test/network_*/ - Network files for each granularity level")
    print("\nKey insights:")
    print("1. Higher granularity = more nodes and edges")
    print("2. More nodes = better for detailed analysis")
    print("3. Choose granularity based on your analysis needs")


if __name__ == "__main__":
    main()
