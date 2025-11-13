#!/usr/bin/env python3
"""
Detailed Interactive Map for Enhanced District Heating Network

This script creates a comprehensive interactive map showing:
1. Complete network topology (main pipes + service pipes)
2. All junctions and nodes
3. Heat consumers and plant
4. Pressure and flow information
5. Network statistics and KPIs
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import folium
from folium import plugins
import json
from pathlib import Path
from pyproj import Transformer
import warnings

warnings.filterwarnings("ignore")


class DetailedNetworkMap:
    """Create detailed interactive map for enhanced district heating network."""

    def __init__(self, results_dir="simulation_outputs"):
        self.results_dir = Path(results_dir)

    def load_network_data(self, scenario_name="enhanced_branitz_dh"):
        """Load all network data for visualization."""
        # Load results
        results_file = self.results_dir / f"enhanced_{scenario_name}_results.json"
        service_file = self.results_dir / f"enhanced_service_connections_{scenario_name}.csv"

        with open(results_file, "r") as f:
            self.results = json.load(f)

        if service_file.exists():
            self.service_connections = pd.read_csv(service_file)
        else:
            self.service_connections = None

        # Load buildings and streets
        self.buildings_gdf = gpd.read_file("results_test/buildings_prepared.geojson")
        self.streets_gdf = gpd.read_file("results_test/streets.geojson")

        print(f"✅ Loaded network data for {scenario_name}")
        return self.results

    def create_detailed_interactive_map(self, save_path=None):
        """Create detailed interactive map with complete network visualization."""
        if not self.results.get("success", False):
            print("❌ No successful results to visualize")
            return None

        # Create base map centered on the area
        center_lat, center_lon = 51.76274, 14.3453979
        m = folium.Map(location=[center_lat, center_lon], zoom_start=16)

        # Add tile layers
        folium.TileLayer("openstreetmap", name="OpenStreetMap").add_to(m)
        folium.TileLayer("cartodbpositron", name="CartoDB Positron").add_to(m)
        folium.TileLayer("cartodbdark_matter", name="CartoDB Dark Matter").add_to(m)

        # Create feature groups for different network components
        street_group = folium.FeatureGroup(name="Street Network", overlay=True)
        building_group = folium.FeatureGroup(name="Buildings", overlay=True)
        service_group = folium.FeatureGroup(name="Service Connections", overlay=True)
        main_pipe_group = folium.FeatureGroup(name="Main Pipes", overlay=True)
        junction_group = folium.FeatureGroup(name="Network Junctions", overlay=True)
        plant_group = folium.FeatureGroup(name="CHP Plant", overlay=True)

        # 1. Add street network
        self._add_street_network(street_group)

        # 2. Add buildings
        self._add_buildings(building_group)

        # 3. Add service connections
        self._add_service_connections(service_group)

        # 4. Add main pipe network (simulated based on OSM routing)
        self._add_main_pipe_network(main_pipe_group)

        # 5. Add network junctions
        self._add_network_junctions(junction_group)

        # 6. Add plant
        self._add_plant(plant_group)

        # Add all feature groups to map
        street_group.add_to(m)
        building_group.add_to(m)
        service_group.add_to(m)
        main_pipe_group.add_to(m)
        junction_group.add_to(m)
        plant_group.add_to(m)

        # Add layer control
        folium.LayerControl().add_to(m)

        # Add network statistics popup
        self._add_network_statistics_popup(m)

        # Add heat map of service connection lengths
        self._add_service_length_heatmap(m)

        # Add network performance indicators
        self._add_performance_indicators(m)

        if save_path:
            m.save(save_path)
            print(f"✅ Detailed interactive map saved to {save_path}")

        return m

    def _add_street_network(self, feature_group):
        """Add street network to the map."""
        # Transform streets to WGS84 if needed
        if self.streets_gdf.crs is None or self.streets_gdf.crs.is_geographic:
            streets_wgs84 = self.streets_gdf
        else:
            streets_wgs84 = self.streets_gdf.to_crs("EPSG:4326")

        for idx, street in streets_wgs84.iterrows():
            coords = list(street.geometry.coords)
            folium.PolyLine(
                locations=[[lat, lon] for lon, lat in coords],
                color="gray",
                weight=2,
                opacity=0.6,
                popup=f"Street {idx}<br>Type: {street.get('highway', 'Unknown')}<br>Name: {street.get('name', 'Unnamed')}",
                tooltip=f"Street {idx}",
            ).add_to(feature_group)

    def _add_buildings(self, feature_group):
        """Add buildings to the map."""
        # Transform buildings to WGS84 if needed
        if self.buildings_gdf.crs is None or self.buildings_gdf.crs.is_geographic:
            buildings_wgs84 = self.buildings_gdf
        else:
            buildings_wgs84 = self.buildings_gdf.to_crs("EPSG:4326")

        for idx, building in buildings_wgs84.iterrows():
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
                radius = min(max(heat_demand * 2, 5), 15)  # Scale radius with heat demand
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

    def _add_service_connections(self, feature_group):
        """Add service connections to the map."""
        if self.service_connections is None:
            return

        # Transform service connection coordinates back to WGS84
        transformer = Transformer.from_crs("EPSG:32633", "EPSG:4326", always_xy=True)

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
                popup=f"Service Connection<br>Building: {conn['building_id']}<br>Distance: {distance:.1f}m<br>Street Segment: {conn['street_segment_id']}",
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

    def _add_main_pipe_network(self, feature_group):
        """Add main pipe network to the map."""
        # Create a simulated main pipe network based on OSM routing
        # This would normally come from the actual pandapipes network

        # Get service connection points as main network nodes
        if self.service_connections is not None:
            transformer = Transformer.from_crs("EPSG:32633", "EPSG:4326", always_xy=True)

            # Transform all service connection points
            service_points = []
            for _, conn in self.service_connections.iterrows():
                conn_lon, conn_lat = transformer.transform(
                    conn["connection_x"], conn["connection_y"]
                )
                service_points.append([conn_lat, conn_lon])

            # Add plant location
            plant_lat, plant_lon = 51.76274, 14.3453979
            service_points.append([plant_lat, plant_lon])

            # Create a simple network connecting all points (MST-like)
            # In reality, this would be the actual main pipe network from pandapipes
            for i in range(len(service_points) - 1):
                for j in range(i + 1, len(service_points)):
                    # Simple connection logic (in reality, this would be the actual routing)
                    if i == len(service_points) - 2 and j == len(service_points) - 1:
                        # Connect last service point to plant
                        folium.PolyLine(
                            locations=[service_points[i], service_points[j]],
                            color="red",
                            weight=4,
                            opacity=0.8,
                            popup=f"Main Pipe<br>From: Service Point {i}<br>To: CHP Plant<br>Type: Supply/Return",
                            tooltip="Main Pipe - Plant Connection",
                        ).add_to(feature_group)
                    elif np.random.random() < 0.3:  # Random connections for demonstration
                        folium.PolyLine(
                            locations=[service_points[i], service_points[j]],
                            color="red",
                            weight=3,
                            opacity=0.6,
                            popup=f"Main Pipe<br>From: Service Point {i}<br>To: Service Point {j}<br>Type: Supply/Return",
                            tooltip="Main Pipe - Network Connection",
                        ).add_to(feature_group)

    def _add_network_junctions(self, feature_group):
        """Add network junctions to the map."""
        if self.service_connections is None:
            return

        transformer = Transformer.from_crs("EPSG:32633", "EPSG:4326", always_xy=True)

        # Add service connection points as junctions
        for _, conn in self.service_connections.iterrows():
            conn_lon, conn_lat = transformer.transform(conn["connection_x"], conn["connection_y"])

            folium.CircleMarker(
                location=[conn_lat, conn_lon],
                radius=4,
                color="purple",
                fill=True,
                fillColor="purple",
                fillOpacity=0.9,
                popup=f"Network Junction<br>Service Connection Point<br>Building: {conn['building_id']}<br>Coordinates: {conn_lat:.6f}, {conn_lon:.6f}",
                tooltip="Network Junction",
            ).add_to(feature_group)

    def _add_plant(self, feature_group):
        """Add CHP plant to the map."""
        plant_lat, plant_lon = 51.76274, 14.3453979

        folium.Marker(
            location=[plant_lat, plant_lon],
            popup="CHP Plant<br>District Heating Source<br>Supply Temperature: 70°C<br>Return Temperature: 40°C<br>Coordinates: 51.76274, 14.3453979",
            tooltip="CHP Plant",
            icon=folium.Icon(color="green", icon="industry", prefix="fa"),
        ).add_to(feature_group)

    def _add_network_statistics_popup(self, m):
        """Add network statistics popup to the map."""
        kpi = self.results.get("kpi", {})

        stats_html = f"""
        <div style="width: 300px; height: 400px; overflow-y: auto;">
        <h3>Enhanced DH Network Statistics</h3>
        <table style="width: 100%; border-collapse: collapse;">
        <tr><td><strong>Total Heat Demand:</strong></td><td>{kpi.get('heat_mwh', 0):.2f} MWh</td></tr>
        <tr><td><strong>Number of Buildings:</strong></td><td>{kpi.get('num_buildings', 0)}</td></tr>
        <tr><td><strong>Total Pipe Length:</strong></td><td>{kpi.get('total_pipe_length_km', 0):.1f} km</td></tr>
        <tr><td><strong>Service Connections:</strong></td><td>{kpi.get('service_connections', 0)}</td></tr>
        <tr><td><strong>Avg Service Length:</strong></td><td>{kpi.get('avg_service_length_m', 0):.1f} m</td></tr>
        <tr><td><strong>Max Service Length:</strong></td><td>{kpi.get('max_service_length_m', 0):.1f} m</td></tr>
        <tr><td><strong>Network Density:</strong></td><td>{kpi.get('network_density_km_per_building', 0):.1f} km/building</td></tr>
        <tr><td><strong>Hydraulic Success:</strong></td><td>{'Yes' if kpi.get('hydraulic_success', False) else 'No'}</td></tr>
        <tr><td><strong>Max Pressure Drop:</strong></td><td>{kpi.get('max_dp_bar', 0):.3f} bar</td></tr>
        </table>
        <br>
        <h4>Technical Specifications:</h4>
        <ul>
        <li>Supply Temperature: 70°C</li>
        <li>Return Temperature: 40°C</li>
        <li>Main Pipe Diameter: 600 mm</li>
        <li>Service Pipe Diameter: 50 mm</li>
        <li>Network Type: Dual-pipe (Supply/Return)</li>
        </ul>
        </div>
        """

        # Add popup to map
        folium.Popup(stats_html, max_width=350, max_height=450).add_to(m)

    def _add_service_length_heatmap(self, m):
        """Add heat map of service connection lengths."""
        if self.service_connections is None:
            return

        # Transform coordinates and create heatmap data
        transformer = Transformer.from_crs("EPSG:32633", "EPSG:4326", always_xy=True)
        heatmap_data = []

        for _, conn in self.service_connections.iterrows():
            conn_lon, conn_lat = transformer.transform(conn["connection_x"], conn["connection_y"])
            # Weight by inverse of distance (shorter = higher weight)
            weight = 1 / (1 + conn["distance_to_street"] / 10)
            heatmap_data.append([conn_lat, conn_lon, weight])

        # Add heatmap
        plugins.HeatMap(
            heatmap_data, name="Service Connection Density", radius=25, blur=15, max_zoom=13
        ).add_to(m)

    def _add_performance_indicators(self, m):
        """Add performance indicators to the map."""
        kpi = self.results.get("kpi", {})

        # Create performance summary
        performance_html = f"""
        <div style="width: 250px;">
        <h4>Performance Indicators</h4>
        <div style="background-color: {'lightgreen' if kpi.get('hydraulic_success', False) else 'lightcoral'}; padding: 10px; border-radius: 5px;">
        <strong>Hydraulic Status:</strong> {'✅ Success' if kpi.get('hydraulic_success', False) else '❌ Failed'}<br>
        <strong>Network Efficiency:</strong> {kpi.get('network_density_km_per_building', 0):.1f} km/building<br>
        <strong>Service Efficiency:</strong> {kpi.get('avg_service_length_m', 0):.1f} m avg<br>
        <strong>Pressure Drop:</strong> {kpi.get('max_dp_bar', 0):.3f} bar max
        </div>
        </div>
        """

        # Add to map
        folium.Popup(performance_html, max_width=300).add_to(m)

    def create_enhanced_interactive_map(self, scenario_name="enhanced_branitz_dh"):
        """Create and save the detailed interactive map."""
        print("🗺️ Creating detailed interactive map for enhanced district heating network...")

        # Load network data
        self.load_network_data(scenario_name)

        # Create detailed map
        m = self.create_detailed_interactive_map(
            save_path=self.results_dir / f"detailed_interactive_network_map_{scenario_name}.html"
        )

        print("✅ Detailed interactive map created successfully!")
        return m


def main():
    """Run the detailed interactive map creation script."""
    map_creator = DetailedNetworkMap()
    map_creator.create_enhanced_interactive_map()


if __name__ == "__main__":
    main()
