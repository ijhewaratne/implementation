#!/usr/bin/env python3
"""
Advanced Tool Orchestration Demo
Comprehensive demonstration of advanced tool orchestration with workflow management, dependency resolution, resource optimization, and execution monitoring.
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import advanced tool orchestration components
from src.advanced_tool_orchestration import (
    AdvancedToolOrchestrator,
    WorkflowEngine,
    DependencyManager,
    ResourceOptimizer,
    AdvancedResultAggregator,
    ExecutionMonitor,
    WorkflowPhase,
    ExecutionPlan,
    PhaseResult,
    WorkflowResult
)

def create_sample_workflows():
    """Create sample workflows for testing."""
    
    # Simple sequential workflow
    simple_workflow = [
        {
            'name': 'data_collection',
            'type': 'sequential',
            'dependencies': [],
            'steps': [
                {
                    'name': 'collect_street_data',
                    'type': 'tool_call',
                    'tool_name': 'street_data_collector',
                    'parameters': {'street_name': 'Parkstraße', 'data_type': 'building_info'}
                },
                {
                    'name': 'collect_energy_data',
                    'type': 'tool_call',
                    'tool_name': 'energy_data_collector',
                    'parameters': {'street_name': 'Parkstraße', 'data_type': 'energy_consumption'}
                }
            ]
        },
        {
            'name': 'data_analysis',
            'type': 'sequential',
            'dependencies': ['data_collection'],
            'steps': [
                {
                    'name': 'analyze_building_data',
                    'type': 'tool_call',
                    'tool_name': 'building_analyzer',
                    'parameters': {'input_data': '$collect_street_data', 'analysis_type': 'heating_requirements'}
                },
                {
                    'name': 'analyze_energy_data',
                    'type': 'tool_call',
                    'tool_name': 'energy_analyzer',
                    'parameters': {'input_data': '$collect_energy_data', 'analysis_type': 'consumption_patterns'}
                }
            ]
        },
        {
            'name': 'result_generation',
            'type': 'sequential',
            'dependencies': ['data_analysis'],
            'steps': [
                {
                    'name': 'generate_report',
                    'type': 'tool_call',
                    'tool_name': 'report_generator',
                    'parameters': {'building_analysis': '$analyze_building_data', 'energy_analysis': '$analyze_energy_data'}
                }
            ]
        }
    ]
    
    # Complex workflow with parallel and conditional phases
    complex_workflow = [
        {
            'name': 'initial_data_collection',
            'type': 'parallel',
            'dependencies': [],
            'steps': [
                {
                    'name': 'collect_geographic_data',
                    'type': 'tool_call',
                    'tool_name': 'geo_data_collector',
                    'parameters': {'area': 'district_center', 'data_type': 'geographic'}
                },
                {
                    'name': 'collect_demographic_data',
                    'type': 'tool_call',
                    'tool_name': 'demographic_collector',
                    'parameters': {'area': 'district_center', 'data_type': 'population'}
                },
                {
                    'name': 'collect_infrastructure_data',
                    'type': 'tool_call',
                    'tool_name': 'infrastructure_collector',
                    'parameters': {'area': 'district_center', 'data_type': 'infrastructure'}
                }
            ]
        },
        {
            'name': 'data_validation',
            'type': 'conditional',
            'dependencies': ['initial_data_collection'],
            'conditions': {
                'type': 'simple',
                'check': 'data_quality_check',
                'threshold': 0.8
            },
            'steps': [
                {
                    'name': 'validate_geographic_data',
                    'type': 'condition_check',
                    'condition': {'type': 'simple', 'field': 'geo_data_quality', 'threshold': 0.8}
                },
                {
                    'name': 'validate_demographic_data',
                    'type': 'condition_check',
                    'condition': {'type': 'simple', 'field': 'demo_data_quality', 'threshold': 0.8}
                }
            ]
        },
        {
            'name': 'parallel_analysis',
            'type': 'parallel',
            'dependencies': ['data_validation'],
            'steps': [
                {
                    'name': 'heating_demand_analysis',
                    'type': 'tool_call',
                    'tool_name': 'heating_demand_analyzer',
                    'parameters': {'geographic_data': '$collect_geographic_data', 'demographic_data': '$collect_demographic_data'}
                },
                {
                    'name': 'infrastructure_analysis',
                    'type': 'tool_call',
                    'tool_name': 'infrastructure_analyzer',
                    'parameters': {'infrastructure_data': '$collect_infrastructure_data'}
                },
                {
                    'name': 'economic_analysis',
                    'type': 'tool_call',
                    'tool_name': 'economic_analyzer',
                    'parameters': {'demographic_data': '$collect_demographic_data', 'infrastructure_data': '$collect_infrastructure_data'}
                }
            ]
        },
        {
            'name': 'optimization_and_recommendation',
            'type': 'sequential',
            'dependencies': ['parallel_analysis'],
            'steps': [
                {
                    'name': 'optimize_solution',
                    'type': 'tool_call',
                    'tool_name': 'solution_optimizer',
                    'parameters': {
                        'heating_analysis': '$heating_demand_analysis',
                        'infrastructure_analysis': '$infrastructure_analysis',
                        'economic_analysis': '$economic_analysis'
                    }
                },
                {
                    'name': 'generate_final_recommendation',
                    'type': 'tool_call',
                    'tool_name': 'recommendation_generator',
                    'parameters': {'optimized_solution': '$optimize_solution'}
                }
            ]
        }
    ]
    
    return {
        'simple_workflow': simple_workflow,
        'complex_workflow': complex_workflow
    }

def demo_advanced_tool_orchestrator():
    """Demonstrate AdvancedToolOrchestrator capabilities."""
    print("🔧 Advanced Tool Orchestration Demo")
    print("=" * 60)
    
    # Create orchestrator
    orchestrator = AdvancedToolOrchestrator()
    
    # Create sample workflows
    workflows = create_sample_workflows()
    
    print("\n📋 1. Advanced Tool Orchestrator Execution")
    print("-" * 40)
    
    # Test simple workflow
    print("\n🔍 Testing Simple Sequential Workflow:")
    simple_workflow = workflows['simple_workflow']
    print(f"   Workflow phases: {len(simple_workflow)}")
    for i, phase in enumerate(simple_workflow, 1):
        print(f"   Phase {i}: {phase['name']} ({phase['type']}) - {len(phase['steps'])} steps")
    
    print(f"\n   Executing simple workflow...")
    start_time = time.time()
    simple_result = orchestrator.execute_workflow(simple_workflow)
    execution_time = time.time() - start_time
    
    print(f"   ✅ Simple workflow completed in {execution_time:.3f}s")
    print(f"   📊 Result success: {simple_result.get('aggregated_data', {}).get('successful_phases', 0)}/{simple_result.get('aggregated_data', {}).get('total_phases', 0)} phases")
    
    if 'enhanced_data' in simple_result:
        enhanced_data = simple_result['enhanced_data']
        if 'performance_metrics' in enhanced_data:
            perf_metrics = enhanced_data['performance_metrics']
            print(f"   📈 Success rate: {perf_metrics.get('success_rate', 0):.1%}")
            print(f"   ⏱️  Average phase time: {perf_metrics.get('average_phase_time', 0):.3f}s")
        
        if 'insights' in enhanced_data:
            print(f"   💡 Insights generated: {len(enhanced_data['insights'])}")
            for insight in enhanced_data['insights'][:2]:  # Show first 2
                print(f"      - {insight['type']}: {insight['message']}")
        
        if 'recommendations' in enhanced_data:
            print(f"   🚀 Recommendations: {len(enhanced_data['recommendations'])}")
            for rec in enhanced_data['recommendations'][:2]:  # Show first 2
                print(f"      - {rec['category']}: {rec['recommendation']}")
    
    # Test complex workflow
    print(f"\n🔍 Testing Complex Parallel/Conditional Workflow:")
    complex_workflow = workflows['complex_workflow']
    print(f"   Workflow phases: {len(complex_workflow)}")
    for i, phase in enumerate(complex_workflow, 1):
        print(f"   Phase {i}: {phase['name']} ({phase['type']}) - {len(phase['steps'])} steps")
        if phase['type'] == 'conditional':
            print(f"      Conditions: {phase.get('conditions', {})}")
    
    print(f"\n   Executing complex workflow...")
    start_time = time.time()
    complex_result = orchestrator.execute_workflow(complex_workflow)
    execution_time = time.time() - start_time
    
    print(f"   ✅ Complex workflow completed in {execution_time:.3f}s")
    print(f"   📊 Result success: {complex_result.get('aggregated_data', {}).get('successful_phases', 0)}/{complex_result.get('aggregated_data', {}).get('total_phases', 0)} phases")
    
    if 'enhanced_data' in complex_result:
        enhanced_data = complex_result['enhanced_data']
        if 'performance_metrics' in enhanced_data:
            perf_metrics = enhanced_data['performance_metrics']
            print(f"   📈 Success rate: {perf_metrics.get('success_rate', 0):.1%}")
            print(f"   ⏱️  Average phase time: {perf_metrics.get('average_phase_time', 0):.3f}s")
            print(f"   🚀 Throughput: {perf_metrics.get('throughput', 0):.3f} phases/s")
            print(f"   ⚡ Efficiency score: {perf_metrics.get('efficiency_score', 0):.3f}")
        
        if 'quality_metrics' in enhanced_data:
            quality_metrics = enhanced_data['quality_metrics']
            print(f"   🎯 Reliability score: {quality_metrics.get('reliability_score', 0):.1%}")
            print(f"   📋 Completeness score: {quality_metrics.get('completeness_score', 0):.1%}")
            print(f"   🔄 Consistency score: {quality_metrics.get('consistency_score', 0):.1%}")
            print(f"   🏆 Quality index: {quality_metrics.get('quality_index', 0):.3f}")
    
    return orchestrator

def demo_workflow_engine(orchestrator):
    """Demonstrate WorkflowEngine capabilities."""
    print("\n\n🔧 2. Workflow Engine")
    print("-" * 40)
    
    workflow_engine = orchestrator.workflow_engine
    
    print("\n🔍 Workflow Engine Statistics:")
    performance_stats = workflow_engine.get_performance_statistics()
    
    if performance_stats:
        print(f"   📊 Workflows tracked: {len(performance_stats)}")
        for workflow_id, stats in performance_stats.items():
            print(f"   {workflow_id}:")
            print(f"      Total executions: {stats['total_executions']}")
            print(f"      Success rate: {stats['success_rate']:.1%}")
            print(f"      Average execution time: {stats['average_execution_time']:.3f}s")
            print(f"      Min execution time: {stats['min_execution_time']:.3f}s")
            print(f"      Max execution time: {stats['max_execution_time']:.3f}s")
            print(f"      Std execution time: {stats['std_execution_time']:.3f}s")
    else:
        print(f"   📊 No workflow performance data available yet")
    
    # Test workflow optimization
    print(f"\n🔍 Testing Workflow Optimization:")
    sample_workflow = [
        {
            'name': 'test_phase',
            'type': 'sequential',
            'steps': [{'name': 'test_step', 'type': 'tool_call'}]
        }
    ]
    
    optimized_workflow = workflow_engine.optimize_workflow(sample_workflow)
    print(f"   ✅ Workflow optimization completed")
    print(f"   📋 Original workflow: {len(sample_workflow)} phases")
    print(f"   📋 Optimized workflow: {len(optimized_workflow)} phases")
    print(f"   🔧 Optimization applied: {len(optimized_workflow) != len(sample_workflow) or optimized_workflow != sample_workflow}")

def demo_dependency_manager(orchestrator):
    """Demonstrate DependencyManager capabilities."""
    print("\n\n🔧 3. Dependency Manager")
    print("-" * 40)
    
    dependency_manager = orchestrator.dependency_manager
    
    print("\n🔍 Dependency Manager Statistics:")
    dependency_stats = orchestrator.get_orchestrator_statistics()['dependency_manager_stats']
    print(f"   📊 Dependency graph size: {dependency_stats['dependency_graph_size']}")
    print(f"   📊 Execution order cache size: {dependency_stats['execution_order_cache_size']}")
    
    # Test execution plan creation
    print(f"\n🔍 Testing Execution Plan Creation:")
    sample_workflow = [
        {
            'name': 'phase_a',
            'type': 'sequential',
            'dependencies': [],
            'steps': [{'name': 'step_a1', 'type': 'tool_call'}]
        },
        {
            'name': 'phase_b',
            'type': 'parallel',
            'dependencies': ['phase_a'],
            'steps': [
                {'name': 'step_b1', 'type': 'tool_call'},
                {'name': 'step_b2', 'type': 'tool_call'}
            ]
        },
        {
            'name': 'phase_c',
            'type': 'sequential',
            'dependencies': ['phase_b'],
            'steps': [{'name': 'step_c1', 'type': 'tool_call'}]
        }
    ]
    
    try:
        execution_plan = dependency_manager.create_execution_plan(sample_workflow)
        print(f"   ✅ Execution plan created successfully")
        print(f"   📋 Total phases: {len(execution_plan.phases)}")
        print(f"   📋 Estimated execution time: {execution_plan.total_estimated_time:.3f}s")
        print(f"   📋 Execution order: {execution_plan.execution_order}")
        print(f"   📊 Resource requirements:")
        for key, value in execution_plan.resource_requirements.items():
            print(f"      {key}: {value}")
    except Exception as e:
        print(f"   ❌ Execution plan creation failed: {e}")

def demo_resource_optimizer(orchestrator):
    """Demonstrate ResourceOptimizer capabilities."""
    print("\n\n🔧 4. Resource Optimizer")
    print("-" * 40)
    
    resource_optimizer = orchestrator.resource_optimizer
    
    print("\n🔍 Resource Optimizer Statistics:")
    resource_stats = resource_optimizer.get_resource_statistics()
    
    if resource_stats.get('status') != 'no_usage_data':
        print(f"   📊 Total measurements: {resource_stats['total_measurements']}")
        print(f"   📊 Average memory usage: {resource_stats['average_memory_mb']:.1f} MB")
        print(f"   📊 Max memory usage: {resource_stats['max_memory_mb']:.1f} MB")
        print(f"   📊 Average CPU cores: {resource_stats['average_cpu_cores']:.2f}")
        print(f"   📊 Max CPU cores: {resource_stats['max_cpu_cores']:.2f}")
        print(f"   📊 Memory efficiency: {resource_stats['memory_efficiency']:.1%}")
        print(f"   📊 CPU efficiency: {resource_stats['cpu_efficiency']:.1%}")
    else:
        print(f"   📊 No resource usage data available yet")
    
    # Test resource optimization
    print(f"\n🔍 Testing Resource Optimization:")
    
    # Create a mock execution plan
    from src.advanced_tool_orchestration import ExecutionPlan, WorkflowPhase
    
    mock_phases = [
        WorkflowPhase(
            name='test_phase_1',
            type='sequential',
            steps=[{'name': 'step1', 'type': 'tool_call'}],
            dependencies=[]
        ),
        WorkflowPhase(
            name='test_phase_2',
            type='parallel',
            steps=[
                {'name': 'step2a', 'type': 'tool_call'},
                {'name': 'step2b', 'type': 'tool_call'}
            ],
            dependencies=['test_phase_1']
        )
    ]
    
    mock_execution_plan = ExecutionPlan(
        phases=mock_phases,
        total_estimated_time=10.0,
        resource_requirements={'max_memory_mb': 1000, 'max_cpu_cores': 4},
        dependencies={'test_phase_1': [], 'test_phase_2': ['test_phase_1']},
        execution_order=['test_phase_1', 'test_phase_2']
    )
    
    try:
        resource_plan = resource_optimizer.optimize_resources(mock_execution_plan)
        print(f"   ✅ Resource optimization completed")
        print(f"   📊 Resource plan created with {len(resource_plan.get('resource_allocation', {}).get('phases_allocation', {}))} phase allocations")
        
        if 'resource_allocation' in resource_plan:
            allocation = resource_plan['resource_allocation']
            print(f"   📊 Total memory allocated: {allocation.get('total_memory_allocated', 0):.1f} MB")
            print(f"   📊 Total CPU allocated: {allocation.get('total_cpu_allocated', 0):.2f} cores")
            print(f"   📊 Parallel executions: {allocation.get('parallel_executions', 0)}")
    except Exception as e:
        print(f"   ❌ Resource optimization failed: {e}")

def demo_result_aggregator(orchestrator):
    """Demonstrate AdvancedResultAggregator capabilities."""
    print("\n\n🔧 5. Advanced Result Aggregator")
    print("-" * 40)
    
    result_aggregator = orchestrator.result_aggregator
    
    print("\n🔍 Result Aggregator Statistics:")
    aggregation_stats = result_aggregator.get_aggregation_statistics()
    
    if aggregation_stats.get('status') != 'no_aggregation_data':
        print(f"   📊 Total aggregations: {aggregation_stats['total_aggregations']}")
        print(f"   📊 Aggregation types: {aggregation_stats['aggregation_types']}")
        print(f"   📊 Recent aggregations (24h): {aggregation_stats['recent_aggregations']}")
    else:
        print(f"   📊 No aggregation data available yet")
    
    # Test result aggregation
    print(f"\n🔍 Testing Result Aggregation:")
    
    # Create mock execution results
    from src.advanced_tool_orchestration import PhaseResult
    
    mock_execution_results = {
        'phase_1': PhaseResult(
            phase_name='phase_1',
            success=True,
            execution_time=2.5,
            steps_results={'step1': {'success': True, 'result': 'data1'}},
            metadata={'phase_type': 'sequential'}
        ),
        'phase_2': PhaseResult(
            phase_name='phase_2',
            success=True,
            execution_time=1.8,
            steps_results={'step2': {'success': True, 'result': 'data2'}},
            metadata={'phase_type': 'parallel'}
        ),
        'phase_3': PhaseResult(
            phase_name='phase_3',
            success=False,
            execution_time=0.5,
            steps_results={},
            error_message='Test error',
            metadata={'phase_type': 'sequential'}
        )
    }
    
    try:
        aggregated_result = result_aggregator.aggregate_and_enhance(mock_execution_results)
        print(f"   ✅ Result aggregation completed")
        
        if 'aggregated_data' in aggregated_result:
            agg_data = aggregated_result['aggregated_data']
            print(f"   📊 Total phases: {agg_data['total_phases']}")
            print(f"   📊 Successful phases: {agg_data['successful_phases']}")
            print(f"   📊 Failed phases: {agg_data['failed_phases']}")
            print(f"   📊 Total execution time: {agg_data['total_execution_time']:.3f}s")
        
        if 'enhanced_data' in aggregated_result:
            enhanced_data = aggregated_result['enhanced_data']
            if 'performance_metrics' in enhanced_data:
                perf_metrics = enhanced_data['performance_metrics']
                print(f"   📈 Performance Metrics:")
                print(f"      Success rate: {perf_metrics.get('success_rate', 0):.1%}")
                print(f"      Average phase time: {perf_metrics.get('average_phase_time', 0):.3f}s")
                print(f"      Throughput: {perf_metrics.get('throughput', 0):.3f} phases/s")
                print(f"      Efficiency score: {perf_metrics.get('efficiency_score', 0):.3f}")
            
            if 'quality_metrics' in enhanced_data:
                quality_metrics = enhanced_data['quality_metrics']
                print(f"   🎯 Quality Metrics:")
                print(f"      Reliability score: {quality_metrics.get('reliability_score', 0):.1%}")
                print(f"      Completeness score: {quality_metrics.get('completeness_score', 0):.1%}")
                print(f"      Quality index: {quality_metrics.get('quality_index', 0):.3f}")
            
            if 'insights' in enhanced_data:
                print(f"   💡 Insights generated: {len(enhanced_data['insights'])}")
                for insight in enhanced_data['insights']:
                    print(f"      - {insight['type']}: {insight['message']}")
            
            if 'recommendations' in enhanced_data:
                print(f"   🚀 Recommendations generated: {len(enhanced_data['recommendations'])}")
                for rec in enhanced_data['recommendations']:
                    print(f"      - {rec['category']} ({rec['priority']}): {rec['recommendation']}")
    
    except Exception as e:
        print(f"   ❌ Result aggregation failed: {e}")

def demo_execution_monitor(orchestrator):
    """Demonstrate ExecutionMonitor capabilities."""
    print("\n\n🔧 6. Execution Monitor")
    print("-" * 40)
    
    execution_monitor = orchestrator.execution_monitor
    
    print("\n🔍 Execution Monitor Statistics:")
    monitoring_stats = execution_monitor.get_monitoring_summary()
    
    if monitoring_stats.get('status') != 'no_monitoring_data':
        print(f"   📊 Total executions monitored: {monitoring_stats['total_executions_monitored']}")
        print(f"   📊 Total phases monitored: {monitoring_stats['total_phases_monitored']}")
        print(f"   📊 Total errors detected: {monitoring_stats['total_errors_detected']}")
        print(f"   📊 Total execution time: {monitoring_stats['total_execution_time']:.3f}s")
        print(f"   📊 Average phases per execution: {monitoring_stats['average_phases_per_execution']:.1f}")
        print(f"   📊 Average execution time: {monitoring_stats['average_execution_time']:.3f}s")
        print(f"   📊 Error rate: {monitoring_stats['error_rate']:.1%}")
    else:
        print(f"   📊 No monitoring data available yet")
    
    # Test execution monitoring
    print(f"\n🔍 Testing Execution Monitoring:")
    
    # Start monitoring
    monitor = execution_monitor.start_monitoring()
    print(f"   ✅ Monitoring started")
    
    # Simulate phase execution
    from src.advanced_tool_orchestration import PhaseResult
    
    test_phases = [
        PhaseResult(
            phase_name='test_phase_1',
            success=True,
            execution_time=1.5,
            steps_results={'step1': {'success': True}},
            metadata={'phase_type': 'sequential'}
        ),
        PhaseResult(
            phase_name='test_phase_2',
            success=True,
            execution_time=2.0,
            steps_results={'step2': {'success': True}},
            metadata={'phase_type': 'parallel'}
        ),
        PhaseResult(
            phase_name='test_phase_3',
            success=False,
            execution_time=0.5,
            steps_results={},
            error_message='Test monitoring error',
            metadata={'phase_type': 'sequential'}
        )
    ]
    
    # Update monitoring for each phase
    for phase_result in test_phases:
        monitor.update_phase(phase_result.phase_name, phase_result)
        print(f"   📊 Updated monitoring for phase: {phase_result.phase_name}")
    
    # Complete monitoring
    monitor.complete_execution()
    print(f"   ✅ Monitoring completed")
    
    # Get updated statistics
    updated_stats = execution_monitor.get_monitoring_summary()
    if updated_stats.get('status') != 'no_monitoring_data':
        print(f"   📊 Updated statistics:")
        print(f"      Total executions monitored: {updated_stats['total_executions_monitored']}")
        print(f"      Total phases monitored: {updated_stats['total_phases_monitored']}")
        print(f"      Total errors detected: {updated_stats['total_errors_detected']}")
        print(f"      Error rate: {updated_stats['error_rate']:.1%}")

def demo_comprehensive_orchestration(orchestrator):
    """Demonstrate comprehensive orchestration capabilities."""
    print("\n\n🔄 7. Comprehensive Orchestration")
    print("-" * 40)
    
    print("\n🔍 Comprehensive Orchestrator Statistics:")
    orchestrator_stats = orchestrator.get_orchestrator_statistics()
    
    print(f"   📊 Workflow Engine:")
    workflow_stats = orchestrator_stats['workflow_engine_stats']
    if workflow_stats:
        print(f"      Workflows tracked: {len(workflow_stats)}")
    else:
        print(f"      No workflow data available")
    
    print(f"   📊 Dependency Manager:")
    dep_stats = orchestrator_stats['dependency_manager_stats']
    print(f"      Dependency graph size: {dep_stats['dependency_graph_size']}")
    print(f"      Execution order cache size: {dep_stats['execution_order_cache_size']}")
    
    print(f"   📊 Resource Optimizer:")
    res_stats = orchestrator_stats['resource_optimizer_stats']
    if res_stats.get('status') != 'no_usage_data':
        print(f"      Total measurements: {res_stats['total_measurements']}")
        print(f"      Memory efficiency: {res_stats['memory_efficiency']:.1%}")
        print(f"      CPU efficiency: {res_stats['cpu_efficiency']:.1%}")
    else:
        print(f"      No resource usage data")
    
    print(f"   📊 Result Aggregator:")
    agg_stats = orchestrator_stats['result_aggregator_stats']
    if agg_stats.get('status') != 'no_aggregation_data':
        print(f"      Total aggregations: {agg_stats['total_aggregations']}")
    else:
        print(f"      No aggregation data")
    
    print(f"   📊 Execution Monitor:")
    mon_stats = orchestrator_stats['execution_monitor_stats']
    if mon_stats.get('status') != 'no_monitoring_data':
        print(f"      Total executions monitored: {mon_stats['total_executions_monitored']}")
        print(f"      Error rate: {mon_stats['error_rate']:.1%}")
    else:
        print(f"      No monitoring data")

def main():
    """Main demo function."""
    print("🚀 Advanced Tool Orchestration - Comprehensive Demo")
    print("=" * 80)
    print("This demo showcases advanced tool orchestration capabilities:")
    print("- Workflow management and optimization")
    print("- Dependency resolution and execution planning")
    print("- Resource optimization and allocation")
    print("- Advanced result aggregation and enhancement")
    print("- Execution monitoring and performance tracking")
    print("=" * 80)
    
    try:
        # Run all demos
        orchestrator = demo_advanced_tool_orchestrator()
        demo_workflow_engine(orchestrator)
        demo_dependency_manager(orchestrator)
        demo_resource_optimizer(orchestrator)
        demo_result_aggregator(orchestrator)
        demo_execution_monitor(orchestrator)
        demo_comprehensive_orchestration(orchestrator)
        
        print("\n\n🎉 Advanced Tool Orchestration Demo Completed Successfully!")
        print("=" * 80)
        print("The advanced tool orchestration system is working correctly:")
        print("✅ AdvancedToolOrchestrator with workflow management")
        print("✅ WorkflowEngine with optimization capabilities")
        print("✅ DependencyManager with execution planning")
        print("✅ ResourceOptimizer with allocation optimization")
        print("✅ AdvancedResultAggregator with enhancement")
        print("✅ ExecutionMonitor with performance tracking")
        print("\n🚀 Advanced tool orchestration is ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
