"""
Static network map generation with color-coded cascading visualizations.

This module creates high-quality static PNG maps with:
- Temperature/voltage gradient color coding
- OSM street map overlays (optional)
- Building context
- Network topology visualization
- Statistical summaries

Adapted from street_final_copy_3/src/network_visualization.py
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import LineString, Point
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Optional imports for enhanced visualization
try:
    import contextily as ctx
    CONTEXTILY_AVAILABLE = True
except ImportError:
    CONTEXTILY_AVAILABLE = False

# Import our color palette
from .colormaps import NETWORK_COLORS, get_temperature_color, get_voltage_color


class NetworkMapGenerator:
    """
    Generate static network maps with color-coded gradients.
    
    Creates high-resolution PNG maps suitable for reports and presentations.
    """
    
    def __init__(self, output_dir: str = "results_test/visualizations/static"):
        """
        Initialize the network map generator.
        
        Args:
            output_dir: Directory to save generated maps
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_dh_network_geometries(self, net) -> Dict[str, gpd.GeoDataFrame]:
        """
        Extract pipe geometries and junction points from pandapipes network.
        
        Args:
            net: pandapipes network object
        
        Returns:
            Dictionary with 'supply_pipes', 'return_pipes', 'junctions' GeoDataFrames
        """
        # Extract supply & return pipes from net.pipe_geodata
        sup_lines = []
        ret_lines = []
        sup_names = []
        ret_names = []
        
        for i, row in net.pipe_geodata.iterrows():
            geom = LineString(row.coords)
            if row.name.startswith("SUP_"):
                sup_lines.append(geom)
                sup_names.append(row.name)
            else:
                # RET_* pipes are the returns
                ret_lines.append(geom)
                ret_names.append(row.name)
        
        # Create GeoDataFrames for pipes
        gdf_sup = gpd.GeoDataFrame(
            {"name": sup_names},
            geometry=sup_lines,
            crs="EPSG:25833"
        )
        gdf_ret = gpd.GeoDataFrame(
            {"name": ret_names},
            geometry=ret_lines,
            crs="EPSG:25833"
        )
        
        # Extract junctions
        pts = []
        types = []
        names = []
        
        for j, row in net.junction.iterrows():
            try:
                if hasattr(row, "geodata") and row.geodata is not None:
                    x, y = row.geodata[0], row.geodata[1]
                else:
                    x, y = row.x, row.y
            except (AttributeError, IndexError):
                x, y = 0, 0
            
            pts.append(Point(x, y))
            types.append("supply" if row.name.startswith("sup_") else "return")
            names.append(row.name)
        
        gdf_j = gpd.GeoDataFrame(
            {"type": types, "name": names},
            geometry=pts,
            crs="EPSG:25833"
        )
        
        return {
            "supply_pipes": gdf_sup,
            "return_pipes": gdf_ret,
            "junctions": gdf_j
        }
    
    def create_dh_temperature_map(
        self,
        net,
        scenario_name: str,
        buildings_gdf: Optional[gpd.GeoDataFrame] = None,
        include_street_map: bool = True
    ) -> str:
        """
        Create DH network map with temperature gradient color coding.
        
        Args:
            net: pandapipes network object
            scenario_name: Name of the scenario
            buildings_gdf: Optional building geometries
            include_street_map: Whether to include OSM overlay
        
        Returns:
            Path to saved PNG file
        """
        if not CONTEXTILY_AVAILABLE and include_street_map:
            print("⚠️  contextily not available, creating map without street overlay")
            include_street_map = False
        
        # Extract network geometries
        network_data = self.extract_dh_network_geometries(net)
        
        # Reproject to Web Mercator for OSM compatibility
        gdf_sup = network_data["supply_pipes"].to_crs(epsg=3857)
        gdf_ret = network_data["return_pipes"].to_crs(epsg=3857)
        gdf_j = network_data["junctions"].to_crs(epsg=3857)
        
        if buildings_gdf is not None:
            buildings_web = buildings_gdf.to_crs(epsg=3857)
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(15, 12))
        
        # Add street map basemap
        if include_street_map:
            try:
                # Get bounds
                all_geoms = list(gdf_sup.geometry) + list(gdf_ret.geometry) + list(gdf_j.geometry)
                if buildings_gdf is not None:
                    all_geoms.extend(list(buildings_web.geometry))
                
                bounds = gpd.GeoSeries(all_geoms, crs=3857).total_bounds
                ax.set_xlim(bounds[0] - 100, bounds[2] + 100)
                ax.set_ylim(bounds[1] - 100, bounds[3] + 100)
                
                # Add OSM basemap
                ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=16)
            except Exception as e:
                print(f"⚠️  Could not add street map: {e}")
                include_street_map = False
        
        # Plot buildings
        if buildings_gdf is not None:
            buildings_web.plot(
                ax=ax,
                color=NETWORK_COLORS['building'],
                edgecolor=NETWORK_COLORS['building_outline'],
                alpha=0.7,
                label="Buildings",
                zorder=1
            )
        
        # Plot supply pipes (red/crimson for hot)
        gdf_sup.plot(
            ax=ax,
            linewidth=3,
            color=NETWORK_COLORS['supply_pipe'],
            label="Supply (hot)",
            zorder=3
        )
        
        # Plot return pipes (blue for cold)
        gdf_ret.plot(
            ax=ax,
            linewidth=2,
            color=NETWORK_COLORS['return_pipe'],
            label="Return (cold)",
            zorder=2
        )
        
        # Plot junctions
        supply_junctions = gdf_j[gdf_j.type == "supply"]
        return_junctions = gdf_j[gdf_j.type == "return"]
        
        supply_junctions.plot(
            ax=ax,
            color=NETWORK_COLORS['supply_junction'],
            markersize=80,
            label="Supply junctions",
            zorder=4
        )
        return_junctions.plot(
            ax=ax,
            color=NETWORK_COLORS['return_junction'],
            markersize=60,
            label="Return junctions",
            zorder=4
        )
        
        # Add heat consumers
        try:
            consumer_positions = []
            for idx, consumer in net.heat_consumer.iterrows():
                try:
                    from_junc = net.junction.loc[consumer.from_junction]
                    if hasattr(from_junc, "geodata") and from_junc.geodata is not None:
                        x, y = from_junc.geodata[0], from_junc.geodata[1]
                    else:
                        x, y = from_junc.x, from_junc.y
                    
                    point = Point(x, y)
                    point_web = gpd.GeoDataFrame([point], crs="EPSG:25833").to_crs(epsg=3857)
                    consumer_positions.append(
                        (point_web.geometry.iloc[0].x, point_web.geometry.iloc[0].y)
                    )
                except Exception:
                    continue
            
            if consumer_positions:
                x_coords, y_coords = zip(*consumer_positions)
                ax.scatter(
                    x_coords,
                    y_coords,
                    c=NETWORK_COLORS['heat_consumer'],
                    s=100,
                    zorder=5,
                    label="Heat consumers",
                    marker="^",
                    edgecolors="black",
                    linewidth=1
                )
        except Exception as e:
            print(f"⚠️  Could not plot consumers: {e}")
        
        # Add CHP plant marker
        try:
            for idx, ext_grid in net.ext_grid.iterrows():
                junction = net.junction.loc[ext_grid.junction]
                if hasattr(junction, "geodata") and junction.geodata is not None:
                    x, y = junction.geodata[0], junction.geodata[1]
                else:
                    x, y = junction.x, junction.y
                
                point = Point(x, y)
                point_web = gpd.GeoDataFrame([point], crs="EPSG:25833").to_crs(epsg=3857)
                ax.scatter(
                    point_web.geometry.iloc[0].x,
                    point_web.geometry.iloc[0].y,
                    c=NETWORK_COLORS['chp_plant'],
                    s=200,
                    zorder=6,
                    label="CHP Plant",
                    marker="s",
                    edgecolors="black",
                    linewidth=2
                )
                break
        except Exception as e:
            print(f"⚠️  Could not plot CHP plant: {e}")
        
        # Customize plot
        ax.set_title(
            f"District Heating Network - {scenario_name}\n"
            f"Buildings: {len(net.heat_consumer)}, Total Length: {net.pipe.length_km.sum():.2f} km",
            fontsize=16,
            fontweight="bold",
            pad=20
        )
        
        if not include_street_map:
            ax.set_xlabel("X coordinate (Web Mercator)", fontsize=12)
            ax.set_ylabel("Y coordinate (Web Mercator)", fontsize=12)
            ax.grid(True, alpha=0.3)
        
        ax.legend(loc="upper right", fontsize=11, framealpha=0.9)
        ax.set_aspect("equal", adjustable="box")
        
        # Add statistics box
        try:
            stats_text = f"Network Statistics:\n"
            stats_text += f"• Total Heat Demand: {net.heat_consumer.qext_w.sum()/1000:.2f} kW\n"
            stats_text += f"• Supply Temperature: {net.junction.tfluid_k.max()-273.15:.0f}°C\n"
            stats_text += f"• Return Temperature: {net.junction.tfluid_k.min()-273.15:.0f}°C\n"
            stats_text += f"• Pipe Diameter: {net.pipe.diameter_m.mean():.3f} m"
            
            ax.text(
                0.02,
                0.98,
                stats_text,
                transform=ax.transAxes,
                fontsize=11,
                verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.9)
            )
        except Exception:
            pass
        
        # Save the plot
        plot_file = self.output_dir / f"dh_network_{scenario_name}.png"
        fig.savefig(plot_file, dpi=300, bbox_inches="tight")
        plt.close(fig)
        
        print(f"✅ DH network map saved: {plot_file}")
        return str(plot_file)
    
    def create_hp_voltage_map(
        self,
        scenario_name: str,
        buildings_gdf: Optional[gpd.GeoDataFrame] = None,
        include_street_map: bool = True
    ) -> str:
        """
        Create HP network map with voltage gradient color coding.
        
        Args:
            scenario_name: Name of the scenario
            buildings_gdf: Optional building geometries
            include_street_map: Whether to include OSM overlay
        
        Returns:
            Path to saved PNG file
        """
        # Placeholder for HP map generation
        # Will be implemented when HP network geometry is available
        
        fig, ax = plt.subplots(figsize=(15, 12))
        
        if buildings_gdf is not None:
            buildings_web = buildings_gdf.to_crs(epsg=3857)
            buildings_web.plot(
                ax=ax,
                color=NETWORK_COLORS['building'],
                edgecolor=NETWORK_COLORS['building_outline'],
                alpha=0.7,
                label="Buildings"
            )
        
        ax.set_title(
            f"Heat Pump Network - {scenario_name}\n(Voltage gradient visualization)",
            fontsize=16,
            fontweight="bold"
        )
        
        ax.legend(loc="upper right")
        
        # Save
        plot_file = self.output_dir / f"hp_network_{scenario_name}.png"
        fig.savefig(plot_file, dpi=300, bbox_inches="tight")
        plt.close(fig)
        
        print(f"✅ HP network map saved: {plot_file}")
        return str(plot_file)

