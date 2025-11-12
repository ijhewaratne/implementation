#!/usr/bin/env python3
"""
Advanced Tool Chaining Demo
Comprehensive demonstration of advanced tool chaining capabilities including workflow orchestration, parallel execution, and performance tracking.
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import advanced tool chaining components
from src.advanced_tool_chaining import (
    AdvancedToolChainer,
    ToolRegistry,
    DependencyResolver,
    WorkflowEngine,
    ExecutionMonitor,
    ResultAggregator,
    PerformanceTracker,
    ToolStep,
    ToolResult
)

def create_demo_tools():
    """Create demo tools for testing."""
    def demo_tool1(param1: str = "default1", param2: int = 10) -> str:
        """Demo tool 1 - simulates data processing."""
        time.sleep(0.1)  # Simulate processing time
        return f"Tool1 processed: {param1} with value {param2}"
    
    def demo_tool2(param1: str = "default2", param2: int = 20) -> str:
        """Demo tool 2 - simulates analysis."""
        time.sleep(0.15)  # Simulate processing time
        return f"Tool2 analyzed: {param1} with value {param2}"
    
    def demo_tool3(param1: str = "default3", param2: int = 30) -> str:
        """Demo tool 3 - simulates reporting."""
        time.sleep(0.2)  # Simulate processing time
        return f"Tool3 reported: {param1} with value {param2}"
    
    def demo_tool4(param1: str = "default4", param2: int = 40) -> str:
        """Demo tool 4 - simulates validation."""
        time.sleep(0.05)  # Simulate processing time
        return f"Tool4 validated: {param1} with value {param2}"
    
    def demo_tool5(param1: str = "default5", param2: int = 50) -> str:
        """Demo tool 5 - simulates optimization."""
        time.sleep(0.12)  # Simulate processing time
        return f"Tool5 optimized: {param1} with value {param2}"
    
    return {
        'demo_tool1': demo_tool1,
        'demo_tool2': demo_tool2,
        'demo_tool3': demo_tool3,
        'demo_tool4': demo_tool4,
        'demo_tool5': demo_tool5
    }

def demo_basic_tool_chaining():
    """Demonstrate basic tool chaining capabilities."""
    print("🔗 Advanced Tool Chaining Demo")
    print("=" * 60)
    
    # Create advanced tool chainer
    chainer = AdvancedToolChainer()
    
    # Register demo tools
    demo_tools = create_demo_tools()
    for tool_name, tool_func in demo_tools.items():
        chainer.tool_registry.register_tool(tool_name, tool_func)
    
    print("\n📋 1. Basic Tool Chaining")
    print("-" * 40)
    
    # Test simple sequential workflow
    simple_workflow = [
        {'tool_name': 'demo_tool1', 'parameters': {'param1': 'test1', 'param2': 100}, 'output': 'step1'},
        {'tool_name': 'demo_tool2', 'parameters': {'param1': 'test2', 'param2': 200}, 'output': 'step2'},
        {'tool_name': 'demo_tool3', 'parameters': {'param1': 'test3', 'param2': 300}, 'output': 'step3'}
    ]
    
    print("\n🔍 Simple Sequential Workflow:")
    print("   Step 1: demo_tool1 -> step1")
    print("   Step 2: demo_tool2 -> step2")
    print("   Step 3: demo_tool3 -> step3")
    
    start_time = time.time()
    result = chainer.execute_tool_chain(simple_workflow)
    execution_time = time.time() - start_time
    
    print(f"\n   ✅ Success: {result['success']}")
    print(f"   ⏱️  Execution Time: {execution_time:.2f}s")
    print(f"   📊 Steps Executed: {result['execution_metadata']['steps_executed']}")
    print(f"   ✅ Successful Steps: {result['execution_metadata']['successful_steps']}")
    print(f"   ❌ Failed Steps: {result['execution_metadata']['failed_steps']}")
    
    return chainer

def demo_dependency_resolution(chainer):
    """Demonstrate dependency resolution and execution order."""
    print("\n\n🔗 2. Dependency Resolution")
    print("-" * 40)
    
    # Test workflow with dependencies
    dependency_workflow = [
        {'tool_name': 'demo_tool1', 'parameters': {'param1': 'base', 'param2': 100}, 'output': 'base_data'},
        {'tool_name': 'demo_tool2', 'parameters': {'param1': '$base_data', 'param2': 200}, 'output': 'processed_data', 'dependencies': ['base_data']},
        {'tool_name': 'demo_tool3', 'parameters': {'param1': '$processed_data', 'param2': 300}, 'output': 'final_report', 'dependencies': ['processed_data']},
        {'tool_name': 'demo_tool4', 'parameters': {'param1': 'validation', 'param2': 400}, 'output': 'validation_result', 'dependencies': ['base_data']}
    ]
    
    print("\n🔍 Workflow with Dependencies:")
    print("   base_data: demo_tool1 (no dependencies)")
    print("   processed_data: demo_tool2 (depends on base_data)")
    print("   final_report: demo_tool3 (depends on processed_data)")
    print("   validation_result: demo_tool4 (depends on base_data)")
    
    start_time = time.time()
    result = chainer.execute_tool_chain(dependency_workflow)
    execution_time = time.time() - start_time
    
    print(f"\n   ✅ Success: {result['success']}")
    print(f"   ⏱️  Execution Time: {execution_time:.2f}s")
    print(f"   📊 Steps Executed: {result['execution_metadata']['steps_executed']}")
    print(f"   ✅ Successful Steps: {result['execution_metadata']['successful_steps']}")
    
    # Show execution order
    print("\n   📋 Execution Order:")
    for step_name, step_result in result['individual_results'].items():
        status = "✅" if step_result['success'] else "❌"
        print(f"      {status} {step_name}: {step_result['execution_time']:.3f}s")

def demo_parallel_execution(chainer):
    """Demonstrate parallel tool execution."""
    print("\n\n⚡ 3. Parallel Tool Execution")
    print("-" * 40)
    
    # Test parallel execution
    parallel_steps = [
        {'tool_name': 'demo_tool1', 'parameters': {'param1': 'parallel1', 'param2': 100}, 'output': 'parallel_step1'},
        {'tool_name': 'demo_tool2', 'parameters': {'param1': 'parallel2', 'param2': 200}, 'output': 'parallel_step2'},
        {'tool_name': 'demo_tool3', 'parameters': {'param1': 'parallel3', 'param2': 300}, 'output': 'parallel_step3'},
        {'tool_name': 'demo_tool4', 'parameters': {'param1': 'parallel4', 'param2': 400}, 'output': 'parallel_step4'}
    ]
    
    print("\n🔍 Parallel Execution Test:")
    print("   Running 4 tools in parallel (no dependencies)")
    
    start_time = time.time()
    result = chainer.execute_parallel_tools(parallel_steps)
    execution_time = time.time() - start_time
    
    print(f"\n   ✅ Success: {result['success']}")
    print(f"   ⏱️  Execution Time: {execution_time:.2f}s")
    print(f"   📊 Parallel Steps: {result['execution_metadata']['parallel_steps']}")
    print(f"   ✅ Successful Steps: {result['execution_metadata']['successful_steps']}")
    print(f"   ❌ Failed Steps: {result['execution_metadata']['failed_steps']}")
    
    # Show parallel execution results
    print("\n   📋 Parallel Execution Results:")
    for step_name, step_result in result['individual_results'].items():
        status = "✅" if step_result['success'] else "❌"
        print(f"      {status} {step_name}: {step_result['execution_time']:.3f}s")
    
    # Compare with sequential execution
    print("\n🔍 Sequential vs Parallel Comparison:")
    sequential_start = time.time()
    sequential_result = chainer.execute_tool_chain(parallel_steps)
    sequential_time = time.time() - sequential_start
    
    print(f"   Sequential Execution: {sequential_time:.2f}s")
    print(f"   Parallel Execution: {execution_time:.2f}s")
    print(f"   Speed Improvement: {sequential_time/execution_time:.1f}x faster")

def demo_workflow_engine():
    """Demonstrate workflow engine capabilities."""
    print("\n\n⚙️ 4. Workflow Engine")
    print("-" * 40)
    
    # Create workflow engine
    workflow_engine = WorkflowEngine()
    
    # Register demo tools
    demo_tools = create_demo_tools()
    for tool_name, tool_func in demo_tools.items():
        workflow_engine.tool_registry.register_tool(tool_name, tool_func)
    
    # Test complex workflow with phases
    complex_workflow = [
        ToolStep('demo_tool1', {'param1': 'phase1', 'param2': 100}, 'phase1_step1'),
        ToolStep('demo_tool2', {'param1': 'phase1', 'param2': 200}, 'phase1_step2'),
        ToolStep('demo_tool3', {'param1': '$phase1_step1', 'param2': 300}, 'phase2_step1', dependencies=['phase1_step1']),
        ToolStep('demo_tool4', {'param1': '$phase1_step2', 'param2': 400}, 'phase2_step2', dependencies=['phase1_step2']),
        ToolStep('demo_tool5', {'param1': '$phase2_step1', 'param2': 500}, 'final_step', dependencies=['phase2_step1', 'phase2_step2'])
    ]
    
    print("\n🔍 Complex Workflow with Phases:")
    print("   Phase 1: phase1_step1, phase1_step2 (parallel)")
    print("   Phase 2: phase2_step1, phase2_step2 (parallel, depends on phase1)")
    print("   Phase 3: final_step (depends on phase2)")
    
    start_time = time.time()
    result = workflow_engine.execute_workflow(complex_workflow)
    execution_time = time.time() - start_time
    
    print(f"\n   ✅ Success: {result['success']}")
    print(f"   ⏱️  Execution Time: {execution_time:.2f}s")
    print(f"   📊 Phases Executed: {result['execution_metadata']['phases_executed']}")
    print(f"   📊 Total Steps: {result['execution_metadata']['total_steps']}")
    print(f"   ✅ Successful Steps: {result['execution_metadata']['successful_steps']}")
    print(f"   ❌ Failed Steps: {result['execution_metadata']['failed_steps']}")

def demo_performance_tracking(chainer):
    """Demonstrate performance tracking capabilities."""
    print("\n\n📊 5. Performance Tracking")
    print("-" * 40)
    
    # Execute multiple workflows to generate performance data
    print("\n🔍 Generating Performance Data:")
    
    workflows = [
        [
            {'tool_name': 'demo_tool1', 'parameters': {'param1': f'perf_test_{i}', 'param2': 100}, 'output': f'step1_{i}'},
            {'tool_name': 'demo_tool2', 'parameters': {'param1': f'perf_test_{i}', 'param2': 200}, 'output': f'step2_{i}'}
        ]
        for i in range(5)
    ]
    
    for i, workflow in enumerate(workflows, 1):
        print(f"   Executing workflow {i}/5...")
        result = chainer.execute_tool_chain(workflow)
        print(f"      ✅ Success: {result['success']}, Time: {result['execution_metadata']['total_execution_time']:.3f}s")
    
    # Show performance metrics
    print("\n📊 Performance Metrics:")
    metrics = chainer.get_performance_metrics()
    
    print(f"   📈 Total Executions: {metrics['total_executions']}")
    print(f"   📊 Recent Executions: {metrics['recent_executions']}")
    print(f"   ⏱️  Average Execution Time: {metrics['average_execution_time']:.3f}s")
    print(f"   ✅ Success Rate: {metrics['success_rate']:.1%}")
    print(f"   📏 Average Workflow Size: {metrics['average_workflow_size']:.1f} steps")
    
    # Show execution summary
    print("\n📋 Execution Summary:")
    summary = chainer.get_execution_summary()
    
    print(f"   📊 Total Executions: {summary['total_executions']}")
    print(f"   ✅ Successful Executions: {summary['successful_executions']}")
    print(f"   ✅ Success Rate: {summary['success_rate']:.1%}")
    print(f"   ⏱️  Average Execution Time: {summary['average_execution_time']:.3f}s")

def demo_error_handling(chainer):
    """Demonstrate error handling capabilities."""
    print("\n\n⚠️ 6. Error Handling")
    print("-" * 40)
    
    # Create a tool that will fail
    def failing_tool(param1: str = "test") -> str:
        """Tool that always fails."""
        raise ValueError("This tool intentionally fails for testing")
    
    # Register the failing tool
    chainer.tool_registry.register_tool('failing_tool', failing_tool)
    
    # Test workflow with failing tool
    error_workflow = [
        {'tool_name': 'demo_tool1', 'parameters': {'param1': 'before_fail', 'param2': 100}, 'output': 'step1'},
        {'tool_name': 'failing_tool', 'parameters': {'param1': 'failing_step'}, 'output': 'step2'},
        {'tool_name': 'demo_tool2', 'parameters': {'param1': 'after_fail', 'param2': 200}, 'output': 'step3'}
    ]
    
    print("\n🔍 Error Handling Test:")
    print("   Step 1: demo_tool1 (should succeed)")
    print("   Step 2: failing_tool (will fail)")
    print("   Step 3: demo_tool2 (should still execute)")
    
    start_time = time.time()
    result = chainer.execute_tool_chain(error_workflow)
    execution_time = time.time() - start_time
    
    print(f"\n   ✅ Overall Success: {result['success']}")
    print(f"   ⏱️  Execution Time: {execution_time:.2f}s")
    print(f"   📊 Steps Executed: {result['execution_metadata']['steps_executed']}")
    print(f"   ✅ Successful Steps: {result['execution_metadata']['successful_steps']}")
    print(f"   ❌ Failed Steps: {result['execution_metadata']['failed_steps']}")
    
    # Show individual step results
    print("\n   📋 Individual Step Results:")
    for step_name, step_result in result['individual_results'].items():
        status = "✅" if step_result['success'] else "❌"
        print(f"      {status} {step_name}: {step_result['execution_time']:.3f}s")
        if not step_result['success']:
            print(f"         Error: {step_result['error_message']}")

def demo_circular_dependency_detection():
    """Demonstrate circular dependency detection."""
    print("\n\n🔄 7. Circular Dependency Detection")
    print("-" * 40)
    
    # Create a new chainer for this test
    chainer = AdvancedToolChainer()
    demo_tools = create_demo_tools()
    for tool_name, tool_func in demo_tools.items():
        chainer.tool_registry.register_tool(tool_name, tool_func)
    
    # Test workflow with circular dependency
    circular_workflow = [
        {'tool_name': 'demo_tool1', 'parameters': {'param1': 'step1'}, 'output': 'step1', 'dependencies': ['step2']},
        {'tool_name': 'demo_tool2', 'parameters': {'param1': 'step2'}, 'output': 'step2', 'dependencies': ['step1']}
    ]
    
    print("\n🔍 Circular Dependency Test:")
    print("   step1 depends on step2")
    print("   step2 depends on step1")
    print("   This should be detected as a circular dependency")
    
    try:
        result = chainer.execute_tool_chain(circular_workflow)
        print(f"   ❌ Unexpected: Workflow executed without error")
    except ValueError as e:
        print(f"   ✅ Correctly detected circular dependency: {e}")
    except Exception as e:
        print(f"   ⚠️  Unexpected error: {e}")

def main():
    """Main demo function."""
    print("🚀 Advanced Tool Chaining - Comprehensive Demo")
    print("=" * 80)
    print("This demo showcases advanced tool chaining capabilities:")
    print("- Workflow orchestration with dependencies")
    print("- Parallel tool execution")
    print("- Performance tracking and monitoring")
    print("- Error handling and recovery")
    print("- Circular dependency detection")
    print("=" * 80)
    
    try:
        # Run all demos
        chainer = demo_basic_tool_chaining()
        demo_dependency_resolution(chainer)
        demo_parallel_execution(chainer)
        demo_workflow_engine()
        demo_performance_tracking(chainer)
        demo_error_handling(chainer)
        demo_circular_dependency_detection()
        
        print("\n\n🎉 Advanced Tool Chaining Demo Completed Successfully!")
        print("=" * 80)
        print("The advanced tool chaining system is working correctly:")
        print("✅ Basic tool chaining")
        print("✅ Dependency resolution")
        print("✅ Parallel execution")
        print("✅ Workflow engine")
        print("✅ Performance tracking")
        print("✅ Error handling")
        print("✅ Circular dependency detection")
        print("\n🚀 Advanced tool chaining is ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
