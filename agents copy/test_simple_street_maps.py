#!/usr/bin/env python3
"""
Simple Street Selection and Interactive Maps Test

This script demonstrates street selection and interactive map creation
using synthetic data for testing purposes.

Usage:
    python test_simple_street_maps.py
"""

import json
import os
import folium
from shapely.geometry import Point, LineString, Polygon
import geopandas as gpd
import questionary

def create_synthetic_street_data():
    """Create synthetic street and building data for testing."""
    print("Creating synthetic street data...")
    
    # Synthetic street data
    streets = [
        "Musterstraße",
        "Beispielweg", 
        "Testallee",
        "Demoplatz",
        "Sample Road"
    ]
    
    # Synthetic buildings for each street
    buildings_data = {
        "Musterstraße": [
            {"id": "B1", "area": 150, "lat": 52.5200, "lon": 13.4050},
            {"id": "B2", "area": 200, "lat": 52.5201, "lon": 13.4051},
            {"id": "B3", "area": 180, "lat": 52.5202, "lon": 13.4052},
        ],
        "Beispielweg": [
            {"id": "B4", "area": 120, "lat": 52.5203, "lon": 13.4053},
            {"id": "B5", "area": 160, "lat": 52.5204, "lon": 13.4054},
        ],
        "Testallee": [
            {"id": "B6", "area": 220, "lat": 52.5205, "lon": 13.4055},
            {"id": "B7", "area": 190, "lat": 52.5206, "lon": 13.4056},
            {"id": "B8", "area": 170, "lat": 52.5207, "lon": 13.4057},
        ],
        "Demoplatz": [
            {"id": "B9", "area": 140, "lat": 52.5208, "lon": 13.4058},
        ],
        "Sample Road": [
            {"id": "B10", "area": 250, "lat": 52.5209, "lon": 13.4059},
            {"id": "B11", "area": 210, "lat": 52.5210, "lon": 13.4060},
        ]
    }
    
    return streets, buildings_data

def select_street_interactive(streets):
    """Interactive street selection."""
    selected_street = questionary.select(
        "Select a street to analyze:",
        choices=streets,
        default=streets[0]
    ).ask()
    
    return selected_street

def create_building_geometries(buildings_data):
    """Convert building data to GeoDataFrame with proper geometries."""
    features = []
    
    for building in buildings_data:
        # Create a simple square building around the point
        lat, lon = building["lat"], building["lon"]
        size = 0.0001  # Small square around the point
        
        # Create square polygon
        coords = [
            (lon - size, lat - size),
            (lon + size, lat - size),
            (lon + size, lat + size),
            (lon - size, lat + size),
            (lon - size, lat - size)
        ]
        
        polygon = Polygon(coords)
        
        feature = {
            "type": "Feature",
            "geometry": polygon,
            "properties": {
                "id": building["id"],
                "area": building["area"],
                "lat": lat,
                "lon": lon
            }
        }
        features.append(feature)
    
    return gpd.GeoDataFrame(features)

def create_district_heating_map(buildings_gdf, street_name):
    """Create District Heating interactive map."""
    print(f"Creating District Heating map for {street_name}...")
    
    # Calculate center
    center_lat = buildings_gdf.geometry.centroid.y.mean()
    center_lon = buildings_gdf.geometry.centroid.x.mean()
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=18)
    
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
            radius=10,
            color="blue",
            fill=True,
            fillColor="lightblue",
            fillOpacity=0.7,
            popup=f"Building {building['properties']['id']}<br>Area: {building['properties']['area']} m²"
        ).add_to(building_group)
    
    # Create pipe network (connect buildings in sequence)
    building_centroids = [b.geometry.centroid for b in buildings_gdf.itertuples()]
    
    for i in range(len(building_centroids) - 1):
        line = LineString([building_centroids[i], building_centroids[i + 1]])
        folium.PolyLine(
            locations=[[p[1], p[0]] for p in line.coords],
            color="red",
            weight=5,
            opacity=0.8,
            popup=f"DH Supply Pipe {i+1}"
        ).add_to(pipe_group)
    
    # Add service connections
    for idx, building in buildings_gdf.iterrows():
        centroid = building.geometry.centroid
        # Simulate street connection
        street_point = Point(centroid.x + 0.00005, centroid.y + 0.00005)
        service_line = LineString([centroid, street_point])
        
        folium.PolyLine(
            locations=[[p[1], p[0]] for p in service_line.coords],
            color="orange",
            weight=3,
            opacity=0.6,
            popup=f"Service Connection {building['properties']['id']}"
        ).add_to(service_group)
    
    # Add feature groups
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

def create_heat_pump_map(buildings_gdf, street_name):
    """Create Heat Pump interactive map."""
    print(f"Creating Heat Pump map for {street_name}...")
    
    # Calculate center
    center_lat = buildings_gdf.geometry.centroid.y.mean()
    center_lon = buildings_gdf.geometry.centroid.x.mean()
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=18)
    
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
            radius=10,
            color="green",
            fill=True,
            fillColor="lightgreen",
            fillOpacity=0.7,
            popup=f"Building {building['properties']['id']}<br>Heat Pump Ready<br>Area: {building['properties']['area']} m²"
        ).add_to(building_group)
    
    # Add transformer
    building_centroids = [b.geometry.centroid for b in buildings_gdf.itertuples()]
    if building_centroids:
        transformer_point = Point(
            building_centroids[0].x + 0.0001,
            building_centroids[0].y + 0.0001
        )
        folium.Marker(
            location=[transformer_point.y, transformer_point.x],
            popup="Transformer<br>400V/230V<br>Heat Pump Power",
            icon=folium.Icon(color="red", icon="bolt", prefix="fa")
        ).add_to(transformer_group)
        
        # Create power lines
        for idx, building in buildings_gdf.iterrows():
            centroid = building.geometry.centroid
            power_line = LineString([transformer_point, centroid])
            
            folium.PolyLine(
                locations=[[p[1], p[0]] for p in power_line.coords],
                color="yellow",
                weight=4,
                opacity=0.8,
                popup=f"Power Line {building['properties']['id']}<br>Heat Pump Connection"
            ).add_to(power_line_group)
    
    # Add service connections
    for idx, building in buildings_gdf.iterrows():
        centroid = building.geometry.centroid
        street_point = Point(centroid.x + 0.00005, centroid.y + 0.00005)
        service_line = LineString([centroid, street_point])
        
        folium.PolyLine(
            locations=[[p[1], p[0]] for p in service_line.coords],
            color="purple",
            weight=3,
            opacity=0.6,
            popup=f"Service Connection {building['properties']['id']}"
        ).add_to(service_group)
    
    # Add feature groups
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

def create_combined_map(buildings_gdf, street_name):
    """Create combined infrastructure map."""
    print(f"Creating combined infrastructure map for {street_name}...")
    
    # Calculate center
    center_lat = buildings_gdf.geometry.centroid.y.mean()
    center_lon = buildings_gdf.geometry.centroid.x.mean()
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=18)
    
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
            radius=10,
            color="gray",
            fill=True,
            fillColor="lightgray",
            fillOpacity=0.7,
            popup=f"Building {building['properties']['id']}<br>Area: {building['properties']['area']} m²<br>Both DH & HP Ready"
        ).add_to(building_group)
    
    # District Heating pipes
    building_centroids = [b.geometry.centroid for b in buildings_gdf.itertuples()]
    for i in range(len(building_centroids) - 1):
        line = LineString([building_centroids[i], building_centroids[i + 1]])
        folium.PolyLine(
            locations=[[p[1], p[0]] for p in line.coords],
            color="red",
            weight=5,
            opacity=0.8,
            popup=f"DH Supply Pipe {i+1}"
        ).add_to(dh_pipe_group)
    
    # Heat Pump infrastructure
    if building_centroids:
        transformer_point = Point(
            building_centroids[0].x + 0.0001,
            building_centroids[0].y + 0.0001
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
                weight=4,
                opacity=0.8,
                popup=f"HP Power Line {building['properties']['id']}"
            ).add_to(hp_power_group)
    
    # Service connections
    for idx, building in buildings_gdf.iterrows():
        centroid = building.geometry.centroid
        street_point = Point(centroid.x + 0.00005, centroid.y + 0.00005)
        service_line = LineString([centroid, street_point])
        
        folium.PolyLine(
            locations=[[p[1], p[0]] for p in service_line.coords],
            color="orange",
            weight=3,
            opacity=0.6,
            popup=f"Service Connection {building['properties']['id']}"
        ).add_to(service_group)
    
    # Add feature groups
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
    🔵 Gray: Buildings<br>
    ⚡ Red Icon: Transformer
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))
    
    return m

def save_maps(dh_map, hp_map, combined_map, street_name, output_dir="test_maps_simple"):
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

def main():
    """Main function to run the simple street selection and map creation test."""
    print("🗺️ Simple Street Selection and Interactive Map Test")
    print("=" * 55)
    
    # Create synthetic data
    streets, buildings_data = create_synthetic_street_data()
    
    print(f"📋 Available streets: {', '.join(streets)}")
    
    # Interactive street selection
    selected_street = select_street_interactive(streets)
    if not selected_street:
        print("❌ No street selected.")
        return
    
    print(f"\n🏠 Selected street: {selected_street}")
    
    # Get buildings for selected street
    buildings = buildings_data.get(selected_street, [])
    if not buildings:
        print(f"❌ No buildings found for street: {selected_street}")
        return
    
    print(f"📊 Found {len(buildings)} buildings for analysis")
    
    # Convert to GeoDataFrame
    buildings_gdf = create_building_geometries(buildings)
    
    # Create maps
    print("\n🗺️ Creating interactive maps...")
    
    # District Heating map
    dh_map = create_district_heating_map(buildings_gdf, selected_street)
    
    # Heat Pump map
    hp_map = create_heat_pump_map(buildings_gdf, selected_street)
    
    # Combined infrastructure map
    combined_map = create_combined_map(buildings_gdf, selected_street)
    
    # Save maps
    print("\n💾 Saving maps...")
    saved_files = save_maps(dh_map, hp_map, combined_map, selected_street)
    
    # Summary
    print("\n" + "=" * 55)
    print("✅ SIMPLE TEST COMPLETED SUCCESSFULLY!")
    print("=" * 55)
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
    
    print("\n📝 Note: This test uses synthetic data for demonstration.")
    print("   For real data analysis, use test_street_selection_and_maps.py")

if __name__ == "__main__":
    main()
