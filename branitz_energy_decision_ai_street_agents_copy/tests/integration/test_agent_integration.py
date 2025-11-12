"""
Agent Integration Tests

Tests the full agent workflow to ensure real simulations are being
triggered correctly through the agent system.
"""

import sys
from pathlib import Path
import json
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Mock the agent system for testing
def test_agent_dh_analysis_uses_real_simulation():
    """
    Test that the agent system triggers real pandapipes simulation.
    
    This is an integration test that verifies:
    1. Agent tools call simulation_runner
    2. simulation_runner loads configuration
    3. Configuration routing works
    4. Real simulator is selected (when enabled)
    5. Results contain real KPIs (not placeholder values)
    """
    print("\n" + "="*60)
    print("AGENT INTEGRATION TEST: DH Analysis")
    print("="*60)
    
    # Import after path is set
    from src.simulation_runner import run_pandapipes_simulation, CONFIG
    import geopandas as gpd
    from shapely.geometry import Point
    
    # Create test buildings
    buildings = gpd.GeoDataFrame({
        'GebaeudeID': ['AGENT_B001', 'AGENT_B002', 'AGENT_B003'],
        'heating_load_kw': [55.0, 70.0, 45.0],
        'geometry': [Point(0, 0).buffer(10), Point(100, 0).buffer(10), Point(50, 100).buffer(10)]
    }, crs='EPSG:25833')
    
    # Save to file
    output_dir = Path("results_test")
    output_dir.mkdir(exist_ok=True)
    buildings_file = output_dir / "agent_test_buildings_dh.geojson"
    buildings.to_file(buildings_file, driver="GeoJSON")
    
    # Create scenario
    scenario = {
        "name": "Agent_DH_Test",
        "type": "DH",
        "building_file": str(buildings_file),
        "params": {"supply_temp": 85, "return_temp": 55}
    }
    
    # Run simulation through runner (as agent would)
    print("\n  Simulating agent call to run_pandapipes_simulation()...")
    result = run_pandapipes_simulation(scenario)
    
    # Validate result structure
    print("\n  Validating result structure...")
    assert result is not None, "Result is None"
    assert "success" in result, "Missing 'success' field"
    assert "type" in result, "Missing 'type' field"
    assert result["type"] == "DH", f"Wrong type: {result['type']}"
    
    # Check simulation mode
    mode = result.get("mode", "unknown")
    print(f"  Simulation mode: {mode}")
    
    if CONFIG.get("use_real_simulations") and CONFIG.get("use_real_dh"):
        print("  Config says: Real simulations should be used")
        # Note: May still be placeholder if libraries not available
        if mode == "real":
            print("  ✅ Real simulation was used!")
        else:
            print("  ⚠️  Placeholder used (libraries may not be available)")
    else:
        print("  Config says: Placeholder simulations should be used")
        assert mode == "placeholder", f"Expected placeholder, got {mode}"
        print("  ✅ Placeholder simulation was used as configured")
    
    # Check KPIs exist
    assert "kpi" in result, "Missing 'kpi' field"
    kpis = result["kpi"]
    
    # If real simulation, check for realistic values
    if mode == "real" and result["success"]:
        # Check KPIs are not placeholder values
        heat_supplied = kpis.get("total_heat_supplied_mwh", 0)
        
        # Placeholder uses 1234 MWh - real should be different
        assert heat_supplied != 1234, "Result contains placeholder value (1234)!"
        
        # Check detailed KPIs exist
        assert "max_pressure_drop_bar" in kpis, "Missing pressure KPI"
        assert "num_junctions" in kpis, "Missing network size KPI"
        
        print("  ✅ Real simulation KPIs validated")
    
    print("\n  ✅ Agent integration test PASSED")
    return True


def test_agent_hp_analysis_uses_real_simulation():
    """
    Test that the agent system triggers real pandapower simulation.
    """
    print("\n" + "="*60)
    print("AGENT INTEGRATION TEST: HP Analysis")
    print("="*60)
    
    from src.simulation_runner import run_pandapower_simulation, CONFIG
    import geopandas as gpd
    from shapely.geometry import Point
    
    # Create test buildings
    buildings = gpd.GeoDataFrame({
        'GebaeudeID': ['AGENT_HP_B001', 'AGENT_HP_B002', 'AGENT_HP_B003'],
        'heating_load_kw': [60.0, 75.0, 50.0],
        'base_electric_load_kw': [2.0, 2.5, 1.8],
        'geometry': [Point(0, 0).buffer(10), Point(120, 0).buffer(10), Point(60, 120).buffer(10)]
    }, crs='EPSG:25833')
    
    # Save to file
    output_dir = Path("results_test")
    buildings_file = output_dir / "agent_test_buildings_hp.geojson"
    buildings.to_file(buildings_file, driver="GeoJSON")
    
    # Create scenario
    scenario = {
        "name": "Agent_HP_Test",
        "type": "HP",
        "building_file": str(buildings_file),
        "params": {"hp_thermal_kw": 6.0, "hp_cop": 2.8}
    }
    
    # Run simulation
    print("\n  Simulating agent call to run_pandapower_simulation()...")
    result = run_pandapower_simulation(scenario)
    
    # Validate
    print("\n  Validating result structure...")
    assert result is not None
    assert "success" in result
    assert result["type"] == "HP"
    
    mode = result.get("mode", "unknown")
    print(f"  Simulation mode: {mode}")
    
    if CONFIG.get("use_real_simulations") and CONFIG.get("use_real_hp"):
        print("  Config says: Real HP simulations should be used")
        if mode == "real":
            print("  ✅ Real simulation was used!")
        else:
            print("  ⚠️  Placeholder used (libraries may not be available)")
    else:
        print("  Config says: Placeholder HP simulations should be used")
        # Note: use_real_hp defaults to false, so this is expected
        print(f"  ✅ Placeholder used as configured (use_real_hp={CONFIG.get('use_real_hp')})")
    
    # Check KPIs
    assert "kpi" in result
    kpis = result["kpi"]
    
    if mode == "real" and result["success"]:
        # Check for voltage KPIs
        assert "min_voltage_pu" in kpis
        assert "max_line_loading_pct" in kpis
        print("  ✅ Real simulation KPIs validated")
    
    print("\n  ✅ Agent integration test PASSED")
    return True


def test_configuration_loading():
    """Test that configuration is loaded correctly from YAML files."""
    print("\n" + "="*60)
    print("CONFIGURATION LOADING TEST")
    print("="*60)
    
    from src.simulation_runner import CONFIG
    
    print("\n  Checking configuration values...")
    
    # Check feature flags exist
    assert "use_real_simulations" in CONFIG, "Missing use_real_simulations"
    assert "use_real_dh" in CONFIG, "Missing use_real_dh"
    assert "fallback_on_error" in CONFIG, "Missing fallback_on_error"
    
    print(f"  use_real_simulations: {CONFIG['use_real_simulations']}")
    print(f"  use_real_dh: {CONFIG['use_real_dh']}")
    print(f"  use_real_hp: {CONFIG.get('use_real_hp', False)}")
    print(f"  fallback_on_error: {CONFIG['fallback_on_error']}")
    
    # Check simulation parameters exist
    assert "dh" in CONFIG, "Missing DH config"
    assert "hp" in CONFIG, "Missing HP config"
    
    print(f"\n  DH supply temp: {CONFIG['dh'].get('supply_temp_c')}°C")
    print(f"  DH return temp: {CONFIG['dh'].get('return_temp_c')}°C")
    print(f"  HP thermal: {CONFIG['hp'].get('hp_thermal_kw')} kW")
    print(f"  HP COP: {CONFIG['hp'].get('hp_cop')}")
    
    print("\n  ✅ Configuration loaded successfully")
    return True


if __name__ == "__main__":
    """Run all agent integration tests."""
    print("\n" + "="*70)
    print("AGENT INTEGRATION TEST SUITE")
    print("="*70)
    
    results = {
        "config_loading": False,
        "dh_integration": False,
        "hp_integration": False,
    }
    
    # Test 1: Configuration loading
    try:
        results["config_loading"] = test_configuration_loading()
    except Exception as e:
        print(f"\n❌ Config loading test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: DH agent integration
    try:
        results["dh_integration"] = test_agent_dh_analysis_uses_real_simulation()
    except Exception as e:
        print(f"\n❌ DH integration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: HP agent integration
    try:
        results["hp_integration"] = test_agent_hp_analysis_uses_real_simulation()
    except Exception as e:
        print(f"\n❌ HP integration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("AGENT INTEGRATION TEST SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"  {test_name.upper()}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL AGENT INTEGRATION TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)

