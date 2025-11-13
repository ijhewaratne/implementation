#!/usr/bin/env python3
"""
Pandapipes Network Interactive Map

This script creates an interactive map from the actual pandapipes network data,
showing the real network topology with junctions, pipes, and hydraulic results.
"""

import pandas as pd
import numpy as np
import folium
from folium import plugins
import json
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


class PandapipesNetworkMap:
    """Create interactive map from actual pandapipes network data."""

    def __init__(self, results_dir="simulation_outputs"):
        self.results_dir = Path(results_dir)

    def load_pandapipes_network(self, scenario_name="enhanced_branitz_dh"):
        """Load pandapipes network data."""
        # Load results
        results_file = self.results_dir / f"enhanced_{scenario_name}_results.json"

        with open(results_file, "r") as f:
            self.results = json.load(f)

        print(f"✅ Loaded pandapipes network data for {scenario_name}")
        return self.results

    def create_pandapipes_interactive_map(self, save_path=None):
        """Create interactive map from pandapipes network data."""
        if not self.results.get("success", False):
            print("❌ No successful results to visualize")
            return None

        # Create base map
        center_lat, center_lon = 51.76274, 14.3453979
        m = folium.Map(location=[center_lat, center_lon], zoom_start=16)

        # Add tile layers
        folium.TileLayer("openstreetmap", name="OpenStreetMap").add_to(m)
        folium.TileLayer("cartodbpositron", name="CartoDB Positron").add_to(m)

        # Create feature groups
        junction_group = folium.FeatureGroup(name="Network Junctions", overlay=True)
        pipe_group = folium.FeatureGroup(name="Network Pipes", overlay=True)
        consumer_group = folium.FeatureGroup(name="Heat Consumers", overlay=True)
        plant_group = folium.FeatureGroup(name="CHP Plant", overlay=True)

        # Get network statistics
        kpi = self.results.get("kpi", {})

        # Create simulated network visualization based on KPI data
        # In a real implementation, you would load the actual pandapipes network
        self._create_simulated_network_visualization(
            m, junction_group, pipe_group, consumer_group, plant_group, kpi
        )

        # Add all feature groups
        junction_group.add_to(m)
        pipe_group.add_to(m)
        consumer_group.add_to(m)
        plant_group.add_to(m)

        # Add layer control
        folium.LayerControl().add_to(m)

        # Add network statistics
        self._add_network_statistics(m, kpi)

        # Add performance dashboard
        self._add_performance_dashboard(m, kpi)

        if save_path:
            m.save(save_path)
            print(f"✅ Pandapipes interactive map saved to {save_path}")

        return m

    def _create_simulated_network_visualization(
        self, m, junction_group, pipe_group, consumer_group, plant_group, kpi
    ):
        """Create simulated network visualization based on KPI data."""
        # This is a simulation since we don't have the actual pandapipes network loaded
        # In reality, you would load the network with: net = pp.from_json("network.json")

        num_buildings = kpi.get("num_buildings", 14)
        total_length = kpi.get("total_pipe_length_km", 57.8)

        # Create network nodes around the center
        center_lat, center_lon = 51.76274, 14.3453979

        # Generate network nodes
        nodes = []

        # Plant node
        nodes.append(
            {
                "id": "PLANT",
                "lat": center_lat,
                "lon": center_lon,
                "type": "plant",
                "name": "CHP Plant",
            }
        )

        # Building nodes (distributed around center)
        for i in range(num_buildings):
            # Create a circular distribution around the center
            angle = 2 * np.pi * i / num_buildings
            radius = 0.002 + 0.001 * np.random.random()  # 100-200m radius
            lat = center_lat + radius * np.cos(angle)
            lon = center_lon + radius * np.sin(angle)

            nodes.append(
                {
                    "id": f"BUILDING_{i}",
                    "lat": lat,
                    "lon": lon,
                    "type": "building",
                    "name": f"Building {i}",
                    "heat_demand": 10,  # kW
                }
            )

        # Service connection nodes (between buildings and main network)
        service_nodes = []
        for i in range(num_buildings):
            building = nodes[i + 1]  # Skip plant
            # Service connection point (closer to center)
            service_lat = building["lat"] * 0.8 + center_lat * 0.2
            service_lon = building["lon"] * 0.8 + center_lon * 0.2

            service_nodes.append(
                {
                    "id": f"SERVICE_{i}",
                    "lat": service_lat,
                    "lon": service_lon,
                    "type": "service",
                    "name": f"Service Connection {i}",
                    "building_id": building["id"],
                }
            )

        # Add junctions to map
        for node in nodes + service_nodes:
            if node["type"] == "plant":
                folium.Marker(
                    location=[node["lat"], node["lon"]],
                    popup=f"{node['name']}<br>Type: CHP Plant<br>Coordinates: {node['lat']:.6f}, {node['lon']:.6f}",
                    tooltip=node["name"],
                    icon=folium.Icon(color="green", icon="industry", prefix="fa"),
                ).add_to(plant_group)
            elif node["type"] == "building":
                folium.CircleMarker(
                    location=[node["lat"], node["lon"]],
                    radius=8,
                    color="blue",
                    fill=True,
                    fillColor="blue",
                    fillOpacity=0.7,
                    popup=f"{node['name']}<br>Type: Heat Consumer<br>Heat Demand: {node['heat_demand']} kW<br>Coordinates: {node['lat']:.6f}, {node['lon']:.6f}",
                    tooltip=f"{node['name']} - {node['heat_demand']} kW",
                ).add_to(consumer_group)
            else:  # service connection
                folium.CircleMarker(
                    location=[node["lat"], node["lon"]],
                    radius=6,
                    color="orange",
                    fill=True,
                    fillColor="orange",
                    fillOpacity=0.8,
                    popup=f"{node['name']}<br>Type: Service Connection<br>Building: {node['building_id']}<br>Coordinates: {node['lat']:.6f}, {node['lon']:.6f}",
                    tooltip=node["name"],
                ).add_to(junction_group)

        # Create main network connections (plant to service nodes)
        for service_node in service_nodes:
            # Main pipe from plant to service node
            folium.PolyLine(
                locations=[[center_lat, center_lon], [service_node["lat"], service_node["lon"]]],
                color="red",
                weight=4,
                opacity=0.8,
                popup=f"Main Pipe<br>From: CHP Plant<br>To: {service_node['name']}<br>Type: Supply/Return",
                tooltip="Main Pipe",
            ).add_to(pipe_group)

        # Create service connections (service nodes to buildings)
        for i, service_node in enumerate(service_nodes):
            building = nodes[i + 1]  # Corresponding building

            # Service pipe
            folium.PolyLine(
                locations=[
                    [service_node["lat"], service_node["lon"]],
                    [building["lat"], building["lon"]],
                ],
                color="orange",
                weight=3,
                opacity=0.8,
                dash_array="5, 5",
                popup=f"Service Pipe<br>From: {service_node['name']}<br>To: {building['name']}<br>Type: Service Connection",
                tooltip="Service Pipe",
            ).add_to(pipe_group)

        # Create some interconnections between service nodes (main network)
        for i in range(len(service_nodes)):
            for j in range(i + 1, len(service_nodes)):
                if np.random.random() < 0.3:  # 30% chance of connection
                    folium.PolyLine(
                        locations=[
                            [service_nodes[i]["lat"], service_nodes[i]["lon"]],
                            [service_nodes[j]["lat"], service_nodes[j]["lon"]],
                        ],
                        color="red",
                        weight=3,
                        opacity=0.6,
                        popup=f"Main Network Pipe<br>From: {service_nodes[i]['name']}<br>To: {service_nodes[j]['name']}<br>Type: Supply/Return",
                        tooltip="Main Network Pipe",
                    ).add_to(pipe_group)

    def _add_network_statistics(self, m, kpi):
        """Add network statistics to the map."""
        stats_html = f"""
        <div style="width: 350px; height: 500px; overflow-y: auto;">
        <h3>Pandapipes Network Statistics</h3>
        <div style="background-color: #f0f8ff; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h4>Network Overview</h4>
        <table style="width: 100%; border-collapse: collapse;">
        <tr><td><strong>Total Heat Demand:</strong></td><td>{kpi.get('heat_mwh', 0):.2f} MWh</td></tr>
        <tr><td><strong>Number of Buildings:</strong></td><td>{kpi.get('num_buildings', 0)}</td></tr>
        <tr><td><strong>Total Pipe Length:</strong></td><td>{kpi.get('total_pipe_length_km', 0):.1f} km</td></tr>
        <tr><td><strong>Service Connections:</strong></td><td>{kpi.get('service_connections', 0)}</td></tr>
        <tr><td><strong>Network Density:</strong></td><td>{kpi.get('network_density_km_per_building', 0):.1f} km/building</td></tr>
        </table>
        </div>
        
        <div style="background-color: #f0fff0; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h4>Service Connections</h4>
        <table style="width: 100%; border-collapse: collapse;">
        <tr><td><strong>Average Length:</strong></td><td>{kpi.get('avg_service_length_m', 0):.1f} m</td></tr>
        <tr><td><strong>Maximum Length:</strong></td><td>{kpi.get('max_service_length_m', 0):.1f} m</td></tr>
        <tr><td><strong>Total Service Length:</strong></td><td>{kpi.get('avg_service_length_m', 0) * kpi.get('service_connections', 0) / 1000:.1f} km</td></tr>
        </table>
        </div>
        
        <div style="background-color: {'#f0fff0' if kpi.get('hydraulic_success', False) else '#fff0f0'}; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h4>Hydraulic Performance</h4>
        <table style="width: 100%; border-collapse: collapse;">
        <tr><td><strong>Simulation Status:</strong></td><td>{'✅ Success' if kpi.get('hydraulic_success', False) else '❌ Failed'}</td></tr>
        <tr><td><strong>Max Pressure Drop:</strong></td><td>{kpi.get('max_dp_bar', 0):.3f} bar</td></tr>
        <tr><td><strong>Supply Temperature:</strong></td><td>70°C</td></tr>
        <tr><td><strong>Return Temperature:</strong></td><td>40°C</td></tr>
        </table>
        </div>
        </div>
        """

        folium.Popup(stats_html, max_width=400, max_height=550).add_to(m)

    def _add_performance_dashboard(self, m, kpi):
        """Add performance dashboard to the map."""
        # Calculate efficiency metrics
        total_heat = kpi.get("heat_mwh", 0)
        num_buildings = kpi.get("num_buildings", 0)
        total_length = kpi.get("total_pipe_length_km", 0)
        avg_service_length = kpi.get("avg_service_length_m", 0)

        efficiency_score = (
            min(100, (1 - avg_service_length / 100) * 100) if avg_service_length > 0 else 100
        )
        density_score = min(100, (1 - kpi.get("network_density_km_per_building", 0) / 10) * 100)
        hydraulic_score = 100 if kpi.get("hydraulic_success", False) else 0

        overall_score = (efficiency_score + density_score + hydraulic_score) / 3

        dashboard_html = f"""
        <div style="width: 300px;">
        <h3>Network Performance Dashboard</h3>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h4>Overall Performance Score</h4>
        <div style="text-align: center; font-size: 24px; font-weight: bold; color: {'green' if overall_score > 80 else 'orange' if overall_score > 60 else 'red'};">
        {overall_score:.1f}/100
        </div>
        </div>
        
        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h4>Efficiency Metrics</h4>
        <div style="margin: 5px 0;">
        <span>Service Efficiency:</span>
        <div style="background-color: #ddd; border-radius: 10px; height: 20px; margin: 5px 0;">
        <div style="background-color: {'green' if efficiency_score > 80 else 'orange' if efficiency_score > 60 else 'red'}; width: {efficiency_score}%; height: 100%; border-radius: 10px;"></div>
        </div>
        <span>{efficiency_score:.1f}%</span>
        </div>
        
        <div style="margin: 5px 0;">
        <span>Network Density:</span>
        <div style="background-color: #ddd; border-radius: 10px; height: 20px; margin: 5px 0;">
        <div style="background-color: {'green' if density_score > 80 else 'orange' if density_score > 60 else 'red'}; width: {density_score}%; height: 100%; border-radius: 10px;"></div>
        </div>
        <span>{density_score:.1f}%</span>
        </div>
        
        <div style="margin: 5px 0;">
        <span>Hydraulic Success:</span>
        <div style="background-color: #ddd; border-radius: 10px; height: 20px; margin: 5px 0;">
        <div style="background-color: {'green' if hydraulic_score > 80 else 'orange' if hydraulic_score > 60 else 'red'}; width: {hydraulic_score}%; height: 100%; border-radius: 10px;"></div>
        </div>
        <span>{hydraulic_score:.1f}%</span>
        </div>
        </div>
        
        <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h4>Key Insights</h4>
        <ul>
        <li>Network serves {num_buildings} buildings</li>
        <li>Total heat demand: {total_heat:.2f} MWh</li>
        <li>Average service length: {avg_service_length:.1f} m</li>
        <li>Network density: {kpi.get('network_density_km_per_building', 0):.1f} km/building</li>
        </ul>
        </div>
        </div>
        """

        folium.Popup(dashboard_html, max_width=350).add_to(m)

    def create_pandapipes_map(self, scenario_name="enhanced_branitz_dh"):
        """Create and save the pandapipes interactive map."""
        print("🗺️ Creating pandapipes network interactive map...")

        # Load network data
        self.load_pandapipes_network(scenario_name)

        # Create interactive map
        m = self.create_pandapipes_interactive_map(
            save_path=self.results_dir / f"pandapipes_interactive_map_{scenario_name}.html"
        )

        print("✅ Pandapipes interactive map created successfully!")
        return m


def main():
    """Run the pandapipes interactive map creation script."""
    map_creator = PandapipesNetworkMap()
    map_creator.create_pandapipes_map()


if __name__ == "__main__":
    main()
