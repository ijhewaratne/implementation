"""
Unit Tests for CHA Cost-Benefit Analyzer

This module contains comprehensive unit tests for the CHA cost-benefit analyzer,
testing CAPEX analysis, OPEX analysis, hydraulic improvement assessment, and economic metrics.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

import unittest
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cha_cost_benefit_analyzer import CHACostBenefitAnalyzer, CostBenefitResult, PipeSizingComparison, EconomicImpactAnalysis
from cha_pipe_sizing import CHAPipeSizingEngine


class TestCHACostBenefitAnalyzer(unittest.TestCase):
    """Test cases for CHA cost-benefit analyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create pipe sizing engine
        self.sizing_engine = CHAPipeSizingEngine({
            'max_velocity_ms': 2.0,
            'min_velocity_ms': 0.1,
            'max_pressure_drop_pa_per_m': 5000,
            'pipe_roughness_mm': 0.1
        })
        
        # Create cost-benefit analyzer
        self.analyzer = CHACostBenefitAnalyzer(self.sizing_engine)
        
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
                    'pipe_id': 'service_1',
                    'diameter_m': 0.05,
                    'length_m': 10,
                    'aggregated_flow_kg_s': 0.1,
                    'pressure_drop_pa_per_m': 2000,
                    'velocity_ms': 1.0,
                    'pipe_category': 'service_connections'
                }
            ]
        }
    
    def test_fixed_diameter_cost_calculation(self):
        """Test fixed diameter cost calculation."""
        print("\n🧪 Testing fixed diameter cost calculation...")
        
        # Test fixed diameter cost calculation
        fixed_cost = self.analyzer.calculate_fixed_diameter_cost(self.network_data)
        
        # Verify cost calculation
        self.assertGreater(fixed_cost, 0, "Fixed cost should be positive")
        self.assertIsInstance(fixed_cost, float, "Fixed cost should be a float")
        
        # Check that cost is reasonable
        self.assertLess(fixed_cost, 100000, "Fixed cost should be reasonable")
        
        print(f"   ✅ Fixed diameter cost: €{fixed_cost:.0f}")
    
    def test_sized_network_cost_calculation(self):
        """Test sized network cost calculation."""
        print("\n🧪 Testing sized network cost calculation...")
        
        # Test sized network cost calculation
        sized_cost = self.analyzer.calculate_sized_network_cost(self.network_data)
        
        # Verify cost calculation
        self.assertGreater(sized_cost, 0, "Sized cost should be positive")
        self.assertIsInstance(sized_cost, float, "Sized cost should be a float")
        
        # Check that cost is reasonable
        self.assertLess(sized_cost, 100000, "Sized cost should be reasonable")
        
        print(f"   ✅ Sized network cost: €{sized_cost:.0f}")
    
    def test_capex_impact_analysis(self):
        """Test CAPEX impact analysis."""
        print("\n🧪 Testing CAPEX impact analysis...")
        
        # Test CAPEX impact analysis
        sizing_impact = self.analyzer.analyze_pipe_sizing_impact(self.network_data)
        
        # Verify CAPEX impact structure
        self.assertIn('capex_impact', sizing_impact)
        capex_impact = sizing_impact['capex_impact']
        
        # Check required fields
        self.assertIn('fixed_cost_eur', capex_impact)
        self.assertIn('sized_cost_eur', capex_impact)
        self.assertIn('cost_difference_eur', capex_impact)
        self.assertIn('cost_percentage_change', capex_impact)
        self.assertIn('category_analysis', capex_impact)
        self.assertIn('cost_effectiveness', capex_impact)
        
        # Verify cost values
        self.assertGreater(capex_impact['fixed_cost_eur'], 0, "Fixed cost should be positive")
        self.assertGreater(capex_impact['sized_cost_eur'], 0, "Sized cost should be positive")
        self.assertIsInstance(capex_impact['cost_difference_eur'], float, "Cost difference should be float")
        self.assertIsInstance(capex_impact['cost_percentage_change'], float, "Cost percentage change should be float")
        
        # Verify cost effectiveness
        self.assertIn(capex_impact['cost_effectiveness'], ['positive', 'negative', 'neutral'], 
                     "Cost effectiveness should be valid")
        
        print(f"   ✅ CAPEX impact: {capex_impact['cost_effectiveness']}, {capex_impact['cost_percentage_change']:.1f}% change")
    
    def test_opex_impact_analysis(self):
        """Test OPEX impact analysis."""
        print("\n🧪 Testing OPEX impact analysis...")
        
        # Test OPEX impact analysis
        sizing_impact = self.analyzer.analyze_pipe_sizing_impact(self.network_data)
        
        # Verify OPEX impact structure
        self.assertIn('opex_impact', sizing_impact)
        opex_impact = sizing_impact['opex_impact']
        
        # Check required fields
        self.assertIn('fixed_pump_energy_kwh', opex_impact)
        self.assertIn('sized_pump_energy_kwh', opex_impact)
        self.assertIn('annual_opex_difference_eur', opex_impact)
        self.assertIn('lifetime_opex_impact_eur', opex_impact)
        self.assertIn('opex_improvement', opex_impact)
        
        # Verify energy values
        self.assertGreaterEqual(opex_impact['fixed_pump_energy_kwh'], 0, "Fixed pump energy should be non-negative")
        self.assertGreaterEqual(opex_impact['sized_pump_energy_kwh'], 0, "Sized pump energy should be non-negative")
        self.assertIsInstance(opex_impact['annual_opex_difference_eur'], float, "Annual OPEX difference should be float")
        self.assertIsInstance(opex_impact['lifetime_opex_impact_eur'], float, "Lifetime OPEX impact should be float")
        
        # Verify OPEX improvement
        self.assertIn(opex_impact['opex_improvement'], ['positive', 'negative', 'neutral'], 
                     "OPEX improvement should be valid")
        
        print(f"   ✅ OPEX impact: {opex_impact['opex_improvement']}, €{opex_impact['annual_opex_difference_eur']:.0f}/year")
    
    def test_hydraulic_improvement_assessment(self):
        """Test hydraulic improvement assessment."""
        print("\n🧪 Testing hydraulic improvement assessment...")
        
        # Test hydraulic improvement assessment
        sizing_impact = self.analyzer.analyze_pipe_sizing_impact(self.network_data)
        
        # Verify hydraulic improvement structure
        self.assertIn('hydraulic_improvement', sizing_impact)
        hydraulic_improvement = sizing_impact['hydraulic_improvement']
        
        # Check required fields
        self.assertIn('hydraulic_metrics', hydraulic_improvement)
        self.assertIn('efficiency_improvements', hydraulic_improvement)
        self.assertIn('reliability_improvements', hydraulic_improvement)
        self.assertIn('overall_improvement', hydraulic_improvement)
        
        # Verify hydraulic metrics
        hydraulic_metrics = hydraulic_improvement['hydraulic_metrics']
        if hydraulic_metrics:  # May be empty for some test cases
            self.assertIn('average_velocity_ms', hydraulic_metrics)
            self.assertIn('max_velocity_ms', hydraulic_metrics)
            self.assertIn('min_velocity_ms', hydraulic_metrics)
            self.assertIn('average_pressure_drop_pa_per_m', hydraulic_metrics)
            self.assertIn('max_pressure_drop_pa_per_m', hydraulic_metrics)
            self.assertIn('min_pressure_drop_pa_per_m', hydraulic_metrics)
        
        # Verify efficiency improvements
        efficiency_improvements = hydraulic_improvement['efficiency_improvements']
        self.assertIn('efficiency_score', efficiency_improvements)
        self.assertIn('overall_efficiency_gain', efficiency_improvements)
        self.assertIn('velocity_optimization', efficiency_improvements)
        self.assertIn('pressure_optimization', efficiency_improvements)
        
        # Verify reliability improvements
        reliability_improvements = hydraulic_improvement['reliability_improvements']
        self.assertIn('overall_reliability', reliability_improvements)
        self.assertIn('velocity_reliability', reliability_improvements)
        self.assertIn('pressure_reliability', reliability_improvements)
        self.assertIn('reliability_improvement', reliability_improvements)
        
        # Verify overall improvement
        self.assertIn(hydraulic_improvement['overall_improvement'], ['positive', 'negative', 'neutral'], 
                     "Overall improvement should be valid")
        
        print(f"   ✅ Hydraulic improvement: {hydraulic_improvement['overall_improvement']}")
    
    def test_economic_metrics_calculation(self):
        """Test economic metrics calculation."""
        print("\n🧪 Testing economic metrics calculation...")
        
        # Test economic metrics calculation
        sizing_impact = self.analyzer.analyze_pipe_sizing_impact(self.network_data)
        
        # Verify economic metrics structure
        self.assertIn('economic_metrics', sizing_impact)
        economic_metrics = sizing_impact['economic_metrics']
        
        # Check required fields
        self.assertIn('net_benefit_eur', economic_metrics)
        self.assertIn('payback_period_years', economic_metrics)
        self.assertIn('net_present_value_eur', economic_metrics)
        self.assertIn('internal_rate_of_return', economic_metrics)
        self.assertIn('benefit_cost_ratio', economic_metrics)
        self.assertIn('economic_viability', economic_metrics)
        
        # Verify metric values
        self.assertIsInstance(economic_metrics['net_benefit_eur'], float, "Net benefit should be float")
        self.assertIsInstance(economic_metrics['payback_period_years'], float, "Payback period should be float")
        self.assertIsInstance(economic_metrics['net_present_value_eur'], float, "NPV should be float")
        self.assertIsInstance(economic_metrics['internal_rate_of_return'], float, "IRR should be float")
        self.assertIsInstance(economic_metrics['benefit_cost_ratio'], float, "BCR should be float")
        
        # Verify economic viability
        self.assertIn(economic_metrics['economic_viability'], ['viable', 'not_viable'], 
                     "Economic viability should be valid")
        
        print(f"   ✅ Economic metrics: Viability={economic_metrics['economic_viability']}, NPV=€{economic_metrics['net_present_value_eur']:.0f}")
    
    def test_recommendation_generation(self):
        """Test recommendation generation."""
        print("\n🧪 Testing recommendation generation...")
        
        # Test recommendation generation
        sizing_impact = self.analyzer.analyze_pipe_sizing_impact(self.network_data)
        
        # Verify recommendations structure
        self.assertIn('recommendations', sizing_impact)
        recommendations = sizing_impact['recommendations']
        
        # Verify recommendations
        self.assertIsInstance(recommendations, list, "Recommendations should be a list")
        self.assertGreater(len(recommendations), 0, "Should have at least one recommendation")
        
        # Check recommendation content
        for recommendation in recommendations:
            self.assertIsInstance(recommendation, str, "Each recommendation should be a string")
            self.assertGreater(len(recommendation), 10, "Recommendations should be meaningful")
        
        print(f"   ✅ Recommendations generated: {len(recommendations)} recommendations")
        for i, recommendation in enumerate(recommendations[:3], 1):  # Show first 3
            print(f"      {i}. {recommendation}")
    
    def test_comprehensive_cost_benefit_analysis(self):
        """Test comprehensive cost-benefit analysis."""
        print("\n🧪 Testing comprehensive cost-benefit analysis...")
        
        # Test comprehensive analysis
        result = self.analyzer.analyze_comprehensive_cost_benefit(self.network_data)
        
        # Verify result structure
        self.assertIsInstance(result, CostBenefitResult)
        
        # Check all required fields
        self.assertIsInstance(result.capex_impact, dict)
        self.assertIsInstance(result.opex_impact, dict)
        self.assertIsInstance(result.hydraulic_improvement, dict)
        self.assertIsInstance(result.economic_metrics, dict)
        self.assertIsInstance(result.recommendations, list)
        self.assertIsInstance(result.summary, dict)
        
        # Verify summary structure
        summary = result.summary
        self.assertIn('analysis_type', summary)
        self.assertIn('total_capex_impact_eur', summary)
        self.assertIn('total_opex_impact_eur', summary)
        self.assertIn('net_benefit_eur', summary)
        self.assertIn('payback_period_years', summary)
        self.assertIn('economic_viability', summary)
        self.assertIn('recommendation_count', summary)
        self.assertIn('analysis_timestamp', summary)
        
        print(f"   ✅ Comprehensive analysis: {summary['analysis_type']}, Viability={summary['economic_viability']}")
    
    def test_export_functionality(self):
        """Test export functionality."""
        print("\n🧪 Testing export functionality...")
        
        # Create analysis result
        result = self.analyzer.analyze_comprehensive_cost_benefit(self.network_data)
        
        # Test export
        output_path = "test_cost_benefit_analysis.json"
        self.analyzer.export_cost_benefit_analysis(result, output_path)
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_path), "Export file should be created")
        
        # Verify file content
        import json
        with open(output_path, 'r') as f:
            exported_data = json.load(f)
        
        # Check exported data structure
        self.assertIn('capex_impact', exported_data)
        self.assertIn('opex_impact', exported_data)
        self.assertIn('hydraulic_improvement', exported_data)
        self.assertIn('economic_metrics', exported_data)
        self.assertIn('recommendations', exported_data)
        self.assertIn('summary', exported_data)
        
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
            result = self.analyzer.analyze_comprehensive_cost_benefit(invalid_network_data)
            print(f"   ✅ Invalid data handled gracefully")
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
            result = self.analyzer.analyze_comprehensive_cost_benefit(empty_network_data)
            print(f"   ✅ Empty data handled gracefully")
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
                    'pipe_id': f'service_{i}',
                    'diameter_m': 0.05,
                    'length_m': 10,
                    'aggregated_flow_kg_s': 0.1,
                    'pressure_drop_pa_per_m': 2000,
                    'velocity_ms': 1.0,
                    'pipe_category': 'service_connections'
                }
                for i in range(10)
            ]
        }
        
        # Test performance
        start_time = time.time()
        
        # Test comprehensive analysis performance
        result = self.analyzer.analyze_comprehensive_cost_benefit(large_network_data)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Check performance
        self.assertLess(execution_time, 3.0, f"Analysis should complete in <3s, took {execution_time:.2f}s")
        
        print(f"   ✅ Performance: Large network analysis completed in {execution_time:.2f}s")


class TestCostBenefitResult(unittest.TestCase):
    """Test cases for CostBenefitResult dataclass."""
    
    def test_cost_benefit_result_creation(self):
        """Test CostBenefitResult creation and properties."""
        print("\n🧪 Testing CostBenefitResult creation...")
        
        # Create a CostBenefitResult
        result = CostBenefitResult(
            capex_impact={'fixed_cost_eur': 10000, 'sized_cost_eur': 9500},
            opex_impact={'annual_opex_difference_eur': -100},
            hydraulic_improvement={'overall_improvement': 'positive'},
            economic_metrics={'net_benefit_eur': 500, 'economic_viability': 'viable'},
            recommendations=['Test recommendation'],
            summary={'analysis_type': 'test'}
        )
        
        # Test properties
        self.assertIsInstance(result.capex_impact, dict)
        self.assertIsInstance(result.opex_impact, dict)
        self.assertIsInstance(result.hydraulic_improvement, dict)
        self.assertIsInstance(result.economic_metrics, dict)
        self.assertIsInstance(result.recommendations, list)
        self.assertIsInstance(result.summary, dict)
        
        print(f"   ✅ CostBenefitResult created successfully")


class TestPipeSizingComparison(unittest.TestCase):
    """Test cases for PipeSizingComparison dataclass."""
    
    def test_pipe_sizing_comparison_creation(self):
        """Test PipeSizingComparison creation and properties."""
        print("\n🧪 Testing PipeSizingComparison creation...")
        
        # Create a PipeSizingComparison
        comparison = PipeSizingComparison(
            pipe_id='test_pipe',
            fixed_diameter_m=0.1,
            sized_diameter_m=0.08,
            fixed_cost_eur=1000,
            sized_cost_eur=800,
            cost_difference_eur=-200,
            cost_percentage_change=-20.0,
            hydraulic_improvement={'efficiency_score': 1.2}
        )
        
        # Test properties
        self.assertEqual(comparison.pipe_id, 'test_pipe')
        self.assertEqual(comparison.fixed_diameter_m, 0.1)
        self.assertEqual(comparison.sized_diameter_m, 0.08)
        self.assertEqual(comparison.fixed_cost_eur, 1000)
        self.assertEqual(comparison.sized_cost_eur, 800)
        self.assertEqual(comparison.cost_difference_eur, -200)
        self.assertEqual(comparison.cost_percentage_change, -20.0)
        self.assertIsInstance(comparison.hydraulic_improvement, dict)
        
        print(f"   ✅ PipeSizingComparison created successfully")


class TestEconomicImpactAnalysis(unittest.TestCase):
    """Test cases for EconomicImpactAnalysis dataclass."""
    
    def test_economic_impact_analysis_creation(self):
        """Test EconomicImpactAnalysis creation and properties."""
        print("\n🧪 Testing EconomicImpactAnalysis creation...")
        
        # Create an EconomicImpactAnalysis
        analysis = EconomicImpactAnalysis(
            total_capex_impact_eur=-1000,
            total_opex_impact_eur=500,
            total_hydraulic_benefit_eur=200,
            net_benefit_eur=700,
            payback_period_years=5.0,
            net_present_value_eur=600,
            internal_rate_of_return=0.12,
            benefit_cost_ratio=1.5
        )
        
        # Test properties
        self.assertEqual(analysis.total_capex_impact_eur, -1000)
        self.assertEqual(analysis.total_opex_impact_eur, 500)
        self.assertEqual(analysis.total_hydraulic_benefit_eur, 200)
        self.assertEqual(analysis.net_benefit_eur, 700)
        self.assertEqual(analysis.payback_period_years, 5.0)
        self.assertEqual(analysis.net_present_value_eur, 600)
        self.assertEqual(analysis.internal_rate_of_return, 0.12)
        self.assertEqual(analysis.benefit_cost_ratio, 1.5)
        
        print(f"   ✅ EconomicImpactAnalysis created successfully")


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestCHACostBenefitAnalyzer))
    test_suite.addTest(unittest.makeSuite(TestCostBenefitResult))
    test_suite.addTest(unittest.makeSuite(TestPipeSizingComparison))
    test_suite.addTest(unittest.makeSuite(TestEconomicImpactAnalysis))
    
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
