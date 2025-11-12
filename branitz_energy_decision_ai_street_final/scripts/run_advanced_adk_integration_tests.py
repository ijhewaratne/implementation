#!/usr/bin/env python3
"""
Advanced ADK Integration Test Runner
Part of Phase 6: Advanced ADK Features
"""

import sys
import os
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List

def run_test_suite(test_name: str, test_file: str, description: str) -> Dict[str, Any]:
    """Run a specific test suite and return results."""
    print(f"\n🧪 Running {test_name}")
    print(f"Description: {description}")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Run the test
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        return {
            "test_name": test_name,
            "success": result.returncode == 0,
            "execution_time": execution_time,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            "test_name": test_name,
            "success": False,
            "execution_time": 300,
            "stdout": "",
            "stderr": "Test timed out after 5 minutes",
            "return_code": -1
        }
    except Exception as e:
        return {
            "test_name": test_name,
            "success": False,
            "execution_time": 0,
            "stdout": "",
            "stderr": str(e),
            "return_code": -1
        }

def run_all_integration_tests():
    """Run all advanced ADK integration tests."""
    print("🚀 Advanced ADK Integration Test Suite")
    print("=" * 80)
    print("This test suite validates the integration of all advanced ADK features:")
    print("- Advanced Agent Capabilities (memory, context, learning)")
    print("- Enhanced Tool Integration (orchestration, monitoring, intelligence)")
    print("- Analytics and Monitoring (performance, usage, dashboards)")
    print("- End-to-End Workflows (complete system integration)")
    print("=" * 80)
    
    # Define test suites
    test_suites = [
        {
            "name": "Advanced ADK Integration Tests",
            "file": "tests/test_advanced_adk_integration.py",
            "description": "Comprehensive integration tests for all advanced ADK features"
        }
    ]
    
    # Run tests
    results = []
    total_start_time = time.time()
    
    for test_suite in test_suites:
        test_file_path = Path(__file__).parent.parent / test_suite["file"]
        
        if not test_file_path.exists():
            print(f"❌ Test file not found: {test_file_path}")
            continue
        
        result = run_test_suite(
            test_suite["name"],
            str(test_file_path),
            test_suite["description"]
        )
        results.append(result)
    
    total_end_time = time.time()
    total_execution_time = total_end_time - total_start_time
    
    # Print results
    print("\n" + "=" * 80)
    print("INTEGRATION TEST RESULTS")
    print("=" * 80)
    
    successful_tests = 0
    failed_tests = 0
    
    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"\n{status} {result['test_name']}")
        print(f"   Execution Time: {result['execution_time']:.2f} seconds")
        print(f"   Return Code: {result['return_code']}")
        
        if result["success"]:
            successful_tests += 1
        else:
            failed_tests += 1
            
            # Print error details
            if result["stderr"]:
                print(f"   Error: {result['stderr']}")
            
            # Print last few lines of output for context
            if result["stdout"]:
                lines = result["stdout"].split('\n')
                if len(lines) > 10:
                    print("   Last 10 lines of output:")
                    for line in lines[-10:]:
                        if line.strip():
                            print(f"     {line}")
                else:
                    print("   Output:")
                    for line in lines:
                        if line.strip():
                            print(f"     {line}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(results)}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(successful_tests / len(results) * 100):.1f}%")
    print(f"Total Execution Time: {total_execution_time:.2f} seconds")
    
    # Overall result
    if failed_tests == 0:
        print("\n🎉 All integration tests passed!")
        print("✅ Advanced ADK features are properly integrated and working correctly!")
        return True
    else:
        print(f"\n❌ {failed_tests} integration test(s) failed!")
        print("🔧 Please review the errors above and fix the issues.")
        return False

def run_individual_component_tests():
    """Run individual component tests to verify each advanced ADK feature."""
    print("\n🔍 Running Individual Component Tests")
    print("=" * 60)
    
    component_tests = [
        {
            "name": "Advanced Agent Capabilities Demo",
            "file": "examples/advanced_agent_capabilities_demo.py",
            "description": "Test advanced agent memory, context, and learning capabilities"
        },
        {
            "name": "Advanced Tool Chaining Demo",
            "file": "examples/advanced_tool_chaining_demo.py",
            "description": "Test advanced tool orchestration and workflow management"
        },
        {
            "name": "ADK Tool Monitoring Demo",
            "file": "examples/adk_tool_monitoring_demo.py",
            "description": "Test tool monitoring and analytics capabilities"
        },
        {
            "name": "ADK Agent Performance Monitoring Demo",
            "file": "examples/adk_agent_performance_monitoring_demo.py",
            "description": "Test agent performance monitoring and optimization"
        },
        {
            "name": "ADK Usage Analytics Demo",
            "file": "examples/adk_usage_analytics_demo.py",
            "description": "Test usage analytics and behavioral insights"
        },
        {
            "name": "ADK Dashboards Demo",
            "file": "examples/adk_dashboards_demo.py",
            "description": "Test dashboard functionality and HTML rendering"
        }
    ]
    
    results = []
    
    for test in component_tests:
        test_file_path = Path(__file__).parent.parent / test["file"]
        
        if not test_file_path.exists():
            print(f"⚠️  Demo file not found: {test_file_path}")
            continue
        
        print(f"\n🧪 Running {test['name']}")
        print(f"Description: {test['description']}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [sys.executable, str(test_file_path)],
                capture_output=True,
                text=True,
                timeout=180  # 3 minute timeout
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            success = result.returncode == 0
            status = "✅ PASSED" if success else "❌ FAILED"
            
            print(f"{status} - Execution Time: {execution_time:.2f}s")
            
            results.append({
                "name": test["name"],
                "success": success,
                "execution_time": execution_time,
                "return_code": result.returncode
            })
            
        except subprocess.TimeoutExpired:
            print("❌ FAILED - Timeout after 3 minutes")
            results.append({
                "name": test["name"],
                "success": False,
                "execution_time": 180,
                "return_code": -1
            })
        except Exception as e:
            print(f"❌ FAILED - Error: {e}")
            results.append({
                "name": test["name"],
                "success": False,
                "execution_time": 0,
                "return_code": -1
            })
    
    # Print component test summary
    print("\n" + "=" * 60)
    print("COMPONENT TEST SUMMARY")
    print("=" * 60)
    
    successful_components = sum(1 for r in results if r["success"])
    failed_components = len(results) - successful_components
    
    print(f"Total Components: {len(results)}")
    print(f"Successful: {successful_components}")
    print(f"Failed: {failed_components}")
    print(f"Success Rate: {(successful_components / len(results) * 100):.1f}%")
    
    if failed_components == 0:
        print("\n🎉 All component tests passed!")
    else:
        print(f"\n❌ {failed_components} component test(s) failed!")
    
    return successful_components == len(results)

def main():
    """Main test runner function."""
    print("🚀 Advanced ADK Integration Test Runner")
    print("=" * 80)
    
    # Check if we're in the right directory
    if not Path("src").exists() or not Path("tests").exists():
        print("❌ Error: Please run this script from the project root directory")
        return 1
    
    try:
        # Run individual component tests first
        component_success = run_individual_component_tests()
        
        # Run comprehensive integration tests
        integration_success = run_all_integration_tests()
        
        # Overall result
        print("\n" + "=" * 80)
        print("OVERALL TEST RESULTS")
        print("=" * 80)
        
        if component_success and integration_success:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Advanced ADK features are fully integrated and production-ready!")
            return 0
        else:
            print("❌ SOME TESTS FAILED!")
            print("🔧 Please review the failures above and fix the issues.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
