"""
Integration tests for full agent workflow with real simulations.

Tests the complete end-to-end flow:
User query → Agent → Tools → Pipeline → Real Simulations → Results
"""

import sys
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point, Polygon
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.simulation_runner import run_pandapipes_simulation, run_pandapower_simulation


def create_test_scenario_dh(output_dir="results_test"):
    """
    Create a complete test scenario for DH simulation.
    
    Returns path to created scenario file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Create test buildings
    buildings = gpd.GeoDataFrame({
        'GebaeudeID': ['TEST_B001', 'TEST_B002', 'TEST_B003', 'TEST_B004', 'TEST_B005'],
        'heating_load_kw': [45.0, 60.0, 35.0, 80.0, 50.0],
        'geometry': [
            Point(0, 0).buffer(10),
            Point(100, 0).buffer(10),
            Point(50, 100).buffer(10),
            Point(150, 50).buffer(10),
            Point(75, 75).buffer(10),
        ]
    }, crs='EPSG:25833')
    
    # Save buildings
    buildings_file = output_dir / "test_buildings_dh.geojson"
    buildings.to_file(buildings_file, driver="GeoJSON")
    
    # Create scenario config
    scenario = {
        "name": "Test_DH_Integration",
        "type": "DH",
        "building_file": str(buildings_file),
        "params": {
            "supply_temp": 85,
            "return_temp": 55
        }
    }
    
    scenario_file = output_dir / "test_scenario_dh.json"
    with open(scenario_file, 'w') as f:
        json.dump(scenario, f, indent=2)
    
    print(f"Created test scenario: {scenario_file}")
    print(f"  Buildings: {len(buildings)}")
    print(f"  Total demand: {buildings['heating_load_kw'].sum()} kW")
    
    return scenario_file


def create_test_scenario_hp(output_dir="results_test"):
    """
    Create a complete test scenario for HP simulation.
    
    Returns path to created scenario file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Create test buildings
    buildings = gpd.GeoDataFrame({
        'GebaeudeID': ['TEST_B101', 'TEST_B102', 'TEST_B103', 'TEST_B104'],
        'heating_load_kw': [50.0, 65.0, 40.0, 75.0],
        'base_electric_load_kw': [2.0, 2.5, 1.8, 3.0],
        'geometry': [
            Point(0, 0).buffer(10),
            Point(120, 0).buffer(10),
            Point(60, 120).buffer(10),
            Point(120, 120).buffer(10),
        ]
    }, crs='EPSG:25833')
    
    # Save buildings
    buildings_file = output_dir / "test_buildings_hp.geojson"
    buildings.to_file(buildings_file, driver="GeoJSON")
    
    # Create scenario config
    scenario = {
        "name": "Test_HP_Integration",
        "type": "HP",
        "building_file": str(buildings_file),
        "params": {
            "hp_thermal_kw": 6.0,
            "hp_cop": 2.8,
            "hp_three_phase": True
        }
    }
    
    scenario_file = output_dir / "test_scenario_hp.json"
    with open(scenario_file, 'w') as f:
        json.dump(scenario, f, indent=2)
    
    print(f"Created test scenario: {scenario_file}")
    print(f"  Buildings: {len(buildings)}")
    print(f"  Total demand: {buildings['heating_load_kw'].sum()} kW")
    
    return scenario_file


def test_dh_integration():
    """Test full DH simulation workflow."""
    print("\n" + "="*60)
    print("INTEGRATION TEST: District Heating")
    print("="*60)
    
    # Create test scenario
    scenario_file = create_test_scenario_dh()
    
    # Load scenario
    with open(scenario_file, 'r') as f:
        scenario = json.load(f)
    
    # Run simulation
    print("\nRunning simulation...")
    result = run_pandapipes_simulation(scenario)
    
    # Validate results
    print("\nValidating results...")
    assert result is not None, "Result is None"
    assert "success" in result, "Missing 'success' field"
    assert "kpi" in result, "Missing 'kpi' field"
    
    if result["success"]:
        print("✅ Simulation successful")
        print(f"  Mode: {result.get('mode', 'unknown')}")
        
        # Check KPIs
        kpi = result["kpi"]
        print(f"\n📊 KPIs Extracted:")
        print(f"  Total heat: {kpi.get('total_heat_supplied_mwh', 0)} MWh")
        print(f"  Peak load: {kpi.get('peak_heat_load_kw', 0)} kW")
        print(f"  Max pressure drop: {kpi.get('max_pressure_drop_bar', 0)} bar")
        print(f"  Pump energy: {kpi.get('pump_energy_kwh', 0)} kWh")
        print(f"  Network: {kpi.get('num_pipes', 0)} pipes, {kpi.get('num_junctions', 0)} junctions")
        
        # Check warnings
        if "warnings" in result and result["warnings"]:
            print(f"\n⚠️  Warnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")
        
        return True
    else:
        print(f"❌ Simulation failed: {result.get('error', 'Unknown error')}")
        return False


def test_hp_integration():
    """Test full HP simulation workflow."""
    print("\n" + "="*60)
    print("INTEGRATION TEST: Heat Pump")
    print("="*60)
    
    # Create test scenario
    scenario_file = create_test_scenario_hp()
    
    # Load scenario
    with open(scenario_file, 'r') as f:
        scenario = json.load(f)
    
    # Run simulation
    print("\nRunning simulation...")
    result = run_pandapower_simulation(scenario)
    
    # Validate results
    print("\nValidating results...")
    assert result is not None, "Result is None"
    assert "success" in result, "Missing 'success' field"
    assert "kpi" in result, "Missing 'kpi' field"
    
    if result["success"]:
        print("✅ Simulation successful")
        print(f"  Mode: {result.get('mode', 'unknown')}")
        
        # Check KPIs
        kpi = result["kpi"]
        print(f"\n📊 KPIs Extracted:")
        print(f"  Min voltage: {kpi.get('min_voltage_pu', 0)} pu")
        print(f"  Max voltage: {kpi.get('max_voltage_pu', 0)} pu")
        print(f"  Max line loading: {kpi.get('max_line_loading_pct', 0)}%")
        print(f"  Transformer loading: {kpi.get('transformer_loading_pct', 0)}%")
        print(f"  Voltage violations: {kpi.get('voltage_violations', 0)}")
        print(f"  Overloaded lines: {kpi.get('overloaded_lines', 0)}")
        print(f"  Total load: {kpi.get('total_load_mw', 0)} MW")
        print(f"  Losses: {kpi.get('total_losses_mw', 0)} MW ({kpi.get('loss_percentage', 0)}%)")
        print(f"  Network: {kpi.get('num_buses', 0)} buses, {kpi.get('num_lines', 0)} lines")
        
        # Check warnings
        if "warnings" in result and result["warnings"]:
            print(f"\n⚠️  Warnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")
        
        return True
    else:
        print(f"❌ Simulation failed: {result.get('error', 'Unknown error')}")
        return False


def test_comparison_workflow():
    """Test running both DH and HP for comparison."""
    print("\n" + "="*60)
    print("INTEGRATION TEST: Scenario Comparison")
    print("="*60)
    
    # Create scenarios for same buildings
    output_dir = Path("results_test")
    
    # Create shared buildings
    buildings = gpd.GeoDataFrame({
        'GebaeudeID': ['COMP_B001', 'COMP_B002', 'COMP_B003'],
        'heating_load_kw': [55.0, 70.0, 45.0],
        'base_electric_load_kw': [2.0, 2.5, 1.8],
        'geometry': [
            Point(0, 0).buffer(10),
            Point(100, 0).buffer(10),
            Point(50, 100).buffer(10),
        ]
    }, crs='EPSG:25833')
    
    buildings_file = output_dir / "test_buildings_comparison.geojson"
    buildings.to_file(buildings_file, driver="GeoJSON")
    
    # DH scenario
    scenario_dh = {
        "name": "Comparison_DH",
        "type": "DH",
        "building_file": str(buildings_file),
        "params": {"supply_temp": 85, "return_temp": 55}
    }
    
    # HP scenario
    scenario_hp = {
        "name": "Comparison_HP",
        "type": "HP",
        "building_file": str(buildings_file),
        "params": {"hp_thermal_kw": 6.0, "hp_cop": 2.8}
    }
    
    # Run both
    print("\n1. Running DH simulation...")
    dh_result = run_pandapipes_simulation(scenario_dh)
    
    print("\n2. Running HP simulation...")
    hp_result = run_pandapower_simulation(scenario_hp)
    
    # Compare
    print("\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)
    
    if dh_result["success"] and hp_result["success"]:
        print("\n✅ Both simulations successful")
        
        print("\nDH vs HP Comparison:")
        print(f"  DH Mode: {dh_result.get('mode', 'unknown')}")
        print(f"  HP Mode: {hp_result.get('mode', 'unknown')}")
        
        # Could add more detailed comparison here
        return True
    else:
        if not dh_result["success"]:
            print(f"❌ DH failed: {dh_result.get('error')}")
        if not hp_result["success"]:
            print(f"❌ HP failed: {hp_result.get('error')}")
        return False


if __name__ == "__main__":
    """Run all integration tests."""
    print("\n" + "="*70)
    print("FULL INTEGRATION TEST SUITE")
    print("="*70)
    
    results = {
        "dh": False,
        "hp": False,
        "comparison": False
    }
    
    # Test 1: DH Integration
    try:
        results["dh"] = test_dh_integration()
    except Exception as e:
        print(f"\n❌ DH integration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: HP Integration
    try:
        results["hp"] = test_hp_integration()
    except Exception as e:
        print(f"\n❌ HP integration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Comparison
    try:
        results["comparison"] = test_comparison_workflow()
    except Exception as e:
        print(f"\n❌ Comparison test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"  {test_name.upper()}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)

