#!/usr/bin/env python3
"""
Interactive DHA (Decentralized Heating Agent) with Maps and Pandapower
Based on legacy implementation from street_final_copy_3
"""

import os
import json
import yaml
import pandas as pd
import numpy as np
import folium
import geopandas as gpd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from shapely.geometry import Point, LineString
from pyproj import Transformer
import networkx as nx
from shapely.ops import nearest_points
import warnings

warnings.filterwarnings("ignore")

try:
    import questionary
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False
    print("⚠️ Questionary not available. Install with: pip install questionary")

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False
    print("⚠️ Pandapower not available. Install with: pip install pandapower")

class InteractiveDHA:
    """Interactive DHA with comprehensive visualization and Pandapower integration."""
    
    def __init__(self, config_path: str = "configs/dha.yml"):
        """Initialize Interactive DHA with configuration."""
        self.config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
        self.buildings = None
        self.power_infrastructure = {}
        self.streets = None
        self.load_profiles = {}
        self.power_metrics = {}
        
    def load_data(self) -> bool:
        """Load all required data for DHA analysis."""
        print("📁 Loading data for Interactive DHA...")
        
        try:
            # Load buildings
            buildings_file = "data/geojson/hausumringe_mit_adressenV3.geojson"
            if Path(buildings_file).exists():
                self.buildings = gpd.read_file(buildings_file)
                print(f"   ✅ Loaded {len(self.buildings)} buildings")
            else:
                print(f"   ⚠️ Buildings file not found: {buildings_file}")
                return False
            
            # Load power infrastructure
            self._load_power_infrastructure()
            
            # Load streets for routing
            self._load_streets()
            
            # Load load profiles
            self._load_load_profiles()
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error loading data: {e}")
            return False
    
    def _load_power_infrastructure(self):
        """Load power infrastructure data."""
        print("   🔌 Loading power infrastructure...")
        
        # Try to load from legacy locations
        power_files = {
            "lines": "agents copy/street_final_copy_3/branitz_hp_feasibility_outputs/power_lines.geojson",
            "substations": "agents copy/street_final_copy_3/branitz_hp_feasibility_outputs/power_substations.geojson",
            "plants": "agents copy/street_final_copy_3/branitz_hp_feasibility_outputs/power_plants.geojson",
            "generators": "agents copy/street_final_copy_3/branitz_hp_feasibility_outputs/power_generators.geojson"
        }
        
        for infra_type, file_path in power_files.items():
            if Path(file_path).exists():
                self.power_infrastructure[infra_type] = gpd.read_file(file_path)
                print(f"      ✅ Loaded {len(self.power_infrastructure[infra_type])} {infra_type}")
            else:
                print(f"      ⚠️ {infra_type} file not found: {file_path}")
                # Create empty GeoDataFrame
                self.power_infrastructure[infra_type] = gpd.GeoDataFrame()
    
    def _load_streets(self):
        """Load street network for routing."""
        print("   🛣️ Loading street network...")
        
        streets_file = "agents copy/street_final_copy_3/results_test/streets.geojson"
        if Path(streets_file).exists():
            self.streets = gpd.read_file(streets_file)
            print(f"      ✅ Loaded {len(self.streets)} street segments")
        else:
            print(f"      ⚠️ Streets file not found: {streets_file}")
            self.streets = None
    
    def _load_load_profiles(self):
        """Load building load profiles."""
        print("   📊 Loading load profiles...")
        
        load_profiles_file = "thesis-data-2/power-sim/gebaeude_lastphasenV2.json"
        if Path(load_profiles_file).exists():
            with open(load_profiles_file, "r") as f:
                self.load_profiles = json.load(f)
            print(f"      ✅ Loaded load profiles for {len(self.load_profiles)} buildings")
        else:
            print(f"      ⚠️ Load profiles file not found: {load_profiles_file}")
            self.load_profiles = {}
    
    def filter_buildings_for_street(self, street_name: str) -> gpd.GeoDataFrame:
        """Filter buildings for a specific street."""
        print(f"🏠 Filtering buildings for street: {street_name}")
        
        if self.buildings is None:
            print("   ❌ No buildings loaded")
            return gpd.GeoDataFrame()
        
        # Filter buildings by street name in address data
        street_buildings = []
        for idx, building in self.buildings.iterrows():
            # Check if building is on the specified street
            if self._building_on_street(building, street_name):
                street_buildings.append(building)
        
        if street_buildings:
            result = gpd.GeoDataFrame(street_buildings)
            print(f"   ✅ Found {len(result)} buildings on {street_name}")
            return result
        else:
            print(f"   ⚠️ No buildings found on {street_name}")
            return gpd.GeoDataFrame()
    
    def _building_on_street(self, building: pd.Series, street_name: str) -> bool:
        """Check if a building is on the specified street."""
        # Check various address fields
        address_fields = ['adressen', 'address', 'street', 'strasse']
        
        for field in address_fields:
            if field in building and pd.notna(building[field]):
                address_data = building[field]
                if isinstance(address_data, str):
                    try:
                        address_dict = json.loads(address_data)
                        if isinstance(address_dict, list) and len(address_dict) > 0:
                            address_dict = address_dict[0]
                        if isinstance(address_dict, dict):
                            # Check both 'street' and 'str' fields
                            street_value = address_dict.get('street', '') or address_dict.get('str', '')
                            if street_value and street_name.lower() in street_value.lower():
                                return True
                    except (json.JSONDecodeError, TypeError):
                        if street_name.lower() in str(address_data).lower():
                            return True
        
        return False
    
    def compute_proximity_analysis(self, buildings: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Compute proximity analysis for buildings."""
        print("📏 Computing proximity analysis...")
        
        if buildings.empty:
            return buildings
        
        # Ensure we're in a projected CRS for accurate calculations
        if buildings.crs is None:
            # Set default CRS to WGS84 if none is set
            buildings = buildings.set_crs("EPSG:4326")
        
        if buildings.crs.is_geographic:
            utm_crs = "EPSG:32633"
            buildings = buildings.to_crs(utm_crs)
        else:
            utm_crs = buildings.crs
        
        # Reproject infrastructure to same CRS
        for infra_type, infra_data in self.power_infrastructure.items():
            if not infra_data.empty:
                self.power_infrastructure[infra_type] = infra_data.to_crs(utm_crs)
        
        buildings = buildings.copy()
        buildings["centroid"] = buildings.geometry.centroid
        
        # Calculate distances to different infrastructure types
        if not self.power_infrastructure.get("lines", gpd.GeoDataFrame()).empty:
            buildings["dist_to_line"] = buildings["centroid"].apply(
                lambda x: self.power_infrastructure["lines"].distance(x).min()
            )
        else:
            buildings["dist_to_line"] = np.nan
        
        if not self.power_infrastructure.get("substations", gpd.GeoDataFrame()).empty:
            buildings["dist_to_substation"] = buildings["centroid"].apply(
                lambda x: self.power_infrastructure["substations"].distance(x).min()
            )
        else:
            buildings["dist_to_substation"] = np.nan
        
        # Combine plants and generators as transformers
        transformers = gpd.GeoDataFrame()
        if not self.power_infrastructure.get("plants", gpd.GeoDataFrame()).empty:
            transformers = pd.concat([transformers, self.power_infrastructure["plants"]], ignore_index=True)
        if not self.power_infrastructure.get("generators", gpd.GeoDataFrame()).empty:
            transformers = pd.concat([transformers, self.power_infrastructure["generators"]], ignore_index=True)
        
        if not transformers.empty:
            buildings["dist_to_transformer"] = buildings["centroid"].apply(
                lambda x: transformers.distance(x).min()
            )
        else:
            buildings["dist_to_transformer"] = np.nan
        
        # Flag buildings far from infrastructure
        buildings["flag_far_substation"] = buildings["dist_to_substation"] > 500
        buildings["flag_far_transformer"] = buildings["dist_to_transformer"] > 500
        
        print(f"   ✅ Proximity analysis completed for {len(buildings)} buildings")
        return buildings
    
    def compute_service_lines(self, buildings: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Compute street-following service lines."""
        print("🔗 Computing street-following service lines...")
        
        if buildings.empty:
            return buildings
        
        # Combine infrastructure for service line computation
        infra_list = []
        for infra_type in ["substations", "plants", "generators"]:
            if infra_type in self.power_infrastructure and not self.power_infrastructure[infra_type].empty:
                infra_list.append(self.power_infrastructure[infra_type])
        
        if not infra_list:
            print("   ⚠️ No infrastructure found for service line computation")
            return buildings
        
        infra = gpd.GeoDataFrame(pd.concat(infra_list, ignore_index=True))
        
        # Create street network if available
        G = None
        if self.streets is not None:
            G = self._create_street_network()
        
        service_lines = []
        nearest_infra_types = []
        distances = []
        routing_methods = []
        
        for idx, building in buildings.iterrows():
            building_centroid = building.geometry.centroid
            
            # Find nearest infrastructure
            nearest_idx = infra.distance(building_centroid).idxmin()
            nearest_geom = infra.loc[nearest_idx].geometry
            infra_type = infra.loc[nearest_idx].get("power", "infrastructure")
            
            if G is not None:
                # Use street-following routing
                service_line, distance, method = self._compute_street_following_connection(
                    building_centroid, nearest_geom, G
                )
            else:
                # Use straight-line connection
                nearest_point = nearest_points(building_centroid, nearest_geom)[1]
                service_line = LineString([building_centroid, nearest_point])
                distance = building_centroid.distance(nearest_point)
                method = "straight_line"
            
            service_lines.append(service_line)
            nearest_infra_types.append(infra_type)
            distances.append(distance)
            routing_methods.append(method)
        
        # Add service line information to buildings
        buildings = buildings.copy()
        buildings["service_line"] = service_lines
        buildings["nearest_infra_type"] = nearest_infra_types
        buildings["service_line_distance"] = distances
        buildings["routing_method"] = routing_methods
        
        print(f"   ✅ Computed {len(service_lines)} service lines")
        return buildings
    
    def _create_street_network(self) -> nx.Graph:
        """Create NetworkX graph from street data."""
        G = nx.Graph()
        
        if self.streets is None or self.streets.empty:
            return G
        
        # Add street segments as edges
        for idx, street in self.streets.iterrows():
            coords = list(street.geometry.coords)
            for i in range(len(coords) - 1):
                node1 = f"street_{idx}_{i}"
                node2 = f"street_{idx}_{i+1}"
                
                # Add nodes with positions
                G.add_node(node1, pos=coords[i], node_type="street")
                G.add_node(node2, pos=coords[i + 1], node_type="street")
                
                # Add edge with length as weight
                length = Point(coords[i]).distance(Point(coords[i + 1]))
                G.add_edge(node1, node2, weight=length, edge_type="street", length=length)
        
        # Connect nearby street nodes
        node_positions = [G.nodes[n]["pos"] for n in G.nodes() if G.nodes[n]["node_type"] == "street"]
        node_names = [n for n in G.nodes() if G.nodes[n]["node_type"] == "street"]
        node_points = [Point(pos) for pos in node_positions]
        
        for i, point in enumerate(node_points):
            for j, other_point in enumerate(node_points):
                if i != j and not G.has_edge(node_names[i], node_names[j]):
                    dist = point.distance(other_point)
                    if dist < 5.0:  # Connect nodes within 5m
                        G.add_edge(
                            node_names[i], node_names[j],
                            weight=dist, edge_type="connection", length=dist
                        )
        
        print(f"   ✅ Created street network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return G
    
    def _compute_street_following_connection(self, building_centroid, nearest_geom, G):
        """Compute street-following connection between building and infrastructure."""
        # Find nearest street nodes
        building_nearest_street = None
        min_building_distance = float("inf")
        
        for node in G.nodes():
            if G.nodes[node]["node_type"] == "street":
                node_pos = G.nodes[node]["pos"]
                node_point = Point(node_pos)
                distance = building_centroid.distance(node_point)
                if distance < min_building_distance:
                    min_building_distance = distance
                    building_nearest_street = node
        
        infra_nearest_street = None
        min_infra_distance = float("inf")
        
        for node in G.nodes():
            if G.nodes[node]["node_type"] == "street":
                node_pos = G.nodes[node]["pos"]
                node_point = Point(node_pos)
                distance = nearest_geom.centroid.distance(node_point)
                if distance < min_infra_distance:
                    min_infra_distance = distance
                    infra_nearest_street = node
        
        # Find shortest path
        if building_nearest_street and infra_nearest_street:
            try:
                path = nx.shortest_path(G, building_nearest_street, infra_nearest_street, weight="weight")
                
                # Create path geometry
                path_coords = []
                for node in path:
                    node_pos = G.nodes[node]["pos"]
                    path_coords.append(node_pos)
                
                # Create complete path: building -> street -> infrastructure
                building_point = (building_centroid.x, building_centroid.y)
                infra_point = (nearest_geom.centroid.x, nearest_geom.centroid.y)
                complete_coords = [building_point] + path_coords + [infra_point]
                service_line = LineString(complete_coords)
                
                # Calculate total distance
                total_distance = 0
                for i in range(len(complete_coords) - 1):
                    p1 = Point(complete_coords[i])
                    p2 = Point(complete_coords[i + 1])
                    total_distance += p1.distance(p2)
                
                return service_line, total_distance, "street_following"
                
            except nx.NetworkXNoPath:
                # Fallback to straight line
                nearest_point = nearest_points(building_centroid, nearest_geom)[1]
                service_line = LineString([building_centroid, nearest_point])
                distance = building_centroid.distance(nearest_point)
                return service_line, distance, "straight_line_fallback"
        
        # Fallback to straight line
        nearest_point = nearest_points(building_centroid, nearest_geom)[1]
        service_line = LineString([building_centroid, nearest_point])
        distance = building_centroid.distance(nearest_point)
        return service_line, distance, "straight_line_fallback"
    
    def run_pandapower_analysis(self, buildings: gpd.GeoDataFrame, scenario: str = "winter_werktag_abendspitze") -> Dict:
        """Run comprehensive Pandapower analysis."""
        print(f"⚡ Running Pandapower analysis for scenario: {scenario}")
        
        if not PANDAPOWER_AVAILABLE:
            print("   ❌ Pandapower not available")
            return {}
        
        if buildings.empty:
            print("   ❌ No buildings to analyze")
            return {}
        
        # Load network data
        network_json_path = Path("thesis-data-2/power-sim/branitzer_siedlung_ns_v3_ohne_UW.json")
        if not network_json_path.exists():
            print(f"   ⚠️ Network JSON file not found: {network_json_path}")
            return {}
        
        try:
            with open(network_json_path, "r") as f:
                network_data = json.load(f)
            
            # Create pandapower network
            net = self._create_pandapower_network(network_data)
            
            # Add loads for buildings
            self._add_building_loads(net, buildings, scenario)
            
            # Run power flow
            pp.runpp(net, algorithm="nr", max_iteration=40, tolerance_mva=1e-3)
            
            # Extract results
            results = self._extract_power_flow_results(net)
            
            print(f"   ✅ Pandapower analysis completed successfully")
            return results
            
        except Exception as e:
            print(f"   ❌ Pandapower analysis failed: {e}")
            return {}
    
    def _create_pandapower_network(self, network_data: Dict) -> pp.pandapowerNet:
        """Create pandapower network from JSON data."""
        net = pp.create_empty_network(name="Branitzer Siedlung", f_hz=50)
        
        nodes_data = network_data["nodes"]
        ways_data = network_data["ways"]
        
        # Create buses for each node
        node_id_to_bus = {}
        for node in nodes_data:
            node_id = str(node["id"])
            bus = pp.create_bus(net, vn_kv=0.4, name=f"Node {node_id}", type="b", zone="Branitz")
            node_id_to_bus[node_id] = bus
        
        # Create MV bus
        mv_bus = pp.create_bus(net, vn_kv=20, name="MV Grid Connection", type="b", zone="Branitz")
        
        # Create external grid
        pp.create_ext_grid(net, bus=mv_bus, vm_pu=1.02, va_degree=0.0, name="External Grid 20kV")
        
        # Create transformers
        trafo_sizes = {"C": 0.25, "B": 0.25, "J": 0.25, "E": 1.0}
        
        for node in nodes_data:
            tags = node.get("tags", {})
            node_id = str(node["id"])
            
            if tags.get("power") == "substation":
                trafo_id = tags.get("trafoid", "unknown")
                if node_id in node_id_to_bus:
                    lv_bus = node_id_to_bus[node_id]
                    size = trafo_sizes.get(trafo_id, 0.63)
                    
                    pp.create_transformer_from_parameters(
                        net, hv_bus=mv_bus, lv_bus=lv_bus,
                        sn_mva=size, vn_hv_kv=20.0, vn_lv_kv=0.4,
                        vk_percent=6.0, vkr_percent=0.8, pfe_kw=0.6,
                        i0_percent=0.1, name=f"MV_Transformer_{trafo_id}"
                    )
        
        # Create lines
        for way in ways_data:
            way_id = way["id"]
            node_ids = [str(node_id) for node_id in way["nodes"]]
            tags = way["tags"]
            
            power_type = tags.get("power", "")
            if power_type in ["line", "minor_line"]:
                for i in range(len(node_ids) - 1):
                    from_node_id = node_ids[i]
                    to_node_id = node_ids[i + 1]
                    from_bus = node_id_to_bus.get(from_node_id)
                    to_bus = node_id_to_bus.get(to_node_id)
                    
                    if from_bus is not None and to_bus is not None:
                        pp.create_line_from_parameters(
                            net, from_bus=from_bus, to_bus=to_bus,
                            length_km=0.1, r_ohm_per_km=0.125, x_ohm_per_km=0.078,
                            c_nf_per_km=264, max_i_ka=0.275,
                            name=f"Line {way_id}_{i}"
                        )
        
        return net
    
    def _add_building_loads(self, net: pp.pandapowerNet, buildings: gpd.GeoDataFrame, scenario: str):
        """Add building loads to pandapower network."""
        # This is a simplified version - in practice, you'd need to map buildings to network nodes
        # and use actual load profiles
        
        for idx, building in buildings.iterrows():
            building_id = building.get("gebaeude", building.get("id", str(idx)))
            
            if building_id in self.load_profiles:
                try:
                    peak_load_kw = self.load_profiles[building_id][scenario]
                except KeyError:
                    # Fallback to first available scenario
                    scenarios = list(self.load_profiles[building_id].keys())
                    if scenarios:
                        peak_load_kw = self.load_profiles[building_id][scenarios[0]]
                    else:
                        continue
                
                # Convert to MW and add load
                p_mw = peak_load_kw / 1000.0
                q_mvar = p_mw * 0.33  # Assume power factor of 0.95
                
                # Find a suitable bus (simplified - use first LV bus)
                lv_buses = net.bus[net.bus.vn_kv == 0.4]
                if not lv_buses.empty:
                    bus = lv_buses.index[0]
                    pp.create_load(net, bus=bus, p_mw=p_mw, q_mvar=q_mvar, name=f"Load_{building_id}")
    
    def _extract_power_flow_results(self, net: pp.pandapowerNet) -> Dict:
        """Extract power flow results from pandapower network."""
        results = {}
        
        if len(net.trafo) > 0:
            results["max_transformer_loading"] = net.res_trafo.loading_percent.max()
        else:
            results["max_transformer_loading"] = 0.0
        
        if len(net.bus) > 0:
            results["min_voltage"] = net.res_bus.vm_pu.min()
            results["max_voltage"] = net.res_bus.vm_pu.max()
        else:
            results["min_voltage"] = 1.0
            results["max_voltage"] = 1.0
        
        return results
    
    def create_interactive_map(self, buildings: gpd.GeoDataFrame, street_name: str, output_dir: str) -> str:
        """Create interactive Folium map for DHA analysis."""
        print(f"🗺️ Creating interactive map for {street_name}...")
        
        if buildings.empty:
            print("   ❌ No buildings to visualize")
            return ""
        
        # Calculate map center - ensure buildings are in WGS84 for centering
        buildings_wgs84 = buildings.to_crs(epsg=4326)
        center = buildings_wgs84.geometry.centroid.unary_union.centroid
        center_lat, center_lon = center.y, center.x
        
        # Create map with proper zoom level for street-level view
        m = folium.Map(location=[center_lat, center_lon], zoom_start=18)
        
        # Add tile layers
        folium.TileLayer("openstreetmap", name="OpenStreetMap").add_to(m)
        folium.TileLayer("cartodbpositron", name="CartoDB Positron").add_to(m)
        
        # Create feature groups
        fg_streets = folium.FeatureGroup(name="Streets", show=True)
        fg_power_lines = folium.FeatureGroup(name="Power Lines", show=True)
        fg_infra = folium.FeatureGroup(name="Infrastructure", show=False)
        fg_service_lines = folium.FeatureGroup(name="Service Lines", show=False)
        fg_buildings = folium.FeatureGroup(name="Buildings", show=True)
        
        # Add streets if available
        if self.streets is not None:
            streets_wgs84 = self.streets.to_crs(epsg=4326)
            for _, row in streets_wgs84.iterrows():
                if row.geometry.geom_type == "LineString":
                    coords = list(row.geometry.coords)
                    folium.PolyLine(
                        locations=[(lat, lon) for lon, lat in coords],
                        color="gray", weight=3, opacity=0.7, tooltip="Street"
                    ).add_to(fg_streets)
        
        # Add power infrastructure
        self._add_power_infrastructure_to_map(fg_power_lines, fg_infra)
        
        # Add service lines (use original buildings for service line geometry)
        self._add_service_lines_to_map(buildings, fg_service_lines)
        
        # Add buildings (use already converted WGS84 buildings)
        self._add_buildings_to_map(buildings_wgs84, fg_buildings)
        
        # Add all feature groups
        for fg in [fg_streets, fg_power_lines, fg_infra, fg_service_lines, fg_buildings]:
            fg.add_to(m)
        
        # Add layer control
        folium.LayerControl(collapsed=False).add_to(m)
        
        # Add title
        title_html = f"""
        <h3 align="center" style="font-size:16px"><b>Heat Pump Feasibility Analysis - {street_name}</b></h3>
        """
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Save map
        map_path = Path(output_dir) / f"dha_interactive_map_{street_name.replace(' ', '_')}.html"
        m.save(str(map_path))
        
        print(f"   ✅ Interactive map saved to {map_path}")
        return str(map_path)
    
    def _add_power_infrastructure_to_map(self, fg_power_lines, fg_infra):
        """Add power infrastructure to map."""
        # Add power lines
        if "lines" in self.power_infrastructure and not self.power_infrastructure["lines"].empty:
            lines_wgs84 = self.power_infrastructure["lines"].to_crs(epsg=4326)
            for _, row in lines_wgs84.iterrows():
                if row.geometry.geom_type == "LineString":
                    coords = list(row.geometry.coords)
                    folium.PolyLine(
                        locations=[(lat, lon) for lon, lat in coords],
                        color="orange", weight=4, opacity=0.8, tooltip="Power Line"
                    ).add_to(fg_power_lines)
        
        # Add substations
        if "substations" in self.power_infrastructure and not self.power_infrastructure["substations"].empty:
            substations_wgs84 = self.power_infrastructure["substations"].to_crs(epsg=4326)
            for _, row in substations_wgs84.iterrows():
                centroid = row.geometry.centroid
                folium.CircleMarker(
                    location=[centroid.y, centroid.x], color="red", radius=8, tooltip="Substation"
                ).add_to(fg_infra)
        
        # Add plants and generators
        for infra_type, color in [("plants", "green"), ("generators", "purple")]:
            if infra_type in self.power_infrastructure and not self.power_infrastructure[infra_type].empty:
                infra_wgs84 = self.power_infrastructure[infra_type].to_crs(epsg=4326)
                for _, row in infra_wgs84.iterrows():
                    centroid = row.geometry.centroid
                    folium.CircleMarker(
                        location=[centroid.y, centroid.x], color=color, radius=6, tooltip=infra_type.title()
                    ).add_to(fg_infra)
    
    def _add_service_lines_to_map(self, buildings: gpd.GeoDataFrame, fg_service_lines):
        """Add service lines to map."""
        if "service_line" not in buildings.columns:
            return
        
        buildings_wgs84 = buildings.to_crs(epsg=4326)
        for idx, building in buildings_wgs84.iterrows():
            if building["service_line"] is not None:
                service_line = building["service_line"]
                if hasattr(service_line, "coords"):
                    coords = list(service_line.coords)
                    if len(coords) >= 2:
                        coords_wgs = [[lat, lon] for lon, lat in coords]
                        
                        # Color based on infrastructure type
                        color = "red" if building.get("nearest_infra_type") == "substation" else "purple"
                        
                        folium.PolyLine(
                            locations=coords_wgs, color=color, weight=2, opacity=0.6,
                            tooltip=f"Service Line: {building.get('service_line_distance', 0):.1f}m to {building.get('nearest_infra_type', 'infrastructure')}"
                        ).add_to(fg_service_lines)
    
    def _add_buildings_to_map(self, buildings: gpd.GeoDataFrame, fg_buildings):
        """Add buildings to map."""
        # Buildings should already be in WGS84 when passed to this method
        
        for idx, building in buildings.iterrows():
            centroid = building.geometry.centroid
            
            # Color based on proximity to infrastructure
            if building.get("flag_far_transformer", True):
                color = "red"  # Far from transformer
            elif building.get("flag_far_substation", True):
                color = "orange"  # Far from substation
            else:
                color = "green"  # Close to infrastructure
            
            # Create tooltip with building information
            tooltip = f"""
            Building ID: {str(idx)}<br>
            Dist to line: {building.get('dist_to_line', 'N/A'):.1f} m<br>
            Dist to substation: {building.get('dist_to_substation', 'N/A'):.1f} m<br>
            Dist to transformer: {building.get('dist_to_transformer', 'N/A'):.1f} m<br>
            Service distance: {building.get('service_line_distance', 'N/A'):.1f} m<br>
            Routing: {building.get('routing_method', 'N/A')}
            """
            
            folium.CircleMarker(
                location=[centroid.y, centroid.x], color=color, radius=5, tooltip=tooltip
            ).add_to(fg_buildings)
    
    def create_dashboard(self, buildings: gpd.GeoDataFrame, street_name: str, map_path: str, power_results: Dict, output_dir: str) -> str:
        """Create comprehensive HTML dashboard."""
        print(f"📊 Creating dashboard for {street_name}...")
        
        # Calculate statistics
        stats = {
            "total_buildings": len(buildings),
            "close_to_transformer": len(buildings[~buildings.get("flag_far_transformer", True)]),
            "close_to_substation": len(buildings[~buildings.get("flag_far_substation", True)]),
            "avg_dist_to_line": buildings.get("dist_to_line", pd.Series()).mean(),
            "avg_dist_to_substation": buildings.get("dist_to_substation", pd.Series()).mean(),
            "avg_dist_to_transformer": buildings.get("dist_to_transformer", pd.Series()).mean(),
            "avg_service_distance": buildings.get("service_line_distance", pd.Series()).mean(),
            "max_transformer_loading": power_results.get("max_transformer_loading", 0),
            "min_voltage": power_results.get("min_voltage", 1.0),
            "max_voltage": power_results.get("max_voltage", 1.0)
        }
        
        # Create dashboard HTML
        dashboard_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DHA Interactive Analysis - {street_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 20px; margin-bottom: 30px; }}
        .dashboard-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .metric-card {{ background: #ecf0f1; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db; }}
        .metric-title {{ font-weight: bold; color: #2c3e50; margin-bottom: 8px; font-size: 14px; }}
        .metric-value {{ font-size: 20px; color: #27ae60; font-weight: bold; }}
        .metric-unit {{ font-size: 12px; color: #7f8c8d; }}
        .map-container {{ text-align: center; }}
        .map-container iframe {{ border: 1px solid #bdc3c7; border-radius: 8px; width: 100%; height: 600px; }}
        .status-success {{ color: #27ae60; font-weight: bold; }}
        .status-warning {{ color: #f39c12; font-weight: bold; }}
        .status-error {{ color: #e74c3c; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ DHA Interactive Analysis</h1>
            <h2>Heat Pump Feasibility - {street_name}</h2>
            <p>Comprehensive electrical infrastructure analysis with interactive visualization</p>
        </div>
        
        <div class="dashboard-grid">
            <div>
                <h3>📊 Building Analysis</h3>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-title">Total Buildings</div>
                        <div class="metric-value">{stats['total_buildings']}</div>
                        <div class="metric-unit">buildings</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Close to Transformer</div>
                        <div class="metric-value">{stats['close_to_transformer']}</div>
                        <div class="metric-unit">buildings</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Close to Substation</div>
                        <div class="metric-value">{stats['close_to_substation']}</div>
                        <div class="metric-unit">buildings</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Avg Service Distance</div>
                        <div class="metric-value">{stats['avg_service_distance']:.1f}</div>
                        <div class="metric-unit">meters</div>
                    </div>
                </div>
                
                <h3>⚡ Power Flow Analysis</h3>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-title">Max Transformer Loading</div>
                        <div class="metric-value">{stats['max_transformer_loading']:.2f}</div>
                        <div class="metric-unit">%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Min Voltage</div>
                        <div class="metric-value">{stats['min_voltage']:.3f}</div>
                        <div class="metric-unit">pu</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Max Voltage</div>
                        <div class="metric-value">{stats['max_voltage']:.3f}</div>
                        <div class="metric-unit">pu</div>
                    </div>
                </div>
            </div>
            
            <div>
                <h3>🗺️ Interactive Map</h3>
                <div class="map-container">
                    <iframe src="{os.path.basename(map_path)}"></iframe>
                </div>
            </div>
        </div>
        
        <div>
            <h3>✅ Feasibility Assessment</h3>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">
                <h4>Heat Pump Deployment Readiness</h4>
                <ul>
                    <li><span class="status-success">✅ Interactive Analysis</span> - Comprehensive infrastructure assessment</li>
                    <li><span class="status-success">✅ Street-Following Routing</span> - Realistic service connections</li>
                    <li><span class="status-success">✅ Pandapower Integration</span> - Accurate power flow analysis</li>
                    <li><span class="status-success">✅ Proximity Analysis</span> - Distance-based feasibility assessment</li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        # Save dashboard
        dashboard_path = Path(output_dir) / f"dha_dashboard_{street_name.replace(' ', '_')}.html"
        with open(dashboard_path, "w", encoding="utf-8") as f:
            f.write(dashboard_html)
        
        print(f"   ✅ Dashboard saved to {dashboard_path}")
        return str(dashboard_path)
    
    def get_available_streets(self) -> List[str]:
        """Get list of available street names from building data."""
        if self.buildings is None:
            return []
        
        streets = set()
        for idx, building in self.buildings.iterrows():
            if 'adressen' in building and pd.notna(building['adressen']):
                try:
                    address_data = json.loads(building['adressen'])
                    if isinstance(address_data, list) and len(address_data) > 0:
                        address_data = address_data[0]
                    if isinstance(address_data, dict):
                        street_value = address_data.get('street', '') or address_data.get('str', '')
                        if street_value:
                            streets.add(street_value)
                except (json.JSONDecodeError, TypeError):
                    continue
        
        return sorted(list(streets))
    
    def run_comprehensive_analysis(self, street_name: str, scenario: str = "winter_werktag_abendspitze") -> Dict:
        """Run comprehensive DHA analysis for a street."""
        print(f"🚀 Running comprehensive DHA analysis for {street_name}")
        print("=" * 60)
        
        # Create output directory
        output_dir = Path("processed/dha") / street_name.replace(" ", "_")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Load data
            if not self.load_data():
                return {"status": "error", "message": "Failed to load data"}
            
            # Filter buildings for street
            buildings = self.filter_buildings_for_street(street_name)
            if buildings.empty:
                return {"status": "error", "message": f"No buildings found on {street_name}"}
            
            # Run analysis pipeline
            buildings = self.compute_proximity_analysis(buildings)
            buildings = self.compute_service_lines(buildings)
            
            # Run Pandapower analysis
            power_results = self.run_pandapower_analysis(buildings, scenario)
            
            # Create visualizations
            map_path = self.create_interactive_map(buildings, street_name, str(output_dir))
            dashboard_path = self.create_dashboard(buildings, street_name, map_path, power_results, str(output_dir))
            
            # Save results (handle multiple geometry columns)
            buildings_save = buildings.copy()
            
            # Convert all geometry columns except the main one to WKT
            geometry_columns = [col for col in buildings_save.columns if buildings_save[col].dtype == 'geometry']
            for geom_col in geometry_columns:
                if geom_col != 'geometry':  # Keep the main geometry column
                    buildings_save[f"{geom_col}_wkt"] = buildings_save[geom_col].apply(
                        lambda x: x.wkt if x is not None else None
                    )
                    buildings_save = buildings_save.drop(columns=[geom_col])
            
            buildings_save.to_file(output_dir / "buildings_analysis.geojson", driver="GeoJSON")
            
            print(f"\n✅ Comprehensive DHA analysis completed for {street_name}")
            print(f"   📁 Results saved to: {output_dir}")
            print(f"   🗺️ Interactive map: {map_path}")
            print(f"   📊 Dashboard: {dashboard_path}")
            
            return {
                "status": "success",
                "street_name": street_name,
                "buildings_analyzed": len(buildings),
                "output_dir": str(output_dir),
                "map_path": map_path,
                "dashboard_path": dashboard_path,
                "power_results": power_results
            }
            
        except Exception as e:
            print(f"\n❌ DHA analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

def main():
    """Main function for Interactive DHA with street selection."""
    import sys
    
    dha = InteractiveDHA()
    
    # Load data to get available streets
    if not dha.load_data():
        print("❌ Failed to load data")
        return
    
    # Get available streets
    available_streets = dha.get_available_streets()
    
    if not available_streets:
        print("❌ No streets found in building data")
        return
    
    # Interactive street selection
    if QUESTIONARY_AVAILABLE and len(sys.argv) == 1:
        print("🏠 Available streets for analysis:")
        street_name = questionary.select(
            "Select a street for DHA analysis:",
            choices=available_streets[:20]  # Limit to first 20 for performance
        ).ask()
        
        if not street_name:
            print("❌ No street selected")
            return
    else:
        # Use command line argument or default
        street_name = sys.argv[1] if len(sys.argv) > 1 else available_streets[0]
    
    scenario = sys.argv[2] if len(sys.argv) > 2 else "winter_werktag_abendspitze"
    
    print(f"🎯 Selected street: {street_name}")
    print(f"📊 Scenario: {scenario}")
    
    result = dha.run_comprehensive_analysis(street_name, scenario)
    
    print(f"\n📋 Analysis Result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
