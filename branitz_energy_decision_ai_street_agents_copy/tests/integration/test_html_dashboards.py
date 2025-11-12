"""
Integration tests for HTML dashboard generation.

Tests the complete HTML dashboard system including:
- HTMLDashboardGenerator class
- DH HTML dashboard generation
- HP HTML dashboard generation
- Map embedding
- Chart embedding
- Agent tool access
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_html_dashboard_generator_init():
    """Test HTMLDashboardGenerator initialization."""
    print("\n" + "="*70)
    print("TEST: HTMLDashboardGenerator Initialization")
    print("="*70)
    
    from src.dashboards import HTMLDashboardGenerator
    
    generator = HTMLDashboardGenerator()
    
    assert generator is not None
    assert generator.output_dir == Path("results_test/visualizations/html_dashboards")
    assert isinstance(generator.colors, dict)
    assert 'primary' in generator.colors
    assert 'success' in generator.colors
    
    print("✅ HTMLDashboardGenerator initialization test passed")


def test_create_dh_html_dashboard():
    """Test DH HTML dashboard generation with sample data."""
    print("\n" + "="*70)
    print("TEST: DH HTML Dashboard Generation")
    print("="*70)
    
    from src.dashboards import HTMLDashboardGenerator
    
    # Sample DH KPI data
    sample_kpi = {
        'total_heat_supplied_mwh': 234.5,
        'peak_heat_load_kw': 1234.5,
        'max_pressure_drop_bar': 0.42,
        'avg_pressure_drop_bar': 0.28,
        'pump_energy_kwh': 4823,
        'min_supply_temp_c': 82.3,
        'avg_supply_temp_c': 83.5,
        'network_heat_loss_kwh': 23450,
        'heat_loss_percentage': 10.0,
        'num_junctions': 32,
        'num_pipes': 30,
        'num_consumers': 15,
        'total_pipe_length_km': 1.2,
        'lcoh_eur_per_mwh': 95.5,
        'co2_t_per_a': 45.6
    }
    
    metadata = {
        'street_name': 'Test_Street_DH',
        'buildings': 15
    }
    
    generator = HTMLDashboardGenerator()
    html_file = generator.create_dh_html_dashboard(
        sample_kpi, 
        "Test_DH_Dashboard", 
        metadata
    )
    
    assert os.path.exists(html_file)
    assert html_file.endswith('.html')
    
    # Read HTML content and verify
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for key elements
    assert '<!DOCTYPE html>' in content
    assert 'District Heating Network Dashboard' in content
    assert 'Test_Street_DH' in content
    assert 'metric-card' in content
    assert 'status-success' in content
    assert '234.5' in content  # Check for data value
    
    # Check for CSS
    assert '<style>' in content
    assert 'container' in content
    assert 'metric-grid' in content
    
    # Check for JavaScript
    assert '<script>' in content
    
    print(f"✅ DH HTML dashboard created: {html_file}")
    print(f"   File size: {os.path.getsize(html_file) / 1024:.2f} KB")
    print("✅ DH HTML dashboard generation test passed")


def test_create_hp_html_dashboard():
    """Test HP HTML dashboard generation with sample data."""
    print("\n" + "="*70)
    print("TEST: HP HTML Dashboard Generation")
    print("="*70)
    
    from src.dashboards import HTMLDashboardGenerator
    
    # Sample HP KPI data
    sample_kpi = {
        'total_load_mw': 0.125,
        'num_lines': 15,
        'num_loads': 15,
        'num_buses': 18,
        'loss_percentage': 3.2,
        'total_losses_mw': 0.004,
        'min_voltage_pu': 0.965,
        'max_voltage_pu': 1.018,
        'avg_voltage_pu': 0.992,
        'voltage_violations': 0,
        'max_line_loading_pct': 75.3,
        'avg_line_loading_pct': 45.2,
        'overloaded_lines': 0,
        'transformer_loading_pct': 68.5,
        'lcoh_eur_per_mwh': 110.2,
        'co2_t_per_a': 52.3
    }
    
    metadata = {
        'street_name': 'Test_Street_HP',
        'buildings': 15
    }
    
    generator = HTMLDashboardGenerator()
    html_file = generator.create_hp_html_dashboard(
        sample_kpi,
        "Test_HP_Dashboard",
        metadata
    )
    
    assert os.path.exists(html_file)
    assert html_file.endswith('.html')
    
    # Read HTML content and verify
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for key elements
    assert '<!DOCTYPE html>' in content
    assert 'Heat Pump Electrical Network Dashboard' in content
    assert 'Test_Street_HP' in content
    assert 'metric-card' in content
    assert '125.0' in content  # Check for data value (125 kW)
    
    # Check for voltage-specific content
    assert 'Voltage Profile' in content
    assert '0.965' in content  # Min voltage
    
    # Check for status colors
    assert 'status-success' in content
    
    print(f"✅ HP HTML dashboard created: {html_file}")
    print(f"   File size: {os.path.getsize(html_file) / 1024:.2f} KB")
    print("✅ HP HTML dashboard generation test passed")


def test_html_dashboard_with_map_embedding():
    """Test HTML dashboard generation with map embedding."""
    print("\n" + "="*70)
    print("TEST: HTML Dashboard with Map Embedding")
    print("="*70)
    
    from src.dashboards import HTMLDashboardGenerator
    
    sample_kpi = {
        'total_heat_supplied_mwh': 200.0,
        'peak_heat_load_kw': 1000.0,
        'num_junctions': 20,
        'num_pipes': 18,
        'num_consumers': 10,
        'total_pipe_length_km': 0.8
    }
    
    # Create a dummy map file for testing
    dummy_map_path = Path("results_test/visualizations/interactive/test_map.html")
    dummy_map_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dummy_map_path, 'w') as f:
        f.write("<html><body>Test Map</body></html>")
    
    generator = HTMLDashboardGenerator()
    html_file = generator.create_dh_html_dashboard(
        sample_kpi,
        "Test_DH_With_Map",
        {'street_name': 'Test_Street'},
        map_file=str(dummy_map_path)
    )
    
    assert os.path.exists(html_file)
    
    # Read HTML content and verify map embedding
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert '<iframe' in content
    assert 'map-container' in content
    
    # Clean up
    dummy_map_path.unlink()
    
    print("✅ Map embedding test passed")


def test_html_dashboard_chart_embedding():
    """Test HTML dashboard with chart embedding (base64)."""
    print("\n" + "="*70)
    print("TEST: HTML Dashboard with Chart Embedding")
    print("="*70)
    
    from src.dashboards import HTMLDashboardGenerator
    import matplotlib.pyplot as plt
    
    sample_kpi = {
        'total_heat_supplied_mwh': 200.0,
        'peak_heat_load_kw': 1000.0,
        'num_junctions': 20,
        'num_pipes': 18,
        'num_consumers': 10,
        'total_pipe_length_km': 0.8
    }
    
    # Create a dummy chart for testing
    dummy_chart_path = Path("results_test/visualizations/dashboards/test_chart.png")
    dummy_chart_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.set_title("Test Chart")
    fig.savefig(dummy_chart_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    generator = HTMLDashboardGenerator()
    html_file = generator.create_dh_html_dashboard(
        sample_kpi,
        "Test_DH_With_Chart",
        {'street_name': 'Test_Street'},
        chart_files=[str(dummy_chart_path)]
    )
    
    assert os.path.exists(html_file)
    
    # Read HTML content and verify chart embedding
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for base64 encoded image
    assert 'data:image/png;base64,' in content
    assert 'chart-container' in content
    
    # Clean up
    dummy_chart_path.unlink()
    
    print("✅ Chart embedding test passed")


def test_html_dashboard_routing_insights_section():
    """Ensure DH dashboard renders routing insights when metadata provided."""
    print("\n" + "="*70)
    print("TEST: DH HTML Dashboard Routing Insights")
    print("="*70)

    from src.dashboards import HTMLDashboardGenerator

    sample_kpi = {
        'total_heat_supplied_mwh': 150.0,
        'peak_heat_load_kw': 850.0,
        'max_pressure_drop_bar': 0.35,
        'avg_pressure_drop_bar': 0.20,
        'min_supply_temp_c': 78.0,
        'avg_supply_temp_c': 80.5,
        'network_heat_loss_kwh': 18000,
        'heat_loss_percentage': 8.5,
        'num_junctions': 18,
        'num_pipes': 16,
        'num_consumers': 9,
        'total_pipe_length_km': 0.65,
        'pump_energy_kwh': 2500,
        'lcoh_eur_per_mwh': 92.0,
        'co2_t_per_a': 40.0,
    }

    routing_analysis = {
        "success_rate": 95.0,
        "total_network_length": 1234.0,
        "total_main_pipe_length": 900.0,
    }

    dual_topology = {
        "stats": {
            "total_supply_length_m": 600.0,
            "total_return_length_m": 580.0,
            "success_rate": 95.0,
        },
        "consumers": [{"id": "B1", "junction_id": 1}],
    }

    thermal_profile = [
        {"building_id": "B1", "temperature_c": 72.0, "pressure_bar": 5.8},
        {"building_id": "B2", "temperature_c": 70.5, "pressure_bar": 5.6},
    ]

    generator = HTMLDashboardGenerator()
    html_file = generator.create_dh_html_dashboard(
        sample_kpi,
        "Test_DH_Routing",
        {'street_name': 'Routing_Test_Street'},
        routing_analysis=routing_analysis,
        dual_topology=dual_topology,
        thermal_profile=thermal_profile,
    )

    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'Routing Insights' in content
    assert 'Thermal & Hydraulic Profile' in content
    assert '95.0%' in content
    assert '0.6' in content or '0.60' in content  # supply length in km formatted

    print("✅ Routing insights section rendered in DH HTML dashboard")


def test_create_html_dashboard_tool_with_routing_data():
    """End-to-end tool should include routing insights in generated dashboard."""
    print("\n" + "="*70)
    print("TEST: create_html_dashboard Tool with Routing Data")
    print("="*70)

    from energy_tools import optimize_network_routing, create_html_dashboard

    scenario_name = "Demo_Parkstrasse_DH"
    optimize_network_routing.func(scenario_name)
    message = create_html_dashboard.func(scenario_name, dashboard_type="dh")

    assert "html dashboard created" in message.lower()

    html_path = None
    for line in message.splitlines():
        if line.strip().startswith("File:"):
            html_path = Path(line.split("File:", 1)[1].strip())
            break

    if html_path is None:
        html_path = Path("results_test/visualizations/html_dashboards") / f"{scenario_name}_dh_html_dashboard.html"

    assert html_path.exists(), "HTML dashboard file not generated"

    content = html_path.read_text(encoding="utf-8")
    assert "Routing Insights" in content
    assert "Thermal & Hydraulic Profile" in content
    assert "Dual-Pipe" in content or "dual-pipe" in content.lower()

    print("✅ create_html_dashboard tool generated routing-aware dashboard")


def test_html_dashboard_agent_tool_access():
    """Test that the create_html_dashboard tool is accessible to agents."""
    print("\n" + "="*70)
    print("TEST: HTML Dashboard Agent Tool Access")
    print("="*70)
    
    from agents import CentralHeatingAgent, DecentralizedHeatingAgent
    from energy_tools import create_html_dashboard
    
    # Check CentralHeatingAgent has the tool
    cha_tools = CentralHeatingAgent.config.tools
    cha_has_tool = any(
        (hasattr(tool, 'func') and tool.func.__name__ == 'create_html_dashboard') or
        (hasattr(tool, '__name__') and tool.__name__ == 'create_html_dashboard')
        for tool in cha_tools
    )
    assert cha_has_tool, "CentralHeatingAgent missing create_html_dashboard tool"
    
    # Check DecentralizedHeatingAgent has the tool
    dha_tools = DecentralizedHeatingAgent.config.tools
    dha_has_tool = any(
        (hasattr(tool, 'func') and tool.func.__name__ == 'create_html_dashboard') or
        (hasattr(tool, '__name__') and tool.__name__ == 'create_html_dashboard')
        for tool in dha_tools
    )
    assert dha_has_tool, "DecentralizedHeatingAgent missing create_html_dashboard tool"
    
    # Verify tool function exists (it's wrapped by @tool decorator)
    assert hasattr(create_html_dashboard, 'func') or callable(create_html_dashboard)
    
    print("✅ CentralHeatingAgent has create_html_dashboard tool")
    print("✅ DecentralizedHeatingAgent has create_html_dashboard tool")
    print("✅ create_html_dashboard tool is accessible")
    print("✅ HTML dashboard agent tool access test passed")


def test_html_dashboard_configuration():
    """Test HTML dashboard configuration loading."""
    print("\n" + "="*70)
    print("TEST: HTML Dashboard Configuration")
    print("="*70)
    
    import yaml
    
    # Load feature flags
    with open('config/feature_flags.yaml', 'r') as f:
        feature_flags = yaml.safe_load(f)
    
    assert 'features' in feature_flags
    assert 'enable_html_dashboards' in feature_flags['features']
    assert feature_flags['features']['enable_html_dashboards'] == True
    
    # Load visualization config
    with open('config/visualization_config.yaml', 'r') as f:
        viz_config = yaml.safe_load(f)
    
    assert 'visualization' in viz_config
    assert 'html_dashboard' in viz_config['visualization']
    
    html_config = viz_config['visualization']['html_dashboard']
    assert html_config['enabled'] == True
    assert 'output_dir' in html_config
    assert 'primary_color' in html_config
    assert 'embed_maps' in html_config
    
    print("✅ Feature flags configuration verified")
    print("✅ Visualization configuration verified")
    print("✅ HTML dashboard configuration test passed")


def run_all_tests():
    """Run all HTML dashboard integration tests."""
    print("\n" + "="*70)
    print("RUNNING HTML DASHBOARD INTEGRATION TESTS")
    print("="*70)
    
    tests = [
        test_html_dashboard_generator_init,
        test_create_dh_html_dashboard,
        test_create_hp_html_dashboard,
        test_html_dashboard_with_map_embedding,
        test_html_dashboard_chart_embedding,
        test_html_dashboard_agent_tool_access,
        test_html_dashboard_configuration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    print(f"  Tests Run:    {passed + failed}")
    print(f"  Passed:       {passed} ✅")
    print(f"  Failed:       {failed} ❌")
    print(f"  Success Rate: {passed/(passed+failed)*100:.1f}%")
    print()
    
    if failed == 0:
        print("🎊 ALL TESTS PASSED! 🎊")
        print()
        print("HTML dashboard system is fully integrated and working!")
    else:
        print(f"⚠️ {failed} test(s) failed. Please review.")
    
    print("="*70)
    
    return passed, failed


if __name__ == "__main__":
    run_all_tests()

