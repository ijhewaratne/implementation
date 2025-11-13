#!/usr/bin/env python3
"""
Realistic District Heating Network in Pandapipes

This script demonstrates how to build a district heating network using:
1. Street graph as backbone for main pipes
2. Service pipes connecting buildings to street mains
3. Pandapipes integration for hydraulic analysis
"""

import geopandas as gpd
import networkx as nx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
from pyproj import Transformer
import pandapipes as pp
import pandapipes.networks as pn
from src import crs_utils
import os

# Plant coordinates in WGS84
PLANT_LAT, PLANT_LON = 51.76274, 14.3453979


class DistrictHeatingNetwork:
    """Build realistic district heating network using street graph backbone."""

    def __init__(self, target_crs="EPSG:32633"):
        """
        Initialize the district heating network builder.

        Args:
            target_crs: Target coordinate reference system
        """
        self.target_crs = target_crs
        self.street_graph = None
        self.buildings_gdf = None
        self.streets_gdf = None
        self.plant_location = None
        self.service_connections = {}
        self.main_pipe_network = None
        self.pandapipes_net = None

    def transform_plant_coordinates(self):
        """Transform plant coordinates from WGS84 to UTM."""
        transformer = Transformer.from_crs("EPSG:4326", self.target_crs, always_xy=True)
        plant_x, plant_y = transformer.transform(PLANT_LON, PLANT_LAT)

        print(f"Plant coordinates:")
        print(f"  WGS84: {PLANT_LAT:.6f}, {PLANT_LON:.6f}")
        print(f"  UTM: {plant_x:.2f}, {plant_y:.2f}")

        self.plant_location = (plant_x, plant_y)
        return plant_x, plant_y

    def build_street_graph(self, streets_gdf, max_segment_length=50):
        """
        Build NetworkX graph from street GeoDataFrame with sufficient granularity.

        Args:
            streets_gdf: GeoDataFrame with street geometries
            max_segment_length: Maximum length of street segments (meters)

        Returns:
            NetworkX graph with nodes at intersections and sufficient granularity
        """
        print(f"Building street graph from {len(streets_gdf)} street segments...")

        # Ensure projected CRS for accurate distances
        streets_proj = crs_utils.ensure_projected_crs(streets_gdf, self.target_crs, "Streets")

        # Create NetworkX graph
        G = nx.Graph()

        # Process each street segment
        for idx, street in streets_proj.iterrows():
            street_geom = street.geometry
            coords = list(street_geom.coords)

            # Split long segments if needed
            segments = self._split_long_segment(coords, max_segment_length)

            # Add nodes and edges for each segment
            for i, segment in enumerate(segments):
                node1_id = f"street_{idx}_{i}"
                node2_id = f"street_{idx}_{i+1}"

                # Add nodes with coordinates
                G.add_node(node1_id, pos=segment[0], node_type="street", street_id=idx)
                G.add_node(node2_id, pos=segment[1], node_type="street", street_id=idx)

                # Add edge with length
                length = Point(segment[0]).distance(Point(segment[1]))
                G.add_edge(
                    node1_id,
                    node2_id,
                    weight=length,
                    length=length,
                    edge_type="street",
                    street_id=idx,
                )

        # Connect nearby nodes to ensure network connectivity
        self._ensure_network_connectivity(G)

        # Merge nearby nodes (within 1 meter) to create intersections
        self._merge_nearby_nodes(G, threshold=1.0)

        print(
            f"✅ Street graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges"
        )

        self.street_graph = G
        return G

    def _split_long_segment(self, coords, max_length):
        """Split a long street segment into smaller segments."""
        segments = []

        for i in range(len(coords) - 1):
            start_point = coords[i]
            end_point = coords[i + 1]

            segment_length = Point(start_point).distance(Point(end_point))

            if segment_length <= max_length:
                segments.append((start_point, end_point))
            else:
                # Split segment into multiple parts
                num_splits = int(np.ceil(segment_length / max_length))
                for j in range(num_splits):
                    t = j / num_splits
                    split_point = (
                        start_point[0] + t * (end_point[0] - start_point[0]),
                        start_point[1] + t * (end_point[1] - start_point[1]),
                    )

                    if j == 0:
                        segments.append((start_point, split_point))
                    else:
                        prev_point = segments[-1][1]
                        segments.append((prev_point, split_point))

                # Add final segment
                segments.append((segments[-1][1], end_point))

        return segments

    def _ensure_network_connectivity(self, G, max_distance=5.0):
        """Ensure network connectivity by connecting nearby nodes."""
        print("Ensuring network connectivity...")

        nodes = list(G.nodes())
        added_edges = 0

        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes[i + 1 :], i + 1):
                if not G.has_edge(node1, node2):
                    pos1 = G.nodes[node1]["pos"]
                    pos2 = G.nodes[node2]["pos"]
                    distance = Point(pos1).distance(Point(pos2))

                    if distance < max_distance:
                        G.add_edge(
                            node1, node2, weight=distance, length=distance, edge_type="connection"
                        )
                        added_edges += 1

        print(f"✅ Added {added_edges} connectivity edges")

    def _merge_nearby_nodes(self, G, threshold=1.0):
        """Merge nearby nodes to create proper intersections."""
        print("Merging nearby nodes...")

        nodes_to_merge = []
        nodes = list(G.nodes())

        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes[i + 1 :], i + 1):
                pos1 = G.nodes[node1]["pos"]
                pos2 = G.nodes[node2]["pos"]
                distance = Point(pos1).distance(Point(pos2))

                if distance < threshold:
                    nodes_to_merge.append((node1, node2))

        # Merge nodes (keep node1, remove node2)
        for node1, node2 in nodes_to_merge:
            if node1 in G.nodes() and node2 in G.nodes():
                # Move all edges from node2 to node1
                for neighbor in list(G.neighbors(node2)):
                    if neighbor != node1:
                        edge_data = G.get_edge_data(node2, neighbor)
                        G.add_edge(node1, neighbor, **edge_data)

                # Remove node2
                G.remove_node(node2)

        print(f"✅ Merged {len(nodes_to_merge)} node pairs")

    def snap_plant_to_street_graph(self):
        """Snap plant location to nearest node on street graph."""
        print("Snapping plant to street graph...")

        if self.street_graph is None:
            raise ValueError("Street graph must be built first")

        plant_point = Point(self.plant_location)
        nearest_node = None
        min_distance = float("inf")

        for node in self.street_graph.nodes():
            node_pos = self.street_graph.nodes[node]["pos"]
            node_point = Point(node_pos)
            distance = plant_point.distance(node_point)

            if distance < min_distance:
                min_distance = distance
                nearest_node = node

        if nearest_node:
            # Add plant node and connect to nearest street node
            self.street_graph.add_node("PLANT", pos=self.plant_location, node_type="plant")
            self.street_graph.add_edge(
                "PLANT",
                nearest_node,
                weight=min_distance,
                length=min_distance,
                edge_type="plant_connection",
            )

            print(f"✅ Plant snapped to street node {nearest_node} ({min_distance:.2f}m)")
            return nearest_node
        else:
            raise ValueError("No street nodes found")

    def snap_buildings_to_street_graph(self, buildings_gdf, max_distance=100):
        """
        Snap buildings to nearest points along street segments.

        Args:
            buildings_gdf: GeoDataFrame with building geometries
            max_distance: Maximum distance to consider for snapping (meters)

        Returns:
            Dictionary with service connection information
        """
        print(f"Snapping {len(buildings_gdf)} buildings to street graph...")

        # Ensure projected CRS
        buildings_proj = crs_utils.ensure_projected_crs(buildings_gdf, self.target_crs, "Buildings")

        service_connections = {}

        for idx, building in buildings_proj.iterrows():
            building_geom = building.geometry
            building_id = building.get("GebaeudeID", f"building_{idx}")

            # Find nearest point along street graph
            nearest_point, nearest_node, distance = self._find_nearest_street_point(building_geom)

            if distance <= max_distance:
                # Create service connection node
                service_node_id = f"service_{building_id}"
                self.street_graph.add_node(
                    service_node_id, pos=nearest_point, node_type="service", building_id=building_id
                )

                # Connect service node to nearest street node
                self.street_graph.add_edge(
                    service_node_id,
                    nearest_node,
                    weight=distance,
                    length=distance,
                    edge_type="service_connection",
                )

                service_connections[building_id] = {
                    "service_node": service_node_id,
                    "nearest_street_node": nearest_node,
                    "connection_point": nearest_point,
                    "building_centroid": (building_geom.centroid.x, building_geom.centroid.y),
                    "distance_to_street": distance,
                }

                print(f"  ✅ {building_id}: {distance:.2f}m to {nearest_node}")
            else:
                print(f"  ❌ {building_id}: No street within {max_distance}m")

        self.service_connections = service_connections
        print(f"✅ Snapped {len(service_connections)} buildings to street graph")
        return service_connections

    def _find_nearest_street_point(self, building_geom):
        """Find nearest point along street graph to building."""
        building_point = building_geom.centroid
        min_distance = float("inf")
        nearest_point = None
        nearest_node = None

        # Check distance to all street nodes
        for node in self.street_graph.nodes():
            if self.street_graph.nodes[node]["node_type"] == "street":
                node_pos = self.street_graph.nodes[node]["pos"]
                node_point = Point(node_pos)
                distance = building_point.distance(node_point)

                if distance < min_distance:
                    min_distance = distance
                    nearest_point = node_pos
                    nearest_node = node

        return nearest_point, nearest_node, min_distance

    def build_main_pipe_network(self):
        """
        Build main pipe network by finding shortest paths from plant to all service connections.

        Returns:
            NetworkX graph representing the main pipe network
        """
        print("Building main pipe network...")

        if "PLANT" not in self.street_graph.nodes():
            raise ValueError("Plant must be snapped to street graph first")

        # Find shortest paths from plant to all service connections
        main_pipe_edges = set()

        for building_id, connection in self.service_connections.items():
            service_node = connection["service_node"]

            try:
                # Find shortest path from plant to service node
                path = nx.shortest_path(self.street_graph, "PLANT", service_node, weight="weight")

                # Add all edges in the path to main pipe network
                for i in range(len(path) - 1):
                    edge = tuple(sorted([path[i], path[i + 1]]))
                    main_pipe_edges.add(edge)

                print(f"  ✅ {building_id}: {len(path)} nodes")

            except nx.NetworkXNoPath:
                print(f"  ❌ {building_id}: No path found")

        # Create main pipe network graph
        main_network = nx.Graph()

        # Add all nodes and edges from main pipe network
        for edge in main_pipe_edges:
            node1, node2 = edge
            edge_data = self.street_graph.get_edge_data(node1, node2)

            # Add nodes if not already present
            if node1 not in main_network.nodes():
                main_network.add_node(node1, **self.street_graph.nodes[node1])
            if node2 not in main_network.nodes():
                main_network.add_node(node2, **self.street_graph.nodes[node2])

            # Add edge
            main_network.add_edge(node1, node2, **edge_data)

        self.main_pipe_network = main_network

        print(
            f"✅ Main pipe network created with {main_network.number_of_nodes()} nodes and {main_network.number_of_edges()} edges"
        )
        return main_network

    def create_pandapipes_network(self, main_pipe_diameter=400, service_pipe_diameter=50):
        """
        Create pandapipes network from the main pipe and service connections.

        Args:
            main_pipe_diameter: Diameter of main pipes (mm)
            service_pipe_diameter: Diameter of service pipes (mm)

        Returns:
            Pandapipes network
        """
        print("Creating pandapipes network...")

        # Create empty pandapipes network
        net = pp.create_empty_network("district_heating_network")

        # Add junctions for all nodes
        junctions = {}

        # Add plant junction (ext_grid)
        plant_junction = pp.create_junction(
            net,
            pn_bar=1.0,
            tfluid_k=353.15,  # 80°C
            name="PLANT",
            geodata=(self.plant_location[0], self.plant_location[1]),
        )
        junctions["PLANT"] = plant_junction

        # Add junctions for main pipe network
        for node in self.main_pipe_network.nodes():
            if node != "PLANT":
                node_data = self.main_pipe_network.nodes[node]
                pos = node_data["pos"]

                junction = pp.create_junction(
                    net, pn_bar=1.0, tfluid_k=353.15, name=node, geodata=(pos[0], pos[1])
                )
                junctions[node] = junction

        # Add junctions for buildings
        for building_id, connection in self.service_connections.items():
            building_pos = connection["building_centroid"]

            building_junction = pp.create_junction(
                net,
                pn_bar=1.0,
                tfluid_k=353.15,
                name=f"building_{building_id}",
                geodata=(building_pos[0], building_pos[1]),
            )
            junctions[f"building_{building_id}"] = building_junction

        # Add main pipes
        main_pipes = []
        for edge in self.main_pipe_network.edges():
            node1, node2 = edge
            edge_data = self.main_pipe_network.get_edge_data(node1, node2)

            pipe = pp.create_pipe_from_parameters(
                net,
                from_junction=junctions[node1],
                to_junction=junctions[node2],
                length_km=edge_data["length"] / 1000,
                diameter_m=main_pipe_diameter / 1000,
                name=f"main_{node1}_{node2}",
            )
            main_pipes.append(pipe)

        # Add service pipes
        service_pipes = []
        for building_id, connection in self.service_connections.items():
            service_node = connection["service_node"]
            building_junction = junctions[f"building_{building_id}"]
            service_junction = junctions[service_node]

            # Calculate service pipe length
            building_pos = connection["building_centroid"]
            service_pos = connection["connection_point"]
            service_length = Point(building_pos).distance(Point(service_pos))

            pipe = pp.create_pipe_from_parameters(
                net,
                from_junction=service_junction,
                to_junction=building_junction,
                length_km=service_length / 1000,
                diameter_m=service_pipe_diameter / 1000,
                name=f"service_{building_id}",
            )
            service_pipes.append(pipe)

        # Add external grid (plant)
        ext_grid = pp.create_ext_grid(
            net, junction=junctions["PLANT"], p_bar=1.0, t_k=353.15, name="PLANT_EXT_GRID"
        )

        # Add heat consumers (buildings)
        consumers = []
        for building_id in self.service_connections.keys():
            building_junction = junctions[f"building_{building_id}"]

            consumer = pp.create_sink(
                net,
                junction=building_junction,
                mdot_kg_per_s=0.1,  # 0.1 kg/s heat demand
                name=f"consumer_{building_id}",
            )
            consumers.append(consumer)

        self.pandapipes_net = net

        print(f"✅ Pandapipes network created:")
        print(f"   - {len(junctions)} junctions")
        print(f"   - {len(main_pipes)} main pipes")
        print(f"   - {len(service_pipes)} service pipes")
        print(f"   - 1 external grid (plant)")
        print(f"   - {len(consumers)} heat consumers")

        return net

    def validate_network(self):
        """Validate that the network meets requirements."""
        print("Validating network...")

        validation_results = {
            "plant_connected": False,
            "all_buildings_connected": False,
            "main_pipes_on_streets": False,
            "service_pipes_short": False,
            "no_star_topology": False,
        }

        # Check if plant is connected
        if "PLANT" in self.street_graph.nodes():
            validation_results["plant_connected"] = True

        # Check if all buildings are connected
        if len(self.service_connections) == len(self.buildings_gdf):
            validation_results["all_buildings_connected"] = True

        # Check if main pipes follow street network
        if self.main_pipe_network:
            street_edges = set()
            for edge in self.street_graph.edges():
                street_edges.add(tuple(sorted(edge)))

            main_edges = set()
            for edge in self.main_pipe_network.edges():
                main_edges.add(tuple(sorted(edge)))

            # All main pipe edges should be street edges
            if main_edges.issubset(street_edges):
                validation_results["main_pipes_on_streets"] = True

        # Check if service pipes are short
        max_service_length = 100  # meters
        service_lengths = [conn["distance_to_street"] for conn in self.service_connections.values()]
        if all(length <= max_service_length for length in service_lengths):
            validation_results["service_pipes_short"] = True

        # Check for no star topology (plant should have only one connection)
        if "PLANT" in self.street_graph.nodes():
            plant_degree = self.street_graph.degree("PLANT")
            if plant_degree == 1:
                validation_results["no_star_topology"] = True

        # Print validation results
        print("Validation Results:")
        for check, result in validation_results.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check}: {result}")

        return validation_results

    def plot_network(self, figsize=(16, 12), save_path=None):
        """Plot the complete district heating network."""
        fig, ax = plt.subplots(figsize=figsize)

        # Plot street network (background)
        if self.streets_gdf is not None:
            self.streets_gdf.plot(ax=ax, color="lightgray", linewidth=1, alpha=0.5)

        # Plot main pipe network
        if self.main_pipe_network:
            main_edges = list(self.main_pipe_network.edges())
            for edge in main_edges:
                node1, node2 = edge
                pos1 = self.main_pipe_network.nodes[node1]["pos"]
                pos2 = self.main_pipe_network.nodes[node2]["pos"]
                ax.plot(
                    [pos1[0], pos2[0]],
                    [pos1[1], pos2[1]],
                    "red",
                    linewidth=3,
                    alpha=0.8,
                    label="Main Pipes" if edge == main_edges[0] else "",
                )

        # Plot service connections
        for building_id, connection in self.service_connections.items():
            building_pos = connection["building_centroid"]
            service_pos = connection["connection_point"]

            # Plot service pipe
            ax.plot(
                [service_pos[0], building_pos[0]],
                [service_pos[1], building_pos[1]],
                "blue",
                linewidth=2,
                alpha=0.8,
                linestyle="--",
            )

        # Plot nodes
        if self.main_pipe_network:
            node_coords = np.array(
                [
                    self.main_pipe_network.nodes[node]["pos"]
                    for node in self.main_pipe_network.nodes()
                ]
            )
            ax.scatter(
                node_coords[:, 0],
                node_coords[:, 1],
                color="red",
                s=50,
                alpha=0.8,
                label="Main Network Nodes",
            )

        # Plot plant
        ax.scatter(
            self.plant_location[0],
            self.plant_location[1],
            color="green",
            s=200,
            marker="s",
            label="Plant",
            zorder=5,
        )

        # Plot buildings
        building_coords = np.array(
            [conn["building_centroid"] for conn in self.service_connections.values()]
        )
        ax.scatter(
            building_coords[:, 0],
            building_coords[:, 1],
            color="blue",
            s=100,
            alpha=0.8,
            label="Buildings",
            zorder=4,
        )

        # Plot service connection points
        service_coords = np.array(
            [conn["connection_point"] for conn in self.service_connections.values()]
        )
        ax.scatter(
            service_coords[:, 0],
            service_coords[:, 1],
            color="orange",
            s=80,
            alpha=0.8,
            label="Service Connections",
            zorder=3,
        )

        ax.set_title("District Heating Network\nMain Pipes (Red) + Service Pipes (Blue)")
        ax.set_aspect("equal")
        ax.legend()
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✅ Plot saved to {save_path}")

        return fig, ax

    def save_network_data(self, output_dir="results_test"):
        """Save network data to files."""
        os.makedirs(output_dir, exist_ok=True)

        # Save main pipe network
        if self.main_pipe_network:
            main_pipe_data = []
            for edge in self.main_pipe_network.edges():
                node1, node2 = edge
                edge_data = self.main_pipe_network.get_edge_data(node1, node2)
                pos1 = self.main_pipe_network.nodes[node1]["pos"]
                pos2 = self.main_pipe_network.nodes[node2]["pos"]

                main_pipe_data.append(
                    {
                        "from_node": node1,
                        "to_node": node2,
                        "from_x": pos1[0],
                        "from_y": pos1[1],
                        "to_x": pos2[0],
                        "to_y": pos2[1],
                        "length_m": edge_data["length"],
                        "edge_type": edge_data["edge_type"],
                    }
                )

            main_pipes_df = pd.DataFrame(main_pipe_data)
            main_pipes_df.to_csv(os.path.join(output_dir, "main_pipe_network.csv"), index=False)
            print(f"✅ Main pipe network saved to {output_dir}/main_pipe_network.csv")

        # Save service connections
        if self.service_connections:
            service_data = []
            for building_id, connection in self.service_connections.items():
                service_data.append(
                    {
                        "building_id": building_id,
                        "service_node": connection["service_node"],
                        "nearest_street_node": connection["nearest_street_node"],
                        "connection_x": connection["connection_point"][0],
                        "connection_y": connection["connection_point"][1],
                        "building_x": connection["building_centroid"][0],
                        "building_y": connection["building_centroid"][1],
                        "distance_to_street": connection["distance_to_street"],
                    }
                )

            service_df = pd.DataFrame(service_data)
            service_df.to_csv(os.path.join(output_dir, "service_connections.csv"), index=False)
            print(f"✅ Service connections saved to {output_dir}/service_connections.csv")

        # Save pandapipes network
        if self.pandapipes_net:
            pp.to_json(self.pandapipes_net, os.path.join(output_dir, "pandapipes_network.json"))
            print(f"✅ Pandapipes network saved to {output_dir}/pandapipes_network.json")


def main():
    """Run the complete district heating network example."""
    print("🏭 Realistic District Heating Network in Pandapipes")
    print("=" * 60)

    # Initialize network builder
    dh_network = DistrictHeatingNetwork()

    # Transform plant coordinates
    dh_network.transform_plant_coordinates()

    # Load data
    buildings_file = "results_test/buildings_prepared.geojson"
    streets_file = "results_test/streets.geojson"

    if not os.path.exists(buildings_file) or not os.path.exists(streets_file):
        print(f"❌ Required files not found.")
        print("Run the data preparation pipeline first:")
        print("python main.py --config config_interactive_run.yaml")
        return

    dh_network.buildings_gdf = gpd.read_file(buildings_file)
    dh_network.streets_gdf = gpd.read_file(streets_file)

    print(
        f"Loaded {len(dh_network.buildings_gdf)} buildings and {len(dh_network.streets_gdf)} street segments"
    )

    # Step 1: Build street graph
    dh_network.build_street_graph(dh_network.streets_gdf, max_segment_length=50)

    # Step 2: Snap plant to street graph
    dh_network.snap_plant_to_street_graph()

    # Step 3: Snap buildings to street graph
    dh_network.snap_buildings_to_street_graph(dh_network.buildings_gdf, max_distance=100)

    # Step 4: Build main pipe network
    dh_network.build_main_pipe_network()

    # Step 5: Create pandapipes network
    dh_network.create_pandapipes_network(main_pipe_diameter=400, service_pipe_diameter=50)

    # Step 6: Validate network
    validation_results = dh_network.validate_network()

    # Step 7: Plot network
    fig, ax = dh_network.plot_network(save_path="results_test/district_heating_network.png")

    # Step 8: Save network data
    dh_network.save_network_data()

    print("\n" + "=" * 60)
    print("✅ District heating network completed!")
    print("=" * 60)
    print("\nKey outputs:")
    print("- main_pipe_network.csv - Main pipe network data")
    print("- service_connections.csv - Service connection data")
    print("- pandapipes_network.json - Pandapipes network file")
    print("- district_heating_network.png - Network visualization")
    print("\nNetwork features:")
    print("- Street graph backbone for main pipes")
    print("- Service pipes connecting buildings to mains")
    print("- Pandapipes integration for hydraulic analysis")
    print("- Realistic network topology")


if __name__ == "__main__":
    main()
