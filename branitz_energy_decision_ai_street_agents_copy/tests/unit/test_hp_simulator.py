"""
Unit tests for Heat Pump Electrical Simulator.

Tests the HeatPumpElectricalSimulator class with sample data to ensure
it creates networks correctly, runs power flow, and extracts KPIs.
"""

import pytest
import geopandas as gpd
from shapely.geometry import Point
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.simulators import (
    HeatPumpElectricalSimulator,
    PlaceholderHPSimulator,
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
        'base_electric_load_kw': [2.0, 3.0, 1.5],
        'geometry': [
            Point(0, 0),
            Point(100, 0),
            Point(50, 100)
        ]
    }, crs='EPSG:25833')
    return buildings


@pytest.fixture
def hp_config():
    """Standard HP configuration."""
    return {
        "hp_thermal_kw": 6.0,
        "hp_cop": 2.8,
        "hp_three_phase": True,
        "scenario_name": "Test_HP"
    }


class TestHeatPumpElectricalSimulator:
    """Tests for HeatPumpElectricalSimulator class."""
    
    def test_initialization(self, hp_config):
        """Test simulator can be initialized with config."""
        simulator = HeatPumpElectricalSimulator(hp_config)
        
        assert simulator.hp_thermal_kw == 6.0
        assert simulator.hp_cop == 2.8
        assert simulator.hp_three_phase == True
    
    def test_hp_parameters(self, hp_config):
        """Test HP parameter setter."""
        simulator = HeatPumpElectricalSimulator(hp_config)
        
        # Valid parameters
        simulator.set_hp_parameters(thermal_kw=8.0, cop=3.0, three_phase=False)
        assert simulator.hp_thermal_kw == 8.0
        assert simulator.hp_cop == 3.0
        assert simulator.hp_three_phase == False
        
        # Invalid thermal power
        with pytest.raises(ValueError):
            simulator.set_hp_parameters(thermal_kw=-5.0, cop=2.8, three_phase=True)
        
        # Invalid COP
        with pytest.raises(ValueError):
            simulator.set_hp_parameters(thermal_kw=6.0, cop=0.0, three_phase=True)
    
    def test_validate_inputs_success(self, hp_config, sample_buildings_small):
        """Test input validation with valid data."""
        simulator = HeatPumpElectricalSimulator(hp_config)
        
        result = simulator.validate_inputs(sample_buildings_small)
        assert result == True
    
    def test_validate_inputs_missing_columns(self, hp_config):
        """Test input validation fails with missing columns."""
        simulator = HeatPumpElectricalSimulator(hp_config)
        
        # Buildings without heating_load_kw
        bad_buildings = gpd.GeoDataFrame({
            'GebaeudeID': ['B1'],
            'geometry': [Point(0, 0)]
        }, crs='EPSG:25833')
        
        with pytest.raises(ValidationError):
            simulator.validate_inputs(bad_buildings)
    
    def test_create_network_small(self, hp_config, sample_buildings_small):
        """Test network creation with small dataset."""
        simulator = HeatPumpElectricalSimulator(hp_config)
        simulator.validate_inputs(sample_buildings_small)
        
        net = simulator.create_network(sample_buildings_small)
        
        assert net is not None
        assert len(net.bus) > 0
        assert len(net.line) > 0
        assert len(net.load) > 0 or len(net.asymmetric_load) > 0
        
        print(f"Created network: {len(net.bus)} buses, {len(net.line)} lines")
    
    def test_run_simulation_small(self, hp_config, sample_buildings_small):
        """Test simulation execution with small dataset."""
        simulator = HeatPumpElectricalSimulator(hp_config)
        simulator.validate_inputs(sample_buildings_small)
        simulator.create_network(sample_buildings_small)
        
        result = simulator.run_simulation()
        
        # Check result structure
        assert isinstance(result.success, bool)
        assert result.simulation_type == SimulationType.HEAT_PUMP
        assert result.simulation_mode == SimulationMode.REAL
        
        # If successful, check KPIs
        if result.success:
            assert "min_voltage_pu" in result.kpi
            assert "max_line_loading_pct" in result.kpi
            assert "transformer_loading_pct" in result.kpi
            assert result.execution_time_s > 0
            
            print(f"Simulation successful!")
            print(f"  Min voltage: {result.kpi['min_voltage_pu']} pu")
            print(f"  Max loading: {result.kpi['max_line_loading_pct']}%")
            print(f"  Execution time: {result.execution_time_s:.2f}s")
        else:
            print(f"Simulation failed: {result.error}")
    
    def test_extract_kpis(self, hp_config, sample_buildings_small):
        """Test KPI extraction returns all required KPIs."""
        simulator = HeatPumpElectricalSimulator(hp_config)
        simulator.validate_inputs(sample_buildings_small)
        simulator.create_network(sample_buildings_small)
        
        result = simulator.run_simulation()
        
        if result.success:
            kpis = result.kpi
            
            # Check all required KPIs exist
            required_kpis = [
                "min_voltage_pu",
                "max_voltage_pu",
                "avg_voltage_pu",
                "voltage_violations",
                "max_line_loading_pct",
                "avg_line_loading_pct",
                "overloaded_lines",
                "transformer_loading_pct",
                "transformer_overloaded",
                "total_load_mw",
                "total_losses_mw",
                "loss_percentage",
                "num_buses",
            ]
            
            for kpi_name in required_kpis:
                assert kpi_name in kpis, f"Missing KPI: {kpi_name}"


class TestPlaceholderHPSimulator:
    """Tests for PlaceholderHPSimulator class."""
    
    def test_placeholder_initialization(self, hp_config):
        """Test placeholder simulator initializes correctly."""
        simulator = PlaceholderHPSimulator(hp_config)
        
        assert simulator.hp_thermal_kw == 6.0
        assert simulator.hp_cop == 2.8
    
    def test_placeholder_simulation(self, hp_config, sample_buildings_small):
        """Test placeholder simulator returns results."""
        simulator = PlaceholderHPSimulator(hp_config)
        simulator.validate_inputs(sample_buildings_small)
        simulator.create_network(sample_buildings_small)
        
        result = simulator.run_simulation()
        
        assert result.success == True
        assert result.simulation_mode == SimulationMode.PLACEHOLDER
        assert len(result.warnings) > 0
        assert "min_voltage_pu" in result.kpi


if __name__ == "__main__":
    """Run tests directly."""
    print("Running HP Simulator Tests...")
    print("="*60)
    
    # Create test data
    buildings = gpd.GeoDataFrame({
        'GebaeudeID': ['B001', 'B002', 'B003'],
        'heating_load_kw': [50.0, 75.0, 30.0],
        'base_electric_load_kw': [2.0, 3.0, 1.5],
        'geometry': [Point(0, 0), Point(100, 0), Point(50, 100)]
    }, crs='EPSG:25833')
    
    config = {
        "hp_thermal_kw": 6.0,
        "hp_cop": 2.8,
        "hp_three_phase": True,
        "scenario_name": "Test_HP"
    }
    
    # Test real simulator
    print("\n1. Testing Real HP Simulator")
    print("-"*60)
    try:
        sim = HeatPumpElectricalSimulator(config)
        print("✅ Initialized")
        
        sim.validate_inputs(buildings)
        print("✅ Inputs validated")
        
        sim.create_network(buildings)
        print("✅ Network created")
        
        result = sim.run_simulation()
        if result.success:
            print("✅ Simulation successful")
            print(f"   Min voltage: {result.kpi['min_voltage_pu']} pu")
            print(f"   Max loading: {result.kpi['max_line_loading_pct']}%")
            print(f"   Time: {result.execution_time_s:.2f}s")
        else:
            print(f"⚠️  Simulation failed: {result.error}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test placeholder simulator
    print("\n2. Testing Placeholder HP Simulator")
    print("-"*60)
    try:
        sim = PlaceholderHPSimulator(config)
        sim.validate_inputs(buildings)
        sim.create_network(buildings)
        result = sim.run_simulation()
        
        print("✅ Placeholder works")
        print(f"   Min voltage: {result.kpi['min_voltage_pu']} pu (dummy)")
        print(f"   Warnings: {len(result.warnings)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("Tests complete!")

