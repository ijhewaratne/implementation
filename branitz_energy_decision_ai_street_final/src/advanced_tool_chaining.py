#!/usr/bin/env python3
"""
Advanced Tool Chaining with ADK Integration
Sophisticated tool orchestration with dependency management, parallel execution, and result aggregation.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import concurrent.futures
import threading
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ToolStep:
    """Tool execution step definition."""
    tool_name: str
    parameters: Dict[str, Any]
    output_name: str
    dependencies: List[str] = None
    timeout: int = 30
    retry_count: int = 3
    parallel_group: Optional[str] = None

@dataclass
class ToolResult:
    """Tool execution result."""
    step_name: str
    success: bool
    result: Any
    execution_time: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

class ToolRegistry:
    """Registry for available tools."""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()
    
    def register_tool(self, name: str, tool_func: Callable, metadata: Dict[str, Any] = None):
        """Register a tool with metadata."""
        self.tools[name] = tool_func
        self.tool_metadata[name] = metadata or {}
        logger.info(f"Registered tool: {name}")
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Get tool function by name."""
        return self.tools.get(name)
    
    def get_tool_metadata(self, name: str) -> Dict[str, Any]:
        """Get tool metadata."""
        return self.tool_metadata.get(name, {})
    
    def list_tools(self) -> List[str]:
        """List all registered tools."""
        return list(self.tools.keys())
    
    def _register_default_tools(self):
        """Register default tools."""
        # Import and register enhanced tools
        try:
            from src.enhanced_tools import (
                run_comprehensive_dh_analysis,
                run_comprehensive_hp_analysis,
                compare_comprehensive_scenarios,
                get_all_street_names,
                list_available_results,
                analyze_kpi_report,
                generate_comprehensive_kpi_report
            )
            
            self.register_tool(
                'run_comprehensive_dh_analysis',
                run_comprehensive_dh_analysis,
                {'type': 'analysis', 'category': 'district_heating', 'timeout': 60}
            )
            
            self.register_tool(
                'run_comprehensive_hp_analysis',
                run_comprehensive_hp_analysis,
                {'type': 'analysis', 'category': 'heat_pump', 'timeout': 60}
            )
            
            self.register_tool(
                'compare_comprehensive_scenarios',
                compare_comprehensive_scenarios,
                {'type': 'comparison', 'category': 'scenario_analysis', 'timeout': 90}
            )
            
            self.register_tool(
                'get_all_street_names',
                get_all_street_names,
                {'type': 'data', 'category': 'exploration', 'timeout': 10}
            )
            
            self.register_tool(
                'list_available_results',
                list_available_results,
                {'type': 'data', 'category': 'exploration', 'timeout': 10}
            )
            
            self.register_tool(
                'analyze_kpi_report',
                analyze_kpi_report,
                {'type': 'analysis', 'category': 'kpi_analysis', 'timeout': 30}
            )
            
            self.register_tool(
                'generate_comprehensive_kpi_report',
                generate_comprehensive_kpi_report,
                {'type': 'generation', 'category': 'reporting', 'timeout': 45}
            )
            
        except ImportError as e:
            logger.warning(f"Could not import enhanced tools: {e}")

class DependencyResolver:
    """Resolve tool execution dependencies."""
    
    def __init__(self):
        self.dependency_graph: Dict[str, List[str]] = defaultdict(list)
        self.reverse_dependencies: Dict[str, List[str]] = defaultdict(list)
    
    def add_dependency(self, tool_name: str, depends_on: List[str]):
        """Add dependency relationship."""
        self.dependency_graph[tool_name] = depends_on
        for dep in depends_on:
            self.reverse_dependencies[dep].append(tool_name)
    
    def resolve_dependencies(self, workflow: List[ToolStep]) -> List[List[ToolStep]]:
        """Resolve dependencies and return execution phases."""
        # Build dependency graph from workflow
        self._build_dependency_graph(workflow)
        
        # Topological sort to determine execution order
        execution_phases = self._topological_sort(workflow)
        
        return execution_phases
    
    def _build_dependency_graph(self, workflow: List[ToolStep]):
        """Build dependency graph from workflow steps."""
        self.dependency_graph.clear()
        self.reverse_dependencies.clear()
        
        for step in workflow:
            if step.dependencies:
                self.dependency_graph[step.output_name] = step.dependencies
    
    def _topological_sort(self, workflow: List[ToolStep]) -> List[List[ToolStep]]:
        """Perform topological sort to determine execution phases."""
        # Create step lookup
        step_lookup = {step.output_name: step for step in workflow}
        
        # Calculate in-degrees
        in_degree = {step.output_name: 0 for step in workflow}
        for step in workflow:
            if step.dependencies:
                for dep in step.dependencies:
                    if dep in in_degree:
                        in_degree[step.output_name] += 1
        
        # Find steps with no dependencies
        queue = deque([step.output_name for step in workflow if in_degree[step.output_name] == 0])
        execution_phases = []
        
        while queue:
            # Current phase - all steps that can be executed in parallel
            current_phase = []
            phase_size = len(queue)
            
            for _ in range(phase_size):
                step_name = queue.popleft()
                current_phase.append(step_lookup[step_name])
                
                # Update in-degrees for dependent steps
                for dependent in self.reverse_dependencies[step_name]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
            
            execution_phases.append(current_phase)
        
        return execution_phases

class WorkflowEngine:
    """Advanced workflow execution engine."""
    
    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.dependency_resolver = DependencyResolver()
        self.execution_monitor = ExecutionMonitor()
        self.result_aggregator = ResultAggregator()
    
    def execute_workflow(self, workflow: List[ToolStep]) -> Dict[str, Any]:
        """Execute workflow with advanced orchestration."""
        start_time = time.time()
        
        try:
            # 1. Validate workflow
            self._validate_workflow(workflow)
            
            # 2. Resolve dependencies
            execution_phases = self.dependency_resolver.resolve_dependencies(workflow)
            
            # 3. Execute phases
            execution_results = self._execute_phases(execution_phases)
            
            # 4. Aggregate results
            final_result = self.result_aggregator.aggregate_results(execution_results)
            
            # 5. Add execution metadata
            final_result['execution_metadata'] = {
                'total_execution_time': time.time() - start_time,
                'phases_executed': len(execution_phases),
                'total_steps': len(workflow),
                'successful_steps': sum(1 for result in execution_results.values() if result.success),
                'failed_steps': sum(1 for result in execution_results.values() if not result.success)
            }
            
            return final_result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def _validate_workflow(self, workflow: List[ToolStep]):
        """Validate workflow before execution."""
        # Check if all tools are registered
        for step in workflow:
            if step.tool_name not in self.tool_registry.tools:
                raise ValueError(f"Tool not registered: {step.tool_name}")
        
        # Check for circular dependencies
        self._check_circular_dependencies(workflow)
        
        # Validate parameters
        for step in workflow:
            self._validate_step_parameters(step)
    
    def _check_circular_dependencies(self, workflow: List[ToolStep]):
        """Check for circular dependencies."""
        # Build dependency graph
        graph = defaultdict(list)
        for step in workflow:
            if step.dependencies:
                graph[step.output_name] = step.dependencies
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for step in workflow:
            if step.output_name not in visited:
                if has_cycle(step.output_name):
                    raise ValueError(f"Circular dependency detected involving {step.output_name}")
    
    def _validate_step_parameters(self, step: ToolStep):
        """Validate step parameters."""
        tool_metadata = self.tool_registry.get_tool_metadata(step.tool_name)
        
        # Check timeout
        if step.timeout > tool_metadata.get('max_timeout', 300):
            logger.warning(f"Step {step.output_name} timeout exceeds tool maximum")
        
        # Check retry count
        if step.retry_count > 5:
            logger.warning(f"Step {step.output_name} retry count is high")
    
    def _execute_phases(self, execution_phases: List[List[ToolStep]]) -> Dict[str, ToolResult]:
        """Execute workflow phases."""
        execution_results = {}
        
        for phase_index, phase in enumerate(execution_phases):
            logger.info(f"Executing phase {phase_index + 1}/{len(execution_phases)} with {len(phase)} steps")
            
            # Execute phase steps
            phase_results = self._execute_phase(phase, execution_results)
            execution_results.update(phase_results)
            
            # Check for critical failures
            failed_steps = [name for name, result in phase_results.items() if not result.success]
            if failed_steps:
                logger.warning(f"Phase {phase_index + 1} had failed steps: {failed_steps}")
        
        return execution_results
    
    def _execute_phase(self, phase: List[ToolStep], previous_results: Dict[str, ToolResult]) -> Dict[str, ToolResult]:
        """Execute a single phase."""
        # Group steps by parallel group
        parallel_groups = defaultdict(list)
        sequential_steps = []
        
        for step in phase:
            if step.parallel_group:
                parallel_groups[step.parallel_group].append(step)
            else:
                sequential_steps.append(step)
        
        phase_results = {}
        
        # Execute parallel groups
        for group_name, group_steps in parallel_groups.items():
            group_results = self._execute_parallel_steps(group_steps, previous_results)
            phase_results.update(group_results)
        
        # Execute sequential steps
        for step in sequential_steps:
            result = self._execute_single_step(step, previous_results)
            phase_results[step.output_name] = result
        
        return phase_results
    
    def _execute_parallel_steps(self, steps: List[ToolStep], previous_results: Dict[str, ToolResult]) -> Dict[str, ToolResult]:
        """Execute steps in parallel."""
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(steps), 5)) as executor:
            # Submit all steps
            future_to_step = {
                executor.submit(self._execute_single_step, step, previous_results): step
                for step in steps
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_step):
                step = future_to_step[future]
                try:
                    result = future.result()
                    results[step.output_name] = result
                except Exception as e:
                    logger.error(f"Parallel execution failed for {step.output_name}: {e}")
                    results[step.output_name] = ToolResult(
                        step_name=step.output_name,
                        success=False,
                        result=None,
                        execution_time=0,
                        error_message=str(e)
                    )
        
        return results
    
    def _execute_single_step(self, step: ToolStep, previous_results: Dict[str, ToolResult]) -> ToolResult:
        """Execute a single tool step."""
        start_time = time.time()
        
        try:
            # Get tool function
            tool_func = self.tool_registry.get_tool(step.tool_name)
            if not tool_func:
                raise ValueError(f"Tool not found: {step.tool_name}")
            
            # Prepare parameters with previous results
            parameters = self._prepare_parameters(step.parameters, previous_results)
            
            # Execute tool with retry logic
            result = self._execute_with_retry(tool_func, parameters, step)
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                step_name=step.output_name,
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={'tool_name': step.tool_name, 'parameters': parameters}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Step execution failed: {step.output_name} - {e}")
            
            return ToolResult(
                step_name=step.output_name,
                success=False,
                result=None,
                execution_time=execution_time,
                error_message=str(e),
                metadata={'tool_name': step.tool_name}
            )
    
    def _prepare_parameters(self, parameters: Dict[str, Any], previous_results: Dict[str, ToolResult]) -> Dict[str, Any]:
        """Prepare parameters with previous results."""
        prepared_params = parameters.copy()
        
        # Replace parameter references with actual results
        for key, value in prepared_params.items():
            if isinstance(value, str) and value.startswith('$'):
                # Reference to previous result
                result_name = value[1:]  # Remove $ prefix
                if result_name in previous_results:
                    prepared_params[key] = previous_results[result_name].result
                else:
                    logger.warning(f"Parameter reference not found: {value}")
        
        return prepared_params
    
    def _execute_with_retry(self, tool_func: Callable, parameters: Dict[str, Any], step: ToolStep) -> Any:
        """Execute tool with retry logic."""
        last_exception = None
        
        for attempt in range(step.retry_count):
            try:
                # Execute tool with timeout
                result = self._execute_with_timeout(tool_func, parameters, step.timeout)
                return result
                
            except Exception as e:
                last_exception = e
                if attempt < step.retry_count - 1:
                    logger.warning(f"Attempt {attempt + 1} failed for {step.output_name}, retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All attempts failed for {step.output_name}")
        
        raise last_exception
    
    def _execute_with_timeout(self, tool_func: Callable, parameters: Dict[str, Any], timeout: int) -> Any:
        """Execute tool with timeout."""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Tool execution timed out after {timeout} seconds")
        
        # Set timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            result = tool_func(**parameters)
            return result
        finally:
            # Restore original handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

class ExecutionMonitor:
    """Monitor workflow execution."""
    
    def __init__(self):
        self.execution_log: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
    
    def log_execution(self, step_name: str, execution_time: float, success: bool, metadata: Dict = None):
        """Log execution details."""
        log_entry = {
            'step_name': step_name,
            'execution_time': execution_time,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.execution_log.append(log_entry)
        self.performance_metrics[step_name].append(execution_time)
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        if not self.execution_log:
            return {'status': 'no_executions'}
        
        total_executions = len(self.execution_log)
        successful_executions = sum(1 for entry in self.execution_log if entry['success'])
        
        avg_execution_time = sum(entry['execution_time'] for entry in self.execution_log) / total_executions
        
        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'success_rate': successful_executions / total_executions,
            'average_execution_time': avg_execution_time,
            'performance_by_step': dict(self.performance_metrics)
        }

class ResultAggregator:
    """Aggregate and enhance workflow results."""
    
    def __init__(self):
        self.aggregation_strategies = {
            'merge': self._merge_results,
            'combine': self._combine_results,
            'summarize': self._summarize_results
        }
    
    def aggregate_results(self, execution_results: Dict[str, ToolResult]) -> Dict[str, Any]:
        """Aggregate workflow execution results."""
        successful_results = {name: result for name, result in execution_results.items() if result.success}
        failed_results = {name: result for name, result in execution_results.items() if not result.success}
        
        # Aggregate successful results
        aggregated_data = self._merge_results(successful_results)
        
        # Add execution summary
        execution_summary = {
            'total_steps': len(execution_results),
            'successful_steps': len(successful_results),
            'failed_steps': len(failed_results),
            'success_rate': len(successful_results) / len(execution_results) if execution_results else 0,
            'total_execution_time': sum(result.execution_time for result in execution_results.values()),
            'failed_steps_details': {name: result.error_message for name, result in failed_results.items()}
        }
        
        return {
            'success': len(failed_results) == 0,
            'aggregated_data': aggregated_data,
            'execution_summary': execution_summary,
            'individual_results': {name: asdict(result) for name, result in execution_results.items()}
        }
    
    def _merge_results(self, results: Dict[str, ToolResult]) -> Dict[str, Any]:
        """Merge results into a single structure."""
        merged = {}
        
        for name, result in results.items():
            if isinstance(result.result, dict):
                merged.update(result.result)
            else:
                merged[name] = result.result
        
        return merged
    
    def _combine_results(self, results: Dict[str, ToolResult]) -> Dict[str, Any]:
        """Combine results with metadata."""
        combined = {}
        
        for name, result in results.items():
            combined[name] = {
                'data': result.result,
                'execution_time': result.execution_time,
                'metadata': result.metadata
            }
        
        return combined
    
    def _summarize_results(self, results: Dict[str, ToolResult]) -> Dict[str, Any]:
        """Summarize results."""
        summary = {
            'total_results': len(results),
            'execution_times': {name: result.execution_time for name, result in results.items()},
            'result_types': {name: type(result.result).__name__ for name, result in results.items()},
            'summary_data': {}
        }
        
        # Create summary of actual data
        for name, result in results.items():
            if isinstance(result.result, dict):
                summary['summary_data'][name] = {
                    'keys': list(result.result.keys()),
                    'size': len(result.result)
                }
            else:
                summary['summary_data'][name] = {
                    'type': type(result.result).__name__,
                    'size': len(str(result.result))
                }
        
        return summary

class AdvancedToolChainer:
    """Advanced tool chaining with ADK integration."""
    
    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.workflow_engine = WorkflowEngine()
        self.dependency_resolver = DependencyResolver()
        self.result_aggregator = ResultAggregator()
        self.execution_monitor = ExecutionMonitor()
        self.performance_tracker = PerformanceTracker()
        
        logger.info("Initialized AdvancedToolChainer")
    
    def execute_tool_chain(self, workflow: List[Dict]) -> Dict:
        """Execute advanced tool chain with dependencies."""
        start_time = time.time()
        
        try:
            # 1. Validate workflow
            self._validate_workflow(workflow)
            
            # 2. Convert dict workflow to ToolStep objects
            tool_steps = []
            for step_dict in workflow:
                tool_step = ToolStep(
                    tool_name=step_dict['tool_name'],
                    parameters=step_dict.get('parameters', {}),
                    output_name=step_dict['output'],
                    dependencies=step_dict.get('dependencies', [])
                )
                tool_steps.append(tool_step)
            
            # 3. Resolve dependencies
            execution_order = self.dependency_resolver.resolve_dependencies(tool_steps)
            
            # 4. Execute tools in order
            results = {}
            for step_phase in execution_order:
                for step in step_phase:
                    tool_result = self._execute_tool_step(step, results)
                    results[step.output_name] = tool_result
            
            # 5. Aggregate results
            final_result = self.result_aggregator.aggregate_results(results)
            
            # 6. Add execution metadata
            execution_time = time.time() - start_time
            total_steps = sum(len(phase) for phase in execution_order)
            final_result['execution_metadata'] = {
                'total_execution_time': execution_time,
                'steps_executed': total_steps,
                'successful_steps': sum(1 for result in results.values() if result.success),
                'failed_steps': sum(1 for result in results.values() if not result.success)
            }
            
            # 7. Track performance
            self.performance_tracker.track_execution(workflow, final_result, execution_time)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Tool chain execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def execute_parallel_tools(self, parallel_steps: List[Dict]) -> Dict:
        """Execute tools in parallel for efficiency."""
        start_time = time.time()
        
        try:
            # Validate parallel steps
            self._validate_parallel_steps(parallel_steps)
            
            # Execute tools in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(parallel_steps), 5)) as executor:
                futures = []
                for step in parallel_steps:
                    future = executor.submit(self._execute_tool_step, step, {})
                    futures.append((step['output'], future))
                
                results = {}
                for output_name, future in futures:
                    try:
                        result = future.result()
                        results[output_name] = result
                    except Exception as e:
                        logger.error(f"Parallel execution failed for {output_name}: {e}")
                        results[output_name] = ToolResult(
                            step_name=output_name,
                            success=False,
                            result=None,
                            execution_time=0,
                            error_message=str(e)
                        )
            
            # Aggregate results
            final_result = self.result_aggregator.aggregate_results(results)
            
            # Add execution metadata
            execution_time = time.time() - start_time
            final_result['execution_metadata'] = {
                'total_execution_time': execution_time,
                'parallel_steps': len(parallel_steps),
                'successful_steps': sum(1 for result in results.values() if result.success),
                'failed_steps': sum(1 for result in results.values() if not result.success),
                'execution_type': 'parallel'
            }
            
            # Track performance
            self.performance_tracker.track_parallel_execution(parallel_steps, final_result, execution_time)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Parallel tool execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def _validate_workflow(self, workflow: List[Dict]):
        """Validate workflow before execution."""
        if not workflow:
            raise ValueError("Workflow cannot be empty")
        
        # Check if all tools are registered
        for step in workflow:
            if step.get('tool_name') not in self.tool_registry.tools:
                raise ValueError(f"Tool not registered: {step.get('tool_name')}")
        
        # Check for circular dependencies
        self._check_circular_dependencies(workflow)
    
    def _validate_parallel_steps(self, parallel_steps: List[Dict]):
        """Validate parallel execution steps."""
        if not parallel_steps:
            raise ValueError("Parallel steps cannot be empty")
        
        # Check if all tools are registered
        for step in parallel_steps:
            if step.get('tool_name') not in self.tool_registry.tools:
                raise ValueError(f"Tool not registered: {step.get('tool_name')}")
        
        # Check for dependencies (parallel steps should not have dependencies)
        for step in parallel_steps:
            if step.get('dependencies'):
                raise ValueError(f"Parallel step {step.get('output')} cannot have dependencies")
    
    def _execute_tool_step(self, step, previous_results: Dict) -> ToolResult:
        """Execute a single tool step."""
        step_start_time = time.time()
        
        try:
            # Handle both ToolStep objects and dictionaries
            if hasattr(step, 'tool_name'):
                # ToolStep object
                tool_name = step.tool_name
                parameters = step.parameters
                output_name = step.output_name
            else:
                # Dictionary
                tool_name = step['tool_name']
                parameters = step.get('parameters', {})
                output_name = step['output']
            
            # Get tool function
            tool_func = self.tool_registry.get_tool(tool_name)
            if not tool_func:
                raise ValueError(f"Tool not found: {tool_name}")
            
            # Prepare parameters with previous results
            prepared_parameters = self._prepare_parameters(parameters, previous_results)
            
            # Execute tool
            result = tool_func(**prepared_parameters)
            
            execution_time = time.time() - step_start_time
            
            # Log execution
            self.execution_monitor.log_execution(
                output_name, execution_time, True, 
                {'tool_name': tool_name, 'parameters': prepared_parameters}
            )
            
            return ToolResult(
                step_name=output_name,
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={'tool_name': tool_name, 'parameters': prepared_parameters}
            )
            
        except Exception as e:
            execution_time = time.time() - step_start_time
            output_name = step.output_name if hasattr(step, 'output_name') else step['output']
            tool_name = step.tool_name if hasattr(step, 'tool_name') else step['tool_name']
            
            logger.error(f"Step execution failed: {output_name} - {e}")
            
            # Log execution failure
            self.execution_monitor.log_execution(
                output_name, execution_time, False, 
                {'tool_name': tool_name, 'error': str(e)}
            )
            
            return ToolResult(
                step_name=output_name,
                success=False,
                result=None,
                execution_time=execution_time,
                error_message=str(e),
                metadata={'tool_name': tool_name}
            )
    
    def _prepare_parameters(self, parameters: Dict[str, Any], previous_results: Dict) -> Dict[str, Any]:
        """Prepare parameters with previous results."""
        prepared_params = parameters.copy()
        
        # Replace parameter references with actual results
        for key, value in prepared_params.items():
            if isinstance(value, str) and value.startswith('$'):
                # Reference to previous result
                result_name = value[1:]  # Remove $ prefix
                if result_name in previous_results:
                    prepared_params[key] = previous_results[result_name].result
                else:
                    logger.warning(f"Parameter reference not found: {value}")
        
        return prepared_params
    
    def _check_circular_dependencies(self, workflow: List[Dict]):
        """Check for circular dependencies in workflow."""
        # Build dependency graph
        graph = {}
        for step in workflow:
            output_name = step.get('output')
            dependencies = step.get('dependencies', [])
            graph[output_name] = dependencies
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for step in workflow:
            output_name = step.get('output')
            if output_name not in visited:
                if has_cycle(output_name):
                    raise ValueError(f"Circular dependency detected involving {output_name}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for tool chaining."""
        return self.performance_tracker.get_metrics()
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        return self.execution_monitor.get_execution_summary()

class PerformanceTracker:
    """Track performance metrics for tool chaining."""
    
    def __init__(self):
        self.execution_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
    
    def track_execution(self, workflow: List[Dict], result: Dict, execution_time: float):
        """Track workflow execution."""
        execution_record = {
            'timestamp': datetime.now().isoformat(),
            'workflow_size': len(workflow),
            'execution_time': execution_time,
            'success': result.get('success', False),
            'steps_executed': result.get('execution_metadata', {}).get('steps_executed', 0),
            'successful_steps': result.get('execution_metadata', {}).get('successful_steps', 0)
        }
        
        self.execution_history.append(execution_record)
        self.performance_metrics['execution_time'].append(execution_time)
        self.performance_metrics['workflow_size'].append(len(workflow))
        
        # Keep only recent history
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
    
    def track_parallel_execution(self, parallel_steps: List[Dict], result: Dict, execution_time: float):
        """Track parallel execution."""
        execution_record = {
            'timestamp': datetime.now().isoformat(),
            'parallel_steps': len(parallel_steps),
            'execution_time': execution_time,
            'success': result.get('success', False),
            'execution_type': 'parallel'
        }
        
        self.execution_history.append(execution_record)
        self.performance_metrics['parallel_execution_time'].append(execution_time)
        self.performance_metrics['parallel_steps'].append(len(parallel_steps))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        if not self.execution_history:
            return {'status': 'no_executions'}
        
        recent_executions = self.execution_history[-20:]  # Last 20 executions
        
        avg_execution_time = sum(exec['execution_time'] for exec in recent_executions) / len(recent_executions)
        success_rate = sum(1 for exec in recent_executions if exec['success']) / len(recent_executions)
        avg_workflow_size = sum(exec.get('workflow_size', 0) for exec in recent_executions) / len(recent_executions)
        
        return {
            'total_executions': len(self.execution_history),
            'recent_executions': len(recent_executions),
            'average_execution_time': avg_execution_time,
            'success_rate': success_rate,
            'average_workflow_size': avg_workflow_size,
            'performance_trends': dict(self.performance_metrics)
        }

# Export classes for use in other modules
__all__ = [
    'AdvancedToolChainer',
    'ToolRegistry',
    'DependencyResolver',
    'WorkflowEngine',
    'ExecutionMonitor',
    'ResultAggregator',
    'PerformanceTracker',
    'ToolStep',
    'ToolResult'
]
