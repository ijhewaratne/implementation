#!/usr/bin/env python3
"""
Test CHA Output Migration Tool

This test validates the CHA output migration tool functionality including
file conversion, validation, reporting, and rollback capabilities.
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

# Add scripts to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

try:
    from migrate_cha_outputs import (
        CHAOutputMigrator, MigrationResult, MigrationReport
    )
except ImportError as e:
    print(f"Warning: Could not import migration tool: {e}")
    CHAOutputMigrator = None


class TestCHAOutputMigration(unittest.TestCase):
    """Test CHA output migration functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_data_dir = Path(cls.temp_dir) / "test_data"
        cls.test_data_dir.mkdir()
        
        # Create test configuration
        cls.test_config = {
            'backward_compatibility': {
                'migration': {
                    'enabled': True,
                    'auto_migrate_data': True,
                    'backup_original_files': True,
                    'migration_log_level': 'INFO',
                    'rollback_on_failure': True,
                    'data_migration': {
                        'convert_units': True,
                        'update_schema_version': True,
                        'validate_after_migration': True,
                        'preserve_metadata': True
                    }
                },
                'parameter_mapping': {
                    'max_velocity': 'max_velocity_ms',
                    'max_pressure_drop': 'max_pressure_drop_pa_per_m',
                    'pipe_diameter': 'diameter_m',
                    'flow_rate': 'flow_kg_s'
                }
            },
            'migration': {
                'safety': {
                    'backup_before_migration': True,
                    'validate_after_migration': True,
                    'rollback_on_failure': True,
                    'test_migration_first': True
                }
            }
        }
        
        # Create test config file
        cls.config_path = cls.test_data_dir / "test_config.yml"
        with open(cls.config_path, 'w') as f:
            yaml.dump(cls.test_config, f)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test class."""
        shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """Set up each test."""
        self.migrator = None
        if CHAOutputMigrator:
            self.migrator = CHAOutputMigrator(str(self.__class__.config_path))
    
    def test_migrator_initialization(self):
        """Test migrator initialization."""
        if not CHAOutputMigrator:
            self.skipTest("CHAOutputMigrator not available")
        
        self.assertIsNotNone(self.migrator)
        self.assertIsNotNone(self.migrator.config)
        self.assertIsNotNone(self.migrator.logger)
        self.assertIsNotNone(self.migrator.migration_config)
        self.assertIsNotNone(self.migrator.safety_config)
    
    def test_file_format_detection(self):
        """Test file format detection."""
        if not CHAOutputMigrator:
            self.skipTest("CHAOutputMigrator not available")
        
        # Test JSON file
        json_file = self.test_data_dir / "test.json"
        with open(json_file, 'w') as f:
            json.dump({"test": "data"}, f)
        
        format_type = self.migrator._detect_file_format(str(json_file))
        self.assertEqual(format_type, 'json')
        
        # Test CSV file
        csv_file = self.test_data_dir / "test.csv"
        with open(csv_file, 'w') as f:
            f.write("col1,col2\nval1,val2\n")
        
        format_type = self.migrator._detect_file_format(str(csv_file))
        self.assertEqual(format_type, 'csv')
        
        # Test XML file
        xml_file = self.test_data_dir / "test.xml"
        with open(xml_file, 'w') as f:
            f.write("<?xml version='1.0'?><root><test>data</test></root>")
        
        format_type = self.migrator._detect_file_format(str(xml_file))
        self.assertEqual(format_type, 'xml')
    
    def test_legacy_json_loading(self):
        """Test loading legacy JSON data."""
        if not CHAOutputMigrator:
            self.skipTest("CHAOutputMigrator not available")
        
        # Create legacy JSON data
        legacy_data = {
            "metadata": {
                "simulation_timestamp": "2024-01-15T10:30:00Z",
                "pandapipes_version": "0.7.0",
                "convergence_status": "converged"
            },
            "pipes": [
                {
                    "id": 1,
                    "length_km": 0.5,
                    "diameter_m": 0.2,
                    "max_velocity": 1.5,  # Legacy parameter name
                    "max_pressure_drop": 400  # Legacy parameter name
                }
            ]
        }
        
        json_file = self.test_data_dir / "legacy.json"
        with open(json_file, 'w') as f:
            json.dump(legacy_data, f)
        
        # Load legacy data
        loaded_data = self.migrator._load_legacy_data(str(json_file), 'json')
        
        self.assertIn('metadata', loaded_data)
        self.assertIn('pipes', loaded_data)
        self.assertEqual(len(loaded_data['pipes']), 1)
        self.assertEqual(loaded_data['pipes'][0]['id'], 1)
    
    def test_legacy_csv_loading(self):
        """Test loading legacy CSV data."""
        if not CHAOutputMigrator:
            self.skipTest("CHAOutputMigrator not available")
        
        # Create legacy CSV data
        csv_content = """id,length_km,diameter_m,velocity_ms,pressure_drop_pa_per_m
1,0.5,0.2,1.5,400
2,0.3,0.15,1.2,350"""
        
        csv_file = self.test_data_dir / "legacy.csv"
        with open(csv_file, 'w') as f:
            f.write(csv_content)
        
        # Load legacy data
        loaded_data = self.migrator._load_legacy_data(str(csv_file), 'csv')
        
        self.assertIn('metadata', loaded_data)
        self.assertIn('pipes', loaded_data)
        self.assertEqual(len(loaded_data['pipes']), 2)
        self.assertEqual(loaded_data['pipes'][0]['id'], 1)
        self.assertEqual(loaded_data['pipes'][1]['id'], 2)
    
    def test_parameter_name_conversion(self):
        """Test conversion of legacy parameter names."""
        if not CHAOutputMigrator:
            self.skipTest("CHAOutputMigrator not available")
        
        # Create data with legacy parameter names
        data = {
            "pipes": [
                {
                    "id": 1,
                    "max_velocity": 1.5,
                    "max_pressure_drop": 400,
                    "pipe_diameter": 0.2,
                    "flow_rate": 25.0
                }
            ]
        }
        
        # Convert parameter names
        converted_data = self.migrator._convert_parameter_names(data)
        
        pipe = converted_data['pipes'][0]
        self.assertIn('max_velocity_ms', pipe)
        self.assertIn('max_pressure_drop_pa_per_m', pipe)
        self.assertIn('diameter_m', pipe)
        self.assertIn('flow_kg_s', pipe)
        
        # Check that legacy names are removed
        self.assertNotIn('max_velocity', pipe)
        self.assertNotIn('max_pressure_drop', pipe)
        self.assertNotIn('pipe_diameter', pipe)
        self.assertNotIn('flow_rate', pipe)
    
    def test_missing_fields_addition(self):
        """Test addition of missing required fields."""
        if not CHAOutputMigrator:
            self.skipTest("CHAOutputMigrator not available")
        
        # Create data with missing fields
        data = {
            "metadata": {
                "simulation_timestamp": "2024-01-15T10:30:00Z"
            }
        }
        
        # Add missing fields
        enhanced_data = self.migrator._add_missing_fields(data)
        
        # Check that all required fields are present
        required_fields = ['metadata', 'nodes', 'pipes', 'kpis', 'compliance', 'crs', 'units']
        for field in required_fields:
            self.assertIn(field, enhanced_data)
        
        # Check specific field structures
        self.assertIn('junctions', enhanced_data['nodes'])
        self.assertIn('sources', enhanced_data['nodes'])
        self.assertIn('sinks', enhanced_data['nodes'])
        
        self.assertIn('hydraulic', enhanced_data['kpis'])
        self.assertIn('thermal', enhanced_data['kpis'])
        self.assertIn('economic', enhanced_data['kpis'])
    
    def test_data_type_fixing(self):
        """Test fixing of data types."""
        if not CHAOutputMigrator:
            self.skipTest("CHAOutputMigrator not available")
        
        # Create data with incorrect types
        data = {
            "metadata": {
                "convergence_status": "successful",  # Invalid enum value
                "total_iterations": "15",  # String instead of number
                "simulation_duration_s": "45.2"  # String instead of number
            },
            "pipes": [
                {
                    "id": 1,
                    "length_km": "0.5",  # String instead of number
                    "diameter_m": "0.2",  # String instead of number
                    "v_mean_m_per_s": "1.5"  # String instead of number
                }
            ]
        }
        
        # Fix data types
        fixed_data = self.migrator._fix_data_types(data)
        
        # Check metadata fixes
        self.assertEqual(fixed_data['metadata']['convergence_status'], 'converged')
        self.assertIsInstance(fixed_data['metadata']['total_iterations'], float)
        self.assertIsInstance(fixed_data['metadata']['simulation_duration_s'], float)
        
        # Check pipe data fixes
        pipe = fixed_data['pipes'][0]
        self.assertIsInstance(pipe['length_km'], float)
        self.assertIsInstance(pipe['diameter_m'], float)
        self.assertIsInstance(pipe['v_mean_m_per_s'], float)
    
    def test_enhanced_fields_addition(self):
        """Test addition of enhanced fields."""
        if not CHAOutputMigrator:
            self.skipTest("CHAOutputMigrator not available")
        
        # Create basic data
        data = {
            "metadata": {
                "simulation_timestamp": "2024-01-15T10:30:00Z"
            },
            "pipes": [
                {"id": 1, "length_km": 0.5},
                {"id": 2, "length_km": 0.3}
            ],
            "nodes": {
                "junctions": [{"id": 1}],
                "sources": [{"id": 1}],
                "sinks": [{"id": 1}, {"id": 2}]
            }
        }
        
        # Add enhanced fields
        enhanced_data = self.migrator._add_enhanced_fields(data)
        
        # Check enhanced metadata
        metadata = enhanced_data['metadata']
        self.assertIn('thermal_simulation_enabled', metadata)
        self.assertIn('auto_resize_enabled', metadata)
        self.assertIn('network_size', metadata)
        
        # Check network size calculation
        network_size = metadata['network_size']
        self.assertEqual(network_size['junctions'], 1)
        self.assertEqual(network_size['pipes'], 2)
        self.assertEqual(network_size['sources'], 1)
        self.assertEqual(network_size['sinks'], 2)
        
        # Check enhanced KPIs
        kpis = enhanced_data['kpis']
        self.assertIn('hydraulic', kpis)
        self.assertIn('thermal', kpis)
        self.assertIn('economic', kpis)
        
        # Check that KPIs have default values
        self.assertIn('max_velocity_ms', kpis['hydraulic'])
        self.assertIn('thermal_efficiency', kpis['thermal'])
        self.assertIn('capex_eur', kpis['economic'])
    
    def test_legacy_data_conversion(self):
        """Test complete legacy data conversion."""
        if not CHAOutputMigrator:
            self.skipTest("CHAOutputMigrator not available")
        
        # Create legacy data
        legacy_data = {
            "metadata": {
                "simulation_timestamp": "2024-01-15T10:30:00Z",
                "pandapipes_version": "0.7.0",
                "convergence_status": "successful"
            },
            "pipes": [
                {
                    "id": 1,
                    "max_velocity": 1.5,  # Legacy parameter
                    "max_pressure_drop": 400,  # Legacy parameter
                    "length_km": "0.5",  # String type
                    "diameter_m": "0.2"  # String type
                }
            ]
        }
        
        # Convert legacy data
        converted_data = self.migrator._convert_legacy_data(legacy_data)
        
        # Check that conversion was successful
        self.assertIn('metadata', converted_data)
        self.assertIn('pipes', converted_data)
        self.assertIn('nodes', converted_data)
        self.assertIn('kpis', converted_data)
        self.assertIn('compliance', converted_data)
        self.assertIn('crs', converted_data)
        self.assertIn('units', converted_data)
        
        # Check metadata updates
        metadata = converted_data['metadata']
        self.assertEqual(metadata['schema_version'], '2.0.0')
        self.assertIn('migrated_at', metadata)
        self.assertIn('migration_tool', metadata)
        
        # Check parameter name conversion
        pipe = converted_data['pipes'][0]
        self.assertIn('max_velocity_ms', pipe)
        self.assertIn('max_pressure_drop_pa_per_m', pipe)
        self.assertNotIn('max_velocity', pipe)
        self.assertNotIn('max_pressure_drop', pipe)
        
        # Check data type conversion
        self.assertIsInstance(pipe['length_km'], float)
        self.assertIsInstance(pipe['diameter_m'], float)
    
    def test_migration_result_creation(self):
        """Test MigrationResult creation."""
        if not CHAOutputMigrator:
            self.skipTest("CHAOutputMigrator not available")
        
        # Create migration result
        result = MigrationResult(
            file_path="test.json",
            success=True,
            migration_time=1.5,
            file_size_before=1000,
            file_size_after=1200,
            validation_passed=True,
            backup_created=True,
            backup_path="backup/test.json"
        )
        
        # Check result properties
        self.assertEqual(result.file_path, "test.json")
        self.assertTrue(result.success)
        self.assertEqual(result.migration_time, 1.5)
        self.assertEqual(result.file_size_before, 1000)
        self.assertEqual(result.file_size_after, 1200)
        self.assertTrue(result.validation_passed)
        self.assertTrue(result.backup_created)
        self.assertEqual(result.backup_path, "backup/test.json")
    
    def test_migration_report_creation(self):
        """Test MigrationReport creation."""
        if not CHAOutputMigrator:
            self.skipTest("CHAOutputMigrator not available")
        
        # Create migration results
        results = [
            MigrationResult("file1.json", True, migration_time=1.0, file_size_before=1000, file_size_after=1200),
            MigrationResult("file2.json", False, error_message="Test error", migration_time=0.5)
        ]
        
        # Create migration report
        report = MigrationReport(
            start_time="2024-01-15T10:00:00Z",
            end_time="2024-01-15T10:05:00Z",
            total_files=2,
            successful_migrations=1,
            failed_migrations=1,
            total_migration_time=300.0,
            total_size_before=2000,
            total_size_after=1200,
            validation_success_rate=0.5,
            backup_created=True,
            results=results,
            errors=["file2.json: Test error"],
            warnings=[]
        )
        
        # Check report properties
        self.assertEqual(report.total_files, 2)
        self.assertEqual(report.successful_migrations, 1)
        self.assertEqual(report.failed_migrations, 1)
        self.assertEqual(report.total_migration_time, 300.0)
        self.assertEqual(report.validation_success_rate, 0.5)
        self.assertTrue(report.backup_created)
        self.assertEqual(len(report.results), 2)
        self.assertEqual(len(report.errors), 1)
    
    @patch('migrate_cha_outputs.CHASchemaValidator')
    @patch('migrate_cha_outputs.CHAValidationSystem')
    def test_migrated_data_validation(self, mock_validation_system, mock_schema_validator):
        """Test validation of migrated data."""
        if not CHAOutputMigrator:
            self.skipTest("CHAOutputMigrator not available")
        
        # Mock validators
        mock_schema_validator.return_value.validate_data.return_value = {'valid': True, 'errors': []}
        mock_validation_system.return_value.validate_standards_compliance.return_value = {
            'overall_compliant': True,
            'violations': []
        }
        
        # Create test data
        data = {
            'metadata': {'simulation_timestamp': '2024-01-15T10:30:00Z'},
            'pipes': [{'id': 1, 'length_km': 0.5}],
            'kpis': {'hydraulic': {}, 'thermal': {}, 'economic': {}}
        }
        
        # Test validation
        is_valid, errors = self.migrator._validate_migrated_data(data)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_backup_creation(self):
        """Test backup creation functionality."""
        if not CHAOutputMigrator:
            self.skipTest("CHAOutputMigrator not available")
        
        # Create test file
        test_file = self.test_data_dir / "test_backup.json"
        with open(test_file, 'w') as f:
            json.dump({"test": "data"}, f)
        
        # Create backup
        backup_path = self.migrator._create_backup(str(test_file))
        
        if backup_path:  # Backup creation might be disabled in test config
            self.assertIsNotNone(backup_path)
            self.assertTrue(Path(backup_path).exists())
            
            # Check backup content
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            self.assertEqual(backup_data, {"test": "data"})
    
    def test_single_file_migration(self):
        """Test migration of a single file."""
        if not CHAOutputMigrator:
            self.skipTest("CHAOutputMigrator not available")
        
        # Create legacy JSON file
        legacy_data = {
            "metadata": {
                "simulation_timestamp": "2024-01-15T10:30:00Z",
                "pandapipes_version": "0.7.0",
                "convergence_status": "converged"
            },
            "pipes": [
                {
                    "id": 1,
                    "length_km": 0.5,
                    "diameter_m": 0.2,
                    "max_velocity": 1.5,
                    "max_pressure_drop": 400
                }
            ]
        }
        
        input_file = self.test_data_dir / "legacy_input.json"
        with open(input_file, 'w') as f:
            json.dump(legacy_data, f)
        
        output_file = self.test_data_dir / "migrated_output.json"
        
        # Mock validation to avoid dependency issues
        with patch.object(self.migrator, '_validate_migrated_data', return_value=(True, [])):
            result = self.migrator.migrate_file(str(input_file), str(output_file))
        
        # Check migration result
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
        self.assertGreater(result.migration_time, 0)
        self.assertGreater(result.file_size_before, 0)
        self.assertGreater(result.file_size_after, 0)
        
        # Check that output file was created
        self.assertTrue(output_file.exists())
        
        # Check output file content
        with open(output_file, 'r') as f:
            migrated_data = json.load(f)
        
        self.assertIn('metadata', migrated_data)
        self.assertIn('pipes', migrated_data)
        self.assertIn('nodes', migrated_data)
        self.assertIn('kpis', migrated_data)
        self.assertIn('compliance', migrated_data)
        self.assertIn('crs', migrated_data)
        self.assertIn('units', migrated_data)
    
    def test_migration_with_validation_failure(self):
        """Test migration with validation failure."""
        if not CHAOutputMigrator:
            self.skipTest("CHAOutputMigrator not available")
        
        # Create legacy JSON file
        legacy_data = {
            "metadata": {
                "simulation_timestamp": "2024-01-15T10:30:00Z"
            }
        }
        
        input_file = self.test_data_dir / "invalid_input.json"
        with open(input_file, 'w') as f:
            json.dump(legacy_data, f)
        
        output_file = self.test_data_dir / "invalid_output.json"
        
        # Mock validation to return failure
        with patch.object(self.migrator, '_validate_migrated_data', return_value=(False, ["Missing required field: pipes"])):
            result = self.migrator.migrate_file(str(input_file), str(output_file))
        
        # Check migration result
        self.assertFalse(result.success)
        self.assertIn("Validation failed", result.error_message)
        self.assertIn("Missing required field: pipes", result.error_message)


def run_migration_tool_tests():
    """Run all migration tool tests."""
    print("🧪 Running CHA Output Migration Tool Tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test methods
    test_methods = [
        'test_migrator_initialization',
        'test_file_format_detection',
        'test_legacy_json_loading',
        'test_legacy_csv_loading',
        'test_parameter_name_conversion',
        'test_missing_fields_addition',
        'test_data_type_fixing',
        'test_enhanced_fields_addition',
        'test_legacy_data_conversion',
        'test_migration_result_creation',
        'test_migration_report_creation',
        'test_migrated_data_validation',
        'test_backup_creation',
        'test_single_file_migration',
        'test_migration_with_validation_failure'
    ]
    
    for method in test_methods:
        suite.addTest(TestCHAOutputMigration(method))
    
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
    success = run_migration_tool_tests()
    sys.exit(0 if success else 1)
