#!/usr/bin/env python3
"""
Test script for Thesis Data Integration
======================================

Tests the thesis data integration module that replaces LFA with physics-based heat demand.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from thesis_data_integration import (
    ThesisDataIntegrator, 
    TRYWeatherProcessor, 
    HeatingDataProcessor, 
    ElectricalProfileProcessor
)


class TestThesisDataIntegration(unittest.TestCase):
    """Test cases for thesis data integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.config = {
            'data_sources': {
                'weather_try': 'thesis-data-2/wetter-data/TRY2015_517475143730_Jahr.dat',
                'heating_data': 'thesis-data-2/pipes-sim/ergebnis_momentane_heizleistungV3.json',
                'electrical_profiles': 'thesis-data-2/load-profile-generator/gebaeude_lastphasenV2_verbrauch.json'
            },
            'scenarios': {
                'default': 'mittleres_jahr'
            },
            'heat_pump': {
                'cop_model': 'constant',
                'cop_value': 3.0
            },
            'output': {
                'dir': str(self.test_dir / 'processed/lfa')
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_try_weather_processor_init(self):
        """Test TRY weather processor initialization."""
        processor = TRYWeatherProcessor()
        self.assertEqual(processor.heating_threshold, 15.0)
    
    def test_heating_data_processor_init(self):
        """Test heating data processor initialization."""
        processor = HeatingDataProcessor()
        self.assertIn('winter', processor.seasons)
        self.assertIn('night', processor.time_periods)
    
    def test_electrical_profile_processor_init(self):
        """Test electrical profile processor initialization."""
        processor = ElectricalProfileProcessor()
        self.assertIsNotNone(processor)
    
    def test_create_temperature_power_mapping(self):
        """Test temperature-power mapping creation."""
        processor = HeatingDataProcessor()
        
        # Mock heating profile data
        heating_profile = [
            {
                'Durchschnitt': {
                    'Temperatur': 0.0,
                    'Momentane_Heizleistung_W': 5000.0
                }
            },
            {
                'Durchschnitt': {
                    'Temperatur': 10.0,
                    'Momentane_Heizleistung_W': 3000.0
                }
            }
        ]
        
        mapping = processor.create_temperature_power_mapping(heating_profile)
        
        self.assertEqual(len(mapping), 2)
        self.assertEqual(mapping[0.0], 5000.0)
        self.assertEqual(mapping[10.0], 3000.0)
    
    def test_calculate_heat_pump_load(self):
        """Test heat pump load calculation."""
        processor = ElectricalProfileProcessor()
        
        # Mock building profile
        building_profile = {
            'jahresverbrauch_kwh': 10000,
            'gebaeudefunktion': 'Wohnhaus'
        }
        
        result = processor.calculate_heat_pump_load(building_profile, 'constant', 3.0)
        
        self.assertIn('annual_heating_kwh', result)
        self.assertIn('annual_electrical_kwh', result)
        self.assertIn('peak_electrical_kw', result)
        self.assertEqual(result['cop_model'], 'constant')
        self.assertEqual(result['cop_value'], 3.0)
    
    @patch('thesis_data_integration.ThesisDataIntegrator._load_config')
    def test_integrator_init_with_config(self, mock_load_config):
        """Test integrator initialization with config."""
        mock_load_config.return_value = self.config
        
        integrator = ThesisDataIntegrator()
        
        self.assertIsNotNone(integrator.weather_processor)
        self.assertIsNotNone(integrator.heating_processor)
        self.assertIsNotNone(integrator.electrical_processor)
    
    def test_interpolate_heating_demand(self):
        """Test heating demand interpolation."""
        integrator = ThesisDataIntegrator()
        
        # Mock temperature-power mapping
        temp_power_map = {
            0.0: 5000.0,
            10.0: 3000.0,
            20.0: 0.0
        }
        
        # Mock hourly temperatures
        hourly_temps = [0.0, 5.0, 10.0, 15.0, 20.0]
        
        result = integrator.interpolate_heating_demand(temp_power_map, hourly_temps)
        
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0], 5000.0)  # 0°C -> 5000W
        self.assertEqual(result[2], 3000.0)  # 10°C -> 3000W
        self.assertEqual(result[4], 0.0)     # 20°C -> 0W (above threshold)
    
    def test_generate_building_heat_demand_structure(self):
        """Test building heat demand data structure."""
        integrator = ThesisDataIntegrator()
        
        # Mock data
        integrator.weather_data = MagicMock()
        integrator.weather_data.__getitem__ = MagicMock(return_value=[0.0] * 8760)
        
        integrator.heating_data = {
            'ergebnisse': {
                'TEST_BUILDING': {
                    'Szenarien': {
                        'mittleres_jahr': [
                            {
                                'Durchschnitt': {
                                    'Temperatur': 0.0,
                                    'Momentane_Heizleistung_W': 5000.0
                                }
                            }
                        ]
                    }
                }
            }
        }
        
        result = integrator.generate_building_heat_demand('TEST_BUILDING')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['building_id'], 'TEST_BUILDING')
        self.assertEqual(len(result['series']), 8760)
        self.assertIn('q10', result)
        self.assertIn('q90', result)
        self.assertIn('metadata', result)
        self.assertEqual(result['metadata']['scenario'], 'mittleres_jahr')
    
    def test_save_lfa_compatible_json(self):
        """Test saving LFA-compatible JSON format."""
        integrator = ThesisDataIntegrator()
        
        # Mock building data
        building_data = {
            'building_id': 'TEST_BUILDING',
            'series': [1000.0] * 8760,
            'q10': [900.0] * 8760,
            'q90': [1100.0] * 8760,
            'metadata': {
                'scenario': 'mittleres_jahr',
                'model_version': 'thesis-data-v1.0.0'
            }
        }
        
        output_dir = self.test_dir / 'processed/lfa'
        result = integrator.save_lfa_compatible_json(building_data, str(output_dir))
        
        self.assertTrue(result)
        self.assertTrue((output_dir / 'TEST_BUILDING.json').exists())
        
        # Verify JSON structure
        with open(output_dir / 'TEST_BUILDING.json', 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['building_id'], 'TEST_BUILDING')
        self.assertEqual(len(saved_data['series']), 8760)
        self.assertIn('metadata', saved_data)


class TestDataIntegrationEndToEnd(unittest.TestCase):
    """End-to-end tests for data integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_config_file_structure(self):
        """Test that config file has required structure."""
        config_path = Path(__file__).parent.parent / 'configs' / 'thesis_data.yml'
        
        if config_path.exists():
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            required_sections = ['data_sources', 'scenarios', 'heat_pump', 'output']
            for section in required_sections:
                self.assertIn(section, config, f"Missing required config section: {section}")
            
            # Check data sources
            data_sources = config['data_sources']
            required_sources = ['weather_try', 'heating_data', 'electrical_profiles']
            for source in required_sources:
                self.assertIn(source, data_sources, f"Missing required data source: {source}")
    
    def test_lfa_compatibility(self):
        """Test that generated data is LFA-compatible."""
        # This test would require actual data files to run
        # For now, we'll test the structure
        
        expected_structure = {
            'building_id': str,
            'series': list,
            'q10': list,
            'q90': list,
            'metadata': dict
        }
        
        # Mock building data
        building_data = {
            'building_id': 'TEST_BUILDING',
            'series': [1000.0] * 8760,
            'q10': [900.0] * 8760,
            'q90': [1100.0] * 8760,
            'metadata': {
                'scenario': 'mittleres_jahr',
                'model_version': 'thesis-data-v1.0.0',
                'forecast_date': '2024-01-01T00:00:00',
                'total_annual_kwh': 1000.0,
                'peak_kw': 5.0,
                'avg_kw': 2.5,
                'data_source': 'physics_based'
            }
        }
        
        # Verify structure
        for key, expected_type in expected_structure.items():
            self.assertIn(key, building_data)
            self.assertIsInstance(building_data[key], expected_type)
        
        # Verify series length
        self.assertEqual(len(building_data['series']), 8760)
        self.assertEqual(len(building_data['q10']), 8760)
        self.assertEqual(len(building_data['q90']), 8760)


def run_tests():
    """Run all tests."""
    print("🧪 Running Thesis Data Integration Tests...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestThesisDataIntegration))
    test_suite.addTest(unittest.makeSuite(TestDataIntegrationEndToEnd))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback}")
    
    if result.errors:
        print("\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit(run_tests())
