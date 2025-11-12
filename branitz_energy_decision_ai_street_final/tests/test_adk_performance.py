#!/usr/bin/env python3
"""
Performance Tests for ADK System
Compare ADK performance vs SimpleAgent fallback, test response times, and verify system stability
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
from contextlib import contextmanager

# Add ADK to path
sys.path.insert(0, 'adk')

class PerformanceMetrics:
    """Class to collect and analyze performance metrics."""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = None
        self.end_time = None
    
    def start_timing(self):
        """Start timing measurement."""
        self.start_time = time.time()
    
    def end_timing(self):
        """End timing measurement."""
        self.end_time = time.time()
        return self.end_time - self.start_time
    
    def add_metric(self, name: str, value: float, unit: str = "seconds"):
        """Add a performance metric."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append({"value": value, "unit": unit, "timestamp": time.time()})
    
    def get_statistics(self, name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        if name not in self.metrics:
            return {}
        
        values = [m["value"] for m in self.metrics[name]]
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values)
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        summary = {}
        for name in self.metrics:
            summary[name] = self.get_statistics(name)
        return summary

@contextmanager
def measure_performance(metrics: PerformanceMetrics, operation_name: str):
    """Context manager to measure performance of operations."""
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    try:
        yield
    finally:
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        metrics.add_metric(f"{operation_name}_execution_time", execution_time, "seconds")
        metrics.add_metric(f"{operation_name}_memory_usage", memory_usage, "MB")

class TestADKPerformanceComparison:
    """Test ADK performance vs SimpleAgent fallback."""
    
    def test_agent_initialization_performance(self):
        """Test agent initialization performance."""
        metrics = PerformanceMetrics()
        
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
            
            # Test agent initialization performance
            for i, agent in enumerate(agents):
                with measure_performance(metrics, f"agent_{i}_initialization"):
                    # Just accessing the agent should trigger any initialization
                    assert agent is not None
            
            # Get performance statistics
            stats = metrics.get_summary()
            
            # Verify performance is reasonable
            for operation in stats:
                if "execution_time" in operation:
                    assert stats[operation]["mean"] < 1.0, f"{operation} took too long: {stats[operation]['mean']:.3f}s"
                    assert stats[operation]["max"] < 2.0, f"{operation} max time too high: {stats[operation]['max']:.3f}s"
            
            print(f"Agent initialization performance: {stats}")
            
        except ImportError:
            pytest.skip("Enhanced agents not available")
    
    def test_tool_execution_performance(self):
        """Test tool execution performance."""
        metrics = PerformanceMetrics()
        
        try:
            from src.enhanced_tools import (
                get_all_street_names,
                get_building_ids_for_street,
                run_comprehensive_hp_analysis,
                run_comprehensive_dh_analysis,
                compare_comprehensive_scenarios,
                analyze_kpi_report,
                list_available_results,
                generate_comprehensive_kpi_report
            )
            
            tools = [
                ("get_all_street_names", get_all_street_names, []),
                ("list_available_results", list_available_results, []),
                ("get_building_ids_for_street", get_building_ids_for_street, ["Parkstraße"]),
                ("run_comprehensive_hp_analysis", run_comprehensive_hp_analysis, ["Parkstraße"]),
                ("run_comprehensive_dh_analysis", run_comprehensive_dh_analysis, ["Parkstraße"]),
                ("compare_comprehensive_scenarios", compare_comprehensive_scenarios, ["Parkstraße"]),
                ("generate_comprehensive_kpi_report", generate_comprehensive_kpi_report, ["Parkstraße"])
            ]
            
            # Test each tool multiple times for statistical significance
            iterations = 3
            
            for tool_name, tool_func, args in tools:
                for i in range(iterations):
                    with measure_performance(metrics, f"{tool_name}_execution"):
                        result = tool_func(*args)
                        assert result is not None
            
            # Get performance statistics
            stats = metrics.get_summary()
            
            # Verify performance is reasonable
            performance_limits = {
                "get_all_street_names_execution_time": 2.0,
                "list_available_results_execution_time": 2.0,
                "get_building_ids_for_street_execution_time": 3.0,
                "run_comprehensive_hp_analysis_execution_time": 10.0,
                "run_comprehensive_dh_analysis_execution_time": 10.0,
                "compare_comprehensive_scenarios_execution_time": 15.0,
                "generate_comprehensive_kpi_report_execution_time": 10.0
            }
            
            for operation, limit in performance_limits.items():
                if operation in stats:
                    assert stats[operation]["mean"] < limit, f"{operation} took too long: {stats[operation]['mean']:.3f}s (limit: {limit}s)"
                    assert stats[operation]["max"] < limit * 1.5, f"{operation} max time too high: {stats[operation]['max']:.3f}s"
            
            print(f"Tool execution performance: {stats}")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_memory_usage_performance(self):
        """Test memory usage performance."""
        metrics = PerformanceMetrics()
        
        try:
            from src.enhanced_tools import get_all_street_names, get_building_ids_for_street
            
            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Test memory usage during operations
            with measure_performance(metrics, "memory_usage_test"):
                # Perform multiple operations
                streets = get_all_street_names()
                assert len(streets) > 0
                
                # Test with multiple streets
                for street in streets[:5]:  # Test first 5 streets
                    building_ids = get_building_ids_for_street(street)
                    assert isinstance(building_ids, list)
            
            # Get final memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Verify memory usage is reasonable
            assert memory_increase < 200, f"Memory usage increased too much: {memory_increase:.2f}MB"
            
            # Get performance statistics
            stats = metrics.get_summary()
            print(f"Memory usage performance: {stats}")
            print(f"Total memory increase: {memory_increase:.2f}MB")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_concurrent_execution_performance(self):
        """Test concurrent execution performance."""
        import threading
        import queue
        
        metrics = PerformanceMetrics()
        results_queue = queue.Queue()
        
        try:
            from src.enhanced_tools import get_all_street_names, get_building_ids_for_street
            
            def worker(street_name, worker_id):
                """Worker function for concurrent execution."""
                start_time = time.time()
                try:
                    building_ids = get_building_ids_for_street(street_name)
                    execution_time = time.time() - start_time
                    results_queue.put({
                        "worker_id": worker_id,
                        "street": street_name,
                        "execution_time": execution_time,
                        "building_count": len(building_ids),
                        "success": True
                    })
                except Exception as e:
                    execution_time = time.time() - start_time
                    results_queue.put({
                        "worker_id": worker_id,
                        "street": street_name,
                        "execution_time": execution_time,
                        "error": str(e),
                        "success": False
                    })
            
            # Get test streets
            streets = get_all_street_names()
            assert len(streets) > 0
            
            # Test concurrent execution with multiple threads
            num_threads = min(5, len(streets))  # Use up to 5 threads
            test_streets = streets[:num_threads]
            
            threads = []
            start_time = time.time()
            
            # Start threads
            for i, street in enumerate(test_streets):
                thread = threading.Thread(target=worker, args=(street, i))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            
            # Collect results
            results = []
            while not results_queue.empty():
                results.append(results_queue.get())
            
            # Verify results
            assert len(results) == num_threads, f"Expected {num_threads} results, got {len(results)}"
            
            successful_results = [r for r in results if r["success"]]
            assert len(successful_results) > 0, "No successful concurrent executions"
            
            # Calculate performance metrics
            execution_times = [r["execution_time"] for r in successful_results]
            avg_execution_time = statistics.mean(execution_times)
            max_execution_time = max(execution_times)
            
            # Verify concurrent performance
            assert total_time < 15.0, f"Concurrent execution took too long: {total_time:.3f}s"
            assert avg_execution_time < 5.0, f"Average execution time too high: {avg_execution_time:.3f}s"
            assert max_execution_time < 10.0, f"Max execution time too high: {max_execution_time:.3f}s"
            
            print(f"Concurrent execution performance:")
            print(f"  Total time: {total_time:.3f}s")
            print(f"  Average execution time: {avg_execution_time:.3f}s")
            print(f"  Max execution time: {max_execution_time:.3f}s")
            print(f"  Successful executions: {len(successful_results)}/{num_threads}")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")

class TestADKAgentResponseTimes:
    """Test ADK agent response times."""
    
    def test_agent_response_time_simulation(self):
        """Test agent response time simulation."""
        metrics = PerformanceMetrics()
        
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
            
            # Test agent access time (simulating response time)
            for agent_name, agent in agents:
                for i in range(3):  # Test multiple times
                    with measure_performance(metrics, f"{agent_name}_access_time"):
                        # Simulate agent access/initialization
                        assert agent is not None
                        if hasattr(agent, 'config'):
                            config = agent.config
                            assert config is not None
            
            # Get performance statistics
            stats = metrics.get_summary()
            
            # Verify response times are reasonable
            for operation in stats:
                if "access_time" in operation:
                    assert stats[operation]["mean"] < 0.1, f"{operation} access time too high: {stats[operation]['mean']:.3f}s"
                    assert stats[operation]["max"] < 0.2, f"{operation} max access time too high: {stats[operation]['max']:.3f}s"
            
            print(f"Agent response time simulation: {stats}")
            
        except ImportError:
            pytest.skip("Enhanced agents not available")
    
    def test_tool_response_time_analysis(self):
        """Test tool response time analysis."""
        metrics = PerformanceMetrics()
        
        try:
            from src.enhanced_tools import (
                get_all_street_names,
                get_building_ids_for_street,
                run_comprehensive_hp_analysis
            )
            
            # Test response times for different tool operations
            operations = [
                ("street_listing", get_all_street_names, []),
                ("building_lookup", get_building_ids_for_street, ["Parkstraße"]),
                ("hp_analysis", run_comprehensive_hp_analysis, ["Parkstraße"])
            ]
            
            for op_name, op_func, args in operations:
                for i in range(3):  # Test multiple times
                    with measure_performance(metrics, f"{op_name}_response_time"):
                        result = op_func(*args)
                        assert result is not None
            
            # Get performance statistics
            stats = metrics.get_summary()
            
            # Define response time limits
            response_time_limits = {
                "street_listing_response_time": 2.0,
                "building_lookup_response_time": 3.0,
                "hp_analysis_response_time": 10.0
            }
            
            # Verify response times
            for operation, limit in response_time_limits.items():
                if operation in stats:
                    assert stats[operation]["mean"] < limit, f"{operation} response time too high: {stats[operation]['mean']:.3f}s"
                    assert stats[operation]["max"] < limit * 1.5, f"{operation} max response time too high: {stats[operation]['max']:.3f}s"
            
            print(f"Tool response time analysis: {stats}")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")

class TestADKSystemStability:
    """Test ADK system stability."""
    
    def test_system_stability_under_load(self):
        """Test system stability under load."""
        metrics = PerformanceMetrics()
        
        try:
            from src.enhanced_tools import get_all_street_names, get_building_ids_for_street
            
            # Test system stability with repeated operations
            num_iterations = 10
            
            with measure_performance(metrics, "stability_test"):
                for i in range(num_iterations):
                    # Perform operations that stress the system
                    streets = get_all_street_names()
                    assert len(streets) > 0
                    
                    # Test with multiple streets
                    for street in streets[:3]:  # Test first 3 streets
                        building_ids = get_building_ids_for_street(street)
                        assert isinstance(building_ids, list)
            
            # Get performance statistics
            stats = metrics.get_summary()
            
            # Verify system remained stable
            assert "stability_test_execution_time" in stats
            assert stats["stability_test_execution_time"]["mean"] < 30.0, "System became unstable under load"
            
            print(f"System stability under load: {stats}")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_memory_stability(self):
        """Test memory stability over time."""
        metrics = PerformanceMetrics()
        
        try:
            from src.enhanced_tools import get_all_street_names, get_building_ids_for_street
            
            process = psutil.Process()
            memory_readings = []
            
            # Test memory stability over multiple operations
            for i in range(10):
                # Perform operations
                streets = get_all_street_names()
                for street in streets[:2]:  # Test first 2 streets
                    building_ids = get_building_ids_for_street(street)
                
                # Record memory usage
                memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                memory_readings.append(memory_usage)
                
                # Small delay to allow memory cleanup
                time.sleep(0.1)
            
            # Analyze memory stability
            initial_memory = memory_readings[0]
            final_memory = memory_readings[-1]
            max_memory = max(memory_readings)
            min_memory = min(memory_readings)
            
            memory_increase = final_memory - initial_memory
            memory_variance = max_memory - min_memory
            
            # Verify memory stability
            assert memory_increase < 100, f"Memory leak detected: {memory_increase:.2f}MB increase"
            assert memory_variance < 150, f"Memory variance too high: {memory_variance:.2f}MB"
            
            print(f"Memory stability analysis:")
            print(f"  Initial memory: {initial_memory:.2f}MB")
            print(f"  Final memory: {final_memory:.2f}MB")
            print(f"  Memory increase: {memory_increase:.2f}MB")
            print(f"  Memory variance: {memory_variance:.2f}MB")
            print(f"  Max memory: {max_memory:.2f}MB")
            print(f"  Min memory: {min_memory:.2f}MB")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_error_recovery_stability(self):
        """Test error recovery and system stability."""
        metrics = PerformanceMetrics()
        
        try:
            from src.enhanced_tools import get_building_ids_for_street, run_comprehensive_hp_analysis
            
            # Test system stability after errors
            error_scenarios = [
                ("empty_street", ""),
                ("invalid_street", "NonExistentStreet123"),
                ("special_chars", "Street@#$%^&*()"),
                ("very_long_street", "A" * 1000)
            ]
            
            with measure_performance(metrics, "error_recovery_test"):
                for scenario_name, test_input in error_scenarios:
                    # Test that system handles errors gracefully
                    try:
                        result = get_building_ids_for_street(test_input)
                        assert isinstance(result, list)  # Should return list even for errors
                    except Exception as e:
                        # System should not crash on errors
                        assert False, f"System crashed on {scenario_name}: {e}"
                    
                    # Test that system can still perform normal operations after errors
                    try:
                        normal_result = get_building_ids_for_street("Parkstraße")
                        assert isinstance(normal_result, list)
                    except Exception as e:
                        assert False, f"System became unstable after {scenario_name}: {e}"
            
            # Get performance statistics
            stats = metrics.get_summary()
            
            # Verify error recovery performance
            assert "error_recovery_test_execution_time" in stats
            assert stats["error_recovery_test_execution_time"]["mean"] < 10.0, "Error recovery took too long"
            
            print(f"Error recovery stability: {stats}")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_system_resource_usage(self):
        """Test system resource usage."""
        metrics = PerformanceMetrics()
        
        try:
            from src.enhanced_tools import get_all_street_names, get_building_ids_for_street
            
            process = psutil.Process()
            
            # Get initial resource usage
            initial_cpu = process.cpu_percent()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            with measure_performance(metrics, "resource_usage_test"):
                # Perform operations
                streets = get_all_street_names()
                for street in streets[:5]:  # Test first 5 streets
                    building_ids = get_building_ids_for_street(street)
            
            # Get final resource usage
            final_cpu = process.cpu_percent()
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            cpu_usage = final_cpu - initial_cpu
            memory_usage = final_memory - initial_memory
            
            # Verify resource usage is reasonable
            assert memory_usage < 200, f"Memory usage too high: {memory_usage:.2f}MB"
            assert cpu_usage < 50, f"CPU usage too high: {cpu_usage:.2f}%"
            
            print(f"System resource usage:")
            print(f"  CPU usage: {cpu_usage:.2f}%")
            print(f"  Memory usage: {memory_usage:.2f}MB")
            print(f"  Initial memory: {initial_memory:.2f}MB")
            print(f"  Final memory: {final_memory:.2f}MB")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")

class TestADKPerformanceBenchmarks:
    """Test ADK performance benchmarks."""
    
    def test_benchmark_comparison(self):
        """Test benchmark comparison between different operations."""
        metrics = PerformanceMetrics()
        
        try:
            from src.enhanced_tools import (
                get_all_street_names,
                get_building_ids_for_street,
                run_comprehensive_hp_analysis,
                run_comprehensive_dh_analysis,
                compare_comprehensive_scenarios
            )
            
            # Define benchmark operations
            benchmarks = [
                ("data_retrieval", get_all_street_names, []),
                ("building_lookup", get_building_ids_for_street, ["Parkstraße"]),
                ("hp_analysis", run_comprehensive_hp_analysis, ["Parkstraße"]),
                ("dh_analysis", run_comprehensive_dh_analysis, ["Parkstraße"]),
                ("scenario_comparison", compare_comprehensive_scenarios, ["Parkstraße"])
            ]
            
            # Run benchmarks
            benchmark_results = {}
            
            for benchmark_name, benchmark_func, args in benchmarks:
                execution_times = []
                
                # Run benchmark multiple times
                for i in range(3):
                    with measure_performance(metrics, f"benchmark_{benchmark_name}"):
                        result = benchmark_func(*args)
                        assert result is not None
                
                # Get statistics
                stats = metrics.get_statistics(f"benchmark_{benchmark_name}")
                benchmark_results[benchmark_name] = stats
            
            # Analyze benchmark results
            print("Benchmark comparison results:")
            for benchmark_name, stats in benchmark_results.items():
                if stats:  # Check if stats is not empty
                    print(f"  {benchmark_name}:")
                    print(f"    Mean: {stats['mean']:.3f}s")
                    print(f"    Median: {stats['median']:.3f}s")
                    print(f"    Std Dev: {stats['std_dev']:.3f}s")
                    print(f"    Min: {stats['min']:.3f}s")
                    print(f"    Max: {stats['max']:.3f}s")
                else:
                    print(f"  {benchmark_name}: No data available")
            
            # Verify benchmark performance
            benchmark_limits = {
                "data_retrieval": 2.0,
                "building_lookup": 3.0,
                "hp_analysis": 10.0,
                "dh_analysis": 10.0,
                "scenario_comparison": 15.0
            }
            
            for benchmark_name, limit in benchmark_limits.items():
                if benchmark_name in benchmark_results:
                    stats = benchmark_results[benchmark_name]
                    assert stats["mean"] < limit, f"{benchmark_name} benchmark failed: {stats['mean']:.3f}s (limit: {limit}s)"
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_scalability_benchmark(self):
        """Test scalability benchmark."""
        metrics = PerformanceMetrics()
        
        try:
            from src.enhanced_tools import get_all_street_names, get_building_ids_for_street
            
            # Test scalability with increasing load
            streets = get_all_street_names()
            assert len(streets) > 0
            
            scalability_results = {}
            
            # Test with different numbers of streets
            test_sizes = [1, 3, 5, min(10, len(streets))]
            
            for size in test_sizes:
                test_streets = streets[:size]
                
                with measure_performance(metrics, f"scalability_{size}_streets"):
                    for street in test_streets:
                        building_ids = get_building_ids_for_street(street)
                        assert isinstance(building_ids, list)
                
                # Get statistics
                stats = metrics.get_statistics(f"scalability_{size}_streets")
                scalability_results[size] = stats
            
            # Analyze scalability
            print("Scalability benchmark results:")
            for size, stats in scalability_results.items():
                if stats:  # Check if stats is not empty
                    print(f"  {size} streets:")
                    print(f"    Mean: {stats['mean']:.3f}s")
                    print(f"    Per street: {stats['mean']/size:.3f}s")
                else:
                    print(f"  {size} streets: No data available")
            
            # Verify scalability (should be roughly linear)
            if len(scalability_results) > 1:
                sizes = list(scalability_results.keys())
                times = [scalability_results[size]["mean"] for size in sizes if scalability_results[size]]
                
                if len(times) > 1:  # Only check if we have valid data
                    # Check that time increases roughly linearly with size
                    for i in range(1, len(times)):
                        time_ratio = times[i] / times[i-1]
                        size_ratio = sizes[i] / sizes[i-1]
                        
                        # Time should not increase more than 2x the size increase
                        assert time_ratio < size_ratio * 2, f"Scalability issue: time increased {time_ratio:.2f}x for {size_ratio:.2f}x size increase"
            
        except ImportError:
            pytest.skip("Enhanced tools not available")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
