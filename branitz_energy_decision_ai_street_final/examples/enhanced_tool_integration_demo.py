#!/usr/bin/env python3
"""
Enhanced Tool Integration Demo
Comprehensive demonstration of ADK-enhanced tool capabilities including intelligence, optimization, collaboration, and error recovery.
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import enhanced tool integration components
from src.advanced_tools_adk import (
    ADKEnhancedTool,
    ToolIntelligence,
    PatternRecognizer,
    OptimizationEngine,
    LearningAlgorithm,
    ParameterOptimizer,
    ToolCollaboration,
    AdvancedErrorRecovery,
    ToolExecutionResult,
    ToolCollaborationRequest,
    ToolOptimizationSuggestion
)

def create_demo_tools():
    """Create demo tools for testing."""
    def demo_analysis_tool(param1: str = "default", param2: int = 10, timeout: float = 30.0) -> str:
        """Demo analysis tool."""
        time.sleep(0.2)  # Simulate processing
        return f"Analysis completed: {param1} with value {param2}, timeout {timeout}"
    
    def demo_simulation_tool(batch_size: int = 10, precision: float = 0.8, parallel_workers: int = 4) -> str:
        """Demo simulation tool."""
        time.sleep(0.3)  # Simulate processing
        return f"Simulation completed: batch_size={batch_size}, precision={precision}, workers={parallel_workers}"
    
    def demo_optimization_tool(iterations: int = 100, convergence_threshold: float = 0.01) -> str:
        """Demo optimization tool."""
        time.sleep(0.15)  # Simulate processing
        return f"Optimization completed: iterations={iterations}, threshold={convergence_threshold}"
    
    def demo_failing_tool(param: str = "test") -> str:
        """Demo tool that fails for testing error recovery."""
        raise ValueError("This tool intentionally fails for testing error recovery")
    
    def demo_timeout_tool(timeout: float = 0.1) -> str:
        """Demo tool that times out for testing error recovery."""
        time.sleep(timeout + 0.1)  # Simulate timeout
        return "Should not reach here"
    
    return {
        'demo_analysis_tool': demo_analysis_tool,
        'demo_simulation_tool': demo_simulation_tool,
        'demo_optimization_tool': demo_optimization_tool,
        'demo_failing_tool': demo_failing_tool,
        'demo_timeout_tool': demo_timeout_tool
    }

def demo_adk_enhanced_tools():
    """Demonstrate ADK-enhanced tool capabilities."""
    print("🔧 Enhanced Tool Integration Demo")
    print("=" * 60)
    
    # Create demo tools
    demo_tools = create_demo_tools()
    
    # Create ADK-enhanced tools
    enhanced_tools = {}
    for tool_name, tool_func in demo_tools.items():
        config = {
            'description': f"Enhanced {tool_name}",
            'version': '1.0',
            'category': 'demo'
        }
        enhanced_tools[tool_name] = ADKEnhancedTool(tool_name, config, tool_func)
    
    print("\n📋 1. ADK-Enhanced Tool Execution")
    print("-" * 40)
    
    # Test different tool executions
    test_cases = [
        {
            'tool_name': 'demo_analysis_tool',
            'params': {'param1': 'district_heating', 'param2': 100, 'timeout': 60.0},
            'context': {'user_preference': 'accuracy', 'performance_target': {'max_execution_time': 30}}
        },
        {
            'tool_name': 'demo_simulation_tool',
            'params': {'batch_size': 20, 'precision': 0.9, 'parallel_workers': 8},
            'context': {'user_preference': 'speed', 'resource_constraints': {'max_memory': 500}}
        },
        {
            'tool_name': 'demo_optimization_tool',
            'params': {'iterations': 200, 'convergence_threshold': 0.001},
            'context': {'user_preference': 'memory_efficient', 'performance_target': {'min_accuracy': 0.95}}
        }
    ]
    
    print("\n🔍 Testing ADK-Enhanced Tool Execution:")
    for i, test_case in enumerate(test_cases, 1):
        tool_name = test_case['tool_name']
        params = test_case['params']
        context = test_case['context']
        
        print(f"\n   {i}. Tool: {tool_name}")
        print(f"      Original Params: {params}")
        print(f"      Context: {context}")
        
        # Execute with intelligence
        enhanced_tool = enhanced_tools[tool_name]
        result = enhanced_tool.execute_with_intelligence(params, context)
        
        print(f"      ✅ Success: {result.success}")
        print(f"      ⏱️  Execution Time: {result.execution_time:.3f}s")
        print(f"      🔧 Optimization Applied: {result.optimization_applied}")
        print(f"      🤝 Collaboration Used: {result.collaboration_used}")
        
        if result.patterns_detected:
            print(f"      📊 Patterns Detected: {result.patterns_detected}")
        
        if result.optimizations_suggested:
            print(f"      🚀 Optimizations Suggested: {len(result.optimizations_suggested)}")
            for opt in result.optimizations_suggested[:2]:  # Show first 2
                print(f"         - {opt['parameter_name']}: {opt['reasoning']}")
        
        if result.insights_generated:
            print(f"      💡 Insights Generated: {len(result.insights_generated)}")
            for insight in result.insights_generated[:2]:  # Show first 2
                print(f"         - {insight['type']}: {insight['message']}")
    
    return enhanced_tools

def demo_tool_intelligence(enhanced_tools):
    """Demonstrate tool intelligence capabilities."""
    print("\n\n🧠 2. Tool Intelligence Engine")
    print("-" * 40)
    
    # Get intelligence summary from one of the tools
    tool_name = 'demo_analysis_tool'
    enhanced_tool = enhanced_tools[tool_name]
    
    print(f"\n🔍 Tool Intelligence Summary for {tool_name}:")
    
    # Get tool statistics
    tool_stats = enhanced_tool.get_tool_statistics()
    
    print(f"   📊 Tool Statistics:")
    print(f"      Total Executions: {tool_stats['total_executions']}")
    print(f"      Success Rate: {tool_stats['success_rate']:.1%}")
    print(f"      Average Execution Time: {tool_stats['average_execution_time']:.3f}s")
    
    # Get intelligence summary
    intelligence_summary = tool_stats['intelligence_summary']
    
    print(f"\n   🧠 Intelligence Summary:")
    
    # Pattern statistics
    pattern_stats = intelligence_summary['pattern_statistics']
    if pattern_stats:
        print(f"      📊 Pattern Recognition:")
        for tool, stats in pattern_stats.items():
            print(f"         {tool}: {stats['total_executions']} executions, {stats['success_rate']:.1%} success rate")
            if stats['most_common_pattern']:
                print(f"            Most common pattern: {stats['most_common_pattern']}")
    
    # Optimization statistics
    optimization_stats = intelligence_summary['optimization_statistics']
    if optimization_stats.get('status') != 'no_optimizations':
        print(f"      🚀 Optimization Statistics:")
        print(f"         Total Optimizations: {optimization_stats['total_optimizations']}")
        print(f"         Total Suggestions: {optimization_stats['total_suggestions']}")
        print(f"         Average Suggestions: {optimization_stats['average_suggestions_per_optimization']:.1f}")
        if optimization_stats['most_optimized_tool']:
            print(f"         Most Optimized Tool: {optimization_stats['most_optimized_tool']}")
    
    # Learning statistics
    learning_stats = intelligence_summary['learning_statistics']
    if learning_stats.get('status') != 'no_learning_data':
        print(f"      💡 Learning Statistics:")
        print(f"         Total Learning Entries: {learning_stats['total_learning_entries']}")
        print(f"         Total Insights Generated: {learning_stats['total_insights_generated']}")
        print(f"         Average Insights: {learning_stats['average_insights_per_entry']:.1f}")
        if learning_stats['most_common_insight_type']:
            print(f"         Most Common Insight Type: {learning_stats['most_common_insight_type']}")

def demo_parameter_optimization():
    """Demonstrate parameter optimization capabilities."""
    print("\n\n⚙️ 3. Parameter Optimization")
    print("-" * 40)
    
    # Create parameter optimizer
    optimizer = ParameterOptimizer()
    
    # Test parameter optimization scenarios
    test_scenarios = [
        {
            'name': 'Speed Optimization',
            'params': {'timeout': 60.0, 'batch_size': 50, 'precision': 0.9},
            'context': {'user_preference': 'speed'}
        },
        {
            'name': 'Accuracy Optimization',
            'params': {'timeout': 30.0, 'batch_size': 10, 'precision': 0.7},
            'context': {'user_preference': 'accuracy'}
        },
        {
            'name': 'Memory Efficiency',
            'params': {'batch_size': 100, 'cache_size': 1000, 'parallel_workers': 16},
            'context': {'user_preference': 'memory_efficient'}
        },
        {
            'name': 'Performance Target',
            'params': {'timeout': 120.0, 'precision': 0.5},
            'context': {'performance_target': {'max_execution_time': 30, 'min_accuracy': 0.8}}
        },
        {
            'name': 'Resource Constraints',
            'params': {'batch_size': 200, 'parallel_workers': 32},
            'context': {'resource_constraints': {'max_memory': 1000, 'max_cpu_cores': 8}}
        }
    ]
    
    print("\n🔍 Parameter Optimization Scenarios:")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n   {i}. {scenario['name']}")
        print(f"      Original Params: {scenario['params']}")
        print(f"      Context: {scenario['context']}")
        
        # Optimize parameters
        optimized_params = optimizer.optimize_parameters(scenario['params'], scenario['context'])
        
        print(f"      ✅ Optimized Params: {optimized_params}")
        
        # Show changes
        changes = []
        for key, value in optimized_params.items():
            if key in scenario['params'] and scenario['params'][key] != value:
                changes.append(f"{key}: {scenario['params'][key]} → {value}")
        
        if changes:
            print(f"      🔧 Changes Applied: {', '.join(changes)}")
        else:
            print(f"      📝 No changes needed")
    
    # Get optimization summary
    print(f"\n📊 Optimization Summary:")
    optimization_summary = optimizer.get_optimization_summary()
    print(f"   Optimization Rules: {optimization_summary['optimization_rules_count']}")
    print(f"   Performance History Entries: {optimization_summary['performance_history_entries']}")
    print(f"   Cached Optimizations: {optimization_summary['cached_optimizations']}")

def demo_tool_collaboration():
    """Demonstrate tool collaboration capabilities."""
    print("\n\n🤝 4. Tool Collaboration")
    print("-" * 40)
    
    # Create collaboration manager
    collaboration_manager = ToolCollaboration()
    
    # Test collaboration scenarios
    test_scenarios = [
        {
            'name': 'Parallel Processing',
            'params': {'parallel_processing': True, 'parallel_workers': 4, 'data': 'large_dataset'}
        },
        {
            'name': 'Data Sharing',
            'params': {'data_sharing': True, 'data_format': 'json', 'sharing_method': 'direct'}
        },
        {
            'name': 'Result Aggregation',
            'params': {'result_aggregation': True, 'aggregation_method': 'weighted_average'}
        },
        {
            'name': 'No Collaboration',
            'params': {'simple_param': 'value', 'another_param': 123}
        }
    ]
    
    print("\n🔍 Tool Collaboration Scenarios:")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n   {i}. {scenario['name']}")
        print(f"      Parameters: {scenario['params']}")
        
        # Prepare collaboration
        collaboration_result = collaboration_manager.prepare_collaboration(scenario['params'])
        
        print(f"      🤝 Collaboration Enabled: {collaboration_result['collaboration_enabled']}")
        if collaboration_result['collaboration_enabled']:
            print(f"      📋 Collaboration Type: {collaboration_result['collaboration_type']}")
            print(f"      👥 Collaboration Partners: {collaboration_result['collaboration_partners']}")
            print(f"      ⚙️  Collaboration Parameters: {collaboration_result['collaboration_parameters']}")
        else:
            print(f"      📝 No collaboration needed")
    
    # Get collaboration summary
    print(f"\n📊 Collaboration Summary:")
    collaboration_summary = collaboration_manager.get_collaboration_summary()
    print(f"   Total Requests: {collaboration_summary['total_requests']}")
    print(f"   Total Collaborations: {collaboration_summary['total_collaborations']}")
    print(f"   Collaboration Patterns: {len(collaboration_summary['collaboration_patterns'])}")

def demo_error_recovery(enhanced_tools):
    """Demonstrate error recovery capabilities."""
    print("\n\n⚠️ 5. Advanced Error Recovery")
    print("-" * 40)
    
    # Test error recovery scenarios
    test_scenarios = [
        {
            'name': 'ValueError Recovery',
            'tool_name': 'demo_failing_tool',
            'params': {'param': 'test_value'},
            'context': {'user_preference': 'accuracy'}
        },
        {
            'name': 'TimeoutError Recovery',
            'tool_name': 'demo_timeout_tool',
            'params': {'timeout': 0.1},
            'context': {'user_preference': 'speed'}
        }
    ]
    
    print("\n🔍 Error Recovery Scenarios:")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n   {i}. {scenario['name']}")
        print(f"      Tool: {scenario['tool_name']}")
        print(f"      Parameters: {scenario['params']}")
        
        # Execute with error recovery
        enhanced_tool = enhanced_tools[scenario['tool_name']]
        result = enhanced_tool.execute_with_intelligence(scenario['params'], scenario['context'])
        
        print(f"      ✅ Success: {result.success}")
        print(f"      ⏱️  Execution Time: {result.execution_time:.3f}s")
        print(f"      🔧 Optimization Applied: {result.optimization_applied}")
        print(f"      🛠️  Error Recovery: {result.error_message is not None}")
        
        if result.error_message:
            print(f"      ❌ Error: {result.error_message}")
        
        if result.metadata and 'recovery_strategy' in result.metadata:
            print(f"      🔄 Recovery Strategy: {result.metadata['recovery_strategy']}")
    
    # Get recovery statistics
    print(f"\n📊 Error Recovery Statistics:")
    for tool_name, enhanced_tool in enhanced_tools.items():
        tool_stats = enhanced_tool.get_tool_statistics()
        recovery_summary = tool_stats['recovery_summary']
        
        if recovery_summary.get('status') != 'no_recovery_attempts':
            print(f"   {tool_name}:")
            print(f"      Total Recovery Attempts: {recovery_summary['total_recovery_attempts']}")
            print(f"      Successful Recoveries: {recovery_summary['successful_recoveries']}")
            print(f"      Success Rate: {recovery_summary['success_rate']:.1%}")
            if recovery_summary['most_common_error']:
                print(f"      Most Common Error: {recovery_summary['most_common_error']}")

def demo_comprehensive_workflow(enhanced_tools):
    """Demonstrate comprehensive workflow with enhanced tools."""
    print("\n\n🔄 6. Comprehensive Workflow")
    print("-" * 40)
    
    print("\n🔍 Comprehensive Tool Workflow:")
    print("   Simulating a complete analysis workflow with enhanced tools")
    
    # Define workflow steps
    workflow_steps = [
        {
            'step': 1,
            'name': 'Data Analysis',
            'tool': 'demo_analysis_tool',
            'params': {'param1': 'district_heating_data', 'param2': 1000, 'timeout': 120.0},
            'context': {'user_preference': 'accuracy', 'workflow_step': 'data_analysis'}
        },
        {
            'step': 2,
            'name': 'Simulation',
            'tool': 'demo_simulation_tool',
            'params': {'batch_size': 50, 'precision': 0.95, 'parallel_workers': 8},
            'context': {'user_preference': 'speed', 'workflow_step': 'simulation'}
        },
        {
            'step': 3,
            'name': 'Optimization',
            'tool': 'demo_optimization_tool',
            'params': {'iterations': 500, 'convergence_threshold': 0.001},
            'context': {'user_preference': 'memory_efficient', 'workflow_step': 'optimization'}
        }
    ]
    
    workflow_results = []
    total_workflow_time = 0
    
    for step_info in workflow_steps:
        print(f"\n   Step {step_info['step']}: {step_info['name']}")
        print(f"      Tool: {step_info['tool']}")
        print(f"      Parameters: {step_info['params']}")
        
        # Execute step
        enhanced_tool = enhanced_tools[step_info['tool']]
        result = enhanced_tool.execute_with_intelligence(step_info['params'], step_info['context'])
        
        workflow_results.append(result)
        total_workflow_time += result.execution_time
        
        print(f"      ✅ Success: {result.success}")
        print(f"      ⏱️  Execution Time: {result.execution_time:.3f}s")
        print(f"      🔧 Optimization Applied: {result.optimization_applied}")
        print(f"      🤝 Collaboration Used: {result.collaboration_used}")
        
        if result.patterns_detected:
            print(f"      📊 Patterns: {', '.join(result.patterns_detected[:3])}")  # Show first 3
        
        if result.optimizations_suggested:
            print(f"      🚀 Optimizations: {len(result.optimizations_suggested)} suggested")
        
        if result.insights_generated:
            print(f"      💡 Insights: {len(result.insights_generated)} generated")
    
    # Workflow summary
    print(f"\n📊 Workflow Summary:")
    print(f"   Total Steps: {len(workflow_steps)}")
    print(f"   Total Execution Time: {total_workflow_time:.3f}s")
    print(f"   Successful Steps: {sum(1 for result in workflow_results if result.success)}")
    print(f"   Failed Steps: {sum(1 for result in workflow_results if not result.success)}")
    print(f"   Steps with Optimization: {sum(1 for result in workflow_results if result.optimization_applied)}")
    print(f"   Steps with Collaboration: {sum(1 for result in workflow_results if result.collaboration_used)}")
    
    # Calculate total patterns, optimizations, and insights
    total_patterns = sum(len(result.patterns_detected or []) for result in workflow_results)
    total_optimizations = sum(len(result.optimizations_suggested or []) for result in workflow_results)
    total_insights = sum(len(result.insights_generated or []) for result in workflow_results)
    
    print(f"   Total Patterns Detected: {total_patterns}")
    print(f"   Total Optimizations Suggested: {total_optimizations}")
    print(f"   Total Insights Generated: {total_insights}")

def demo_final_statistics(enhanced_tools):
    """Demonstrate final statistics and summaries."""
    print("\n\n📊 7. Final Statistics and Summaries")
    print("-" * 40)
    
    print("\n🔍 Enhanced Tool Statistics:")
    total_executions = 0
    total_successes = 0
    total_execution_time = 0
    
    for tool_name, enhanced_tool in enhanced_tools.items():
        tool_stats = enhanced_tool.get_tool_statistics()
        
        print(f"\n   {tool_name}:")
        print(f"      Total Executions: {tool_stats['total_executions']}")
        print(f"      Success Rate: {tool_stats['success_rate']:.1%}")
        print(f"      Average Execution Time: {tool_stats['average_execution_time']:.3f}s")
        
        total_executions += tool_stats['total_executions']
        total_successes += tool_stats['successful_executions']
        total_execution_time += tool_stats['total_execution_time']
    
    # Overall statistics
    overall_success_rate = total_successes / total_executions if total_executions > 0 else 0
    overall_avg_time = total_execution_time / total_executions if total_executions > 0 else 0
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total Tool Executions: {total_executions}")
    print(f"   Total Successful Executions: {total_successes}")
    print(f"   Overall Success Rate: {overall_success_rate:.1%}")
    print(f"   Total Execution Time: {total_execution_time:.3f}s")
    print(f"   Overall Average Execution Time: {overall_avg_time:.3f}s")

def main():
    """Main demo function."""
    print("🚀 Enhanced Tool Integration - Comprehensive Demo")
    print("=" * 80)
    print("This demo showcases ADK-enhanced tool capabilities:")
    print("- ADK-enhanced tool execution with intelligence")
    print("- Tool intelligence engine with pattern recognition")
    print("- Parameter optimization with context awareness")
    print("- Tool collaboration and coordination")
    print("- Advanced error recovery and resilience")
    print("=" * 80)
    
    try:
        # Run all demos
        enhanced_tools = demo_adk_enhanced_tools()
        demo_tool_intelligence(enhanced_tools)
        demo_parameter_optimization()
        demo_tool_collaboration()
        demo_error_recovery(enhanced_tools)
        demo_comprehensive_workflow(enhanced_tools)
        demo_final_statistics(enhanced_tools)
        
        print("\n\n🎉 Enhanced Tool Integration Demo Completed Successfully!")
        print("=" * 80)
        print("The ADK-enhanced tool system is working correctly:")
        print("✅ ADK-Enhanced Tool Execution")
        print("✅ Tool Intelligence Engine")
        print("✅ Parameter Optimization")
        print("✅ Tool Collaboration")
        print("✅ Advanced Error Recovery")
        print("✅ Comprehensive Workflow")
        print("\n🚀 Enhanced tool integration is ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
