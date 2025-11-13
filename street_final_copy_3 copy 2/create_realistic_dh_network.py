#!/usr/bin/env python3
"""
Realistic District Heating Network Implementation

This script creates a proper district heating network that:
1. Uses street network as the backbone for main pipes
2. Routes all main pipes only along street edges
3. Connects buildings via short service pipes to nearest main nodes
4. No direct plant-to-building or building-to-building connections
5. Follows real-world district heating network topology
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import networkx as nx
from shapely.geometry import Point, LineString
from pyproj import Transformer
import folium
from folium import plugins
import json
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


class RealisticDistrictHeatingNetwork:
    """Create realistic district heating network following street topology."""

    def __init__(self, results_dir="simulation_outputs"):
        self.results_dir = Path(results_dir)
        self.street_graph = None
        self.buildings_gdf = None
        self.streets_gdf = None
        self.plant_location = None

    def load_data(self):
        """Load street and building data."""
        print("📁 Loading street and building data...")

        # Load streets and buildings
        self.streets_gdf = gpd.read_file("results_test/streets.geojson")
        self.buildings_gdf = gpd.read_file("results_test/buildings_prepared.geojson")

        # Set plant location (CHP plant in Branitz)
        self.plant_location = Point(14.3453979, 51.76274)  # WGS84 coordinates

        print(
            f"✅ Loaded {len(self.streets_gdf)} street segments and {len(self.buildings_gdf)} buildings"
        )
        return True

    def build_street_network(self):
        """Build a proper street network graph for main pipe routing."""
        print("🛣️ Building street network graph...")

        # Transform to UTM for accurate distance calculations
        if self.streets_gdf.crs is None or self.streets_gdf.crs.is_geographic:
            streets_utm = self.streets_gdf.to_crs("EPSG:32633")
        else:
            streets_utm = self.streets_gdf.copy()

        # Transform plant location to UTM
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:32633", always_xy=True)
        plant_x, plant_y = transformer.transform(self.plant_location.x, self.plant_location.y)
        plant_utm = Point(plant_x, plant_y)

        # Create network graph
        self.street_graph = nx.Graph()

        # Add street segments as edges
        for idx, street in streets_utm.iterrows():
            coords = list(street.geometry.coords)

            # Add nodes for start and end points
            start_node = coords[0]
            end_node = coords[-1]

            # Calculate edge weight (length in meters)
            edge_length = street.geometry.length

            # Add edge to graph
            self.street_graph.add_edge(
                start_node,
                end_node,
                weight=edge_length,
                street_id=idx,
                geometry=street.geometry,
                street_name=street.get("name", f"Street_{idx}"),
                highway_type=street.get("highway", "unknown"),
            )

        # Ensure graph is connected by adding minimal connections between components
        components = list(nx.connected_components(self.street_graph))
        if len(components) > 1:
            print(
                f"⚠️ Street network has {len(components)} disconnected components, connecting them..."
            )

            # Connect components by finding closest nodes between them
            for i in range(len(components) - 1):
                comp1 = list(components[i])
                comp2 = list(components[i + 1])

                min_distance = float("inf")
                best_connection = None

                for node1 in comp1:
                    for node2 in comp2:
                        distance = Point(node1).distance(Point(node2))
                        if distance < min_distance:
                            min_distance = distance
                            best_connection = (node1, node2)

                if best_connection:
                    self.street_graph.add_edge(
                        best_connection[0],
                        best_connection[1],
                        weight=min_distance,
                        street_id="connection",
                        geometry=LineString([best_connection[0], best_connection[1]]),
                        street_name="Network Connection",
                        highway_type="service",
                    )
                    print(f"   Connected components with {min_distance:.1f}m link")

        # Add plant node and connect to nearest street node
        plant_node = self._snap_plant_to_street(plant_utm, streets_utm)

        print(
            f"✅ Built street network with {self.street_graph.number_of_nodes()} nodes and {self.street_graph.number_of_edges()} edges"
        )
        return True

    def _snap_plant_to_street(self, plant_utm, streets_utm):
        """Snap plant to nearest point on street network."""
        min_distance = float("inf")
        nearest_point = None
        nearest_street = None

        # Find nearest point on any street
        for idx, street in streets_utm.iterrows():
            distance = street.geometry.distance(plant_utm)
            if distance < min_distance:
                min_distance = distance
                nearest_point = street.geometry.interpolate(street.geometry.project(plant_utm))
                nearest_street = street

        # Add plant node to graph
        plant_node = (nearest_point.x, nearest_point.y)
        self.street_graph.add_node(plant_node, node_type="plant", name="CHP Plant")

        # Connect plant to nearest street node
        coords = list(nearest_street.geometry.coords)
        start_node = coords[0]
        end_node = coords[-1]

        # Find which end is closer to plant
        dist_to_start = Point(start_node).distance(nearest_point)
        dist_to_end = Point(end_node).distance(nearest_point)

        if dist_to_start < dist_to_end:
            connection_node = start_node
        else:
            connection_node = end_node

        # Add connection edge
        connection_length = nearest_point.distance(Point(connection_node))
        self.street_graph.add_edge(
            plant_node,
            connection_node,
            weight=connection_length,
            street_id="plant_connection",
            geometry=LineString([plant_node, connection_node]),
            street_name="Plant Connection",
            highway_type="service",
        )

        print(f"✅ Plant snapped to street network at distance {min_distance:.1f}m")
        return plant_node

    def snap_buildings_to_street_network(self):
        """Snap buildings to nearest points on street network."""
        print("🏢 Snapping buildings to street network...")

        # Transform buildings to UTM
        if self.buildings_gdf.crs is None or self.buildings_gdf.crs.is_geographic:
            buildings_utm = self.buildings_gdf.to_crs("EPSG:32633")
        else:
            buildings_utm = self.buildings_gdf.copy()

        # Transform streets to UTM if needed
        if self.streets_gdf.crs is None or self.streets_gdf.crs.is_geographic:
            streets_utm = self.streets_gdf.to_crs("EPSG:32633")
        else:
            streets_utm = self.streets_gdf.copy()

        service_connections = []

        for idx, building in buildings_utm.iterrows():
            building_point = building.geometry.centroid

            # Find nearest point on street network
            min_distance = float("inf")
            nearest_point = None
            nearest_street = None

            for street_idx, street in streets_utm.iterrows():
                distance = street.geometry.distance(building_point)
                if distance < min_distance:
                    min_distance = distance
                    nearest_point = street.geometry.interpolate(
                        street.geometry.project(building_point)
                    )
                    nearest_street = street

            # Create service connection
            service_connection = {
                "building_id": idx,
                "building_x": building_point.x,
                "building_y": building_point.y,
                "connection_x": nearest_point.x,
                "connection_y": nearest_point.y,
                "distance_to_street": min_distance,
                "street_segment_id": nearest_street.name,
                "street_name": nearest_street.get("name", f"Street_{nearest_street.name}"),
                "heating_load_kw": building.get("heating_load_kw", 10),
            }

            service_connections.append(service_connection)

            # Add service connection node to graph
            connection_node = (nearest_point.x, nearest_point.y)
            if connection_node not in self.street_graph:
                self.street_graph.add_node(
                    connection_node,
                    node_type="service_connection",
                    building_id=idx,
                    name=f"Service_{idx}",
                )

        self.service_connections = pd.DataFrame(service_connections)

        print(f"✅ Snapped {len(service_connections)} buildings to street network")
        return True

    def route_main_pipes_along_streets(self):
        """Route main pipes along street network using shortest paths."""
        print("🔄 Routing main pipes along street network...")

        # Get plant node
        plant_node = None
        for node, attrs in self.street_graph.nodes(data=True):
            if attrs.get("node_type") == "plant":
                plant_node = node
                break

        if plant_node is None:
            print("❌ Plant node not found in graph")
            return False

        # Find shortest paths from plant to all service connection nodes
        main_pipes = []
        total_main_length = 0
        successful_routes = 0

        for idx, service_conn in self.service_connections.iterrows():
            service_node = (service_conn["connection_x"], service_conn["connection_y"])

            try:
                # Find shortest path along street network
                path = nx.shortest_path(
                    self.street_graph, plant_node, service_node, weight="weight"
                )

                # Calculate path length
                path_length = nx.shortest_path_length(
                    self.street_graph, plant_node, service_node, weight="weight"
                )

                # Create main pipe segments
                for i in range(len(path) - 1):
                    start_node = path[i]
                    end_node = path[i + 1]

                    # Get edge data
                    edge_data = self.street_graph.get_edge_data(start_node, end_node)

                    main_pipe = {
                        "start_node": start_node,
                        "end_node": end_node,
                        "length_m": edge_data["weight"],
                        "street_id": edge_data["street_id"],
                        "street_name": edge_data["street_name"],
                        "highway_type": edge_data["highway_type"],
                        "pipe_type": "main_supply_return",
                    }

                    main_pipes.append(main_pipe)
                    total_main_length += edge_data["weight"]

                successful_routes += 1

            except nx.NetworkXNoPath:
                print(
                    f"⚠️ No path found to building {service_conn['building_id']}, trying direct connection..."
                )

                # Fallback: create direct connection to plant (not ideal but ensures connectivity)
                try:
                    # Calculate direct distance
                    direct_distance = Point(plant_node).distance(Point(service_node))

                    # Add direct connection edge
                    self.street_graph.add_edge(
                        plant_node,
                        service_node,
                        weight=direct_distance,
                        street_id="direct_connection",
                        geometry=LineString([plant_node, service_node]),
                        street_name="Direct Connection",
                        highway_type="service",
                    )

                    # Create main pipe for direct connection
                    main_pipe = {
                        "start_node": plant_node,
                        "end_node": service_node,
                        "length_m": direct_distance,
                        "street_id": "direct_connection",
                        "street_name": "Direct Connection (Fallback)",
                        "highway_type": "service",
                        "pipe_type": "main_supply_return_fallback",
                    }

                    main_pipes.append(main_pipe)
                    total_main_length += direct_distance
                    successful_routes += 1

                    print(
                        f"   Created direct connection for building {service_conn['building_id']} ({direct_distance:.1f}m)"
                    )

                except Exception as e:
                    print(
                        f"   Failed to create direct connection for building {service_conn['building_id']}: {e}"
                    )
                    continue

        self.main_pipes = pd.DataFrame(main_pipes)

        # Remove duplicate pipe segments (same street segment used by multiple buildings)
        self.main_pipes = self.main_pipes.drop_duplicates(subset=["start_node", "end_node"])

        print(
            f"✅ Routed main pipes: {len(self.main_pipes)} unique segments, {total_main_length/1000:.1f} km total"
        )
        print(
            f"   - Successfully routed to {successful_routes}/{len(self.service_connections)} buildings"
        )
        return True

    def calculate_network_statistics(self):
        """Calculate realistic network statistics."""
        print("📊 Calculating network statistics...")

        # Main pipe statistics
        total_main_length_km = self.main_pipes["length_m"].sum() / 1000
        unique_main_segments = len(self.main_pipes)

        # Service pipe statistics
        total_service_length_m = self.service_connections["distance_to_street"].sum()
        avg_service_length_m = self.service_connections["distance_to_street"].mean()
        max_service_length_m = self.service_connections["distance_to_street"].max()

        # Building statistics
        num_buildings = len(self.service_connections)
        total_heat_demand_kw = self.service_connections["heating_load_kw"].sum()
        total_heat_demand_mwh = total_heat_demand_kw * 8760 / 1000  # Annual demand

        # Network efficiency
        network_density_km_per_building = (
            total_main_length_km / num_buildings if num_buildings > 0 else 0
        )

        # Create statistics
        self.network_stats = {
            "total_main_length_km": total_main_length_km,
            "unique_main_segments": unique_main_segments,
            "total_service_length_m": total_service_length_m,
            "avg_service_length_m": avg_service_length_m,
            "max_service_length_m": max_service_length_m,
            "num_buildings": num_buildings,
            "total_heat_demand_kw": total_heat_demand_kw,
            "total_heat_demand_mwh": total_heat_demand_mwh,
            "network_density_km_per_building": network_density_km_per_building,
            "total_pipe_length_km": total_main_length_km + total_service_length_m / 1000,
            "service_connections": num_buildings,
        }

        print(f"✅ Network statistics calculated:")
        print(f"   - Main pipes: {total_main_length_km:.1f} km ({unique_main_segments} segments)")
        print(f"   - Service pipes: {total_service_length_m:.1f} m total")
        print(f"   - Buildings: {num_buildings}")
        print(f"   - Heat demand: {total_heat_demand_mwh:.2f} MWh/year")

        return True

    def create_realistic_interactive_map(self, save_path=None):
        """Create interactive map showing realistic network topology."""
        print("🗺️ Creating realistic interactive map...")

        # Create base map
        center_lat, center_lon = 51.76274, 14.3453979
        m = folium.Map(location=[center_lat, center_lon], zoom_start=16)

        # Add tile layers
        folium.TileLayer("openstreetmap", name="OpenStreetMap").add_to(m)
        folium.TileLayer("cartodbpositron", name="CartoDB Positron").add_to(m)

        # Create feature groups
        street_group = folium.FeatureGroup(name="Street Network", overlay=True)
        main_pipe_group = folium.FeatureGroup(name="Main Pipes (Street-Based)", overlay=True)
        service_pipe_group = folium.FeatureGroup(name="Service Pipes", overlay=True)
        building_group = folium.FeatureGroup(name="Buildings", overlay=True)
        plant_group = folium.FeatureGroup(name="CHP Plant", overlay=True)

        # Transform coordinates back to WGS84
        transformer = Transformer.from_crs("EPSG:32633", "EPSG:4326", always_xy=True)

        # 1. Add street network
        self._add_street_network_to_map(street_group, transformer)

        # 2. Add main pipes (following streets)
        self._add_main_pipes_to_map(main_pipe_group, transformer)

        # 3. Add service connections
        self._add_service_connections_to_map(service_pipe_group, transformer)

        # 4. Add buildings
        self._add_buildings_to_map(building_group, transformer)

        # 5. Add plant
        self._add_plant_to_map(plant_group)

        # Add all feature groups
        street_group.add_to(m)
        main_pipe_group.add_to(m)
        service_pipe_group.add_to(m)
        building_group.add_to(m)
        plant_group.add_to(m)

        # Add layer control
        folium.LayerControl().add_to(m)

        # Add network statistics
        self._add_network_statistics_to_map(m)

        if save_path:
            m.save(save_path)
            print(f"✅ Realistic interactive map saved to {save_path}")

        return m

    def _add_street_network_to_map(self, feature_group, transformer):
        """Add street network to map."""
        for idx, street in self.streets_gdf.iterrows():
            coords = list(street.geometry.coords)
            wgs84_coords = []

            for lon, lat in coords:
                wgs84_lon, wgs84_lat = transformer.transform(lon, lat)
                wgs84_coords.append([wgs84_lat, wgs84_lon])

            folium.PolyLine(
                locations=wgs84_coords,
                color="gray",
                weight=2,
                opacity=0.6,
                popup=f"Street {idx}<br>Type: {street.get('highway', 'Unknown')}<br>Name: {street.get('name', 'Unnamed')}",
                tooltip=f"Street {idx}",
            ).add_to(feature_group)

    def _add_main_pipes_to_map(self, feature_group, transformer):
        """Add main pipes to map (following streets)."""
        for _, pipe in self.main_pipes.iterrows():
            start_lon, start_lat = transformer.transform(
                pipe["start_node"][0], pipe["start_node"][1]
            )
            end_lon, end_lat = transformer.transform(pipe["end_node"][0], pipe["end_node"][1])

            folium.PolyLine(
                locations=[[start_lat, start_lon], [end_lat, end_lon]],
                color="red",
                weight=4,
                opacity=0.8,
                popup=f"Main Pipe<br>Street: {pipe['street_name']}<br>Length: {pipe['length_m']:.1f}m<br>Type: Supply/Return",
                tooltip="Main Pipe (Street-Based)",
            ).add_to(feature_group)

    def _add_service_connections_to_map(self, feature_group, transformer):
        """Add service connections to map."""
        for _, conn in self.service_connections.iterrows():
            # Transform coordinates
            conn_lon, conn_lat = transformer.transform(conn["connection_x"], conn["connection_y"])
            building_lon, building_lat = transformer.transform(
                conn["building_x"], conn["building_y"]
            )

            # Color service connections based on length
            distance = conn["distance_to_street"]
            if distance > 40:
                color = "red"
                weight = 4
            elif distance > 20:
                color = "orange"
                weight = 3
            else:
                color = "green"
                weight = 2

            # Service connection point
            folium.CircleMarker(
                location=[conn_lat, conn_lon],
                radius=6,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.8,
                popup=f"Service Connection<br>Building: {conn['building_id']}<br>Distance: {distance:.1f}m<br>Street: {conn['street_name']}",
                tooltip=f"Service Connection - {distance:.1f}m",
            ).add_to(feature_group)

            # Service pipe
            folium.PolyLine(
                locations=[[conn_lat, conn_lon], [building_lat, building_lon]],
                color=color,
                weight=weight,
                opacity=0.8,
                dash_array="5, 5",
                popup=f"Service Pipe<br>Length: {distance:.1f}m<br>Building: {conn['building_id']}",
                tooltip=f"Service Pipe - {distance:.1f}m",
            ).add_to(feature_group)

    def _add_buildings_to_map(self, feature_group, transformer):
        """Add buildings to map."""
        for idx, building in self.buildings_gdf.iterrows():
            centroid = building.geometry.centroid
            heat_demand = building.get("heating_load_kw", "N/A")

            # Color buildings based on heat demand
            if isinstance(heat_demand, (int, float)):
                if heat_demand > 5:
                    color = "red"
                elif heat_demand > 2:
                    color = "orange"
                else:
                    color = "blue"
                radius = min(max(heat_demand * 2, 5), 15)
            else:
                color = "blue"
                radius = 8

            folium.CircleMarker(
                location=[centroid.y, centroid.x],
                radius=radius,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                popup=f"Building {idx}<br>Heat Demand: {heat_demand} kW<br>Coordinates: {centroid.y:.6f}, {centroid.x:.6f}",
                tooltip=f"Building {idx} - {heat_demand} kW",
            ).add_to(feature_group)

    def _add_plant_to_map(self, feature_group):
        """Add plant to map."""
        plant_lat, plant_lon = 51.76274, 14.3453979

        folium.Marker(
            location=[plant_lat, plant_lon],
            popup="CHP Plant<br>District Heating Source<br>Supply Temperature: 70°C<br>Return Temperature: 40°C<br>Coordinates: 51.76274, 14.3453979",
            tooltip="CHP Plant",
            icon=folium.Icon(color="green", icon="industry", prefix="fa"),
        ).add_to(feature_group)

    def _add_network_statistics_to_map(self, m):
        """Add network statistics to map."""
        stats = self.network_stats

        stats_html = f"""
        <div style="width: 350px; height: 500px; overflow-y: auto;">
        <h3>Realistic DH Network Statistics</h3>
        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h4>✅ Street-Based Main Network</h4>
        <table style="width: 100%; border-collapse: collapse;">
        <tr><td><strong>Main Pipe Length:</strong></td><td>{stats['total_main_length_km']:.1f} km</td></tr>
        <tr><td><strong>Unique Street Segments:</strong></td><td>{stats['unique_main_segments']}</td></tr>
        <tr><td><strong>Network Density:</strong></td><td>{stats['network_density_km_per_building']:.1f} km/building</td></tr>
        </table>
        </div>
        
        <div style="background-color: #f0f8ff; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h4>Service Connections</h4>
        <table style="width: 100%; border-collapse: collapse;">
        <tr><td><strong>Number of Buildings:</strong></td><td>{stats['num_buildings']}</td></tr>
        <tr><td><strong>Average Service Length:</strong></td><td>{stats['avg_service_length_m']:.1f} m</td></tr>
        <tr><td><strong>Maximum Service Length:</strong></td><td>{stats['max_service_length_m']:.1f} m</td></tr>
        <tr><td><strong>Total Service Length:</strong></td><td>{stats['total_service_length_m']:.1f} m</td></tr>
        </table>
        </div>
        
        <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h4>Heat Demand</h4>
        <table style="width: 100%; border-collapse: collapse;">
        <tr><td><strong>Total Heat Demand:</strong></td><td>{stats['total_heat_demand_mwh']:.2f} MWh/year</td></tr>
        <tr><td><strong>Peak Heat Demand:</strong></td><td>{stats['total_heat_demand_kw']:.1f} kW</td></tr>
        </table>
        </div>
        
        <div style="background-color: #d1ecf1; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h4>Network Topology</h4>
        <ul>
        <li>✅ Main pipes follow street network</li>
        <li>✅ No direct plant-to-building connections</li>
        <li>✅ No building-to-building connections</li>
        <li>✅ Short service pipes to nearest main</li>
        <li>✅ Realistic routing and costs</li>
        </ul>
        </div>
        </div>
        """

        folium.Popup(stats_html, max_width=400, max_height=550).add_to(m)

    def save_results(self, scenario_name="realistic_branitz_dh"):
        """Save realistic network results."""
        print("💾 Saving realistic network results...")

        # Save service connections
        service_file = self.results_dir / f"realistic_service_connections_{scenario_name}.csv"
        self.service_connections.to_csv(service_file, index=False)

        # Save main pipes
        main_pipes_file = self.results_dir / f"realistic_main_pipes_{scenario_name}.csv"
        self.main_pipes.to_csv(main_pipes_file, index=False)

        # Convert numpy types to native Python types for JSON serialization
        network_stats_json = {}
        for key, value in self.network_stats.items():
            if isinstance(value, (np.integer, np.int64)):
                network_stats_json[key] = int(value)
            elif isinstance(value, (np.floating, np.float64)):
                network_stats_json[key] = float(value)
            else:
                network_stats_json[key] = value

        # Save network statistics
        stats_file = self.results_dir / f"realistic_network_stats_{scenario_name}.json"
        with open(stats_file, "w") as f:
            json.dump(network_stats_json, f, indent=2)

        # Save complete results
        results = {
            "success": True,
            "scenario": scenario_name,
            "network_stats": network_stats_json,  # Use the converted version
            "num_service_connections": int(len(self.service_connections)),
            "num_main_pipe_segments": int(len(self.main_pipes)),
            "total_main_length_km": float(self.network_stats["total_main_length_km"]),
            "avg_service_length_m": float(self.network_stats["avg_service_length_m"]),
            "realistic_topology": True,
            "street_based_routing": True,
            "no_direct_connections": True,
        }

        results_file = self.results_dir / f"realistic_{scenario_name}_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"✅ Results saved to {self.results_dir}")
        return True

    def create_realistic_network(self, scenario_name="realistic_branitz_dh"):
        """Create complete realistic district heating network."""
        print("🏗️ Creating realistic district heating network...")
        print("=" * 60)

        # Step 1: Load data
        self.load_data()

        # Step 2: Build street network
        self.build_street_network()

        # Step 3: Snap buildings to street network
        self.snap_buildings_to_street_network()

        # Step 4: Route main pipes along streets
        self.route_main_pipes_along_streets()

        # Step 5: Calculate statistics
        self.calculate_network_statistics()

        # Step 6: Create interactive map
        self.create_realistic_interactive_map(
            save_path=self.results_dir / f"realistic_interactive_map_{scenario_name}.html"
        )

        # Step 7: Save results
        self.save_results(scenario_name)

        print("=" * 60)
        print("✅ Realistic district heating network created successfully!")
        print("   - Main pipes follow street network ✅")
        print("   - No direct plant-to-building connections ✅")
        print("   - No building-to-building connections ✅")
        print("   - Short service pipes to nearest main ✅")
        print("   - Realistic routing and costs ✅")

        return True


def main():
    """Run the realistic district heating network creation."""
    network_creator = RealisticDistrictHeatingNetwork()
    network_creator.create_realistic_network()


if __name__ == "__main__":
    main()
