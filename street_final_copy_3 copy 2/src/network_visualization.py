# src/network_visualization.py

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import LineString, Point
import json
import os
from pathlib import Path

# Optional imports for enhanced visualization
try:
    import contextily as ctx

    CONTEXTILY_AVAILABLE = True
except ImportError:
    CONTEXTILY_AVAILABLE = False
    print(
        "Warning: contextily not available. Install with 'pip install contextily' for street map overlays."
    )

try:
    import folium

    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print("Warning: folium not available. Install with 'pip install folium' for interactive maps.")


def extract_network_geometries(net):
    """
    Extract pipe geometries and junction points from pandapipes network.

    Args:
        net: pandapipes network object

    Returns:
        dict: Contains supply/return pipes and junctions as GeoDataFrames
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
            # RET_… pipes are the returns
            ret_lines.append(geom)
            ret_names.append(row.name)

    # Create GeoDataFrames for pipes
    gdf_sup = gpd.GeoDataFrame({"name": sup_names}, geometry=sup_lines, crs="EPSG:25833")
    gdf_ret = gpd.GeoDataFrame({"name": ret_names}, geometry=ret_lines, crs="EPSG:25833")

    # Extract junctions (from net.junction geodata)
    pts = []
    types = []
    names = []

    for j, row in net.junction.iterrows():
        try:
            # Try to get coordinates from geodata
            if hasattr(row, "geodata") and row.geodata is not None:
                x, y = row.geodata[0], row.geodata[1]
            else:
                # Fallback to x, y columns
                x, y = row.x, row.y
        except (AttributeError, IndexError):
            # Last fallback
            x, y = 0, 0

        pts.append(Point(x, y))
        types.append("supply" if row.name.startswith("sup_") else "return")
        names.append(row.name)

    gdf_j = gpd.GeoDataFrame({"type": types, "name": names}, geometry=pts, crs="EPSG:25833")

    return {"supply_pipes": gdf_sup, "return_pipes": gdf_ret, "junctions": gdf_j}


def create_static_network_map(
    net, scenario_name, output_dir="simulation_outputs", include_street_map=True, buildings_gdf=None
):
    """
    Create a static network map with optional street map overlay using GeoPandas + Contextily.

    Args:
        net: pandapipes network object
        scenario_name: Name of the scenario for the plot title
        output_dir: Directory to save the output
        include_street_map: Whether to include OSM street map overlay
        buildings_gdf: Optional GeoDataFrame of buildings to plot

    Returns:
        str: Path to the saved plot file
    """
    if not CONTEXTILY_AVAILABLE and include_street_map:
        print("Warning: contextily not available, creating map without street overlay")
        include_street_map = False

    # Extract network geometries
    network_data = extract_network_geometries(net)

    # Reproject everything to Web-Mercator for OSM compatibility
    gdf_sup = network_data["supply_pipes"].to_crs(epsg=3857)
    gdf_ret = network_data["return_pipes"].to_crs(epsg=3857)
    gdf_j = network_data["junctions"].to_crs(epsg=3857)

    # Reproject buildings if provided
    if buildings_gdf is not None:
        buildings_web = buildings_gdf.to_crs(epsg=3857)

    # Create the plot
    fig, ax = plt.subplots(figsize=(15, 12))

    # Add street map basemap if requested
    if include_street_map:
        try:
            # Get the bounds of our network
            all_geoms = list(gdf_sup.geometry) + list(gdf_ret.geometry) + list(gdf_j.geometry)
            if buildings_gdf is not None:
                all_geoms.extend(list(buildings_web.geometry))

            # Calculate bounds
            bounds = gpd.GeoSeries(all_geoms, crs=3857).total_bounds
            ax.set_xlim(bounds[0] - 100, bounds[2] + 100)
            ax.set_ylim(bounds[1] - 100, bounds[3] + 100)

            # Add OSM basemap
            ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=16)
        except Exception as e:
            print(f"Warning: Could not add street map overlay: {e}")
            include_street_map = False

    # Plot buildings if provided
    if buildings_gdf is not None:
        buildings_web.plot(
            ax=ax, color="lightgrey", edgecolor="black", alpha=0.7, label="Buildings", zorder=1
        )

    # Plot supply pipes
    gdf_sup.plot(ax=ax, linewidth=3, color="crimson", label="Supply main", zorder=3)

    # Plot return pipes
    gdf_ret.plot(ax=ax, linewidth=2, color="steelblue", label="Return main", zorder=2)

    # Plot junctions
    supply_junctions = gdf_j[gdf_j.type == "supply"]
    return_junctions = gdf_j[gdf_j.type == "return"]

    supply_junctions.plot(ax=ax, color="crimson", markersize=80, label="Supply junctions", zorder=4)
    return_junctions.plot(
        ax=ax, color="steelblue", markersize=60, label="Return junctions", zorder=4
    )

    # Add heat consumers (buildings connected to supply)
    if buildings_gdf is not None:
        # Find buildings that are heat consumers
        consumer_positions = []
        for idx, consumer in net.heat_consumer.iterrows():
            try:
                from_junc = net.junction.loc[consumer.from_junction]
                if hasattr(from_junc, "geodata") and from_junc.geodata is not None:
                    x, y = from_junc.geodata[0], from_junc.geodata[1]
                else:
                    x, y = from_junc.x, from_junc.y

                # Convert to Web Mercator
                from shapely.geometry import Point

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
                c="orange",
                s=100,
                zorder=5,
                label="Heat consumers",
                marker="^",
                edgecolors="black",
                linewidth=1,
            )

    # Add CHP plant marker (usually the external grid)
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
                c="green",
                s=200,
                zorder=6,
                label="CHP Plant",
                marker="s",
                edgecolors="black",
                linewidth=2,
            )
            break
    except Exception:
        pass

    # Customize the plot
    ax.set_title(
        f"District Heating Network - {scenario_name}\n"
        f"Buildings: {len(net.heat_consumer)}, Total Length: {net.pipe.length_km.sum():.2f} km",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )

    if not include_street_map:
        ax.set_xlabel("X coordinate (Web Mercator)", fontsize=12)
        ax.set_ylabel("Y coordinate (Web Mercator)", fontsize=12)
        ax.grid(True, alpha=0.3)

    ax.legend(loc="upper right", fontsize=11, framealpha=0.9)
    ax.set_aspect("equal", adjustable="box")

    # Add statistics box
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
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.9),
    )

    # Save the plot
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    plot_file = output_path / f"street_map_dh_{scenario_name}.png"
    fig.savefig(plot_file, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Static network map with street overlay saved to: {plot_file}")
    return str(plot_file)


def create_interactive_network_map(
    net, scenario_name, output_dir="simulation_outputs", buildings_gdf=None
):
    """
    Create an interactive network map using Folium.

    Args:
        net: pandapipes network object
        scenario_name: Name of the scenario for the plot title
        output_dir: Directory to save the output
        buildings_gdf: Optional GeoDataFrame of buildings to plot

    Returns:
        str: Path to the saved HTML file
    """
    if not FOLIUM_AVAILABLE:
        print("Error: folium not available. Install with 'pip install folium'")
        return None

    from shapely.geometry import mapping

    # Find center point for the map
    center_x, center_y = 0, 0
    count = 0

    for idx, junction in net.junction.iterrows():
        try:
            if hasattr(junction, "geodata") and junction.geodata is not None:
                x, y = junction.geodata[0], junction.geodata[1]
            else:
                x, y = junction.x, junction.y

            # Convert to lat/lon if in projected CRS
            if net.junction.crs and net.junction.crs.is_projected:
                from pyproj import Transformer

                transformer = Transformer.from_crs(net.junction.crs, "EPSG:4326", always_xy=True)
                x, y = transformer.transform(x, y)

            center_x += x
            center_y += y
            count += 1
        except Exception:
            continue

    if count > 0:
        center_x /= count
        center_y /= count
    else:
        # Default to Cottbus coordinates
        center_x, center_y = 14.3453979, 51.76274

    # Create the map
    m = folium.Map(location=[center_y, center_x], zoom_start=16, tiles="OpenStreetMap")

    # Add supply pipes
    for i, row in net.pipe_geodata.iterrows():
        if row.name.startswith("SUP_"):
            geom = LineString(row.coords)
            geo = mapping(geom)

            # Convert to lat/lon if needed
            if net.pipe_geodata.crs and net.pipe_geodata.crs.is_projected:
                from pyproj import Transformer

                transformer = Transformer.from_crs(
                    net.pipe_geodata.crs, "EPSG:4326", always_xy=True
                )

                # Transform coordinates
                coords = list(geom.coords)
                transformed_coords = [transformer.transform(x, y) for x, y in coords]
                geom = LineString(transformed_coords)
                geo = mapping(geom)

            folium.GeoJson(
                geo,
                style_function=lambda feat: {"color": "red", "weight": 4, "opacity": 0.8},
                tooltip=f"Supply Pipe: {row.name}",
            ).add_to(m)

    # Add return pipes
    for i, row in net.pipe_geodata.iterrows():
        if not row.name.startswith("SUP_"):
            geom = LineString(row.coords)
            geo = mapping(geom)

            # Convert to lat/lon if needed
            if net.pipe_geodata.crs and net.pipe_geodata.crs.is_projected:
                from pyproj import Transformer

                transformer = Transformer.from_crs(
                    net.pipe_geodata.crs, "EPSG:4326", always_xy=True
                )

                # Transform coordinates
                coords = list(geom.coords)
                transformed_coords = [transformer.transform(x, y) for x, y in coords]
                geom = LineString(transformed_coords)
                geo = mapping(geom)

            folium.GeoJson(
                geo,
                style_function=lambda feat: {"color": "blue", "weight": 3, "opacity": 0.6},
                tooltip=f"Return Pipe: {row.name}",
            ).add_to(m)

    # Add junction markers
    for j, row in net.junction.iterrows():
        try:
            if hasattr(row, "geodata") and row.geodata is not None:
                x, y = row.geodata[0], row.geodata[1]
            else:
                x, y = row.x, row.y

            # Convert to lat/lon if needed
            if net.junction.crs and net.junction.crs.is_projected:
                from pyproj import Transformer

                transformer = Transformer.from_crs(net.junction.crs, "EPSG:4326", always_xy=True)
                x, y = transformer.transform(x, y)

            color = "red" if row.name.startswith("sup_") else "blue"
            folium.CircleMarker(
                [y, x],
                radius=4,
                color=color,
                fill=True,
                popup=f"Junction: {row.name}",
                tooltip=f"Junction: {row.name}",
            ).add_to(m)
        except Exception:
            continue

    # Add heat consumers (orange triangles)
    for hc in net.heat_consumer.itertuples():
        try:
            sup_j = net.junction.loc[hc.from_junction]
            if hasattr(sup_j, "geodata") and sup_j.geodata is not None:
                x, y = sup_j.geodata[0], sup_j.geodata[1]
            else:
                x, y = sup_j.x, sup_j.y

            # Convert to lat/lon if needed
            if net.junction.crs and net.junction.crs.is_projected:
                from pyproj import Transformer

                transformer = Transformer.from_crs(net.junction.crs, "EPSG:4326", always_xy=True)
                x, y = transformer.transform(x, y)

            folium.RegularPolygonMarker(
                [y, x],
                number_of_sides=3,
                radius=6,
                color="orange",
                rotation=0,
                fill=True,
                popup=f"Heat Consumer: {hc.name}",
                tooltip=f"Heat Consumer: {hc.name}",
            ).add_to(m)
        except Exception:
            continue

    # Add CHP plant marker
    try:
        for idx, ext_grid in net.ext_grid.iterrows():
            junction = net.junction.loc[ext_grid.junction]
            if hasattr(junction, "geodata") and junction.geodata is not None:
                x, y = junction.geodata[0], junction.geodata[1]
            else:
                x, y = junction.x, junction.y

            # Convert to lat/lon if needed
            if net.junction.crs and net.junction.crs.is_projected:
                from pyproj import Transformer

                transformer = Transformer.from_crs(net.junction.crs, "EPSG:4326", always_xy=True)
                x, y = transformer.transform(x, y)

            folium.RegularPolygonMarker(
                [y, x],
                number_of_sides=4,
                radius=8,
                color="green",
                rotation=45,
                fill=True,
                popup="CHP Plant",
                tooltip="CHP Plant",
            ).add_to(m)
            break
    except Exception:
        pass

    # Add legend
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>Network Legend</b></p>
    <p><i class="fa fa-circle" style="color:red"></i> Supply Pipes</p>
    <p><i class="fa fa-circle" style="color:blue"></i> Return Pipes</p>
    <p><i class="fa fa-circle" style="color:orange"></i> Heat Consumers</p>
    <p><i class="fa fa-circle" style="color:green"></i> CHP Plant</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Save the map
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    html_file = output_path / f"interactive_dh_{scenario_name}.html"
    m.save(str(html_file))

    print(f"Interactive network map saved to: {html_file}")
    return str(html_file)


def create_enhanced_network_visualization(
    net,
    scenario_name,
    output_dir="simulation_outputs",
    buildings_gdf=None,
    create_static=True,
    create_interactive=True,
):
    """
    Create both static and interactive network visualizations with street map overlays.

    Args:
        net: pandapipes network object
        scenario_name: Name of the scenario
        output_dir: Directory to save outputs
        buildings_gdf: Optional GeoDataFrame of buildings
        create_static: Whether to create static map
        create_interactive: Whether to create interactive map

    Returns:
        dict: Paths to created files
    """
    results = {}

    if create_static:
        try:
            static_file = create_static_network_map(
                net, scenario_name, output_dir, include_street_map=True, buildings_gdf=buildings_gdf
            )
            results["static_map"] = static_file
        except Exception as e:
            print(f"Error creating static map: {e}")
            results["static_map"] = None

    if create_interactive:
        try:
            interactive_file = create_interactive_network_map(
                net, scenario_name, output_dir, buildings_gdf=buildings_gdf
            )
            results["interactive_map"] = interactive_file
        except Exception as e:
            print(f"Error creating interactive map: {e}")
            results["interactive_map"] = None

    return results
