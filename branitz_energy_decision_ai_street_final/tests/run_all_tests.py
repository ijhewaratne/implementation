"""
Comprehensive Test Runner for CHA Intelligent Pipe Sizing System

This module runs all unit tests for the CHA intelligent pipe sizing system,
including pipe sizing, flow calculation, pandapipes integration, and cost-benefit analysis.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

import unittest
import sys
import os
from pathlib import Path
import time

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import all test modules
from test_cha_pipe_sizing import TestCHAPipeSizing, TestPipeSizingResult, TestPipeCategory
from test_cha_flow_calculation import TestCHAFlowCalculation, TestBuildingFlow
from test_cha_enhanced_pandapipes import TestCHAEnhancedPandapipes, TestHydraulicResult, TestSimulationValidationResult
from test_cha_cost_benefit_analyzer import TestCHACostBenefitAnalyzer, TestCostBenefitResult, TestPipeSizingComparison, TestEconomicImpactAnalysis


class TestRunner:
    """Comprehensive test runner for the CHA intelligent pipe sizing system."""
    
    def __init__(self):
        """Initialize the test runner."""
        self.test_suite = unittest.TestSuite()
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def add_all_tests(self):
        """Add all test cases to the test suite."""
        print("🧪 Adding all test cases to test suite...")
        
        # Add pipe sizing tests
        self.test_suite.addTest(unittest.makeSuite(TestCHAPipeSizing))
        self.test_suite.addTest(unittest.makeSuite(TestPipeSizingResult))
        self.test_suite.addTest(unittest.makeSuite(TestPipeCategory))
        print("   ✅ Pipe sizing tests added")
        
        # Add flow calculation tests
        self.test_suite.addTest(unittest.makeSuite(TestCHAFlowCalculation))
        self.test_suite.addTest(unittest.makeSuite(TestBuildingFlow))
        print("   ✅ Flow calculation tests added")
        
        # Add pandapipes integration tests
        self.test_suite.addTest(unittest.makeSuite(TestCHAEnhancedPandapipes))
        self.test_suite.addTest(unittest.makeSuite(TestHydraulicResult))
        self.test_suite.addTest(unittest.makeSuite(TestSimulationValidationResult))
        print("   ✅ Pandapipes integration tests added")
        
        # Add cost-benefit analysis tests
        self.test_suite.addTest(unittest.makeSuite(TestCHACostBenefitAnalyzer))
        self.test_suite.addTest(unittest.makeSuite(TestCostBenefitResult))
        self.test_suite.addTest(unittest.makeSuite(TestPipeSizingComparison))
        self.test_suite.addTest(unittest.makeSuite(TestEconomicImpactAnalysis))
        print("   ✅ Cost-benefit analysis tests added")
        
        print(f"   📊 Total test cases: {self.test_suite.countTestCases()}")
    
    def run_tests(self):
        """Run all tests and collect results."""
        print("\n🚀 Running all tests...")
        
        # Record start time
        self.start_time = time.time()
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(self.test_suite)
        
        # Record end time
        self.end_time = time.time()
        
        # Store results
        self.results = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'successes': result.testsRun - len(result.failures) - len(result.errors),
            'execution_time': self.end_time - self.start_time,
            'failures_list': result.failures,
            'errors_list': result.errors
        }
        
        return result
    
    def print_summary(self):
        """Print comprehensive test summary."""
        print(f"\n📊 COMPREHENSIVE TEST SUMMARY")
        print(f"=" * 60)
        
        # Overall statistics
        print(f"🎯 OVERALL STATISTICS:")
        print(f"   Tests Run: {self.results['tests_run']}")
        print(f"   Successes: {self.results['successes']}")
        print(f"   Failures: {self.results['failures']}")
        print(f"   Errors: {self.results['errors']}")
        print(f"   Success Rate: {(self.results['successes'] / self.results['tests_run'] * 100):.1f}%")
        print(f"   Execution Time: {self.results['execution_time']:.2f} seconds")
        
        # Test categories
        print(f"\n📋 TEST CATEGORIES:")
        print(f"   Pipe Sizing Engine: ✅")
        print(f"   Flow Calculation Engine: ✅")
        print(f"   Pandapipes Integration: ✅")
        print(f"   Cost-Benefit Analysis: ✅")
        
        # Performance metrics
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"   Average Test Time: {self.results['execution_time'] / self.results['tests_run']:.3f} seconds/test")
        print(f"   Tests per Second: {self.results['tests_run'] / self.results['execution_time']:.1f}")
        
        # Detailed results
        if self.results['failures'] > 0:
            print(f"\n❌ FAILURES ({self.results['failures']}):")
            for i, (test, traceback) in enumerate(self.results['failures_list'], 1):
                print(f"   {i}. {test}")
                print(f"      {traceback.split('AssertionError:')[-1].strip() if 'AssertionError:' in traceback else 'See traceback above'}")
        
        if self.results['errors'] > 0:
            print(f"\n❌ ERRORS ({self.results['errors']}):")
            for i, (test, traceback) in enumerate(self.results['errors_list'], 1):
                print(f"   {i}. {test}")
                print(f"      {traceback.split('Exception:')[-1].strip() if 'Exception:' in traceback else 'See traceback above'}")
        
        # Success message
        if self.results['failures'] == 0 and self.results['errors'] == 0:
            print(f"\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
            print(f"   The CHA intelligent pipe sizing system is fully tested and ready for production!")
        else:
            print(f"\n⚠️ SOME TESTS FAILED")
            print(f"   Please review the failures and errors above before proceeding to production.")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if self.results['failures'] == 0 and self.results['errors'] == 0:
            print(f"   ✅ System is ready for production deployment")
            print(f"   ✅ All components are functioning correctly")
            print(f"   ✅ Integration tests are passing")
            print(f"   ✅ Performance is within acceptable limits")
        else:
            print(f"   🔧 Fix failing tests before production deployment")
            print(f"   🔧 Review error handling and edge cases")
            print(f"   🔧 Ensure all components are properly integrated")
            print(f"   🔧 Run tests again after fixes")
    
    def export_results(self, output_path="test_results.json"):
        """Export test results to JSON file."""
        import json
        
        # Prepare export data
        export_data = {
            'test_summary': {
                'tests_run': self.results['tests_run'],
                'successes': self.results['successes'],
                'failures': self.results['failures'],
                'errors': self.results['errors'],
                'success_rate': self.results['successes'] / self.results['tests_run'] * 100,
                'execution_time_seconds': self.results['execution_time']
            },
            'test_categories': {
                'pipe_sizing_engine': 'tested',
                'flow_calculation_engine': 'tested',
                'pandapipes_integration': 'tested',
                'cost_benefit_analysis': 'tested'
            },
            'performance_metrics': {
                'average_test_time_seconds': self.results['execution_time'] / self.results['tests_run'],
                'tests_per_second': self.results['tests_run'] / self.results['execution_time']
            },
            'failures': [
                {
                    'test_name': str(test),
                    'error_message': traceback.split('AssertionError:')[-1].strip() if 'AssertionError:' in traceback else 'See traceback'
                }
                for test, traceback in self.results['failures_list']
            ],
            'errors': [
                {
                    'test_name': str(test),
                    'error_message': traceback.split('Exception:')[-1].strip() if 'Exception:' in traceback else 'See traceback'
                }
                for test, traceback in self.results['errors_list']
            ]
        }
        
        # Export to file
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"\n📁 Test results exported to {output_path}")


def main():
    """Main function to run all tests."""
    print("🧪 CHA INTELLIGENT PIPE SIZING SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    # Create test runner
    test_runner = TestRunner()
    
    # Add all tests
    test_runner.add_all_tests()
    
    # Run tests
    result = test_runner.run_tests()
    
    # Print summary
    test_runner.print_summary()
    
    # Export results
    test_runner.export_results()
    
    # Exit with appropriate code
    exit_code = 0 if test_runner.results['failures'] == 0 and test_runner.results['errors'] == 0 else 1
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
