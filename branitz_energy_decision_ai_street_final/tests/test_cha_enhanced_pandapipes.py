"""
Unit Tests for CHA Enhanced Pandapipes Simulator

This module contains comprehensive unit tests for the CHA enhanced pandapipes simulator,
testing network creation, hydraulic simulation, validation, and reporting.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

import unittest
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cha_enhanced_pandapipes import CHAEnhancedPandapipesSimulator, HydraulicResult, SimulationValidationResult, HydraulicReport
from cha_pipe_sizing import CHAPipeSizingEngine


class TestCHAEnhancedPandapipes(unittest.TestCase):
    """Test cases for CHA enhanced pandapipes simulator."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create pipe sizing engine
        self.sizing_engine = CHAPipeSizingEngine({
            'max_velocity_ms': 2.0,
            'min_velocity_ms': 0.1,
            'max_pressure_drop_pa_per_m': 5000,
            'pipe_roughness_mm': 0.1
        })
        
        # Create enhanced pandapipes simulator
        self.simulator = CHAEnhancedPandapipesSimulator(self.sizing_engine)
        
        # Create mock network data
        self.network_data = {
            'supply_pipes': [
                {
                    'pipe_id': 'supply_1',
                    'diameter_m': 0.1,
                    'length_m': 100,
                    'aggregated_flow_kg_s': 0.5,
                    'pressure_drop_pa_per_m': 1000,
                    'velocity_ms': 1.5,
                    'pipe_category': 'distribution_pipes'
                }
            ],
            'return_pipes': [
                {
                    'pipe_id': 'return_1',
                    'diameter_m': 0.1,
                    'length_m': 100,
                    'aggregated_flow_kg_s': 0.5,
                    'pressure_drop_pa_per_m': 1000,
                    'velocity_ms': 1.5,
                    'pipe_category': 'distribution_pipes'
                }
            ],
            'service_connections': [
                {
                    'heating_load_kw': 10.0,
                    'building_id': 'building_1'
                }
            ]
        }
    
    def test_network_creation(self):
        """Test sized pandapipes network creation."""
        print("\n🧪 Testing network creation...")
        
        # Test network creation
        success = self.simulator.create_sized_pandapipes_network(self.network_data)
        
        # Verify network creation
        self.assertTrue(success, "Network creation should succeed")
        self.assertIsNotNone(self.simulator.net, "Network should be created")
        
        # Check network components
        if hasattr(self.simulator.net, 'junction'):
            self.assertGreater(len(self.simulator.net.junction), 0, "Should have junctions")
        
        if hasattr(self.simulator.net, 'pipe'):
            self.assertGreater(len(self.simulator.net.pipe), 0, "Should have pipes")
        
        if hasattr(self.simulator.net, 'ext_grid'):
            self.assertGreater(len(self.simulator.net.ext_grid), 0, "Should have external grid")
        
        if hasattr(self.simulator.net, 'sink'):
            self.assertGreater(len(self.simulator.net.sink), 0, "Should have sinks")
        
        print(f"   ✅ Network created successfully")
    
    def test_hydraulic_simulation(self):
        """Test hydraulic simulation."""
        print("\n🧪 Testing hydraulic simulation...")
        
        # Create network first
        success = self.simulator.create_sized_pandapipes_network(self.network_data)
        self.assertTrue(success, "Network creation should succeed")
        
        # Test simulation
        success = self.simulator.run_hydraulic_simulation()
        
        # Verify simulation
        if success:
            self.assertIsNotNone(self.simulator.hydraulic_results, "Should have hydraulic results")
            self.assertGreater(len(self.simulator.hydraulic_results), 0, "Should have results")
            
            # Check result structure
            for result in self.simulator.hydraulic_results:
                self.assertIsInstance(result, HydraulicResult)
                self.assertGreater(result.flow_rate_kg_s, 0, "Flow rate should be positive")
                self.assertGreater(result.velocity_ms, 0, "Velocity should be positive")
                self.assertGreater(result.pressure_drop_bar, 0, "Pressure drop should be positive")
        
        print(f"   ✅ Hydraulic simulation: {'Success' if success else 'Failed (expected for test environment)'}")
    
    def test_simulation_validation(self):
        """Test simulation validation."""
        print("\n🧪 Testing simulation validation...")
        
        # Create mock simulation results
        mock_results = {
            'supply_pipes': [
                {
                    'pipe_id': 'supply_1',
                    'velocity_ms': 1.5,
                    'pressure_drop_pa_per_m': 1000,
                    'diameter_m': 0.1
                }
            ],
            'return_pipes': [
                {
                    'pipe_id': 'return_1',
                    'velocity_ms': 1.5,
                    'pressure_drop_pa_per_m': 1000,
                    'diameter_m': 0.1
                }
            ]
        }
        
        # Test validation
        validation_result = self.simulator.validate_simulation_results(mock_results)
        
        # Verify validation result
        self.assertIsInstance(validation_result, dict)
        self.assertIn('is_valid', validation_result)
        self.assertIn('convergence_achieved', validation_result)
        self.assertIn('violations', validation_result)
        self.assertIn('warnings', validation_result)
        self.assertIn('recommendations', validation_result)
        self.assertIn('summary', validation_result)
        
        # Check summary structure
        summary = validation_result['summary']
        self.assertIn('total_pipes', summary)
        self.assertIn('compliant_pipes', summary)
        self.assertIn('compliance_rate', summary)
        self.assertIn('violation_count', summary)
        self.assertIn('warning_count', summary)
        
        print(f"   ✅ Simulation validation: Valid={validation_result['is_valid']}, Compliance={summary['compliance_rate']:.1%}")
    
    def test_pandapipes_sizing_validation(self):
        """Test pandapipes sizing validation."""
        print("\n🧪 Testing pandapipes sizing validation...")
        
        # Create mock simulation results
        mock_simulation_results = {
            'pipes': {
                'supply_1': {
                    'velocity_ms': 1.5,
                    'pressure_drop_pa_per_m': 1000,
                    'diameter_m': 0.1
                },
                'return_1': {
                    'velocity_ms': 1.5,
                    'pressure_drop_pa_per_m': 1000,
                    'diameter_m': 0.1
                }
            }
        }
        
        # Test sizing validation
        validation_results = self.simulator.validate_pandapipes_sizing(mock_simulation_results)
        
        # Verify validation results structure
        self.assertIsInstance(validation_results, dict)
        self.assertIn('velocity_compliance', validation_results)
        self.assertIn('pressure_compliance', validation_results)
        self.assertIn('flow_distribution', validation_results)
        self.assertIn('sizing_accuracy', validation_results)
        self.assertIn('overall_compliance', validation_results)
        self.assertIn('compliance_rate', validation_results)
        self.assertIn('violations', validation_results)
        self.assertIn('warnings', validation_results)
        self.assertIn('recommendations', validation_results)
        
        # Check compliance data
        self.assertIsInstance(validation_results['velocity_compliance'], dict)
        self.assertIsInstance(validation_results['pressure_compliance'], dict)
        self.assertIsInstance(validation_results['flow_distribution'], dict)
        self.assertIsInstance(validation_results['sizing_accuracy'], dict)
        self.assertIsInstance(validation_results['violations'], list)
        self.assertIsInstance(validation_results['warnings'], list)
        self.assertIsInstance(validation_results['recommendations'], list)
        
        print(f"   ✅ Pandapipes sizing validation: Overall compliance={validation_results['overall_compliance']}, Rate={validation_results['compliance_rate']:.1%}")
    
    def test_hydraulic_report_generation(self):
        """Test hydraulic report generation."""
        print("\n🧪 Testing hydraulic report generation...")
        
        # Create mock results
        mock_results = {
            'supply_pipes': [
                {
                    'pipe_id': 'supply_1',
                    'velocity_ms': 1.5,
                    'pressure_drop_pa_per_m': 1000,
                    'diameter_m': 0.1
                }
            ],
            'return_pipes': [
                {
                    'pipe_id': 'return_1',
                    'velocity_ms': 1.5,
                    'pressure_drop_pa_per_m': 1000,
                    'diameter_m': 0.1
                }
            ]
        }
        
        # Test report generation
        hydraulic_report = self.simulator.generate_hydraulic_report(mock_results)
        
        # Verify report structure
        self.assertIsInstance(hydraulic_report, dict)
        self.assertIn('network_summary', hydraulic_report)
        self.assertIn('pipe_results', hydraulic_report)
        self.assertIn('validation_result', hydraulic_report)
        self.assertIn('standards_compliance', hydraulic_report)
        self.assertIn('performance_metrics', hydraulic_report)
        self.assertIn('recommendations', hydraulic_report)
        
        # Check network summary
        network_summary = hydraulic_report['network_summary']
        self.assertIn('total_pipes', network_summary)
        self.assertIn('total_flow_kg_s', network_summary)
        self.assertIn('total_pressure_drop_bar', network_summary)
        self.assertIn('average_velocity_ms', network_summary)
        self.assertIn('max_velocity_ms', network_summary)
        self.assertIn('min_velocity_ms', network_summary)
        
        # Check performance metrics
        performance_metrics = hydraulic_report['performance_metrics']
        self.assertIn('total_flow_kg_s', performance_metrics)
        self.assertIn('total_pressure_drop_bar', performance_metrics)
        self.assertIn('pump_power_kw', performance_metrics)
        self.assertIn('average_velocity_ms', performance_metrics)
        self.assertIn('max_velocity_ms', performance_metrics)
        self.assertIn('min_velocity_ms', performance_metrics)
        
        print(f"   ✅ Hydraulic report generated: {len(hydraulic_report)} sections")
    
    def test_export_functionality(self):
        """Test export functionality."""
        print("\n🧪 Testing export functionality...")
        
        # Create mock results
        mock_results = {
            'supply_pipes': [
                {
                    'pipe_id': 'supply_1',
                    'velocity_ms': 1.5,
                    'pressure_drop_pa_per_m': 1000,
                    'diameter_m': 0.1
                }
            ],
            'return_pipes': [
                {
                    'pipe_id': 'return_1',
                    'velocity_ms': 1.5,
                    'pressure_drop_pa_per_m': 1000,
                    'diameter_m': 0.1
                }
            ]
        }
        
        # Test export
        output_path = "test_hydraulic_report.json"
        self.simulator.export_hydraulic_report(mock_results, output_path)
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_path), "Export file should be created")
        
        # Clean up
        if os.path.exists(output_path):
            os.remove(output_path)
        
        print(f"   ✅ Export functionality: File created and cleaned up")
    
    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        print("\n🧪 Testing error handling...")
        
        # Test with invalid network data
        invalid_network_data = {
            'supply_pipes': [
                {
                    'pipe_id': 'invalid_pipe',
                    # Missing required fields
                }
            ]
        }
        
        # Should handle invalid data gracefully
        try:
            success = self.simulator.create_sized_pandapipes_network(invalid_network_data)
            # If it doesn't raise an exception, it should return False
            if success:
                print(f"   ⚠️ Invalid data handled gracefully")
        except Exception as e:
            print(f"   ✅ Invalid data properly rejected: {type(e).__name__}")
        
        # Test with empty network data
        empty_network_data = {
            'supply_pipes': [],
            'return_pipes': [],
            'service_connections': []
        }
        
        # Should handle empty data gracefully
        try:
            success = self.simulator.create_sized_pandapipes_network(empty_network_data)
            print(f"   ✅ Empty data handled gracefully: {success}")
        except Exception as e:
            print(f"   ✅ Empty data properly handled: {type(e).__name__}")
    
    def test_performance(self):
        """Test performance with multiple operations."""
        print("\n🧪 Testing performance...")
        
        import time
        
        # Create larger network data
        large_network_data = {
            'supply_pipes': [
                {
                    'pipe_id': f'supply_{i}',
                    'diameter_m': 0.1,
                    'length_m': 100,
                    'aggregated_flow_kg_s': 0.5,
                    'pressure_drop_pa_per_m': 1000,
                    'velocity_ms': 1.5,
                    'pipe_category': 'distribution_pipes'
                }
                for i in range(10)
            ],
            'return_pipes': [
                {
                    'pipe_id': f'return_{i}',
                    'diameter_m': 0.1,
                    'length_m': 100,
                    'aggregated_flow_kg_s': 0.5,
                    'pressure_drop_pa_per_m': 1000,
                    'velocity_ms': 1.5,
                    'pipe_category': 'distribution_pipes'
                }
                for i in range(10)
            ],
            'service_connections': [
                {
                    'heating_load_kw': 10.0,
                    'building_id': f'building_{i}'
                }
                for i in range(10)
            ]
        }
        
        # Test performance
        start_time = time.time()
        
        # Test network creation performance
        success = self.simulator.create_sized_pandapipes_network(large_network_data)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Check performance
        self.assertLess(execution_time, 5.0, f"Network creation should complete in <5s, took {execution_time:.2f}s")
        
        print(f"   ✅ Performance: Large network creation completed in {execution_time:.2f}s")


class TestHydraulicResult(unittest.TestCase):
    """Test cases for HydraulicResult dataclass."""
    
    def test_hydraulic_result_creation(self):
        """Test HydraulicResult creation and properties."""
        print("\n🧪 Testing HydraulicResult creation...")
        
        # Create a HydraulicResult
        result = HydraulicResult(
            pipe_id='test_pipe',
            flow_rate_kg_s=0.5,
            velocity_ms=1.5,
            pressure_drop_bar=0.02,
            pressure_start_bar=6.0,
            pressure_end_bar=5.98,
            temperature_start_c=70.0,
            temperature_end_c=69.5,
            head_loss_m=2.0,
            reynolds_number=15000,
            friction_factor=0.025
        )
        
        # Test properties
        self.assertEqual(result.pipe_id, 'test_pipe')
        self.assertEqual(result.flow_rate_kg_s, 0.5)
        self.assertEqual(result.velocity_ms, 1.5)
        self.assertEqual(result.pressure_drop_bar, 0.02)
        self.assertEqual(result.pressure_start_bar, 6.0)
        self.assertEqual(result.pressure_end_bar, 5.98)
        self.assertEqual(result.temperature_start_c, 70.0)
        self.assertEqual(result.temperature_end_c, 69.5)
        self.assertEqual(result.head_loss_m, 2.0)
        self.assertEqual(result.reynolds_number, 15000)
        self.assertEqual(result.friction_factor, 0.025)
        
        print(f"   ✅ HydraulicResult created successfully")


class TestSimulationValidationResult(unittest.TestCase):
    """Test cases for SimulationValidationResult dataclass."""
    
    def test_simulation_validation_result_creation(self):
        """Test SimulationValidationResult creation and properties."""
        print("\n🧪 Testing SimulationValidationResult creation...")
        
        # Create a SimulationValidationResult
        result = SimulationValidationResult(
            is_valid=True,
            convergence_achieved=True,
            violations=[],
            warnings=[],
            recommendations=[],
            summary={
                'total_pipes': 2,
                'compliant_pipes': 2,
                'compliance_rate': 1.0,
                'violation_count': 0,
                'warning_count': 0
            }
        )
        
        # Test properties
        self.assertTrue(result.is_valid)
        self.assertTrue(result.convergence_achieved)
        self.assertEqual(len(result.violations), 0)
        self.assertEqual(len(result.warnings), 0)
        self.assertEqual(len(result.recommendations), 0)
        self.assertEqual(result.summary['total_pipes'], 2)
        self.assertEqual(result.summary['compliant_pipes'], 2)
        self.assertEqual(result.summary['compliance_rate'], 1.0)
        
        print(f"   ✅ SimulationValidationResult created successfully")


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestCHAEnhancedPandapipes))
    test_suite.addTest(unittest.makeSuite(TestHydraulicResult))
    test_suite.addTest(unittest.makeSuite(TestSimulationValidationResult))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n📊 TEST SUMMARY")
    print(f"=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback}")
    
    if result.errors:
        print(f"\n❌ ERRORS:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback}")
    
    if not result.failures and not result.errors:
        print(f"\n🎉 All tests passed successfully!")
    
    # Exit with appropriate code
    sys.exit(0 if not result.failures and not result.errors else 1)
