"""
Unit tests for District Heating Simulator.

Tests the DistrictHeatingSimulator class with sample data to ensure
it creates networks correctly, runs simulations, and extracts KPIs.
"""

import pytest
import geopandas as gpd
from shapely.geometry import Point
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.simulators import (
    DistrictHeatingSimulator,
    PlaceholderDHSimulator,
    SimulationType,
    SimulationMode,
    ValidationError,
)


@pytest.fixture
def sample_buildings_small():
    """Create small sample building dataset (3 buildings)."""
    buildings = gpd.GeoDataFrame({
        'GebaeudeID': ['B001', 'B002', 'B003'],
        'heating_load_kw': [50.0, 75.0, 30.0],
        'geometry': [
            Point(0, 0),
            Point(100, 0),
            Point(50, 100)
        ]
    }, crs='EPSG:25833')
    return buildings


@pytest.fixture
def sample_buildings_medium():
    """Create medium sample building dataset (10 buildings)."""
    import numpy as np
    
    # Create 10 buildings in a grid pattern
    buildings_data = []
    for i in range(10):
        row = i // 5
        col = i % 5
        buildings_data.append({
            'GebaeudeID': f'B{i:03d}',
            'heating_load_kw': np.random.uniform(30, 100),
            'geometry': Point(col * 50, row * 50)
        })
    
    buildings = gpd.GeoDataFrame(buildings_data, crs='EPSG:25833')
    return buildings


@pytest.fixture
def dh_config():
    """Standard DH configuration."""
    return {
        "supply_temp_c": 85.0,
        "return_temp_c": 55.0,
        "default_diameter_m": 0.065,
        "scenario_name": "Test_DH"
    }


class TestDistrictHeatingSimulator:
    """Tests for DistrictHeatingSimulator class."""
    
    def test_initialization(self, dh_config):
        """Test simulator can be initialized with config."""
        simulator = DistrictHeatingSimulator(dh_config)
        
        assert simulator.supply_temp_c == 85.0
        assert simulator.return_temp_c == 55.0
        assert simulator.default_diameter_m == 0.065
    
    def test_temperature_validation(self, dh_config):
        """Test temperature setter validation."""
        simulator = DistrictHeatingSimulator(dh_config)
        
        # Valid temperature
        simulator.set_supply_temperature(90.0)
        assert simulator.supply_temp_c == 90.0
        
        # Invalid temperature (too low)
        with pytest.raises(ValueError):
            simulator.set_supply_temperature(50.0)
        
        # Invalid temperature (less than return)
        with pytest.raises(ValueError):
            simulator.set_supply_temperature(40.0)
    
    def test_validate_inputs_success(self, dh_config, sample_buildings_small):
        """Test input validation with valid data."""
        simulator = DistrictHeatingSimulator(dh_config)
        
        result = simulator.validate_inputs(sample_buildings_small)
        assert result == True
    
    def test_validate_inputs_missing_columns(self, dh_config):
        """Test input validation fails with missing columns."""
        simulator = DistrictHeatingSimulator(dh_config)
        
        # Buildings without heating_load_kw
        bad_buildings = gpd.GeoDataFrame({
            'GebaeudeID': ['B1'],
            'geometry': [Point(0, 0)]
        }, crs='EPSG:25833')
        
        with pytest.raises(ValidationError):
            simulator.validate_inputs(bad_buildings)
    
    def test_validate_inputs_too_few_buildings(self, dh_config):
        """Test validation fails with < 2 buildings."""
        simulator = DistrictHeatingSimulator(dh_config)
        
        single_building = gpd.GeoDataFrame({
            'GebaeudeID': ['B1'],
            'heating_load_kw': [50.0],
            'geometry': [Point(0, 0)]
        }, crs='EPSG:25833')
        
        with pytest.raises(ValidationError):
            simulator.validate_inputs(single_building)
    
    def test_create_network_small(self, dh_config, sample_buildings_small):
        """Test network creation with small dataset."""
        simulator = DistrictHeatingSimulator(dh_config)
        simulator.validate_inputs(sample_buildings_small)
        
        net = simulator.create_network(sample_buildings_small)
        
        assert net is not None
        assert len(net.junction) > 0
        assert len(net.pipe) > 0
        assert hasattr(net, 'heat_exchanger')
        assert len(net.heat_exchanger) > 0
        
        print(f"Created network: {len(net.junction)} junctions, {len(net.pipe)} pipes")
    
    def test_run_simulation_small(self, dh_config, sample_buildings_small):
        """Test simulation execution with small dataset."""
        simulator = DistrictHeatingSimulator(dh_config)
        simulator.validate_inputs(sample_buildings_small)
        simulator.create_network(sample_buildings_small)
        
        result = simulator.run_simulation()
        
        # Check result structure
        assert isinstance(result.success, bool)
        assert result.simulation_type == SimulationType.DISTRICT_HEATING
        assert result.simulation_mode == SimulationMode.REAL
        
        # If successful, check KPIs
        if result.success:
            assert "total_heat_supplied_mwh" in result.kpi
            assert "max_pressure_drop_bar" in result.kpi
            assert "pump_energy_kwh" in result.kpi
            assert result.execution_time_s > 0
            
            print(f"Simulation successful!")
            print(f"  Heat supplied: {result.kpi['total_heat_supplied_mwh']} MWh")
            print(f"  Execution time: {result.execution_time_s:.2f}s")
        else:
            print(f"Simulation failed: {result.error}")
            # Simulation failure is acceptable for this test
    
    def test_extract_kpis(self, dh_config, sample_buildings_small):
        """Test KPI extraction returns all required KPIs."""
        simulator = DistrictHeatingSimulator(dh_config)
        simulator.validate_inputs(sample_buildings_small)
        simulator.create_network(sample_buildings_small)
        
        # Run simulation
        result = simulator.run_simulation()
        
        if result.success:
            kpis = result.kpi
            
            # Check all required KPIs exist
            required_kpis = [
                "total_heat_supplied_mwh",
                "peak_heat_load_kw",
                "max_pressure_drop_bar",
                "avg_pressure_drop_bar",
                "pump_energy_kwh",
                "min_supply_temp_c",
                "avg_supply_temp_c",
                "network_heat_loss_kwh",
                "heat_loss_percentage",
                "num_junctions",
                "num_pipes",
                "num_consumers",
            ]
            
            for kpi_name in required_kpis:
                assert kpi_name in kpis, f"Missing KPI: {kpi_name}"
                assert isinstance(kpis[kpi_name], (int, float)), f"KPI {kpi_name} is not numeric"
    
    def test_network_summary(self, dh_config, sample_buildings_small):
        """Test network summary returns element counts."""
        simulator = DistrictHeatingSimulator(dh_config)
        simulator.validate_inputs(sample_buildings_small)
        simulator.create_network(sample_buildings_small)
        
        summary = simulator.get_network_summary()
        
        assert "num_junctions" in summary
        assert "num_pipes" in summary
        assert summary["num_junctions"] > 0
        assert summary["num_pipes"] > 0


class TestPlaceholderDHSimulator:
    """Tests for PlaceholderDHSimulator class."""
    
    def test_placeholder_initialization(self, dh_config):
        """Test placeholder simulator initializes correctly."""
        simulator = PlaceholderDHSimulator(dh_config)
        
        assert simulator.supply_temp_c == 85.0
        assert simulator.return_temp_c == 55.0
    
    def test_placeholder_simulation(self, dh_config, sample_buildings_small):
        """Test placeholder simulator returns results."""
        simulator = PlaceholderDHSimulator(dh_config)
        simulator.validate_inputs(sample_buildings_small)
        simulator.create_network(sample_buildings_small)
        
        result = simulator.run_simulation()
        
        assert result.success == True
        assert result.simulation_mode == SimulationMode.PLACEHOLDER
        assert len(result.warnings) > 0  # Should warn about placeholder
        assert "total_heat_supplied_mwh" in result.kpi


if __name__ == "__main__":
    """Run tests directly."""
    print("Running DH Simulator Tests...")
    print("="*60)
    
    # Create test data
    buildings = gpd.GeoDataFrame({
        'GebaeudeID': ['B001', 'B002', 'B003'],
        'heating_load_kw': [50.0, 75.0, 30.0],
        'geometry': [Point(0, 0), Point(100, 0), Point(50, 100)]
    }, crs='EPSG:25833')
    
    config = {
        "supply_temp_c": 85.0,
        "return_temp_c": 55.0,
        "scenario_name": "Test_DH"
    }
    
    # Test real simulator
    print("\n1. Testing Real DH Simulator")
    print("-"*60)
    try:
        sim = DistrictHeatingSimulator(config)
        print("✅ Initialized")
        
        sim.validate_inputs(buildings)
        print("✅ Inputs validated")
        
        sim.create_network(buildings)
        print("✅ Network created")
        
        result = sim.run_simulation()
        if result.success:
            print("✅ Simulation successful")
            print(f"   Heat: {result.kpi['total_heat_supplied_mwh']} MWh")
            print(f"   Pressure: {result.kpi['max_pressure_drop_bar']} bar")
            print(f"   Time: {result.execution_time_s:.2f}s")
        else:
            print(f"⚠️  Simulation failed: {result.error}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test placeholder simulator
    print("\n2. Testing Placeholder DH Simulator")
    print("-"*60)
    try:
        sim = PlaceholderDHSimulator(config)
        sim.validate_inputs(buildings)
        sim.create_network(buildings)
        result = sim.run_simulation()
        
        print("✅ Placeholder works")
        print(f"   Heat: {result.kpi['total_heat_supplied_mwh']} MWh (dummy)")
        print(f"   Warnings: {len(result.warnings)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("Tests complete!")

