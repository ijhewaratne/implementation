from pathlib import Path
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString

def _fake_streets(tmp: Path):
    """Create fake street data for testing."""
    (tmp/"data/geojson").mkdir(parents=True, exist_ok=True)
    
    # Create simple street network
    streets_data = [
        {"name": "Test Street 1", "highway": "residential", "geometry": LineString([(0, 0), (100, 0)])},
        {"name": "Test Street 2", "highway": "residential", "geometry": LineString([(100, 0), (100, 100)])},
        {"name": "Test Street 3", "highway": "residential", "geometry": LineString([(100, 100), (0, 100)])},
        {"name": "Test Street 4", "highway": "residential", "geometry": LineString([(0, 100), (0, 0)])},
    ]
    
    streets_gdf = gpd.GeoDataFrame(streets_data, crs="EPSG:32633")
    streets_gdf.to_file(tmp/"data/geojson/strassen_mit_adressenV3.geojson", driver="GeoJSON")

def _fake_buildings(tmp: Path):
    """Create fake building data for testing."""
    (tmp/"data/geojson").mkdir(parents=True, exist_ok=True)
    
    # Create buildings at street corners
    buildings_data = [
        {"id": 1, "strasse": "Test Street 1", "building_type": "residential", "heating_load_kw": 15.0, "annual_heat_demand_kwh": 30000, "building_area_m2": 150, "geometry": Point(50, 50)},
        {"id": 2, "strasse": "Test Street 2", "building_type": "residential", "heating_load_kw": 12.0, "annual_heat_demand_kwh": 25000, "building_area_m2": 120, "geometry": Point(25, 25)},
        {"id": 3, "strasse": "Test Street 3", "building_type": "residential", "heating_load_kw": 18.0, "annual_heat_demand_kwh": 35000, "building_area_m2": 180, "geometry": Point(75, 75)},
    ]
    
    buildings_gdf = gpd.GeoDataFrame(buildings_data, crs="EPSG:32633")
    buildings_gdf.to_file(tmp/"data/geojson/hausumringe_mit_adressenV3.geojson", driver="GeoJSON")

def _fake_config(tmp: Path) -> str:
    """Create fake CHA config for testing."""
    (tmp/"configs").mkdir(parents=True, exist_ok=True)
    
    config = f"""
# Test CHA Configuration
streets_path: {tmp/'data/geojson/strassen_mit_adressenV3.geojson'}
buildings_path: {tmp/'data/geojson/hausumringe_mit_adressenV3.geojson'}

# Plant location
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
"""
    
    (tmp/"configs/cha.yml").write_text(config, encoding="utf-8")
    return str(tmp/"configs/cha.yml")

def test_cha_smoke(tmp_path: Path, monkeypatch):
    """Test that CHA can run without errors."""
    # Create fake data
    _fake_streets(tmp_path)
    _fake_buildings(tmp_path)
    config_path = _fake_config(tmp_path)
    
    # Import and run CHA
    import sys
    sys.path.insert(0, str(tmp_path))
    
    try:
        from src.cha import CentralizedHeatingAgent
        
        # Create CHA instance
        cha = CentralizedHeatingAgent(config_path)
        
        # Test that it can be created
        assert cha is not None
        assert cha.config is not None
        
        # Test that it can load data (should work with fake data)
        result = cha.load_data()
        assert result is True
        
        print("✅ CHA smoke test passed - basic functionality works")
        
    except Exception as e:
        print(f"❌ CHA smoke test failed: {e}")
        raise

def test_cha_network_construction(tmp_path: Path, monkeypatch):
    """Test that CHA can construct the network."""
    # Create fake data
    _fake_streets(tmp_path)
    _fake_buildings(tmp_path)
    config_path = _fake_config(tmp_path)
    
    # Import and run CHA
    import sys
    sys.path.insert(0, str(tmp_path))
    
    try:
        from src.cha import CentralizedHeatingAgent
        
        # Create CHA instance and run full workflow
        cha = CentralizedHeatingAgent(config_path)
        
        # Run the complete workflow
        result = cha.run(config_path)
        
        # Check that it completed successfully
        assert result["status"] == "ok"
        assert "output_dir" in result
        assert "network_stats" in result
        assert "num_buildings" in result
        
        # Check that output files were created
        output_dir = Path(result["output_dir"])
        assert output_dir.exists()
        assert (output_dir / "supply_pipes.csv").exists()
        assert (output_dir / "return_pipes.csv").exists()
        assert (output_dir / "service_connections.csv").exists()
        assert (output_dir / "network_stats.json").exists()
        assert (output_dir / "network_map.html").exists()
        
        print("✅ CHA network construction test passed - full workflow works")
        
    except Exception as e:
        print(f"❌ CHA network construction test failed: {e}")
        raise
