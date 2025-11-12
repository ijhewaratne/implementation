"""
Unit Tests for CHA Flow Calculation Engine

This module contains comprehensive unit tests for the CHA flow calculation engine,
testing flow rate calculation, building flow aggregation, and network flow distribution.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

import unittest
import sys
import os
from pathlib import Path
import numpy as np

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cha_flow_rate_calculator import CHAFlowRateCalculator, BuildingFlow


class TestCHAFlowCalculation(unittest.TestCase):
    """Test cases for CHA flow calculation engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock LFA data
        self.lfa_data = {
            'building_1': {
                'series': [10.0, 12.0, 8.0, 15.0, 11.0] + [10.0] * 8755,  # 8760 hours
                'building_type': 'residential',
                'area_m2': 120
            },
            'building_2': {
                'series': [20.0, 25.0, 18.0, 30.0, 22.0] + [20.0] * 8755,  # 8760 hours
                'building_type': 'commercial',
                'area_m2': 300
            },
            'building_3': {
                'series': [5.0, 6.0, 4.0, 8.0, 5.5] + [5.0] * 8755,  # 8760 hours
                'building_type': 'residential',
                'area_m2': 80
            }
        }
        
        # Create flow calculator
        self.flow_calculator = CHAFlowRateCalculator(
            lfa_data=self.lfa_data,
            cp_water=4180,  # J/kg·K
            delta_t=30,     # K (70°C - 40°C)
            safety_factor=1.1,
            diversity_factor=0.8
        )
    
    def test_building_flow_calculation(self):
        """Test building flow rate calculation."""
        print("\n🧪 Testing building flow calculation...")
        
        # Test flow calculation for building_1 at peak hour
        building_flow = self.flow_calculator.calculate_building_flow_rate('building_1', 3)  # Peak hour 3
        
        # Verify flow calculation
        self.assertIsInstance(building_flow, BuildingFlow)
        self.assertEqual(building_flow.building_id, 'building_1')
        self.assertEqual(building_flow.peak_heat_demand_kw, 15.0)  # Peak hour 3 value
        
        # Calculate expected design heat demand
        expected_design = 15.0 * 1.1 * 0.8  # peak * safety * diversity
        self.assertAlmostEqual(building_flow.design_heat_demand_kw, expected_design, places=2)
        
        # Calculate expected mass flow rate: m = Q / (cp * delta_T)
        expected_flow = (expected_design * 1000) / (4180 * 30)  # Convert kW to W
        self.assertAlmostEqual(building_flow.mass_flow_rate_kg_s, expected_flow, places=4)
        
        print(f"   ✅ Building 1: Peak {building_flow.peak_heat_demand_kw}kW → Flow {building_flow.mass_flow_rate_kg_s:.3f}kg/s")
    
    def test_all_building_flows(self):
        """Test flow calculation for all buildings."""
        print("\n🧪 Testing all building flows...")
        
        # Calculate flows for all buildings
        building_flows = self.flow_calculator.calculate_all_building_flows(peak_hour=3)
        
        # Verify all buildings are processed
        self.assertEqual(len(building_flows), 3)
        self.assertIn('building_1', building_flows)
        self.assertIn('building_2', building_flows)
        self.assertIn('building_3', building_flows)
        
        # Verify flow values are reasonable
        for building_id, flow in building_flows.items():
            self.assertGreater(flow.mass_flow_rate_kg_s, 0, f"Flow should be positive for {building_id}")
            self.assertLess(flow.mass_flow_rate_kg_s, 10.0, f"Flow should be reasonable for {building_id}")
            self.assertGreater(flow.annual_heat_demand_kwh, 0, f"Annual heat should be positive for {building_id}")
        
        # Verify building_2 has highest flow (highest peak demand)
        self.assertGreater(building_flows['building_2'].mass_flow_rate_kg_s, 
                          building_flows['building_1'].mass_flow_rate_kg_s)
        self.assertGreater(building_flows['building_1'].mass_flow_rate_kg_s, 
                          building_flows['building_3'].mass_flow_rate_kg_s)
        
        print(f"   ✅ All buildings processed: {len(building_flows)} buildings")
        for building_id, flow in building_flows.items():
            print(f"      {building_id}: {flow.mass_flow_rate_kg_s:.3f}kg/s")
    
    def test_flow_aggregation(self):
        """Test flow aggregation for pipe segments."""
        print("\n🧪 Testing flow aggregation...")
        
        # Create mock pipe segments
        pipe_segments = [
            {
                'pipe_id': 'pipe_1',
                'connected_buildings': ['building_1', 'building_2'],
                'pipe_category': 'distribution_pipe'
            },
            {
                'pipe_id': 'pipe_2',
                'connected_buildings': ['building_3'],
                'pipe_category': 'service_connection'
            }
        ]
        
        # Calculate building flows first
        building_flows = self.flow_calculator.calculate_all_building_flows(peak_hour=3)
        
        # Aggregate flows for pipe segments
        pipe_flows = self.flow_calculator.aggregate_flow_rates(pipe_segments, building_flows)
        
        # Verify aggregation
        self.assertEqual(len(pipe_flows), 2)
        
        # Check pipe_1 (should have sum of building_1 and building_2)
        pipe_1_flow = pipe_flows['pipe_1']
        expected_flow = (building_flows['building_1'].mass_flow_rate_kg_s + 
                        building_flows['building_2'].mass_flow_rate_kg_s)
        self.assertAlmostEqual(pipe_1_flow['aggregated_flow_kg_s'], expected_flow, places=4)
        
        # Check pipe_2 (should have building_3 flow)
        pipe_2_flow = pipe_flows['pipe_2']
        expected_flow = building_flows['building_3'].mass_flow_rate_kg_s
        self.assertAlmostEqual(pipe_2_flow['aggregated_flow_kg_s'], expected_flow, places=4)
        
        print(f"   ✅ Flow aggregation: Pipe 1 = {pipe_1_flow['aggregated_flow_kg_s']:.3f}kg/s, Pipe 2 = {pipe_2_flow['aggregated_flow_kg_s']:.3f}kg/s")
    
    def test_network_flow_distribution(self):
        """Test network flow distribution calculation."""
        print("\n🧪 Testing network flow distribution...")
        
        # Create mock network topology
        network_topology = {
            'nodes': {
                'plant': {'type': 'source', 'flow_kg_s': 0},
                'junction_1': {'type': 'junction', 'flow_kg_s': 0},
                'junction_2': {'type': 'junction', 'flow_kg_s': 0},
                'building_1': {'type': 'sink', 'flow_kg_s': 0.1},
                'building_2': {'type': 'sink', 'flow_kg_s': 0.2},
                'building_3': {'type': 'sink', 'flow_kg_s': 0.05}
            },
            'edges': [
                ('plant', 'junction_1'),
                ('junction_1', 'junction_2'),
                ('junction_1', 'building_1'),
                ('junction_2', 'building_2'),
                ('junction_2', 'building_3')
            ]
        }
        
        # Calculate flow distribution
        flow_distribution = self.flow_calculator.calculate_network_flow_distribution(network_topology)
        
        # Verify flow distribution
        self.assertIn('plant', flow_distribution)
        self.assertIn('junction_1', flow_distribution)
        self.assertIn('junction_2', flow_distribution)
        
        # Check that plant has total flow
        total_flow = 0.1 + 0.2 + 0.05  # Sum of all building flows
        self.assertAlmostEqual(flow_distribution['plant']['flow_kg_s'], total_flow, places=3)
        
        # Check that junction_1 has flow to building_1 and junction_2
        junction_1_flow = flow_distribution['junction_1']['flow_kg_s']
        self.assertAlmostEqual(junction_1_flow, 0.1 + 0.2 + 0.05, places=3)  # All downstream flows
        
        print(f"   ✅ Network flow distribution calculated")
        for node, data in flow_distribution.items():
            print(f"      {node}: {data['flow_kg_s']:.3f}kg/s")
    
    def test_physics_calculations(self):
        """Test physics-based flow calculations."""
        print("\n🧪 Testing physics calculations...")
        
        # Test with known values
        heat_demand_kw = 10.0  # 10 kW
        cp_water = 4180  # J/kg·K
        delta_t = 30  # K
        
        # Calculate expected mass flow rate
        expected_flow = (heat_demand_kw * 1000) / (cp_water * delta_t)  # Convert kW to W
        
        # Create test LFA data
        test_lfa_data = {
            'test_building': {
                'series': [heat_demand_kw] * 8760,
                'building_type': 'test',
                'area_m2': 100
            }
        }
        
        # Create flow calculator
        test_calculator = CHAFlowRateCalculator(
            lfa_data=test_lfa_data,
            cp_water=cp_water,
            delta_t=delta_t,
            safety_factor=1.0,  # No safety factor for exact calculation
            diversity_factor=1.0  # No diversity factor for exact calculation
        )
        
        # Calculate flow
        building_flow = test_calculator.calculate_building_flow_rate('test_building', 0)
        
        # Verify calculation
        self.assertAlmostEqual(building_flow.mass_flow_rate_kg_s, expected_flow, places=6)
        
        print(f"   ✅ Physics calculation: {heat_demand_kw}kW → {building_flow.mass_flow_rate_kg_s:.6f}kg/s (expected {expected_flow:.6f}kg/s)")
    
    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        print("\n🧪 Testing error handling...")
        
        # Test invalid building ID
        with self.assertRaises(ValueError):
            self.flow_calculator.calculate_building_flow_rate('invalid_building', 0)
        
        # Test invalid peak hour
        with self.assertRaises(ValueError):
            self.flow_calculator.calculate_building_flow_rate('building_1', 10000)  # Out of bounds
        
        # Test invalid LFA data structure
        invalid_lfa_data = {
            'invalid_building': {
                'series': 'invalid',  # Should be list
                'building_type': 'test',
                'area_m2': 100
            }
        }
        
        with self.assertRaises(ValueError):
            invalid_calculator = CHAFlowRateCalculator(invalid_lfa_data)
            invalid_calculator.calculate_building_flow_rate('invalid_building', 0)
        
        print(f"   ✅ Error handling: Proper exceptions raised for invalid inputs")
    
    def test_performance(self):
        """Test performance with large datasets."""
        print("\n🧪 Testing performance...")
        
        import time
        
        # Create large LFA dataset
        large_lfa_data = {}
        for i in range(100):
            building_id = f'building_{i}'
            large_lfa_data[building_id] = {
                'series': [10.0 + i * 0.1] * 8760,  # Varying heat demands
                'building_type': 'residential',
                'area_m2': 100 + i
            }
        
        # Create flow calculator for large dataset
        large_calculator = CHAFlowRateCalculator(large_lfa_data)
        
        # Test performance
        start_time = time.time()
        building_flows = large_calculator.calculate_all_building_flows(peak_hour=0)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Verify results
        self.assertEqual(len(building_flows), 100)
        
        # Check performance (should complete 100 buildings in reasonable time)
        self.assertLess(execution_time, 2.0, f"100 buildings should be processed in <2s, took {execution_time:.2f}s")
        
        print(f"   ✅ Performance: 100 buildings processed in {execution_time:.2f}s")


class TestBuildingFlow(unittest.TestCase):
    """Test cases for BuildingFlow dataclass."""
    
    def test_building_flow_creation(self):
        """Test BuildingFlow creation and properties."""
        print("\n🧪 Testing BuildingFlow creation...")
        
        # Create a BuildingFlow
        building_flow = BuildingFlow(
            building_id='test_building',
            peak_heat_demand_kw=15.0,
            design_heat_demand_kw=13.2,
            mass_flow_rate_kg_s=0.105,
            annual_heat_demand_kwh=87600.0
        )
        
        # Test properties
        self.assertEqual(building_flow.building_id, 'test_building')
        self.assertEqual(building_flow.peak_heat_demand_kw, 15.0)
        self.assertEqual(building_flow.design_heat_demand_kw, 13.2)
        self.assertEqual(building_flow.mass_flow_rate_kg_s, 0.105)
        self.assertEqual(building_flow.annual_heat_demand_kwh, 87600.0)
        
        print(f"   ✅ BuildingFlow created successfully")


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestCHAFlowCalculation))
    test_suite.addTest(unittest.makeSuite(TestBuildingFlow))
    
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
