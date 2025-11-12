from pathlib import Path
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import pytest

def _create_test_network_data(tmp: Path):
    """Create comprehensive test network data."""
    # Create streets directory
    (tmp/"data/geojson").mkdir(parents=True, exist_ok=True)
    
    # Create a realistic street network (square with diagonal)
    streets_data = [
        {"name": "Main Street", "highway": "residential", "geometry": LineString([(0, 0), (100, 0)])},
        {"name": "Side Street", "highway": "residential", "geometry": LineString([(100, 0), (100, 100)])},
        {"name": "Back Street", "highway": "residential", "geometry": LineString([(100, 100), (0, 100)])},
        {"name": "Cross Street", "highway": "residential", "geometry": LineString([(0, 100), (0, 0)])},
        {"name": "Diagonal Street", "highway": "residential", "geometry": LineString([(0, 0), (100, 100)])},
    ]
    
    streets_gdf = gpd.GeoDataFrame(streets_data, crs="EPSG:32633")
    streets_gdf.to_file(tmp/"data/geojson/strassen_mit_adressenV3.geojson", driver="GeoJSON")
    
    # Create buildings at strategic locations
    buildings_data = [
        {"id": 1, "strasse": "Main Street", "building_type": "residential", "heating_load_kw": 15.0, "annual_heat_demand_kwh": 30000, "building_area_m2": 150, "geometry": Point(25, 25)},
        {"id": 2, "strasse": "Side Street", "building_type": "residential", "heating_load_kw": 12.0, "annual_heat_demand_kwh": 25000, "building_area_m2": 120, "geometry": Point(75, 25)},
        {"id": 3, "strasse": "Back Street", "building_type": "residential", "heating_load_kw": 18.0, "annual_heat_demand_kwh": 35000, "building_area_m2": 180, "geometry": Point(75, 75)},
        {"id": 4, "strasse": "Cross Street", "building_type": "residential", "heating_load_kw": 14.0, "annual_heat_demand_kwh": 28000, "building_area_m2": 140, "geometry": Point(25, 75)},
        {"id": 5, "strasse": "Diagonal Street", "building_type": "residential", "heating_load_kw": 16.0, "annual_heat_demand_kwh": 32000, "building_area_m2": 160, "geometry": Point(50, 50)},
    ]
    
    buildings_gdf = gpd.GeoDataFrame(buildings_data, crs="EPSG:32633")
    buildings_gdf.to_file(tmp/"data/geojson/hausumringe_mit_adressenV3.geojson", driver="GeoJSON")

def _create_test_config(tmp: Path) -> str:
    """Create test CHA configuration."""
    (tmp/"configs").mkdir(parents=True, exist_ok=True)
    
    config = f"""
# Test CHA Configuration
streets_path: {tmp/'data/geojson/strassen_mit_adressenV3.geojson'}
buildings_path: {tmp/'data/geojson/hausumringe_mit_adressenV3.geojson'}

# Plant location (center of network)
plant_lon: 50.0
plant_lat: 50.0

# Network parameters
max_building_distance_m: 50
connectivity_fix_distance_m: 100

# Output settings
output_dir: {tmp/'processed/cha'}
map_filename: "network_map.html"
geopackage_filename: "cha.gpkg"

# Temperature and pressure settings
supply_temperature_c: 70
return_temperature_c: 40
supply_pressure_bar: 6.0
return_pressure_bar: 2.0

# Building attributes (fallback values)
default_heating_load_kw: 10.0
default_annual_heat_demand_kwh: 24000
default_building_type: "residential"
default_building_area_m2: 120

# Pandapipes simulation settings
enable_pandapipes_simulation: true
simulation_output_dir: {tmp/'eval/cha'}
default_pipe_diameter_m: 0.1
default_pipe_roughness_mm: 0.1
default_mass_flow_kg_s: 0.1
"""
    
    (tmp/"configs/cha.yml").write_text(config, encoding="utf-8")
    return str(tmp/"configs/cha.yml")

def test_cha_dual_pipe_network_construction(tmp_path: Path, monkeypatch):
    """Test that CHA can construct a complete dual-pipe network."""
    # Create test data
    _create_test_network_data(tmp_path)
    config_path = _create_test_config(tmp_path)
    
    # Import and run CHA
    import sys
    sys.path.insert(0, str(tmp_path))
    
    try:
        from src.cha import CentralizedHeatingAgent
        
        # Create CHA instance and run full workflow
        cha = CentralizedHeatingAgent(config_path)
        result = cha.run(config_path)
        
        # Verify successful execution
        assert result["status"] == "ok"
        assert "network_stats" in result
        assert "num_buildings" in result
        
        # Check network statistics
        stats = result["network_stats"]
        assert stats["complete_dual_pipe_system"] is True
        assert stats["street_based_routing"] is True
        assert stats["all_connections_follow_streets"] is True
        assert stats["no_direct_connections"] is True
        assert stats["engineering_compliant"] is True
        
        # Check that we have both supply and return networks
        assert stats["total_supply_length_km"] > 0
        assert stats["total_return_length_km"] > 0
        assert stats["total_main_length_km"] > 0
        assert stats["total_service_length_m"] > 0
        
        # Check building connections
        assert stats["num_buildings"] > 0
        assert stats["service_connections"] > 0
        
        print("✅ CHA dual-pipe network construction test passed")
        
    except Exception as e:
        print(f"❌ CHA dual-pipe network construction test failed: {e}")
        raise

def test_cha_street_following_routing(tmp_path: Path, monkeypatch):
    """Test that all connections follow street network."""
    # Create test data
    _create_test_network_data(tmp_path)
    config_path = _create_test_config(tmp_path)
    
    # Import and run CHA
    import sys
    sys.path.insert(0, str(tmp_path))
    
    try:
        from src.cha import CentralizedHeatingAgent
        
        # Create CHA instance and run network construction
        cha = CentralizedHeatingAgent(config_path)
        cha.load_data()
        cha.build_connected_street_network()
        cha.snap_buildings_to_street_network()
        cha.create_dual_pipe_network()
        cha.create_dual_service_connections()
        
        # Verify that all pipes follow streets
        for _, pipe in cha.supply_pipes.iterrows():
            assert pipe["follows_street"] is True
            assert "street_id" in pipe
            assert "street_name" in pipe
        
        for _, pipe in cha.return_pipes.iterrows():
            assert pipe["follows_street"] is True
            assert "street_id" in pipe
            assert "street_name" in pipe
        
        # Verify that all service connections follow streets
        for _, service in cha.dual_service_connections.iterrows():
            assert service["follows_street"] is True
            assert "street_segment_id" in service
            assert "street_name" in service
        
        print("✅ CHA street-following routing test passed")
        
    except Exception as e:
        print(f"❌ CHA street-following routing test failed: {e}")
        raise

def test_cha_dual_service_connections(tmp_path: Path, monkeypatch):
    """Test that each building has truly dual service connections."""
    # Create test data
    _create_test_network_data(tmp_path)
    config_path = _create_test_config(tmp_path)
    
    # Import and run CHA
    import sys
    sys.path.insert(0, str(tmp_path))
    
    try:
        from src.cha import CentralizedHeatingAgent
        
        # Create CHA instance and run network construction
        cha = CentralizedHeatingAgent(config_path)
        cha.load_data()
        cha.build_connected_street_network()
        cha.snap_buildings_to_street_network()
        cha.create_dual_pipe_network()
        cha.create_dual_service_connections()
        
        # Get unique building IDs
        building_ids = cha.service_connections["building_id"].unique()
        
        # Verify each building has exactly 2 service connections
        for building_id in building_ids:
            building_services = cha.dual_service_connections[
                cha.dual_service_connections["building_id"] == building_id
            ]
            
            assert len(building_services) == 2, f"Building {building_id} should have 2 service connections"
            
            # Check that one is supply and one is return
            service_types = building_services["pipe_type"].tolist()
            assert "supply_service" in service_types, f"Building {building_id} missing supply service"
            assert "return_service" in service_types, f"Building {building_id} missing return service"
            
            # Check that both reference the correct building_id
            for _, service in building_services.iterrows():
                assert service["building_id"] == building_id
        
        print("✅ CHA dual service connections test passed")
        
    except Exception as e:
        print(f"❌ CHA dual service connections test failed: {e}")
        raise

def test_cha_interactive_map_generation(tmp_path: Path, monkeypatch):
    """Test that CHA can generate interactive maps with all layers."""
    # Create test data
    _create_test_network_data(tmp_path)
    config_path = _create_test_config(tmp_path)
    
    # Import and run CHA
    import sys
    sys.path.insert(0, str(tmp_path))
    
    try:
        from src.cha import CentralizedHeatingAgent
        
        # Create CHA instance and run network construction
        cha = CentralizedHeatingAgent(config_path)
        cha.load_data()
        cha.build_connected_street_network()
        cha.snap_buildings_to_street_network()
        cha.create_dual_pipe_network()
        cha.create_dual_service_connections()
        cha.calculate_network_statistics()
        
        # Test interactive map creation
        map_obj = cha.create_interactive_map()
        
        # Verify map object was created
        assert map_obj is not None
        
        # Test map saving
        map_file = tmp_path / "test_map.html"
        cha.create_interactive_map(str(map_file))
        
        # Verify map file was created
        assert map_file.exists()
        assert map_file.stat().st_size > 0
        
        # Check map content for required elements
        map_content = map_file.read_text()
        assert "Street Network" in map_content
        assert "Supply Pipes" in map_content
        assert "Return Pipes" in map_content
        assert "Service Pipes" in map_content
        assert "Buildings" in map_content
        assert "CHP Plant" in map_content
        
        print("✅ CHA interactive map generation test passed")
        
    except Exception as e:
        print(f"❌ CHA interactive map generation test failed: {e}")
        raise

def test_cha_output_files(tmp_path: Path, monkeypatch):
    """Test that CHA generates all required output files."""
    # Create test data
    _create_test_network_data(tmp_path)
    config_path = _create_test_config(tmp_path)
    
    # Import and run CHA
    import sys
    sys.path.insert(0, str(tmp_path))
    
    try:
        from src.cha import CentralizedHeatingAgent
        
        # Create CHA instance and run full workflow
        cha = CentralizedHeatingAgent(config_path)
        result = cha.run(config_path)
        
        # Verify successful execution
        assert result["status"] == "ok"
        
        # Check output directory
        output_dir = Path(result["output_dir"])
        assert output_dir.exists()
        
        # Check required CSV files
        required_csv_files = [
            "supply_pipes.csv",
            "return_pipes.csv", 
            "service_connections.csv"
        ]
        
        for csv_file in required_csv_files:
            file_path = output_dir / csv_file
            assert file_path.exists(), f"Missing required CSV file: {csv_file}"
            assert file_path.stat().st_size > 0, f"CSV file is empty: {csv_file}"
        
        # Check JSON files
        stats_file = output_dir / "network_stats.json"
        assert stats_file.exists(), "Missing network_stats.json"
        
        # Check HTML map
        map_file = output_dir / "network_map.html"
        assert map_file.exists(), "Missing network_map.html"
        assert map_file.stat().st_size > 0, "Map file is empty"
        
        # Check GeoPackage
        gpkg_file = output_dir / "cha.gpkg"
        assert gpkg_file.exists(), "Missing cha.gpkg"
        
        print("✅ CHA output files test passed")
        
    except Exception as e:
        print(f"❌ CHA output files test failed: {e}")
        raise

def test_cha_network_statistics(tmp_path: Path, monkeypatch):
    """Test that CHA calculates comprehensive network statistics."""
    # Create test data
    _create_test_network_data(tmp_path)
    config_path = _create_test_config(tmp_path)
    
    # Import and run CHA
    import sys
    sys.path.insert(0, str(tmp_path))
    
    try:
        from src.cha import CentralizedHeatingAgent
        
        # Create CHA instance and run network construction
        cha = CentralizedHeatingAgent(config_path)
        cha.load_data()
        cha.build_connected_street_network()
        cha.snap_buildings_to_street_network()
        cha.create_dual_pipe_network()
        cha.create_dual_service_connections()
        cha.calculate_network_statistics()
        
        # Verify network statistics
        stats = cha.network_stats
        
        # Check required statistics
        required_stats = [
            "total_supply_length_km",
            "total_return_length_km", 
            "total_main_length_km",
            "total_service_length_m",
            "unique_supply_segments",
            "unique_return_segments",
            "num_buildings",
            "service_connections",
            "total_heat_demand_mwh",
            "network_density_km_per_building"
        ]
        
        for stat in required_stats:
            assert stat in stats, f"Missing required statistic: {stat}"
            assert stats[stat] >= 0, f"Statistic {stat} should be non-negative"
        
        # Check boolean flags
        boolean_flags = [
            "complete_dual_pipe_system",
            "street_based_routing",
            "all_connections_follow_streets",
            "no_direct_connections",
            "engineering_compliant"
        ]
        
        for flag in boolean_flags:
            assert flag in stats, f"Missing required flag: {flag}"
            assert isinstance(stats[flag], bool), f"Flag {flag} should be boolean"
            assert stats[flag] is True, f"Flag {flag} should be True"
        
        print("✅ CHA network statistics test passed")
        
    except Exception as e:
        print(f"❌ CHA network statistics test failed: {e}")
        raise
