#!/usr/bin/env python3
"""
Test CHA Graceful Degradation

This test validates the graceful degradation functionality in the CHA system,
including fallback to topology-only mode when hydraulic simulation fails.
"""

import unittest
import tempfile
import shutil
import json
import yaml
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from cha import CentralizedHeatingAgent
except ImportError as e:
    print(f"Warning: Could not import CHA: {e}")
    CentralizedHeatingAgent = None


class TestCHAGracefulDegradation(unittest.TestCase):
    """Test CHA graceful degradation functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_data_dir = Path(cls.temp_dir) / "test_data"
        cls.test_data_dir.mkdir()
        
        # Create test configuration with graceful degradation enabled
        cls.test_config = {
            'streets_path': str(cls.test_data_dir / "streets.geojson"),
            'buildings_path': str(cls.test_data_dir / "buildings.geojson"),
            'plant_lon': 14.3453979,
            'plant_lat': 51.76274,
            'output_dir': str(cls.test_data_dir / "output"),
            'hydraulic_simulation': {
                'enabled': True
            },
            'compatibility': {
                'enable_hydraulic_simulation': True,
                'fallback_to_topology_only': True
            }
        }
        
        # Create test config file
        cls.config_path = cls.test_data_dir / "test_config.yml"
        with open(cls.config_path, 'w') as f:
            yaml.dump(cls.test_config, f)
        
        # Create minimal test data files
        cls._create_test_data_files()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test class."""
        shutil.rmtree(cls.temp_dir)
    
    @classmethod
    def _create_test_data_files(cls):
        """Create minimal test data files."""
        # Create minimal streets GeoJSON
        streets_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "Test Street"},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[14.345, 51.762], [14.346, 51.763]]
                    }
                }
            ]
        }
        
        with open(cls.test_data_dir / "streets.geojson", 'w') as f:
            json.dump(streets_data, f)
        
        # Create minimal buildings GeoJSON
        buildings_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"address": "Test Building"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[14.3451, 51.7621], [14.3452, 51.7621], [14.3452, 51.7622], [14.3451, 51.7622], [14.3451, 51.7621]]]
                    }
                }
            ]
        }
        
        with open(cls.test_data_dir / "buildings.geojson", 'w') as f:
            json.dump(buildings_data, f)
    
    def setUp(self):
        """Set up each test."""
        self.cha = None
        if CentralizedHeatingAgent:
            self.cha = CentralizedHeatingAgent(str(self.__class__.config_path))
    
    def test_graceful_degradation_initialization(self):
        """Test that graceful degradation is properly initialized."""
        if not CentralizedHeatingAgent:
            self.skipTest("CentralizedHeatingAgent not available")
        
        self.assertIsNotNone(self.cha)
        self.assertIsNotNone(self.cha.config)
        
        # Check that compatibility settings are loaded
        compatibility = self.cha.config.get('compatibility', {})
        self.assertIn('enable_hydraulic_simulation', compatibility)
        self.assertIn('fallback_to_topology_only', compatibility)
        
        # Check default values
        self.assertTrue(compatibility.get('enable_hydraulic_simulation', True))
        self.assertTrue(compatibility.get('fallback_to_topology_only', True))
    
    def test_fallback_to_topology_only_enabled(self):
        """Test fallback to topology-only mode when enabled."""
        if not CentralizedHeatingAgent:
            self.skipTest("CentralizedHeatingAgent not available")
        
        # Test fallback method directly
        result = self.cha._fallback_to_topology_only("Test failure reason")
        
        self.assertTrue(result)
        self.assertIsNotNone(self.cha.simulation_results)
        self.assertIsNotNone(self.cha.hydraulic_kpis)
        
        # Check simulation results
        self.assertEqual(self.cha.simulation_results["simulation_mode"], "topology_only")
        self.assertEqual(self.cha.simulation_results["fallback_reason"], "Test failure reason")
        self.assertTrue(self.cha.simulation_results["simulation_success"])
        
        # Check KPIs
        self.assertEqual(self.cha.hydraulic_kpis["simulation_mode"], "topology_only")
        self.assertEqual(self.cha.hydraulic_kpis["fallback_reason"], "Test failure reason")
        self.assertEqual(self.cha.hydraulic_kpis["status"], "fallback")
    
    def test_fallback_to_topology_only_disabled(self):
        """Test fallback behavior when disabled."""
        if not CentralizedHeatingAgent:
            self.skipTest("CentralizedHeatingAgent not available")
        
        # Disable fallback in config
        self.cha.config['compatibility']['fallback_to_topology_only'] = False
        
        # Test fallback method
        result = self.cha._fallback_to_topology_only("Test failure reason")
        
        self.assertFalse(result)
        self.assertIsNone(self.cha.simulation_results)
        self.assertIsNone(self.cha.hydraulic_kpis)
    
    def test_create_fallback_simulation_results(self):
        """Test creation of fallback simulation results."""
        if not CentralizedHeatingAgent:
            self.skipTest("CentralizedHeatingAgent not available")
        
        # Create mock pipe data
        import pandas as pd
        self.cha.supply_pipes = pd.DataFrame({
            'length_km': [0.5, 0.3, 0.2]
        })
        self.cha.return_pipes = pd.DataFrame({
            'length_km': [0.5, 0.3, 0.2]
        })
        
        # Create fallback results
        self.cha._create_fallback_simulation_results("Test reason")
        
        # Check results structure
        self.assertIsNotNone(self.cha.simulation_results)
        self.assertEqual(self.cha.simulation_results["simulation_mode"], "topology_only")
        self.assertEqual(self.cha.simulation_results["fallback_reason"], "Test reason")
        self.assertTrue(self.cha.simulation_results["simulation_success"])
        
        # Check network stats
        network_stats = self.cha.simulation_results["network_stats"]
        self.assertIn("total_pipes", network_stats)
        self.assertIn("total_length_km", network_stats)
        self.assertIn("max_velocity_ms", network_stats)
        self.assertIn("max_pressure_drop_pa_per_m", network_stats)
        
        # Check total length calculation
        self.assertEqual(network_stats["total_length_km"], 2.0)  # 1.0 + 1.0
        
        # Check warnings
        warnings = self.cha.simulation_results["warnings"]
        self.assertIn("Hydraulic simulation failed: Test reason", warnings)
        self.assertIn("Using topology-only mode with estimated values", warnings)
    
    def test_create_fallback_kpis(self):
        """Test creation of fallback KPIs."""
        if not CentralizedHeatingAgent:
            self.skipTest("CentralizedHeatingAgent not available")
        
        # Create fallback KPIs
        self.cha._create_fallback_kpis("Test reason")
        
        # Check KPIs structure
        self.assertIsNotNone(self.cha.hydraulic_kpis)
        self.assertEqual(self.cha.hydraulic_kpis["status"], "fallback")
        self.assertEqual(self.cha.hydraulic_kpis["simulation_mode"], "topology_only")
        self.assertEqual(self.cha.hydraulic_kpis["fallback_reason"], "Test reason")
        
        # Check metrics structure
        self.assertIn("hydraulic_metrics", self.cha.hydraulic_kpis)
        self.assertIn("thermal_metrics", self.cha.hydraulic_kpis)
        self.assertIn("economic_metrics", self.cha.hydraulic_kpis)
        self.assertIn("compliance", self.cha.hydraulic_kpis)
        
        # Check hydraulic metrics
        hydraulic = self.cha.hydraulic_kpis["hydraulic_metrics"]
        self.assertEqual(hydraulic["max_velocity_ms"], 0.0)
        self.assertEqual(hydraulic["max_pressure_drop_pa_per_m"], 0.0)
        self.assertEqual(hydraulic["total_flow_kg_s"], 0.0)
        self.assertEqual(hydraulic["pump_power_kw"], 0.0)
        self.assertEqual(hydraulic["network_efficiency"], 0.0)
        
        # Check thermal metrics
        thermal = self.cha.hydraulic_kpis["thermal_metrics"]
        self.assertEqual(thermal["thermal_efficiency"], 0.85)
        self.assertEqual(thermal["total_thermal_loss_kw"], 0.0)
        self.assertEqual(thermal["temperature_drop_c"], 0.0)
        self.assertEqual(thermal["heat_transfer_coefficient_avg"], 0.6)
        
        # Check compliance
        compliance = self.cha.hydraulic_kpis["compliance"]
        self.assertFalse(compliance["overall_compliant"])
        self.assertIn("Hydraulic simulation failed: Test reason", compliance["violations"])
        
        # Check warnings
        warnings = self.cha.hydraulic_kpis["warnings"]
        self.assertIn("Hydraulic simulation failed: Test reason", warnings)
        self.assertIn("Using topology-only mode with estimated values", warnings)
    
    def test_update_pipe_data_with_fallback(self):
        """Test updating pipe data with fallback values."""
        if not CentralizedHeatingAgent:
            self.skipTest("CentralizedHeatingAgent not available")
        
        # Create mock pipe data
        import pandas as pd
        self.cha.supply_pipes = pd.DataFrame({
            'id': [1, 2, 3],
            'length_km': [0.5, 0.3, 0.2]
        })
        self.cha.return_pipes = pd.DataFrame({
            'id': [1, 2, 3],
            'length_km': [0.5, 0.3, 0.2]
        })
        
        # Update with fallback values
        self.cha._update_pipe_data_with_fallback()
        
        # Check supply pipes
        self.assertIn('d_inner_m', self.cha.supply_pipes.columns)
        self.assertIn('v_mean_m_per_s', self.cha.supply_pipes.columns)
        self.assertIn('p_from_bar', self.cha.supply_pipes.columns)
        self.assertIn('p_to_bar', self.cha.supply_pipes.columns)
        self.assertIn('mdot_kg_per_s', self.cha.supply_pipes.columns)
        self.assertIn('t_from_k', self.cha.supply_pipes.columns)
        self.assertIn('t_to_k', self.cha.supply_pipes.columns)
        self.assertIn('alpha_w_per_m2k', self.cha.supply_pipes.columns)
        self.assertIn('text_k', self.cha.supply_pipes.columns)
        self.assertIn('simulation_mode', self.cha.supply_pipes.columns)
        self.assertIn('fallback_values', self.cha.supply_pipes.columns)
        
        # Check default values
        self.assertEqual(self.cha.supply_pipes['d_inner_m'].iloc[0], 0.2)
        self.assertEqual(self.cha.supply_pipes['v_mean_m_per_s'].iloc[0], 0.0)
        self.assertEqual(self.cha.supply_pipes['p_from_bar'].iloc[0], 6.0)
        self.assertEqual(self.cha.supply_pipes['p_to_bar'].iloc[0], 6.0)
        self.assertEqual(self.cha.supply_pipes['t_from_k'].iloc[0], 353.15)
        self.assertEqual(self.cha.supply_pipes['simulation_mode'].iloc[0], 'topology_only')
        self.assertTrue(self.cha.supply_pipes['fallback_values'].iloc[0])
        
        # Check return pipes
        self.assertIn('d_inner_m', self.cha.return_pipes.columns)
        self.assertIn('v_mean_m_per_s', self.cha.return_pipes.columns)
        self.assertIn('p_from_bar', self.cha.return_pipes.columns)
        self.assertIn('p_to_bar', self.cha.return_pipes.columns)
        self.assertIn('mdot_kg_per_s', self.cha.return_pipes.columns)
        self.assertIn('t_from_k', self.cha.return_pipes.columns)
        self.assertIn('t_to_k', self.cha.return_pipes.columns)
        self.assertIn('alpha_w_per_m2k', self.cha.return_pipes.columns)
        self.assertIn('text_k', self.cha.return_pipes.columns)
        self.assertIn('simulation_mode', self.cha.return_pipes.columns)
        self.assertIn('fallback_values', self.cha.return_pipes.columns)
        
        # Check default values for return pipes
        self.assertEqual(self.cha.return_pipes['d_inner_m'].iloc[0], 0.2)
        self.assertEqual(self.cha.return_pipes['v_mean_m_per_s'].iloc[0], 0.0)
        self.assertEqual(self.cha.return_pipes['p_from_bar'].iloc[0], 2.0)
        self.assertEqual(self.cha.return_pipes['p_to_bar'].iloc[0], 2.0)
        self.assertEqual(self.cha.return_pipes['t_from_k'].iloc[0], 323.15)
        self.assertEqual(self.cha.return_pipes['simulation_mode'].iloc[0], 'topology_only')
        self.assertTrue(self.cha.return_pipes['fallback_values'].iloc[0])
    
    @patch('src.cha.PANDAPIPES_AVAILABLE', False)
    def test_hydraulic_simulation_pandapipes_unavailable(self):
        """Test graceful degradation when Pandapipes is not available."""
        if not CentralizedHeatingAgent:
            self.skipTest("CentralizedHeatingAgent not available")
        
        # Mock pipe data
        import pandas as pd
        self.cha.supply_pipes = pd.DataFrame({'length_km': [0.5]})
        self.cha.return_pipes = pd.DataFrame({'length_km': [0.5]})
        
        # Run hydraulic simulation
        result = self.cha.run_hydraulic_simulation()
        
        # Should fallback to topology-only mode
        self.assertTrue(result)
        self.assertIsNotNone(self.cha.simulation_results)
        self.assertIsNotNone(self.cha.hydraulic_kpis)
        
        # Check that fallback was used
        self.assertEqual(self.cha.simulation_results["simulation_mode"], "topology_only")
        self.assertEqual(self.cha.simulation_results["fallback_reason"], "Pandapipes not available")
    
    def test_hydraulic_simulation_disabled(self):
        """Test graceful degradation when hydraulic simulation is disabled."""
        if not CentralizedHeatingAgent:
            self.skipTest("CentralizedHeatingAgent not available")
        
        # Disable hydraulic simulation
        self.cha.config['compatibility']['enable_hydraulic_simulation'] = False
        
        # Mock pipe data
        import pandas as pd
        self.cha.supply_pipes = pd.DataFrame({'length_km': [0.5]})
        self.cha.return_pipes = pd.DataFrame({'length_km': [0.5]})
        
        # Run hydraulic simulation
        result = self.cha.run_hydraulic_simulation()
        
        # Should fallback to topology-only mode
        self.assertTrue(result)
        self.assertIsNotNone(self.cha.simulation_results)
        self.assertIsNotNone(self.cha.hydraulic_kpis)
        
        # Check that fallback was used
        self.assertEqual(self.cha.simulation_results["simulation_mode"], "topology_only")
        self.assertEqual(self.cha.simulation_results["fallback_reason"], "Hydraulic simulation disabled")
    
    @patch('src.cha.CHAPandapipesSimulator')
    def test_hydraulic_simulation_failure(self, mock_simulator_class):
        """Test graceful degradation when hydraulic simulation fails."""
        if not CentralizedHeatingAgent:
            self.skipTest("CentralizedHeatingAgent not available")
        
        # Mock simulator to fail
        mock_simulator = Mock()
        mock_simulator.load_cha_network.return_value = False
        mock_simulator_class.return_value = mock_simulator
        
        # Mock pipe data
        import pandas as pd
        self.cha.supply_pipes = pd.DataFrame({'length_km': [0.5]})
        self.cha.return_pipes = pd.DataFrame({'length_km': [0.5]})
        
        # Run hydraulic simulation
        result = self.cha.run_hydraulic_simulation()
        
        # Should fallback to topology-only mode
        self.assertTrue(result)
        self.assertIsNotNone(self.cha.simulation_results)
        self.assertIsNotNone(self.cha.hydraulic_kpis)
        
        # Check that fallback was used
        self.assertEqual(self.cha.simulation_results["simulation_mode"], "topology_only")
        self.assertEqual(self.cha.simulation_results["fallback_reason"], "Failed to load CHA network")
    
    def test_simulation_mode_detection(self):
        """Test simulation mode detection in run method."""
        if not CentralizedHeatingAgent:
            self.skipTest("CentralizedHeatingAgent not available")
        
        # Test full hydraulic mode
        self.cha.simulation_results = {
            "simulation_mode": "full_hydraulic",
            "simulation_success": True
        }
        
        simulation_mode = "full_hydraulic" if self.cha.simulation_results and self.cha.simulation_results.get("simulation_mode") != "topology_only" else "topology_only"
        self.assertEqual(simulation_mode, "full_hydraulic")
        
        # Test topology-only mode
        self.cha.simulation_results = {
            "simulation_mode": "topology_only",
            "simulation_success": True
        }
        
        simulation_mode = "full_hydraulic" if self.cha.simulation_results and self.cha.simulation_results.get("simulation_mode") != "topology_only" else "topology_only"
        self.assertEqual(simulation_mode, "topology_only")
        
        # Test no simulation results
        self.cha.simulation_results = None
        
        simulation_mode = "full_hydraulic" if self.cha.simulation_results and self.cha.simulation_results.get("simulation_mode") != "topology_only" else "topology_only"
        self.assertEqual(simulation_mode, "topology_only")
    
    def test_fallback_configuration_options(self):
        """Test different fallback configuration options."""
        if not CentralizedHeatingAgent:
            self.skipTest("CentralizedHeatingAgent not available")
        
        # Test with fallback enabled
        self.cha.config['compatibility']['fallback_to_topology_only'] = True
        result = self.cha._fallback_to_topology_only("Test reason")
        self.assertTrue(result)
        
        # Test with fallback disabled
        self.cha.config['compatibility']['fallback_to_topology_only'] = False
        result = self.cha._fallback_to_topology_only("Test reason")
        self.assertFalse(result)
        
        # Test with missing compatibility section
        del self.cha.config['compatibility']
        result = self.cha._fallback_to_topology_only("Test reason")
        self.assertTrue(result)  # Should default to True


def run_graceful_degradation_tests():
    """Run all graceful degradation tests."""
    print("🧪 Running CHA Graceful Degradation Tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test methods
    test_methods = [
        'test_graceful_degradation_initialization',
        'test_fallback_to_topology_only_enabled',
        'test_fallback_to_topology_only_disabled',
        'test_create_fallback_simulation_results',
        'test_create_fallback_kpis',
        'test_update_pipe_data_with_fallback',
        'test_hydraulic_simulation_pandapipes_unavailable',
        'test_hydraulic_simulation_disabled',
        'test_hydraulic_simulation_failure',
        'test_simulation_mode_detection',
        'test_fallback_configuration_options'
    ]
    
    for method in test_methods:
        suite.addTest(TestCHAGracefulDegradation(method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n📊 Test Results Summary:")
    print(f"✅ Tests run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    print(f"📈 Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Test Failures:")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"  - {test}: {error_msg}")
    
    if result.errors:
        print(f"\n⚠️  Test Errors:")
        for test, traceback in result.errors:
            error_msg = traceback.split('\n')[-2]
            print(f"  - {test}: {error_msg}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_graceful_degradation_tests()
    sys.exit(0 if success else 1)
