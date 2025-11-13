#!/usr/bin/env python3
"""
Enhanced District Heating Network Visualizations

This script creates comprehensive visualizations for the enhanced district heating network:
1. Network layout with service connections
2. Pressure and flow analysis
3. Service connection details
4. Interactive maps
5. Comparative analysis
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from shapely.geometry import Point, LineString
import json
from pathlib import Path
import folium
from folium import plugins
import branca.colormap as cm
import warnings

warnings.filterwarnings("ignore")

# Set style
plt.style.use("default")
sns.set_palette("husl")


class EnhancedNetworkVisualizer:
    """Create comprehensive visualizations for enhanced district heating network."""

    def __init__(self, results_dir="simulation_outputs"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)

    def load_enhanced_results(self, scenario_name="enhanced_branitz_dh"):
        """Load enhanced simulation results."""
        results_file = self.results_dir / f"enhanced_{scenario_name}_results.json"
        service_file = self.results_dir / f"enhanced_service_connections_{scenario_name}.csv"

        if not results_file.exists():
            raise FileNotFoundError(f"Results file not found: {results_file}")

        with open(results_file, "r") as f:
            self.results = json.load(f)

        if service_file.exists():
            self.service_connections = pd.read_csv(service_file)
        else:
            self.service_connections = None

        print(f"✅ Loaded results for {scenario_name}")
        print(f"   - Success: {self.results.get('success', False)}")
        print(f"   - KPIs: {self.results.get('kpi', {})}")

        return self.results

    def create_network_layout_visualization(self, save_path=None):
        """Create comprehensive network layout visualization."""
        if not self.results.get("success", False):
            print("❌ No successful results to visualize")
            return None

        # Load buildings and streets for context
        buildings_gdf = gpd.read_file("results_test/buildings_prepared.geojson")
        streets_gdf = gpd.read_file("results_test/streets.geojson")

        # Create figure with multiple subplots
        fig = plt.figure(figsize=(20, 16))

        # Main network layout
        ax1 = plt.subplot(2, 3, (1, 2))
        self._plot_network_layout(ax1, buildings_gdf, streets_gdf)

        # Service connections detail
        ax2 = plt.subplot(2, 3, 3)
        self._plot_service_connections_detail(ax2)

        # Network statistics
        ax3 = plt.subplot(2, 3, 4)
        self._plot_network_statistics(ax3)

        # Service length distribution
        ax4 = plt.subplot(2, 3, 5)
        self._plot_service_length_distribution(ax4)

        # Heat demand distribution
        ax5 = plt.subplot(2, 3, 6)
        self._plot_heat_demand_distribution(ax5, buildings_gdf)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✅ Network layout visualization saved to {save_path}")

        return fig

    def _plot_network_layout(self, ax, buildings_gdf, streets_gdf):
        """Plot main network layout with service connections."""
        # Plot street network (background)
        streets_gdf.plot(ax=ax, color="lightgray", linewidth=1, alpha=0.5, label="Street Network")

        # Plot buildings
        buildings_gdf.plot(ax=ax, color="blue", markersize=100, alpha=0.7, label="Buildings")

        # Plot service connections if available
        if self.service_connections is not None:
            for _, conn in self.service_connections.iterrows():
                # Service connection point
                ax.scatter(
                    conn["connection_x"],
                    conn["connection_y"],
                    color="orange",
                    s=80,
                    alpha=0.8,
                    zorder=5,
                )

                # Service pipe
                ax.plot(
                    [conn["connection_x"], conn["building_x"]],
                    [conn["connection_y"], conn["building_y"]],
                    "orange",
                    linewidth=2,
                    alpha=0.8,
                    linestyle="--",
                )

        # Plot plant location
        plant_lat, plant_lon = 51.76274, 14.3453979
        # Transform to UTM for plotting
        from pyproj import Transformer

        transformer = Transformer.from_crs("EPSG:4326", "EPSG:32633", always_xy=True)
        plant_x, plant_y = transformer.transform(plant_lon, plant_lat)

        ax.scatter(
            plant_x,
            plant_y,
            color="green",
            s=300,
            marker="s",
            edgecolors="black",
            linewidth=2,
            label="CHP Plant",
            zorder=6,
        )

        ax.set_title(
            "Enhanced District Heating Network Layout\nService Connections & Street Network",
            fontsize=14,
            fontweight="bold",
        )
        ax.set_xlabel("X coordinate (m)")
        ax.set_ylabel("Y coordinate (m)")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3)
        ax.set_aspect("equal")

    def _plot_service_connections_detail(self, ax):
        """Plot service connection details."""
        if self.service_connections is None:
            ax.text(
                0.5,
                0.5,
                "No service connection data",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return

        # Service length statistics
        lengths = self.service_connections["distance_to_street"]

        ax.hist(lengths, bins=10, color="skyblue", alpha=0.7, edgecolor="black")
        ax.axvline(
            lengths.mean(), color="red", linestyle="--", label=f"Mean: {lengths.mean():.1f}m"
        )
        ax.axvline(
            lengths.median(),
            color="orange",
            linestyle="--",
            label=f"Median: {lengths.median():.1f}m",
        )

        ax.set_title("Service Connection Lengths", fontsize=12, fontweight="bold")
        ax.set_xlabel("Distance to Street (m)")
        ax.set_ylabel("Number of Buildings")
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_network_statistics(self, ax):
        """Plot network statistics."""
        kpi = self.results.get("kpi", {})

        # Create bar chart of key metrics
        metrics = ["Total Heat (MWh)", "Pipe Length (km)", "Buildings", "Network Density"]
        values = [
            kpi.get("heat_mwh", 0),
            kpi.get("total_pipe_length_km", 0),
            kpi.get("num_buildings", 0),
            kpi.get("network_density_km_per_building", 0),
        ]

        colors = ["#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
        bars = ax.bar(metrics, values, color=colors, alpha=0.7)

        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + max(values) * 0.01,
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        ax.set_title("Network Key Performance Indicators", fontsize=12, fontweight="bold")
        ax.set_ylabel("Value")
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, alpha=0.3, axis="y")

    def _plot_service_length_distribution(self, ax):
        """Plot service length distribution."""
        if self.service_connections is None:
            ax.text(
                0.5,
                0.5,
                "No service connection data",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return

        lengths = self.service_connections["distance_to_street"]

        # Create box plot
        ax.boxplot(
            lengths,
            patch_artist=True,
            boxprops=dict(facecolor="lightblue", alpha=0.7),
            medianprops=dict(color="red", linewidth=2),
        )

        ax.set_title("Service Connection Length Distribution", fontsize=12, fontweight="bold")
        ax.set_ylabel("Distance to Street (m)")
        ax.set_xticklabels(["Service Connections"])
        ax.grid(True, alpha=0.3, axis="y")

        # Add statistics text
        stats_text = f"Mean: {lengths.mean():.1f}m\n"
        stats_text += f"Std: {lengths.std():.1f}m\n"
        stats_text += f"Min: {lengths.min():.1f}m\n"
        stats_text += f"Max: {lengths.max():.1f}m"

        ax.text(
            0.02,
            0.98,
            stats_text,
            transform=ax.transAxes,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

    def _plot_heat_demand_distribution(self, ax, buildings_gdf):
        """Plot heat demand distribution."""
        if "heating_load_kw" not in buildings_gdf.columns:
            ax.text(
                0.5, 0.5, "No heat demand data", ha="center", va="center", transform=ax.transAxes
            )
            return

        heat_demands = buildings_gdf["heating_load_kw"]

        ax.hist(heat_demands, bins=8, color="lightgreen", alpha=0.7, edgecolor="black")
        ax.axvline(
            heat_demands.mean(),
            color="red",
            linestyle="--",
            label=f"Mean: {heat_demands.mean():.1f}kW",
        )

        ax.set_title("Building Heat Demand Distribution", fontsize=12, fontweight="bold")
        ax.set_xlabel("Heat Demand (kW)")
        ax.set_ylabel("Number of Buildings")
        ax.legend()
        ax.grid(True, alpha=0.3)

    def create_service_connection_analysis(self, save_path=None):
        """Create detailed service connection analysis."""
        if self.service_connections is None:
            print("❌ No service connection data available")
            return None

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Service length vs building ID
        ax1 = axes[0, 0]
        building_ids = range(len(self.service_connections))
        lengths = self.service_connections["distance_to_street"]
        ax1.bar(building_ids, lengths, color="skyblue", alpha=0.7)
        ax1.set_title("Service Connection Lengths by Building", fontweight="bold")
        ax1.set_xlabel("Building ID")
        ax1.set_ylabel("Distance to Street (m)")
        ax1.grid(True, alpha=0.3)

        # Cumulative distribution
        ax2 = axes[0, 1]
        sorted_lengths = np.sort(lengths)
        cumulative = np.arange(1, len(sorted_lengths) + 1) / len(sorted_lengths)
        ax2.plot(sorted_lengths, cumulative, "b-", linewidth=2)
        ax2.set_title("Cumulative Distribution of Service Lengths", fontweight="bold")
        ax2.set_xlabel("Distance to Street (m)")
        ax2.set_ylabel("Cumulative Probability")
        ax2.grid(True, alpha=0.3)

        # Service connection map
        ax3 = axes[1, 0]
        ax3.scatter(
            self.service_connections["connection_x"],
            self.service_connections["connection_y"],
            c=lengths,
            cmap="viridis",
            s=100,
            alpha=0.8,
        )
        ax3.set_title("Service Connection Points\nColored by Distance", fontweight="bold")
        ax3.set_xlabel("X coordinate (m)")
        ax3.set_ylabel("Y coordinate (m)")
        ax3.grid(True, alpha=0.3)

        # Statistics summary
        ax4 = axes[1, 1]
        ax4.axis("off")
        stats_text = "Service Connection Statistics\n\n"
        stats_text += f"Total Connections: {len(self.service_connections)}\n"
        stats_text += f"Average Length: {lengths.mean():.2f}m\n"
        stats_text += f"Median Length: {lengths.median():.2f}m\n"
        stats_text += f"Standard Deviation: {lengths.std():.2f}m\n"
        stats_text += f"Minimum Length: {lengths.min():.2f}m\n"
        stats_text += f"Maximum Length: {lengths.max():.2f}m\n"
        stats_text += f"Total Service Length: {lengths.sum():.2f}m"

        ax4.text(
            0.1,
            0.9,
            stats_text,
            transform=ax4.transAxes,
            fontsize=12,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.8),
        )

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✅ Service connection analysis saved to {save_path}")

        return fig

    def create_interactive_map(self, save_path=None):
        """Create interactive map with folium."""
        if not self.results.get("success", False):
            print("❌ No successful results to visualize")
            return None

        # Load data
        buildings_gdf = gpd.read_file("results_test/buildings_prepared.geojson")
        streets_gdf = gpd.read_file("results_test/streets.geojson")

        # Create base map centered on the area
        center_lat, center_lon = 51.76274, 14.3453979
        m = folium.Map(location=[center_lat, center_lon], zoom_start=16)

        # Add street network
        for idx, street in streets_gdf.iterrows():
            coords = list(street.geometry.coords)
            folium.PolyLine(
                locations=[[lat, lon] for lon, lat in coords],
                color="gray",
                weight=2,
                opacity=0.6,
                popup=f"Street {idx}",
            ).add_to(m)

        # Add buildings
        for idx, building in buildings_gdf.iterrows():
            centroid = building.geometry.centroid
            folium.CircleMarker(
                location=[centroid.y, centroid.x],
                radius=8,
                color="blue",
                fill=True,
                fillColor="blue",
                fillOpacity=0.7,
                popup=f"Building {idx}<br>Heat Demand: {building.get('heating_load_kw', 'N/A')} kW",
            ).add_to(m)

        # Add service connections
        if self.service_connections is not None:
            # Transform service connection coordinates back to WGS84
            from pyproj import Transformer

            transformer = Transformer.from_crs("EPSG:32633", "EPSG:4326", always_xy=True)

            for _, conn in self.service_connections.iterrows():
                # Transform coordinates
                conn_lon, conn_lat = transformer.transform(
                    conn["connection_x"], conn["connection_y"]
                )
                building_lon, building_lat = transformer.transform(
                    conn["building_x"], conn["building_y"]
                )

                # Service connection point
                folium.CircleMarker(
                    location=[conn_lat, conn_lon],
                    radius=6,
                    color="orange",
                    fill=True,
                    fillColor="orange",
                    fillOpacity=0.8,
                    popup=f"Service Connection<br>Distance: {conn['distance_to_street']:.1f}m",
                ).add_to(m)

                # Service pipe
                folium.PolyLine(
                    locations=[[conn_lat, conn_lon], [building_lat, building_lon]],
                    color="orange",
                    weight=3,
                    opacity=0.8,
                    dash_array="5, 5",
                ).add_to(m)

        # Add plant
        folium.Marker(
            location=[center_lat, center_lon],
            popup="CHP Plant<br>District Heating Source",
            icon=folium.Icon(color="green", icon="industry", prefix="fa"),
        ).add_to(m)

        # Add legend
        legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Enhanced DH Network</b></p>
        <p><i class="fa fa-industry" style="color:green"></i> CHP Plant</p>
        <p><i class="fa fa-circle" style="color:blue"></i> Buildings</p>
        <p><i class="fa fa-circle" style="color:orange"></i> Service Connections</p>
        <p><i class="fa fa-minus" style="color:gray"></i> Street Network</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

        if save_path:
            m.save(save_path)
            print(f"✅ Interactive map saved to {save_path}")

        return m

    def create_comparative_analysis(self, save_path=None):
        """Create comparative analysis with other network types."""
        # Load other results for comparison
        comparison_data = []

        # Enhanced results
        if self.results.get("success", False):
            kpi = self.results.get("kpi", {})
            comparison_data.append(
                {
                    "Network Type": "Enhanced DH",
                    "Heat Demand (MWh)": kpi.get("heat_mwh", 0),
                    "Pipe Length (km)": kpi.get("total_pipe_length_km", 0),
                    "Buildings": kpi.get("num_buildings", 0),
                    "Network Density": kpi.get("network_density_km_per_building", 0),
                    "Avg Service Length (m)": kpi.get("avg_service_length_m", 0),
                }
            )

        # Try to load other results
        other_results_files = ["base_dh_results.json", "low_temp_dh_results.json"]

        for file_name in other_results_files:
            file_path = self.results_dir / file_name
            if file_path.exists():
                try:
                    with open(file_path, "r") as f:
                        other_results = json.load(f)
                    if other_results.get("success", False):
                        kpi = other_results.get("kpi", {})
                        network_type = (
                            file_name.replace("_results.json", "").replace("_", " ").title()
                        )
                        comparison_data.append(
                            {
                                "Network Type": network_type,
                                "Heat Demand (MWh)": kpi.get("heat_mwh", 0),
                                "Pipe Length (km)": kpi.get("total_pipe_length_km", 0),
                                "Buildings": kpi.get("num_buildings", 0),
                                "Network Density": kpi.get("network_density_km_per_building", 0),
                                "Avg Service Length (m)": kpi.get("avg_service_length_m", 0),
                            }
                        )
                except Exception as e:
                    print(f"Warning: Could not load {file_name}: {e}")

        if len(comparison_data) < 2:
            print("❌ Not enough data for comparative analysis")
            return None

        df = pd.DataFrame(comparison_data)

        # Create comparison plots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Heat demand comparison
        ax1 = axes[0, 0]
        ax1.bar(df["Network Type"], df["Heat Demand (MWh)"], color="lightcoral", alpha=0.7)
        ax1.set_title("Heat Demand Comparison", fontweight="bold")
        ax1.set_ylabel("Heat Demand (MWh)")
        ax1.tick_params(axis="x", rotation=45)

        # Pipe length comparison
        ax2 = axes[0, 1]
        ax2.bar(df["Network Type"], df["Pipe Length (km)"], color="lightblue", alpha=0.7)
        ax2.set_title("Total Pipe Length Comparison", fontweight="bold")
        ax2.set_ylabel("Pipe Length (km)")
        ax2.tick_params(axis="x", rotation=45)

        # Network density comparison
        ax3 = axes[1, 0]
        ax3.bar(df["Network Type"], df["Network Density"], color="lightgreen", alpha=0.7)
        ax3.set_title("Network Density Comparison", fontweight="bold")
        ax3.set_ylabel("Network Density (km/building)")
        ax3.tick_params(axis="x", rotation=45)

        # Service length comparison (if available)
        ax4 = axes[1, 1]
        if "Avg Service Length (m)" in df.columns and not df["Avg Service Length (m)"].isna().all():
            ax4.bar(df["Network Type"], df["Avg Service Length (m)"], color="orange", alpha=0.7)
            ax4.set_title("Average Service Length Comparison", fontweight="bold")
            ax4.set_ylabel("Service Length (m)")
        else:
            ax4.text(
                0.5,
                0.5,
                "Service length data not available",
                ha="center",
                va="center",
                transform=ax4.transAxes,
            )
        ax4.tick_params(axis="x", rotation=45)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✅ Comparative analysis saved to {save_path}")

        return fig

    def create_all_visualizations(self, scenario_name="enhanced_branitz_dh"):
        """Create all visualizations for the enhanced network."""
        print("🎨 Creating comprehensive visualizations for enhanced district heating network...")

        # Load results
        self.load_enhanced_results(scenario_name)

        # Create all visualizations
        visualizations = {}

        # 1. Network layout visualization
        print("📊 Creating network layout visualization...")
        fig1 = self.create_network_layout_visualization(
            save_path=self.results_dir / f"enhanced_network_layout_{scenario_name}.png"
        )
        visualizations["network_layout"] = fig1

        # 2. Service connection analysis
        print("🔗 Creating service connection analysis...")
        fig2 = self.create_service_connection_analysis(
            save_path=self.results_dir / f"enhanced_service_analysis_{scenario_name}.png"
        )
        visualizations["service_analysis"] = fig2

        # 3. Interactive map
        print("🗺️ Creating interactive map...")
        map_obj = self.create_interactive_map(
            save_path=self.results_dir / f"enhanced_interactive_map_{scenario_name}.html"
        )
        visualizations["interactive_map"] = map_obj

        # 4. Comparative analysis
        print("📈 Creating comparative analysis...")
        fig3 = self.create_comparative_analysis(
            save_path=self.results_dir / f"enhanced_comparative_analysis_{scenario_name}.png"
        )
        visualizations["comparative_analysis"] = fig3

        print("✅ All visualizations created successfully!")
        print(f"📁 Output directory: {self.results_dir}")

        return visualizations


def main():
    """Run the enhanced visualization script."""
    visualizer = EnhancedNetworkVisualizer()
    visualizer.create_all_visualizations()


if __name__ == "__main__":
    main()
