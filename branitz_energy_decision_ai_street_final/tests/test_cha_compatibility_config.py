#!/usr/bin/env python3
"""
Test CHA Backward Compatibility and Migration Configuration

This test validates the new backward compatibility and migration settings
in the CHA configuration file.
"""

import unittest
import yaml
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestCHACompatibilityConfig(unittest.TestCase):
    """Test CHA backward compatibility and migration configuration."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_config_path = Path(cls.temp_dir) / "test_cha.yml"
        
        # Load the actual CHA configuration
        with open("configs/cha.yml", 'r') as f:
            cls.original_config = yaml.safe_load(f)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test class."""
        shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """Set up each test."""
        # Create a copy of the config for testing
        self.test_config = self.original_config.copy()
    
    def test_compatibility_section_exists(self):
        """Test that compatibility section exists and has required fields."""
        self.assertIn('compatibility', self.test_config)
        
        compatibility = self.test_config['compatibility']
        
        # Test feature flags
        self.assertIn('enable_hydraulic_simulation', compatibility)
        self.assertIn('fallback_to_topology_only', compatibility)
        self.assertIn('legacy_output_format', compatibility)
        self.assertIn('migration_mode', compatibility)
        
        # Test schema version compatibility
        self.assertIn('schema_version', compatibility)
        self.assertIn('support_legacy_schema', compatibility)
        self.assertIn('auto_migrate_schema', compatibility)
        
        # Test output format compatibility
        self.assertIn('maintain_old_outputs', compatibility)
        self.assertIn('dual_output_mode', compatibility)
        self.assertIn('legacy_validation', compatibility)
        
        # Test API compatibility
        self.assertIn('maintain_legacy_api', compatibility)
        self.assertIn('deprecated_warnings', compatibility)
        self.assertIn('api_version', compatibility)
    
    def test_backward_compatibility_section_exists(self):
        """Test that backward_compatibility section exists and has required fields."""
        self.assertIn('backward_compatibility', self.test_config)
        
        backward_compatibility = self.test_config['backward_compatibility']
        
        # Test legacy system support
        self.assertIn('maintain_old_outputs', backward_compatibility)
        self.assertIn('dual_output_mode', backward_compatibility)
        self.assertIn('legacy_validation', backward_compatibility)
        
        # Test legacy file formats
        self.assertIn('export_legacy_csv', backward_compatibility)
        self.assertIn('export_legacy_json', backward_compatibility)
        self.assertIn('export_legacy_xml', backward_compatibility)
        
        # Test legacy parameter names
        self.assertIn('use_legacy_parameter_names', backward_compatibility)
        self.assertIn('parameter_mapping', backward_compatibility)
        
        # Test legacy validation rules
        self.assertIn('use_legacy_validation_rules', backward_compatibility)
        self.assertIn('legacy_standards_only', backward_compatibility)
        
        # Test migration settings
        self.assertIn('migration', backward_compatibility)
    
    def test_migration_section_exists(self):
        """Test that migration section exists and has required fields."""
        self.assertIn('migration', self.test_config)
        
        migration = self.test_config['migration']
        
        # Test general migration settings
        self.assertIn('enabled', migration)
        self.assertIn('mode', migration)
        
        # Test migration phases
        self.assertIn('phases', migration)
        phases = migration['phases']
        self.assertIn('data_migration', phases)
        self.assertIn('output_migration', phases)
        self.assertIn('config_migration', phases)
        self.assertIn('validation_migration', phases)
        
        # Test migration safety settings
        self.assertIn('safety', migration)
        
        # Test migration logging
        self.assertIn('logging', migration)
        
        # Test migration validation
        self.assertIn('validation', migration)
        
        # Test migration rollback
        self.assertIn('rollback', migration)
    
    def test_compatibility_feature_flags(self):
        """Test compatibility feature flags have correct types and values."""
        compatibility = self.test_config['compatibility']
        
        # Test boolean flags
        self.assertIsInstance(compatibility['enable_hydraulic_simulation'], bool)
        self.assertIsInstance(compatibility['fallback_to_topology_only'], bool)
        self.assertIsInstance(compatibility['legacy_output_format'], bool)
        self.assertIsInstance(compatibility['migration_mode'], bool)
        self.assertIsInstance(compatibility['support_legacy_schema'], bool)
        self.assertIsInstance(compatibility['auto_migrate_schema'], bool)
        self.assertIsInstance(compatibility['maintain_old_outputs'], bool)
        self.assertIsInstance(compatibility['dual_output_mode'], bool)
        self.assertIsInstance(compatibility['legacy_validation'], bool)
        self.assertIsInstance(compatibility['maintain_legacy_api'], bool)
        self.assertIsInstance(compatibility['deprecated_warnings'], bool)
        
        # Test string values
        self.assertIsInstance(compatibility['schema_version'], str)
        self.assertIsInstance(compatibility['api_version'], str)
        
        # Test expected values
        self.assertEqual(compatibility['schema_version'], "2.0.0")
        self.assertEqual(compatibility['api_version'], "2.0")
        self.assertTrue(compatibility['enable_hydraulic_simulation'])
        self.assertTrue(compatibility['fallback_to_topology_only'])
        self.assertFalse(compatibility['legacy_output_format'])
        self.assertFalse(compatibility['migration_mode'])
    
    def test_backward_compatibility_settings(self):
        """Test backward compatibility settings have correct types and values."""
        backward_compatibility = self.test_config['backward_compatibility']
        
        # Test boolean flags
        self.assertIsInstance(backward_compatibility['maintain_old_outputs'], bool)
        self.assertIsInstance(backward_compatibility['dual_output_mode'], bool)
        self.assertIsInstance(backward_compatibility['legacy_validation'], bool)
        self.assertIsInstance(backward_compatibility['export_legacy_csv'], bool)
        self.assertIsInstance(backward_compatibility['export_legacy_json'], bool)
        self.assertIsInstance(backward_compatibility['export_legacy_xml'], bool)
        self.assertIsInstance(backward_compatibility['use_legacy_parameter_names'], bool)
        self.assertIsInstance(backward_compatibility['use_legacy_validation_rules'], bool)
        self.assertIsInstance(backward_compatibility['legacy_standards_only'], bool)
        
        # Test parameter mapping
        parameter_mapping = backward_compatibility['parameter_mapping']
        self.assertIsInstance(parameter_mapping, dict)
        self.assertIn('max_velocity', parameter_mapping)
        self.assertIn('max_pressure_drop', parameter_mapping)
        self.assertIn('pipe_diameter', parameter_mapping)
        self.assertIn('flow_rate', parameter_mapping)
        
        # Test expected mapping values
        self.assertEqual(parameter_mapping['max_velocity'], 'max_velocity_ms')
        self.assertEqual(parameter_mapping['max_pressure_drop'], 'max_pressure_drop_pa_per_m')
        self.assertEqual(parameter_mapping['pipe_diameter'], 'diameter_m')
        self.assertEqual(parameter_mapping['flow_rate'], 'flow_kg_s')
    
    def test_migration_settings(self):
        """Test migration settings have correct types and values."""
        migration = self.test_config['migration']
        
        # Test general settings
        self.assertIsInstance(migration['enabled'], bool)
        self.assertIsInstance(migration['mode'], str)
        self.assertIn(migration['mode'], ['automatic', 'manual', 'guided'])
        
        # Test phases
        phases = migration['phases']
        for phase_name, phase_config in phases.items():
            self.assertIsInstance(phase_config, dict)
            self.assertIn('enabled', phase_config)
            self.assertIn('priority', phase_config)
            self.assertIn('description', phase_config)
            self.assertIsInstance(phase_config['enabled'], bool)
            self.assertIsInstance(phase_config['priority'], int)
            self.assertIsInstance(phase_config['description'], str)
        
        # Test safety settings
        safety = migration['safety']
        self.assertIsInstance(safety['backup_before_migration'], bool)
        self.assertIsInstance(safety['validate_after_migration'], bool)
        self.assertIsInstance(safety['rollback_on_failure'], bool)
        self.assertIsInstance(safety['test_migration_first'], bool)
        
        # Test logging settings
        logging = migration['logging']
        self.assertIsInstance(logging['log_level'], str)
        self.assertIsInstance(logging['log_file'], str)
        self.assertIsInstance(logging['detailed_logging'], bool)
        self.assertIsInstance(logging['progress_reporting'], bool)
        
        # Test validation settings
        validation = migration['validation']
        self.assertIsInstance(validation['validate_schema_compatibility'], bool)
        self.assertIsInstance(validation['validate_data_integrity'], bool)
        self.assertIsInstance(validation['validate_output_format'], bool)
        self.assertIsInstance(validation['validate_configuration'], bool)
        
        # Test rollback settings
        rollback = migration['rollback']
        self.assertIsInstance(rollback['enabled'], bool)
        self.assertIsInstance(rollback['backup_retention_days'], int)
        self.assertIsInstance(rollback['auto_cleanup_backups'], bool)
        self.assertIsInstance(rollback['rollback_confirmation_required'], bool)
    
    def test_migration_phases_priority(self):
        """Test that migration phases have correct priority order."""
        migration = self.test_config['migration']
        phases = migration['phases']
        
        # Test that priorities are sequential and start from 1
        priorities = [phase['priority'] for phase in phases.values()]
        priorities.sort()
        
        self.assertEqual(priorities, [1, 2, 3, 4])
        
        # Test that each phase has a unique priority
        self.assertEqual(len(priorities), len(set(priorities)))
    
    def test_migration_sub_settings(self):
        """Test migration sub-settings in backward_compatibility section."""
        backward_compatibility = self.test_config['backward_compatibility']
        migration = backward_compatibility['migration']
        
        # Test general migration settings
        self.assertIsInstance(migration['enabled'], bool)
        self.assertIsInstance(migration['auto_migrate_data'], bool)
        self.assertIsInstance(migration['backup_original_files'], bool)
        self.assertIsInstance(migration['migration_log_level'], str)
        self.assertIsInstance(migration['rollback_on_failure'], bool)
        
        # Test data migration settings
        data_migration = migration['data_migration']
        self.assertIsInstance(data_migration['convert_units'], bool)
        self.assertIsInstance(data_migration['update_schema_version'], bool)
        self.assertIsInstance(data_migration['validate_after_migration'], bool)
        self.assertIsInstance(data_migration['preserve_metadata'], bool)
        
        # Test output migration settings
        output_migration = migration['output_migration']
        self.assertIsInstance(output_migration['convert_to_new_format'], bool)
        self.assertIsInstance(output_migration['maintain_legacy_files'], bool)
        self.assertIsInstance(output_migration['update_file_extensions'], bool)
        self.assertIsInstance(output_migration['compress_legacy_files'], bool)
        
        # Test configuration migration settings
        config_migration = migration['config_migration']
        self.assertIsInstance(config_migration['update_parameter_names'], bool)
        self.assertIsInstance(config_migration['add_missing_parameters'], bool)
        self.assertIsInstance(config_migration['validate_new_config'], bool)
        self.assertIsInstance(config_migration['backup_old_config'], bool)
    
    def test_configuration_consistency(self):
        """Test that configuration settings are consistent."""
        compatibility = self.test_config['compatibility']
        backward_compatibility = self.test_config['backward_compatibility']
        
        # Test that maintain_old_outputs is consistent
        self.assertEqual(
            compatibility['maintain_old_outputs'],
            backward_compatibility['maintain_old_outputs']
        )
        
        # Test that dual_output_mode is consistent
        self.assertEqual(
            compatibility['dual_output_mode'],
            backward_compatibility['dual_output_mode']
        )
        
        # Test that legacy_validation is consistent
        self.assertEqual(
            compatibility['legacy_validation'],
            backward_compatibility['legacy_validation']
        )
    
    def test_configuration_validation(self):
        """Test that configuration can be validated and loaded."""
        # Test that the configuration is valid YAML
        config_yaml = yaml.dump(self.test_config)
        parsed_config = yaml.safe_load(config_yaml)
        
        self.assertEqual(parsed_config, self.test_config)
        
        # Test that all required sections exist
        required_sections = ['compatibility', 'backward_compatibility', 'migration']
        for section in required_sections:
            self.assertIn(section, parsed_config)
    
    def test_feature_flag_combinations(self):
        """Test that feature flag combinations make sense."""
        compatibility = self.test_config['compatibility']
        
        # If hydraulic simulation is enabled, fallback should be available
        if compatibility['enable_hydraulic_simulation']:
            self.assertTrue(compatibility['fallback_to_topology_only'])
        
        # If migration mode is enabled, auto_migrate_schema should be enabled
        if compatibility['migration_mode']:
            self.assertTrue(compatibility['auto_migrate_schema'])
        
        # If legacy output format is enabled, maintain_old_outputs should be true
        if compatibility['legacy_output_format']:
            self.assertTrue(compatibility['maintain_old_outputs'])
    
    def test_migration_safety_settings(self):
        """Test that migration safety settings are properly configured."""
        migration = self.test_config['migration']
        safety = migration['safety']
        
        # Safety settings should be enabled by default
        self.assertTrue(safety['backup_before_migration'])
        self.assertTrue(safety['validate_after_migration'])
        self.assertTrue(safety['rollback_on_failure'])
        self.assertTrue(safety['test_migration_first'])
        
        # Rollback settings should be enabled
        rollback = migration['rollback']
        self.assertTrue(rollback['enabled'])
        self.assertTrue(rollback['rollback_confirmation_required'])
        self.assertGreater(rollback['backup_retention_days'], 0)
    
    def test_logging_configuration(self):
        """Test that logging configuration is properly set up."""
        migration = self.test_config['migration']
        logging = migration['logging']
        
        # Log level should be valid
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        self.assertIn(logging['log_level'], valid_log_levels)
        
        # Log file should have a valid path
        self.assertTrue(logging['log_file'].endswith('.log'))
        
        # Detailed logging and progress reporting should be enabled
        self.assertTrue(logging['detailed_logging'])
        self.assertTrue(logging['progress_reporting'])


def run_compatibility_config_tests():
    """Run all compatibility configuration tests."""
    print("🧪 Running CHA Backward Compatibility and Migration Configuration Tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test methods
    test_methods = [
        'test_compatibility_section_exists',
        'test_backward_compatibility_section_exists',
        'test_migration_section_exists',
        'test_compatibility_feature_flags',
        'test_backward_compatibility_settings',
        'test_migration_settings',
        'test_migration_phases_priority',
        'test_migration_sub_settings',
        'test_configuration_consistency',
        'test_configuration_validation',
        'test_feature_flag_combinations',
        'test_migration_safety_settings',
        'test_logging_configuration'
    ]
    
    for method in test_methods:
        suite.addTest(TestCHACompatibilityConfig(method))
    
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
    success = run_compatibility_config_tests()
    sys.exit(0 if success else 1)
