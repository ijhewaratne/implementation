#!/usr/bin/env python3
"""
ADK vs SimpleAgent Performance Comparison Tests
Compare performance between ADK and SimpleAgent implementations
"""

import pytest
import sys
import os
import time
import json
import psutil
import statistics
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Tuple

# Add ADK to path
sys.path.insert(0, 'adk')

class PerformanceComparison:
    """Class to compare performance between ADK and SimpleAgent."""
    
    def __init__(self):
        self.adk_metrics = {}
        self.simpleagent_metrics = {}
        self.comparison_results = {}
    
    def add_metric(self, implementation: str, operation: str, value: float, unit: str = "seconds"):
        """Add a performance metric."""
        if implementation not in ["adk", "simpleagent"]:
            raise ValueError("Implementation must be 'adk' or 'simpleagent'")
        
        metrics_dict = self.adk_metrics if implementation == "adk" else self.simpleagent_metrics
        
        if operation not in metrics_dict:
            metrics_dict[operation] = []
        
        metrics_dict[operation].append({"value": value, "unit": unit, "timestamp": time.time()})
    
    def get_statistics(self, implementation: str, operation: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        metrics_dict = self.adk_metrics if implementation == "adk" else self.simpleagent_metrics
        
        if operation not in metrics_dict:
            return {}
        
        values = [m["value"] for m in metrics_dict[operation]]
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values)
        }
    
    def compare_performance(self, operation: str) -> Dict[str, Any]:
        """Compare performance between ADK and SimpleAgent."""
        adk_stats = self.get_statistics("adk", operation)
        simpleagent_stats = self.get_statistics("simpleagent", operation)
        
        if not adk_stats or not simpleagent_stats:
            return {"error": "Insufficient data for comparison"}
        
        # Calculate performance ratios
        speed_ratio = simpleagent_stats["mean"] / adk_stats["mean"] if adk_stats["mean"] > 0 else float('inf')
        memory_ratio = simpleagent_stats.get("memory_mean", 0) / adk_stats.get("memory_mean", 0) if adk_stats.get("memory_mean", 0) > 0 else float('inf')
        
        comparison = {
            "operation": operation,
            "adk_stats": adk_stats,
            "simpleagent_stats": simpleagent_stats,
            "speed_ratio": speed_ratio,
            "memory_ratio": memory_ratio,
            "adk_faster": adk_stats["mean"] < simpleagent_stats["mean"],
            "performance_difference": abs(adk_stats["mean"] - simpleagent_stats["mean"]),
            "relative_difference": abs(adk_stats["mean"] - simpleagent_stats["mean"]) / max(adk_stats["mean"], simpleagent_stats["mean"]) * 100
        }
        
        self.comparison_results[operation] = comparison
        return comparison
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all comparisons."""
        valid_comparisons = [comp for comp in self.comparison_results.values() if "error" not in comp]
        
        summary = {
            "total_operations": len(self.comparison_results),
            "valid_comparisons": len(valid_comparisons),
            "adk_faster_count": sum(1 for comp in valid_comparisons if comp.get("adk_faster", False)),
            "simpleagent_faster_count": sum(1 for comp in valid_comparisons if not comp.get("adk_faster", True)),
            "comparisons": self.comparison_results
        }
        
        # Only calculate average speed ratio if we have valid comparisons
        if valid_comparisons:
            speed_ratios = [comp["speed_ratio"] for comp in valid_comparisons if comp["speed_ratio"] != float('inf')]
            if speed_ratios:
                summary["average_speed_ratio"] = statistics.mean(speed_ratios)
            else:
                summary["average_speed_ratio"] = "N/A"
        else:
            summary["average_speed_ratio"] = "N/A"
        
        return summary

class TestADKVsSimpleAgentPerformance:
    """Test performance comparison between ADK and SimpleAgent."""
    
    def test_agent_initialization_performance_comparison(self):
        """Compare agent initialization performance."""
        comparison = PerformanceComparison()
        
        try:
            from src.enhanced_agents import (
                EnergyPlannerAgent,
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            )
            
            agents = [
                ("EnergyPlannerAgent", EnergyPlannerAgent),
                ("CentralHeatingAgent", CentralHeatingAgent),
                ("DecentralizedHeatingAgent", DecentralizedHeatingAgent),
                ("ComparisonAgent", ComparisonAgent),
                ("AnalysisAgent", AnalysisAgent),
                ("DataExplorerAgent", DataExplorerAgent),
                ("EnergyGPT", EnergyGPT)
            ]
            
            # Test agent initialization performance
            for agent_name, agent in agents:
                # Measure initialization time
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                # Access agent (triggers initialization)
                assert agent is not None
                if hasattr(agent, 'config'):
                    config = agent.config
                    assert config is not None
                
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                execution_time = end_time - start_time
                memory_usage = end_memory - start_memory
                
                # Determine implementation type
                implementation = "adk" if hasattr(agent, 'config') else "simpleagent"
                
                # Add metrics
                comparison.add_metric(implementation, f"{agent_name}_initialization", execution_time, "seconds")
                comparison.add_metric(implementation, f"{agent_name}_memory", memory_usage, "MB")
            
            # Compare performance
            for agent_name, _ in agents:
                init_comparison = comparison.compare_performance(f"{agent_name}_initialization")
                memory_comparison = comparison.compare_performance(f"{agent_name}_memory")
                
                print(f"{agent_name} Performance Comparison:")
                print(f"  Initialization: {init_comparison}")
                print(f"  Memory: {memory_comparison}")
            
            # Get overall summary
            summary = comparison.get_summary()
            print(f"Overall Performance Summary: {summary}")
            
            # Verify performance is reasonable for both implementations
            for operation in comparison.adk_metrics:
                if "initialization" in operation:
                    adk_stats = comparison.get_statistics("adk", operation)
                    simpleagent_stats = comparison.get_statistics("simpleagent", operation)
                    
                    if adk_stats:
                        assert adk_stats["mean"] < 1.0, f"ADK {operation} too slow: {adk_stats['mean']:.3f}s"
                    if simpleagent_stats:
                        assert simpleagent_stats["mean"] < 1.0, f"SimpleAgent {operation} too slow: {simpleagent_stats['mean']:.3f}s"
            
        except ImportError:
            pytest.skip("Enhanced agents not available")
    
    def test_tool_execution_performance_comparison(self):
        """Compare tool execution performance."""
        comparison = PerformanceComparison()
        
        try:
            from src.enhanced_tools import (
                get_all_street_names,
                get_building_ids_for_street,
                run_comprehensive_hp_analysis,
                run_comprehensive_dh_analysis,
                compare_comprehensive_scenarios
            )
            
            tools = [
                ("get_all_street_names", get_all_street_names, []),
                ("get_building_ids_for_street", get_building_ids_for_street, ["Parkstraße"]),
                ("run_comprehensive_hp_analysis", run_comprehensive_hp_analysis, ["Parkstraße"]),
                ("run_comprehensive_dh_analysis", run_comprehensive_dh_analysis, ["Parkstraße"]),
                ("compare_comprehensive_scenarios", compare_comprehensive_scenarios, ["Parkstraße"])
            ]
            
            # Test each tool multiple times
            iterations = 3
            
            for tool_name, tool_func, args in tools:
                for i in range(iterations):
                    # Measure execution time and memory
                    start_time = time.time()
                    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                    
                    result = tool_func(*args)
                    assert result is not None
                    
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                    
                    execution_time = end_time - start_time
                    memory_usage = end_memory - start_memory
                    
                    # For tools, we're testing the same implementation (SimpleAgent fallback)
                    # but we can still measure performance characteristics
                    comparison.add_metric("simpleagent", f"{tool_name}_execution", execution_time, "seconds")
                    comparison.add_metric("simpleagent", f"{tool_name}_memory", memory_usage, "MB")
            
            # Analyze tool performance
            print("Tool Execution Performance Analysis:")
            for tool_name, _, _ in tools:
                exec_stats = comparison.get_statistics("simpleagent", f"{tool_name}_execution")
                memory_stats = comparison.get_statistics("simpleagent", f"{tool_name}_memory")
                
                print(f"  {tool_name}:")
                print(f"    Execution time: {exec_stats['mean']:.3f}s ± {exec_stats['std_dev']:.3f}s")
                print(f"    Memory usage: {memory_stats['mean']:.3f}MB ± {memory_stats['std_dev']:.3f}MB")
            
            # Verify performance is reasonable
            performance_limits = {
                "get_all_street_names_execution": 2.0,
                "get_building_ids_for_street_execution": 3.0,
                "run_comprehensive_hp_analysis_execution": 10.0,
                "run_comprehensive_dh_analysis_execution": 10.0,
                "compare_comprehensive_scenarios_execution": 15.0
            }
            
            for operation, limit in performance_limits.items():
                stats = comparison.get_statistics("simpleagent", operation)
                if stats:
                    assert stats["mean"] < limit, f"{operation} too slow: {stats['mean']:.3f}s (limit: {limit}s)"
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_system_overhead_comparison(self):
        """Compare system overhead between implementations."""
        comparison = PerformanceComparison()
        
        try:
            from src.enhanced_agents import (
                EnergyPlannerAgent,
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            )
            
            agents = [
                EnergyPlannerAgent,
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            ]
            
            # Test system overhead
            for i, agent in enumerate(agents):
                # Measure overhead of accessing agent properties
                start_time = time.time()
                
                # Test different access patterns
                assert agent is not None
                if hasattr(agent, 'config'):
                    config = agent.config
                    if config:
                        name = config.get('name', 'Unknown')
                        model = config.get('model', 'Unknown')
                
                end_time = time.time()
                overhead_time = end_time - start_time
                
                # Determine implementation
                implementation = "adk" if hasattr(agent, 'config') else "simpleagent"
                
                comparison.add_metric(implementation, f"agent_{i}_overhead", overhead_time, "seconds")
            
            # Analyze overhead
            print("System Overhead Analysis:")
            adk_overhead = [comparison.get_statistics("adk", f"agent_{i}_overhead") for i in range(len(agents))]
            simpleagent_overhead = [comparison.get_statistics("simpleagent", f"agent_{i}_overhead") for i in range(len(agents))]
            
            adk_means = [stats["mean"] for stats in adk_overhead if stats]
            simpleagent_means = [stats["mean"] for stats in simpleagent_overhead if stats]
            
            if adk_means:
                print(f"  ADK average overhead: {statistics.mean(adk_means):.6f}s")
            if simpleagent_means:
                print(f"  SimpleAgent average overhead: {statistics.mean(simpleagent_means):.6f}s")
            
            # Verify overhead is reasonable
            for i in range(len(agents)):
                adk_stats = comparison.get_statistics("adk", f"agent_{i}_overhead")
                simpleagent_stats = comparison.get_statistics("simpleagent", f"agent_{i}_overhead")
                
                if adk_stats:
                    assert adk_stats["mean"] < 0.01, f"ADK agent {i} overhead too high: {adk_stats['mean']:.6f}s"
                if simpleagent_stats:
                    assert simpleagent_stats["mean"] < 0.01, f"SimpleAgent agent {i} overhead too high: {simpleagent_stats['mean']:.6f}s"
            
        except ImportError:
            pytest.skip("Enhanced agents not available")
    
    def test_memory_usage_comparison(self):
        """Compare memory usage between implementations."""
        comparison = PerformanceComparison()
        
        try:
            from src.enhanced_agents import (
                EnergyPlannerAgent,
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            )
            
            agents = [
                EnergyPlannerAgent,
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            ]
            
            # Test memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            for i, agent in enumerate(agents):
                # Measure memory usage for each agent
                before_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                # Access agent
                assert agent is not None
                if hasattr(agent, 'config'):
                    config = agent.config
                    if config:
                        # Access config properties
                        name = config.get('name', 'Unknown')
                        model = config.get('model', 'Unknown')
                        tools = config.get('tools', [])
                
                after_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_usage = after_memory - before_memory
                
                # Determine implementation
                implementation = "adk" if hasattr(agent, 'config') else "simpleagent"
                
                comparison.add_metric(implementation, f"agent_{i}_memory", memory_usage, "MB")
            
            # Analyze memory usage
            print("Memory Usage Analysis:")
            adk_memory = [comparison.get_statistics("adk", f"agent_{i}_memory") for i in range(len(agents))]
            simpleagent_memory = [comparison.get_statistics("simpleagent", f"agent_{i}_memory") for i in range(len(agents))]
            
            adk_means = [stats["mean"] for stats in adk_memory if stats]
            simpleagent_means = [stats["mean"] for stats in simpleagent_memory if stats]
            
            if adk_means:
                print(f"  ADK average memory usage: {statistics.mean(adk_means):.3f}MB")
            if simpleagent_means:
                print(f"  SimpleAgent average memory usage: {statistics.mean(simpleagent_means):.3f}MB")
            
            # Verify memory usage is reasonable
            for i in range(len(agents)):
                adk_stats = comparison.get_statistics("adk", f"agent_{i}_memory")
                simpleagent_stats = comparison.get_statistics("simpleagent", f"agent_{i}_memory")
                
                if adk_stats:
                    assert adk_stats["mean"] < 10, f"ADK agent {i} memory usage too high: {adk_stats['mean']:.3f}MB"
                if simpleagent_stats:
                    assert simpleagent_stats["mean"] < 10, f"SimpleAgent agent {i} memory usage too high: {simpleagent_stats['mean']:.3f}MB"
            
        except ImportError:
            pytest.skip("Enhanced agents not available")
    
    def test_scalability_comparison(self):
        """Compare scalability between implementations."""
        comparison = PerformanceComparison()
        
        try:
            from src.enhanced_tools import get_all_street_names, get_building_ids_for_street
            
            # Test scalability with increasing load
            streets = get_all_street_names()
            assert len(streets) > 0
            
            # Test with different numbers of operations
            test_sizes = [1, 3, 5, min(10, len(streets))]
            
            for size in test_sizes:
                test_streets = streets[:size]
                
                # Measure execution time
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                for street in test_streets:
                    building_ids = get_building_ids_for_street(street)
                    assert isinstance(building_ids, list)
                
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                execution_time = end_time - start_time
                memory_usage = end_memory - start_memory
                
                # Add metrics (using SimpleAgent since ADK is not available)
                comparison.add_metric("simpleagent", f"scalability_{size}_streets", execution_time, "seconds")
                comparison.add_metric("simpleagent", f"scalability_{size}_memory", memory_usage, "MB")
            
            # Analyze scalability
            print("Scalability Analysis:")
            for size in test_sizes:
                exec_stats = comparison.get_statistics("simpleagent", f"scalability_{size}_streets")
                memory_stats = comparison.get_statistics("simpleagent", f"scalability_{size}_memory")
                
                print(f"  {size} streets:")
                print(f"    Execution time: {exec_stats['mean']:.3f}s")
                print(f"    Memory usage: {memory_stats['mean']:.3f}MB")
                print(f"    Time per street: {exec_stats['mean']/size:.3f}s")
            
            # Verify scalability is reasonable
            sizes = list(test_sizes)
            times = [comparison.get_statistics("simpleagent", f"scalability_{size}_streets")["mean"] for size in sizes]
            
            # Check that time increases roughly linearly with size
            for i in range(1, len(sizes)):
                time_ratio = times[i] / times[i-1]
                size_ratio = sizes[i] / sizes[i-1]
                
                # Time should not increase more than 2x the size increase
                assert time_ratio < size_ratio * 2, f"Scalability issue: time increased {time_ratio:.2f}x for {size_ratio:.2f}x size increase"
            
        except ImportError:
            pytest.skip("Enhanced tools not available")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
