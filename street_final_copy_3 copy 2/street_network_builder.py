#!/usr/bin/env python3
"""
Street Network Builder for Branitz Energy Decision AI

This script demonstrates how to build NetworkX graphs from street data using:
1. OSMnx (recommended for OSM data)
2. GeoDataFrame of streets (for custom data)

Features:
- Automatic CRS handling
- Node granularity control
- Street intersection detection
- Geometry preservation
- Network analysis capabilities
"""

import geopandas as gpd
import networkx as nx
import numpy as np
import os
import json
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
from scipy.spatial import distance_matrix
import matplotlib.pyplot as plt
from src import crs_utils

try:
    import osmnx as ox

    OSMNX_AVAILABLE = True
except ImportError:
    OSMNX_AVAILABLE = False
    print("Warning: OSMnx not available. Install with: pip install osmnx")


class StreetNetworkBuilder:
    """Build NetworkX graphs from street data with various options."""

    def __init__(self, target_crs="EPSG:32633"):
        """
        Initialize the street network builder.

        Args:
            target_crs: Target coordinate reference system (default: UTM Zone 33N)
        """
        self.target_crs = target_crs
        self.graph = None
        self.nodes_gdf = None
        self.edges_gdf = None

    def build_from_osmnx(
        self, osm_file, simplify=True, clean_periphery=True, custom_filter=None, max_length=None
    ):
        """
        Build NetworkX graph from OSM file using OSMnx.

        Args:
            osm_file: Path to OSM file
            simplify: Whether to simplify the graph topology
            clean_periphery: Whether to remove peripheral nodes
            custom_filter: Custom OSM filter (e.g., '["highway"~"primary|secondary|tertiary"]')
            max_length: Maximum edge length in meters (for granularity control)
        """
        if not OSMNX_AVAILABLE:
            raise ImportError("OSMnx is required for this method. Install with: pip install osmnx")

        print(f"Building network from OSM file: {osm_file}")

        # Load OSM data
        if custom_filter:
            G = ox.graph_from_xml(osm_file, custom_filter=custom_filter)
        else:
            G = ox.graph_from_xml(osm_file)

        # Project to target CRS
        G = ox.project_graph(G, to_crs=self.target_crs)

        # Simplify topology if requested
        if simplify:
            G = ox.simplify_graph(G)

        # Clean periphery if requested
        if clean_periphery:
            G = ox.remove_isolated_nodes(G)

        # Control granularity by splitting long edges
        if max_length:
            G = self._split_long_edges(G, max_length)

        # Convert to GeoDataFrames
        self.nodes_gdf, self.edges_gdf = ox.graph_to_gdfs(G)
        self.graph = G

        print(f"✅ Built network with {len(self.nodes_gdf)} nodes and {len(self.edges_gdf)} edges")
        return G, self.nodes_gdf, self.edges_gdf

    def build_from_geodataframe(
        self, streets_gdf, max_length=None, intersection_tolerance=1.0, simplify_edges=True
    ):
        """
        Build NetworkX graph from GeoDataFrame of streets.

        Args:
            streets_gdf: GeoDataFrame with street geometries
            max_length: Maximum edge length in meters (for granularity control)
            intersection_tolerance: Distance tolerance for intersection detection (meters)
            simplify_edges: Whether to simplify edge geometries
        """
        print("Building network from GeoDataFrame...")

        # Ensure projected CRS
        streets_proj = crs_utils.ensure_projected_crs(streets_gdf, self.target_crs, "Streets")

        # Create NetworkX graph
        G = nx.Graph()

        # Process each street segment
        edge_id = 0
        all_points = []
        edge_data = []

        for idx, street in streets_proj.iterrows():
            geometry = street.geometry

            if geometry.geom_type == "LineString":
                # Get coordinates
                coords = list(geometry.coords)

                # Split long edges if requested
                if max_length:
                    coords = self._split_line_at_intervals(coords, max_length)

                # Add nodes and edges
                for i in range(len(coords) - 1):
                    point1 = Point(coords[i])
                    point2 = Point(coords[i + 1])

                    # Create edge
                    edge_geom = LineString([point1, point2])
                    edge_length = edge_geom.length

                    # Add nodes
                    node1_id = f"node_{edge_id}_{i}"
                    node2_id = f"node_{edge_id}_{i+1}"

                    G.add_node(node1_id, x=point1.x, y=point1.y, geometry=point1)
                    G.add_node(node2_id, x=point2.x, y=point2.y, geometry=point2)

                    # Add edge
                    G.add_edge(
                        node1_id,
                        node2_id,
                        length=edge_length,
                        geometry=edge_geom,
                        street_id=idx,
                        original_geometry=geometry,
                    )

                    all_points.extend([point1, point2])
                    edge_data.append(
                        {
                            "u": node1_id,
                            "v": node2_id,
                            "length": edge_length,
                            "geometry": edge_geom,
                            "street_id": idx,
                        }
                    )

                edge_id += 1

        # Merge nearby nodes (intersections)
        G = self._merge_nearby_nodes(G, intersection_tolerance)

        # Create GeoDataFrames
        self.nodes_gdf = self._graph_to_nodes_gdf(G)
        self.edges_gdf = self._graph_to_edges_gdf(G, edge_data)
        self.graph = G

        print(f"✅ Built network with {len(self.nodes_gdf)} nodes and {len(self.edges_gdf)} edges")
        return G, self.nodes_gdf, self.edges_gdf

    def _split_line_at_intervals(self, coords, max_length):
        """Split a line at regular intervals."""
        if len(coords) < 2:
            return coords

        result_coords = [coords[0]]

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
                    result_coords.append((x, y))

            result_coords.append(end)

        return result_coords

    def _split_long_edges(self, G, max_length):
        """Split long edges in OSMnx graph."""
        print(f"Splitting edges longer than {max_length} meters...")

        edges_to_remove = []
        edges_to_add = []

        for u, v, data in G.edges(data=True):
            if data.get("length", 0) > max_length:
                # Get edge geometry
                if "geometry" in data:
                    line = data["geometry"]
                else:
                    # Create line from node coordinates
                    u_coords = (G.nodes[u]["x"], G.nodes[u]["y"])
                    v_coords = (G.nodes[v]["x"], G.nodes[v]["y"])
                    line = LineString([u_coords, v_coords])

                # Split line
                coords = list(line.coords)
                split_coords = self._split_line_at_intervals(coords, max_length)

                # Mark edge for removal
                edges_to_remove.append((u, v))

                # Add new edges
                for i in range(len(split_coords) - 1):
                    if i == 0:
                        new_u = u
                    else:
                        new_u = f"split_{u}_{v}_{i}"
                        G.add_node(new_u, x=split_coords[i][0], y=split_coords[i][1])

                    if i == len(split_coords) - 2:
                        new_v = v
                    else:
                        new_v = f"split_{u}_{v}_{i+1}"
                        G.add_node(new_v, x=split_coords[i + 1][0], y=split_coords[i + 1][1])

                    new_edge_data = data.copy()
                    new_edge_data["length"] = np.sqrt(
                        (split_coords[i + 1][0] - split_coords[i][0]) ** 2
                        + (split_coords[i + 1][1] - split_coords[i][1]) ** 2
                    )
                    new_edge_data["geometry"] = LineString([split_coords[i], split_coords[i + 1]])

                    edges_to_add.append((new_u, new_v, new_edge_data))

        # Apply changes
        G.remove_edges_from(edges_to_remove)
        G.add_edges_from(edges_to_add)

        print(f"Split {len(edges_to_remove)} edges into {len(edges_to_add)} edges")
        return G

    def _merge_nearby_nodes(self, G, tolerance):
        """Merge nodes that are very close to each other."""
        print(f"Merging nodes within {tolerance} meters...")

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
            if len(group) > 1:
                # Use the first node as the representative
                representative = group[0]

                # Merge edges
                for node in group[1:]:
                    # Move all edges from this node to the representative
                    for neighbor in list(G.neighbors(node)):
                        if neighbor not in group:  # Don't create self-loops
                            if not G.has_edge(representative, neighbor):
                                G.add_edge(representative, neighbor, **G.edges[node, neighbor])
                    G.remove_node(node)

        print(f"Merged {sum(len(g) - 1 for g in node_groups)} nodes")
        return G

    def _graph_to_nodes_gdf(self, G):
        """Convert NetworkX graph nodes to GeoDataFrame."""
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
            gdf = gpd.GeoDataFrame(nodes_data, crs=self.target_crs)
            return gdf
        else:
            return gpd.GeoDataFrame(crs=self.target_crs)

    def _graph_to_edges_gdf(self, G, edge_data):
        """Convert NetworkX graph edges to GeoDataFrame."""
        if edge_data:
            gdf = gpd.GeoDataFrame(edge_data, crs=self.target_crs)
            return gdf
        else:
            return gpd.GeoDataFrame(crs=self.target_crs)

    def save_network(self, output_dir="results_test"):
        """Save the network to files."""
        os.makedirs(output_dir, exist_ok=True)

        if self.nodes_gdf is not None:
            self.nodes_gdf.to_file(
                os.path.join(output_dir, "network_nodes.geojson"), driver="GeoJSON"
            )

        if self.edges_gdf is not None:
            self.edges_gdf.to_file(
                os.path.join(output_dir, "network_edges.geojson"), driver="GeoJSON"
            )

        if self.graph is not None:
            # Save as GraphML
            nx.write_graphml(self.graph, os.path.join(output_dir, "street_network.graphml"))

            # Save as pickle
            import pickle

            with open(os.path.join(output_dir, "street_network.pkl"), "wb") as f:
                pickle.dump(self.graph, f)

        print(f"✅ Network saved to {output_dir}")

    def plot_network(self, figsize=(12, 12), node_size=20, edge_width=2):
        """Plot the network."""
        if self.nodes_gdf is None or self.edges_gdf is None:
            print("❌ No network to plot. Build network first.")
            return

        fig, ax = plt.subplots(figsize=figsize)

        # Plot edges
        self.edges_gdf.plot(ax=ax, color="blue", linewidth=edge_width, alpha=0.7)

        # Plot nodes
        self.nodes_gdf.plot(ax=ax, color="red", markersize=node_size, alpha=0.8)

        # Add node labels for high-degree nodes
        for idx, row in self.nodes_gdf.iterrows():
            if row["degree"] > 2:  # Only label intersection nodes
                ax.annotate(
                    row["node_id"], (row["x"], row["y"]), fontsize=8, ha="center", va="bottom"
                )

        ax.set_title(f"Street Network: {len(self.nodes_gdf)} nodes, {len(self.edges_gdf)} edges")
        ax.set_aspect("equal")
        plt.tight_layout()

        return fig, ax

    def analyze_network(self):
        """Analyze network properties."""
        if self.graph is None:
            print("❌ No network to analyze. Build network first.")
            return

        analysis = {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "is_connected": nx.is_connected(self.graph),
            "num_components": nx.number_connected_components(self.graph),
            "density": nx.density(self.graph),
            "average_degree": sum(dict(self.graph.degree()).values())
            / self.graph.number_of_nodes(),
            "average_clustering": nx.average_clustering(self.graph),
            "average_shortest_path_length": (
                nx.average_shortest_path_length(self.graph) if nx.is_connected(self.graph) else None
            ),
        }

        print("\n=== Network Analysis ===")
        for key, value in analysis.items():
            print(f"{key}: {value}")

        return analysis


def example_osmnx_approach():
    """Example using OSMnx approach."""
    print("=" * 60)
    print("Example 1: OSMnx Approach")
    print("=" * 60)

    if not OSMNX_AVAILABLE:
        print("❌ OSMnx not available. Skipping this example.")
        return

    builder = StreetNetworkBuilder()

    # Build network with different granularity levels
    osm_file = "data/osm/branitzer_siedlung.osm"

    # High granularity (more nodes)
    G_high, nodes_high, edges_high = builder.build_from_osmnx(
        osm_file,
        max_length=50,  # Split edges longer than 50m
        custom_filter='["highway"~"primary|secondary|tertiary|residential"]',
    )

    print(f"High granularity: {len(nodes_high)} nodes, {len(edges_high)} edges")

    # Save and plot
    builder.save_network("results_test/network_high_granularity")
    fig, ax = builder.plot_network()
    plt.savefig("results_test/network_high_granularity.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Analyze network
    analysis = builder.analyze_network()

    return builder


def example_geodataframe_approach():
    """Example using GeoDataFrame approach."""
    print("\n" + "=" * 60)
    print("Example 2: GeoDataFrame Approach")
    print("=" * 60)

    builder = StreetNetworkBuilder()

    # Load streets from processed data
    streets_file = "results_test/streets.geojson"
    if not os.path.exists(streets_file):
        print(f"❌ Streets file not found: {streets_file}")
        print("Run the data preparation pipeline first.")
        return

    streets_gdf = gpd.read_file(streets_file)

    # Build network with different granularity levels
    G, nodes, edges = builder.build_from_geodataframe(
        streets_gdf,
        max_length=100,  # Split edges longer than 100m
        intersection_tolerance=2.0,  # Merge nodes within 2m
    )

    print(f"GeoDataFrame approach: {len(nodes)} nodes, {len(edges)} edges")

    # Save and plot
    builder.save_network("results_test/network_geodataframe")
    fig, ax = builder.plot_network()
    plt.savefig("results_test/network_geodataframe.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Analyze network
    analysis = builder.analyze_network()

    return builder


def example_granularity_comparison():
    """Compare different granularity levels."""
    print("\n" + "=" * 60)
    print("Example 3: Granularity Comparison")
    print("=" * 60)

    streets_file = "results_test/streets.geojson"
    if not os.path.exists(streets_file):
        print(f"❌ Streets file not found: {streets_file}")
        return

    streets_gdf = gpd.read_file(streets_file)

    granularity_levels = [None, 200, 100, 50]  # No split, 200m, 100m, 50m

    results = []

    for max_length in granularity_levels:
        print(f"\nBuilding network with max_length={max_length}m...")

        builder = StreetNetworkBuilder()
        G, nodes, edges = builder.build_from_geodataframe(
            streets_gdf, max_length=max_length, intersection_tolerance=2.0
        )

        analysis = builder.analyze_network()
        results.append(
            {
                "max_length": max_length,
                "num_nodes": analysis["num_nodes"],
                "num_edges": analysis["num_edges"],
                "average_degree": analysis["average_degree"],
                "density": analysis["density"],
            }
        )

        # Save network
        builder.save_network(f"results_test/network_granularity_{max_length or 'none'}")

    # Print comparison
    print("\n=== Granularity Comparison ===")
    print(f"{'Max Length':<12} {'Nodes':<8} {'Edges':<8} {'Avg Degree':<12} {'Density':<10}")
    print("-" * 50)
    for result in results:
        print(
            f"{result['max_length'] or 'None':<12} "
            f"{result['num_nodes']:<8} "
            f"{result['num_edges']:<8} "
            f"{result['average_degree']:<12.2f} "
            f"{result['density']:<10.4f}"
        )

    return results


def main():
    """Run all examples."""
    print("🏗️  Street Network Builder Examples")
    print("=" * 60)

    # Check dependencies
    try:
        import geopandas as gpd
        import networkx as nx

        print("✅ Required packages available")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        return

    # Run examples
    example_osmnx_approach()
    example_geodataframe_approach()
    example_granularity_comparison()

    print("\n" + "=" * 60)
    print("🎉 All examples completed!")
    print("=" * 60)
    print("\nGenerated files:")
    print("- results_test/network_*/ - Network files for each approach")
    print("- results_test/*.png - Network visualizations")
    print("- results_test/*.geojson - Node and edge GeoJSON files")
    print("- results_test/*.graphml - NetworkX GraphML files")


if __name__ == "__main__":
    main()
