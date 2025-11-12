"""
Comprehensive integration tests for the visualization system.

Tests the complete visualization pipeline from configuration loading
through map generation and dashboard creation.
"""

import pytest
from pathlib import Path
import json
import os
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestVisualizationSystemIntegration:
    """Integration tests for complete visualization system."""
    
    def test_configuration_loading(self):
        """Test that visualization configuration loads correctly."""
        from src.visualization import get_visualization_config
        
        config = get_visualization_config()
        
        # Check configuration loaded
        assert config is not None
        assert config.is_enabled() is True
        
        # Check key settings accessible
        assert config.get('visualization.static.dpi') == 300
        assert config.get('visualization.interactive.zoom_start') == 16
        
        # Check output directories configured
        static_dir = config.get_output_dir('static')
        assert 'static' in static_dir
        
        print("✅ Configuration loading test passed")
    
    def test_color_palette_system(self):
        """Test that color palette system is working."""
        from src.visualization import (
            NETWORK_COLORS,
            get_temperature_color,
            get_voltage_color,
            get_loading_color
        )
        
        # Check color constants defined
        assert 'supply_pipe' in NETWORK_COLORS
        assert 'return_pipe' in NETWORK_COLORS
        assert 'normal' in NETWORK_COLORS
        assert 'warning' in NETWORK_COLORS
        assert 'critical' in NETWORK_COLORS
        
        # Test temperature color function
        hot_color = get_temperature_color(85)  # High temp
        cold_color = get_temperature_color(45)  # Low temp
        assert hot_color != cold_color
        assert isinstance(hot_color, str)
        assert hot_color.startswith('#')
        
        # Test voltage color function
        normal_v = get_voltage_color(1.0)  # Normal
        low_v = get_voltage_color(0.90)  # Critical (below 0.92)
        warning_v = get_voltage_color(0.93)  # Warning (0.92-0.95)
        assert normal_v == NETWORK_COLORS['normal']  # Should be green
        assert low_v == NETWORK_COLORS['critical']  # Should be red
        assert warning_v == NETWORK_COLORS['warning']  # Should be orange
        
        # Test loading color function
        light_load = get_loading_color(50)  # Light load
        overload = get_loading_color(105)  # Overload
        assert light_load == NETWORK_COLORS['normal']
        assert overload == NETWORK_COLORS['critical']
        
        print("✅ Color palette system test passed")
    
    def test_network_map_generator_initialization(self):
        """Test that NetworkMapGenerator can be initialized."""
        from src.visualization import NetworkMapGenerator
        
        map_gen = NetworkMapGenerator()
        
        # Check output directory created
        assert map_gen.output_dir.exists()
        assert 'static' in str(map_gen.output_dir)
        
        # Check methods exist
        assert hasattr(map_gen, 'create_dh_temperature_map')
        assert hasattr(map_gen, 'create_hp_voltage_map')
        assert hasattr(map_gen, 'extract_dh_network_geometries')
        
        print("✅ NetworkMapGenerator initialization test passed")
    
    def test_interactive_map_generator_initialization(self):
        """Test that InteractiveMapGenerator can be initialized."""
        from src.visualization import InteractiveMapGenerator
        
        map_gen = InteractiveMapGenerator()
        
        # Check output directory created
        assert map_gen.output_dir.exists()
        assert 'interactive' in str(map_gen.output_dir)
        
        # Check methods exist
        assert hasattr(map_gen, 'create_dh_interactive_map')
        assert hasattr(map_gen, 'create_hp_interactive_map')
        
        print("✅ InteractiveMapGenerator initialization test passed")
    
    def test_summary_dashboard_initialization(self):
        """Test that SummaryDashboard can be initialized."""
        from src.dashboards import SummaryDashboard
        
        dashboard = SummaryDashboard()
        
        # Check output directory created
        assert dashboard.output_dir.exists()
        assert 'dashboards' in str(dashboard.output_dir)
        
        # Check methods exist
        assert hasattr(dashboard, 'create_dh_summary')
        assert hasattr(dashboard, 'create_hp_summary')
        
        print("✅ SummaryDashboard initialization test passed")
    
    def test_comparison_dashboard_initialization(self):
        """Test that ComparisonDashboard can be initialized."""
        from src.dashboards import ComparisonDashboard
        
        dashboard = ComparisonDashboard()
        
        # Check output directory created
        assert dashboard.output_dir.exists()
        assert 'dashboards' in str(dashboard.output_dir)
        
        # Check methods exist
        assert hasattr(dashboard, 'create_comparison')
        
        print("✅ ComparisonDashboard initialization test passed")
    
    def test_agent_tool_integration(self):
        """Test that visualization tools are accessible to agents."""
        from agents import (
            CentralHeatingAgent,
            DecentralizedHeatingAgent,
            ComparisonAgent
        )
        
        # Check CentralHeatingAgent has visualization tools
        cha_tools = [t.func.__name__ if hasattr(t, 'func') else str(t) 
                     for t in CentralHeatingAgent.config.tools]
        assert len(cha_tools) >= 3
        print(f"  CentralHeatingAgent has {len(cha_tools)} tools")
        
        # Check DecentralizedHeatingAgent has visualization tools
        dha_tools = [t.func.__name__ if hasattr(t, 'func') else str(t) 
                     for t in DecentralizedHeatingAgent.config.tools]
        assert len(dha_tools) >= 3
        print(f"  DecentralizedHeatingAgent has {len(dha_tools)} tools")
        
        # Check ComparisonAgent has comparison dashboard
        ca_tools = [t.func.__name__ if hasattr(t, 'func') else str(t) 
                    for t in ComparisonAgent.config.tools]
        assert len(ca_tools) >= 2
        print(f"  ComparisonAgent has {len(ca_tools)} tools")
        
        print("✅ Agent tool integration test passed")
    
    def test_energy_tools_visualization_functions(self):
        """Test that energy_tools has visualization functions."""
        from energy_tools import (
            create_interactive_map,
            create_summary_dashboard,
            create_comparison_dashboard
        )
        
        # Tools are Tool objects, check if they have func attribute
        assert hasattr(create_interactive_map, 'func')
        assert hasattr(create_summary_dashboard, 'func')
        assert hasattr(create_comparison_dashboard, 'func')
        
        # Check the underlying functions are callable
        assert callable(create_interactive_map.func)
        assert callable(create_summary_dashboard.func)
        assert callable(create_comparison_dashboard.func)
        
        # Check tools have correct signatures
        import inspect
        
        # create_interactive_map should have scenario_name parameter
        sig1 = inspect.signature(create_interactive_map.func)
        assert 'scenario_name' in sig1.parameters
        
        # create_summary_dashboard should have scenario_name parameter  
        sig2 = inspect.signature(create_summary_dashboard.func)
        assert 'scenario_name' in sig2.parameters
        
        # create_comparison_dashboard should have dh_scenario and hp_scenario
        sig3 = inspect.signature(create_comparison_dashboard.func)
        assert 'dh_scenario' in sig3.parameters
        assert 'hp_scenario' in sig3.parameters
        
        print("✅ Energy tools visualization functions test passed")
    
    def test_output_directory_structure(self):
        """Test that output directory structure is created correctly."""
        from src.visualization import get_visualization_config
        
        config = get_visualization_config()
        
        # Check directories exist
        static_dir = Path(config.get_output_dir('static'))
        interactive_dir = Path(config.get_output_dir('interactive'))
        dashboard_dir = Path(config.get_output_dir('dashboard'))
        
        assert static_dir.exists()
        assert interactive_dir.exists()
        assert dashboard_dir.exists()
        
        print("✅ Output directory structure test passed")
    
    def test_feature_flags_integration(self):
        """Test that feature flags are loaded and accessible."""
        import yaml
        
        flags_path = Path("config/feature_flags.yaml")
        assert flags_path.exists()
        
        with open(flags_path, 'r') as f:
            flags = yaml.safe_load(f)
        
        # Check visualization flags exist
        features = flags.get('features', {})
        assert 'enable_visualizations' in features
        assert 'auto_generate_visualizations' in features
        assert 'enable_interactive_maps' in features
        assert 'enable_dashboards' in features
        
        print("✅ Feature flags integration test passed")

    def test_interactive_map_requires_dual_topology(self):
        """Interactive map tool should prompt for routing data when missing."""
        from energy_tools import optimize_network_routing, create_interactive_map

        scenario_name = "Demo_Parkstrasse_DH"
        routing_dir = Path("results_test/routing") / scenario_name
        routing_dir.mkdir(parents=True, exist_ok=True)

        # Ensure routing artefacts exist, then temporarily remove dual topology
        optimize_network_routing.func(scenario_name)
        dual_topology_path = routing_dir / "dual_topology.json"
        backup_path = routing_dir / "dual_topology.json.bak"

        if dual_topology_path.exists():
            dual_topology_path.replace(backup_path)
        try:
            message = create_interactive_map.func(scenario_name)
            assert "dual-pipe routing data not found" in message.lower()
        finally:
            if backup_path.exists():
                backup_path.replace(dual_topology_path)
            else:
                # Regenerate artefacts if backup missing
                optimize_network_routing.func(scenario_name)

    def test_dual_pipe_interactive_map_generation(self):
        """Interactive map should render dual-pipe overlays when data exists."""
        from energy_tools import optimize_network_routing, create_interactive_map

        scenario_name = "Demo_Parkstrasse_DH"
        optimize_network_routing.func(scenario_name)
        message = create_interactive_map.func(scenario_name)

        assert "dual-pipe" in message.lower()

        html_file = Path("results_test/visualizations/interactive") / f"{scenario_name}_dh_interactive.html"
        assert html_file.exists(), "Interactive DH map HTML not generated"

        content = html_file.read_text(encoding="utf-8")
        assert "Dual-Pipe Routing Summary" in content
        assert "Thermal & Hydraulic Profile" in content


def run_all_tests():
    """Run all integration tests."""
    print("=" * 70)
    print("RUNNING VISUALIZATION SYSTEM INTEGRATION TESTS")
    print("=" * 70)
    print()
    
    test_suite = TestVisualizationSystemIntegration()
    
    tests = [
        ("Configuration Loading", test_suite.test_configuration_loading),
        ("Color Palette System", test_suite.test_color_palette_system),
        ("NetworkMapGenerator Init", test_suite.test_network_map_generator_initialization),
        ("InteractiveMapGenerator Init", test_suite.test_interactive_map_generator_initialization),
        ("SummaryDashboard Init", test_suite.test_summary_dashboard_initialization),
        ("ComparisonDashboard Init", test_suite.test_comparison_dashboard_initialization),
        ("Agent Tool Integration", test_suite.test_agent_tool_integration),
        ("Energy Tools Functions", test_suite.test_energy_tools_visualization_functions),
        ("Output Directory Structure", test_suite.test_output_directory_structure),
        ("Feature Flags Integration", test_suite.test_feature_flags_integration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 70}")
        print(f"TEST: {test_name}")
        print(f"{'=' * 70}")
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"  Tests Run:    {passed + failed}")
    print(f"  Passed:       {passed} ✅")
    print(f"  Failed:       {failed} ❌")
    print(f"  Success Rate: {passed/(passed+failed)*100:.1f}%")
    print()
    
    if failed == 0:
        print("🎊 ALL TESTS PASSED! 🎊")
        print("\nVisualization system is fully integrated and working!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print(f"\n{failed} test(s) need attention.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

