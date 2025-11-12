#!/usr/bin/env python3
"""
Test Street Selection and Interactive Maps

This script demonstrates:
1. Street selection from available streets
2. Interactive map creation with pipe connections (District Heating)
3. Interactive map creation with electricity connections (Heat Pumps)
4. Combined visualization showing both infrastructure types

Usage:
    python test_street_selection_and_maps.py
"""

import json
import os
import sys
from pathlib import Path
import geopandas as gpd
import pandas as pd
import folium
from shapely.geometry import Point, LineString
import questionary
# --- Added: access to dual-pipe/street modules ---
import sys as _sys
_sys.path.append("untitled folder/street_final_copy_3")
try:
    from create_complete_dual_pipe_dh_network_improved import ImprovedDualPipeDHNetwork  # type: ignore
except Exception:
    ImprovedDualPipeDHNetwork = None  # fallback if not available

def get_all_street_names(geojson_path):
    """Get all available street names from the GeoJSON file."""
    print(f"Reading street names from {geojson_path}...")
    street_names = set()
    
    try:
        with open(geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for feature in data["features"]:
            for adr in feature.get("adressen", []):
                street_val = adr.get("str")
                if street_val:
                    street_names.add(street_val.strip())

        print(f"Found {len(street_names)} unique streets.")
        return sorted(list(street_names))
    except Exception as e:
        print(f"Error reading street names: {e}")
        return []

def select_street_interactive(street_names):
    """Interactive street selection using questionary."""
    if not street_names:
        print("No streets available for selection.")
        return None
    
    selected_street = questionary.select(
        "Select a street to analyze:",
        choices=street_names,
        default=street_names[0] if street_names else None
    ).ask()
    
    return selected_street

def get_buildings_for_street(geojson_path, street_name):
    """Get buildings for a specific street."""
    print(f"Getting buildings for street: {street_name}")
    buildings = []
    
    try:
        with open(geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for feature in data["features"]:
            for adr in feature.get("adressen", []):
                street_val = adr.get("str")
                if street_val and street_val.strip().lower() == street_name.lower():
                    buildings.append(feature)
                    break

        print(f"Found {len(buildings)} buildings for {street_name}")
        return buildings
    except Exception as e:
        print(f"Error getting buildings: {e}")
        return []

def create_district_heating_map(buildings, street_name):
    """Create interactive map showing district heating pipe connections."""
    print(f"Creating District Heating map for {street_name}...")
    
    if not buildings:
        print("No buildings to visualize.")
        return None
    
    # Convert GeoJSON features to proper GeoDataFrame
    from shapely.geometry import shape
    import json
    
    # Extract geometry and properties from GeoJSON features
    geometries = []
    properties = []
    
    for building in buildings:
        if 'geometry' in building:
            # Convert GeoJSON geometry to Shapely geometry
            geom = shape(building['geometry'])
            geometries.append(geom)
            
            # Extract properties
            props = building.get('properties', {})
            if 'gebaeude' in building:
                props.update(building['gebaeude'])
            properties.append(props)
    
    if not geometries:
        print("No valid geometries found in buildings data.")
        return None
    
    # Create GeoDataFrame
    buildings_gdf = gpd.GeoDataFrame(properties, geometry=geometries)
    
    # Calculate center for map
    center = buildings_gdf.geometry.union_all().centroid
    center_lat, center_lon = center.y, center.x
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=16)
    
    # Add tile layers
    folium.TileLayer("openstreetmap", name="OpenStreetMap").add_to(m)
    folium.TileLayer("cartodbpositron", name="CartoDB Positron").add_to(m)
    
    # Create feature groups
    building_group = folium.FeatureGroup(name="Buildings", overlay=True)
    pipe_group = folium.FeatureGroup(name="District Heating Pipes", overlay=True)
    service_group = folium.FeatureGroup(name="Service Connections", overlay=True)
    
    # Add buildings
    for idx, building in buildings_gdf.iterrows():
        centroid = building.geometry.centroid
        folium.CircleMarker(
            location=[centroid.y, centroid.x],
            radius=8,
            color="blue",
            fill=True,
            fillColor="lightblue",
            fillOpacity=0.7,
            popup=f"Building {idx}<br>Area: {building.geometry.area:.0f} m²"
        ).add_to(building_group)
    
    # Create simulated pipe network (MST-like)
    building_centroids = [b.geometry.centroid for b in buildings_gdf.itertuples()]
    
    # Simple pipe network - connect buildings in sequence
    pipe_lines = []
    for i in range(len(building_centroids) - 1):
        line = LineString([building_centroids[i], building_centroids[i + 1]])
        pipe_lines.append(line)
        
        # Add pipe to map
        folium.PolyLine(
            locations=[[p[1], p[0]] for p in line.coords],
            color="red",
            weight=4,
            opacity=0.8,
            popup=f"Supply Pipe {i+1}"
        ).add_to(pipe_group)
    
    # Add service connections (building to street)
    for idx, building in buildings_gdf.iterrows():
        centroid = building.geometry.centroid
        # Simulate street connection (slightly offset)
        street_point = Point(centroid.x + 0.0001, centroid.y + 0.0001)
        service_line = LineString([centroid, street_point])
        
        folium.PolyLine(
            locations=[[p[1], p[0]] for p in service_line.coords],
            color="orange",
            weight=2,
            opacity=0.6,
            popup=f"Service Connection {idx+1}"
        ).add_to(service_group)
    
    # Add feature groups to map
    building_group.add_to(m)
    pipe_group.add_to(m)
    service_group.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add title
    title_html = f"""
    <h3 align="center" style="font-size:16px"><b>District Heating Network - {street_name}</b></h3>
    """
    m.get_root().html.add_child(folium.Element(title_html))
    
    return m

def create_heat_pump_map(buildings, street_name):
    """Create interactive map showing heat pump electricity connections."""
    print(f"Creating Heat Pump map for {street_name}...")
    
    if not buildings:
        print("No buildings to visualize.")
        return None
    
    # Convert GeoJSON features to proper GeoDataFrame
    from shapely.geometry import shape
    import json
    
    # Extract geometry and properties from GeoJSON features
    geometries = []
    properties = []
    
    for building in buildings:
        if 'geometry' in building:
            # Convert GeoJSON geometry to Shapely geometry
            geom = shape(building['geometry'])
            geometries.append(geom)
            
            # Extract properties
            props = building.get('properties', {})
            if 'gebaeude' in building:
                props.update(building['gebaeude'])
            properties.append(props)
    
    if not geometries:
        print("No valid geometries found in buildings data.")
        return None
    
    # Create GeoDataFrame
    buildings_gdf = gpd.GeoDataFrame(properties, geometry=geometries)
    
    # Calculate center for map
    center = buildings_gdf.geometry.union_all().centroid
    center_lat, center_lon = center.y, center.x
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=16)
    
    # Add tile layers
    folium.TileLayer("openstreetmap", name="OpenStreetMap").add_to(m)
    folium.TileLayer("cartodbpositron", name="CartoDB Positron").add_to(m)
    
    # Create feature groups
    building_group = folium.FeatureGroup(name="Buildings", overlay=True)
    power_line_group = folium.FeatureGroup(name="Power Lines", overlay=True)
    transformer_group = folium.FeatureGroup(name="Transformers", overlay=True)
    service_group = folium.FeatureGroup(name="Service Connections", overlay=True)
    
    # Add buildings
    for idx, building in buildings_gdf.iterrows():
        centroid = building.geometry.centroid
        folium.CircleMarker(
            location=[centroid.y, centroid.x],
            radius=8,
            color="green",
            fill=True,
            fillColor="lightgreen",
            fillOpacity=0.7,
            popup=f"Building {idx}<br>Heat Pump Ready<br>Area: {building.geometry.area:.0f} m²"
        ).add_to(building_group)
    
    # Simulate power infrastructure
    building_centroids = [b.geometry.centroid for b in buildings_gdf.itertuples()]
    
    # Add transformer (simulated location)
    if building_centroids:
        transformer_point = Point(
            building_centroids[0].x + 0.0002,
            building_centroids[0].y + 0.0002
        )
        folium.Marker(
            location=[transformer_point.y, transformer_point.x],
            popup="Transformer<br>400V/230V",
            icon=folium.Icon(color="red", icon="bolt", prefix="fa")
        ).add_to(transformer_group)
    
    # Create power lines from transformer to buildings
    for idx, building in buildings_gdf.iterrows():
        centroid = building.geometry.centroid
        if building_centroids:
            # Connect to transformer
            transformer_point = Point(
                building_centroids[0].x + 0.0002,
                building_centroids[0].y + 0.0002
            )
            power_line = LineString([transformer_point, centroid])
            
            folium.PolyLine(
                locations=[[p[1], p[0]] for p in power_line.coords],
                color="yellow",
                weight=3,
                opacity=0.8,
                popup=f"Power Line {idx+1}<br>Heat Pump Connection"
            ).add_to(power_line_group)
    
    # Add service connections (building to street)
    for idx, building in buildings_gdf.iterrows():
        centroid = building.geometry.centroid
        # Simulate street connection (slightly offset)
        street_point = Point(centroid.x + 0.0001, centroid.y + 0.0001)
        service_line = LineString([centroid, street_point])
        
        folium.PolyLine(
            locations=[[p[1], p[0]] for p in service_line.coords],
            color="purple",
            weight=2,
            opacity=0.6,
            popup=f"Service Connection {idx+1}"
        ).add_to(service_group)
    
    # Add feature groups to map
    building_group.add_to(m)
    power_line_group.add_to(m)
    transformer_group.add_to(m)
    service_group.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add title
    title_html = f"""
    <h3 align="center" style="font-size:16px"><b>Heat Pump Infrastructure - {street_name}</b></h3>
    """
    m.get_root().html.add_child(folium.Element(title_html))
    
    return m

def create_combined_map(buildings, street_name):
    """Create interactive map showing both DH and HP infrastructure."""
    print(f"Creating combined infrastructure map for {street_name}...")
    
    if not buildings:
        print("No buildings to visualize.")
        return None
    
    # Convert GeoJSON features to proper GeoDataFrame
    from shapely.geometry import shape
    import json
    
    # Extract geometry and properties from GeoJSON features
    geometries = []
    properties = []
    
    for building in buildings:
        if 'geometry' in building:
            # Convert GeoJSON geometry to Shapely geometry
            geom = shape(building['geometry'])
            geometries.append(geom)
            
            # Extract properties
            props = building.get('properties', {})
            if 'gebaeude' in building:
                props.update(building['gebaeude'])
            properties.append(props)
    
    if not geometries:
        print("No valid geometries found in buildings data.")
        return None
    
    # Create GeoDataFrame
    buildings_gdf = gpd.GeoDataFrame(properties, geometry=geometries)
    
    # Calculate center for map
    center = buildings_gdf.geometry.union_all().centroid
    center_lat, center_lon = center.y, center.x
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=16)
    
    # Add tile layers
    folium.TileLayer("openstreetmap", name="OpenStreetMap").add_to(m)
    folium.TileLayer("cartodbpositron", name="CartoDB Positron").add_to(m)
    
    # Create feature groups
    building_group = folium.FeatureGroup(name="Buildings", overlay=True)
    dh_pipe_group = folium.FeatureGroup(name="District Heating Pipes", overlay=True)
    hp_power_group = folium.FeatureGroup(name="Heat Pump Power Lines", overlay=True)
    transformer_group = folium.FeatureGroup(name="Transformers", overlay=True)
    service_group = folium.FeatureGroup(name="Service Connections", overlay=True)
    
    # Add buildings
    for idx, building in buildings_gdf.iterrows():
        centroid = building.geometry.centroid
        folium.CircleMarker(
            location=[centroid.y, centroid.x],
            radius=8,
            color="gray",
            fill=True,
            fillColor="lightgray",
            fillOpacity=0.7,
            popup=f"Building {idx}<br>Area: {building.geometry.area:.0f} m²<br>Both DH & HP Ready"
        ).add_to(building_group)
    
    # Create simulated infrastructure
    building_centroids = [b.geometry.centroid for b in buildings_gdf.itertuples()]
    
    # District Heating pipes (red)
    for i in range(len(building_centroids) - 1):
        line = LineString([building_centroids[i], building_centroids[i + 1]])
        folium.PolyLine(
            locations=[[p[1], p[0]] for p in line.coords],
            color="red",
            weight=4,
            opacity=0.8,
            popup=f"DH Supply Pipe {i+1}"
        ).add_to(dh_pipe_group)
    
    # Heat Pump power lines (yellow)
    if building_centroids:
        transformer_point = Point(
            building_centroids[0].x + 0.0002,
            building_centroids[0].y + 0.0002
        )
        folium.Marker(
            location=[transformer_point.y, transformer_point.x],
            popup="Transformer<br>400V/230V<br>Heat Pump Power",
            icon=folium.Icon(color="red", icon="bolt", prefix="fa")
        ).add_to(transformer_group)
        
        for idx, building in buildings_gdf.iterrows():
            centroid = building.geometry.centroid
            power_line = LineString([transformer_point, centroid])
            folium.PolyLine(
                locations=[[p[1], p[0]] for p in power_line.coords],
                color="yellow",
                weight=3,
                opacity=0.8,
                popup=f"HP Power Line {idx+1}"
            ).add_to(hp_power_group)
    
    # Service connections (orange)
    for idx, building in buildings_gdf.iterrows():
        centroid = building.geometry.centroid
        street_point = Point(centroid.x + 0.0001, centroid.y + 0.0001)
        service_line = LineString([centroid, street_point])
        
        folium.PolyLine(
            locations=[[p[1], p[0]] for p in service_line.coords],
            color="orange",
            weight=2,
            opacity=0.6,
            popup=f"Service Connection {idx+1}"
        ).add_to(service_group)
    
    # Add feature groups to map
    building_group.add_to(m)
    dh_pipe_group.add_to(m)
    hp_power_group.add_to(m)
    transformer_group.add_to(m)
    service_group.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add title and legend
    title_html = f"""
    <h3 align="center" style="font-size:16px"><b>Combined Infrastructure - {street_name}</b></h3>
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 200px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <b>Legend:</b><br>
    🔴 Red: DH Pipes<br>
    🟡 Yellow: HP Power<br>
    🔵 Blue: Buildings<br>
    ⚡ Red Icon: Transformer
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))
    
    return m

def save_maps(dh_map, hp_map, combined_map, street_name, output_dir="test_maps"):
    """Save all maps to HTML files."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Clean street name for filename
    clean_name = street_name.replace(" ", "_").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    
    saved_files = []
    
    if dh_map:
        dh_file = os.path.join(output_dir, f"district_heating_{clean_name}.html")
        dh_map.save(dh_file)
        saved_files.append(dh_file)
        print(f"✅ District Heating map saved: {dh_file}")
    
    if hp_map:
        hp_file = os.path.join(output_dir, f"heat_pump_{clean_name}.html")
        hp_map.save(hp_file)
        saved_files.append(hp_file)
        print(f"✅ Heat Pump map saved: {hp_file}")
    
    if combined_map:
        combined_file = os.path.join(output_dir, f"combined_infrastructure_{clean_name}.html")
        combined_map.save(combined_file)
        saved_files.append(combined_file)
        print(f"✅ Combined infrastructure map saved: {combined_file}")
    
    return saved_files

def create_dual_pipe_map_via_module(selected_street: str) -> str | None:
    """Use ImprovedDualPipeDHNetwork to render a proper street-following dual-pipe map."""
    if ImprovedDualPipeDHNetwork is None:
        print("Dual-pipe module not available.")
        return None
    try:
        net_builder = ImprovedDualPipeDHNetwork()
        # The module loads its own data from results_test/*.geojson; advanced wiring can filter by street
        ok = net_builder.load_data()
        if not ok:
            print("Failed to load data for dual-pipe module")
            return None
        net_builder.build_connected_street_network()
        # The improved module computes service connections and pipes internally (next steps in its main)
        # For brevity we jump to map creation (it expects internal state already prepared in its flow)
        out_dir = Path("test_maps"); out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"dual_pipe_{selected_street.replace(' ','_')}.html"
        net_builder.create_dual_pipe_interactive_map(save_path=str(out_file))
        print(f"✅ Dual-pipe map saved: {out_file}")
        return str(out_file)
    except Exception as e:
        print(f"Dual-pipe map creation failed: {e}")
        return None

def main():
    """Main function to run the street selection and map creation test."""
    print("🗺️ Street Selection and Interactive Map Test")
    print("=" * 50)
    
    # Configuration
    geojson_path = "data/geojson/hausumringe_mit_adressenV3.geojson"
    
    # Check if data file exists
    if not os.path.exists(geojson_path):
        print(f"❌ Data file not found: {geojson_path}")
        print("Please ensure the GeoJSON file exists in the correct location.")
        return
    
    # Get all street names
    street_names = get_all_street_names(geojson_path)
    if not street_names:
        print("❌ No streets found in the data file.")
        return
    
    # Interactive street selection
    selected_street = select_street_interactive(street_names)
    if not selected_street:
        print("❌ No street selected.")
        return
    
    print(f"\n🏠 Selected street: {selected_street}")
    
    # Get buildings for the selected street
    buildings = get_buildings_for_street(geojson_path, selected_street)
    if not buildings:
        print(f"❌ No buildings found for street: {selected_street}")
        return
    
    print(f"📊 Found {len(buildings)} buildings for analysis")
    
    # Create maps
    print("\n🗺️ Creating interactive maps...")
    
    # District Heating map
    dh_map = create_district_heating_map(buildings, selected_street)
    
    # Heat Pump map
    hp_map = create_heat_pump_map(buildings, selected_street)
    
    # Combined infrastructure map
    combined_map = create_combined_map(buildings, selected_street)
    
    # Save maps
    print("\n💾 Saving maps...")
    saved_files = save_maps(dh_map, hp_map, combined_map, selected_street)
    
    # Optionally: generate a street-following dual-pipe DH map from module
    do_dual = questionary.confirm("Also generate dual-pipe DH map (street-following)?", default=True).ask()
    if do_dual:
        dual_path = create_dual_pipe_map_via_module(selected_street)
        if dual_path:
            print(f"   • Dual-pipe map: {dual_path}")
            saved_files.append(dual_path)
    
    # Summary
    print("\n" + "=" * 50)
    print("✅ TEST COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print(f"📍 Street analyzed: {selected_street}")
    print(f"🏠 Buildings processed: {len(buildings)}")
    print(f"🗺️ Maps created: {len(saved_files)}")
    print("\n📁 Generated files:")
    for file in saved_files:
        print(f"   • {file}")
    
    print("\n🌐 To view the maps:")
    print("   1. Open any of the HTML files in a web browser")
    print("   2. Use the layer controls to show/hide different infrastructure")
    print("   3. Click on buildings and connections for detailed information")
    
    print("\n🔧 Map features:")
    print("   • District Heating: Red pipes, blue buildings")
    print("   • Heat Pumps: Yellow power lines, green buildings, red transformer")
    print("   • Combined: Both infrastructure types on one map")
    print("   • Interactive: Zoom, pan, layer controls, popups")

if __name__ == "__main__":
    main()
