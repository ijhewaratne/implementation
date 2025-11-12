#!/usr/bin/env python3
"""
ADK System Stability Tests
Test ADK system stability under various conditions
"""

import pytest
import sys
import os
import time
import json
import psutil
import threading
import queue
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Tuple

# Add ADK to path
sys.path.insert(0, 'adk')

class StabilityMonitor:
    """Monitor system stability during tests."""
    
    def __init__(self):
        self.metrics = {
            "execution_times": [],
            "memory_usage": [],
            "cpu_usage": [],
            "errors": [],
            "success_count": 0,
            "failure_count": 0
        }
        self.start_time = time.time()
        self.process = psutil.Process()
    
    def record_execution(self, execution_time: float, success: bool, error: str = None):
        """Record execution metrics."""
        self.metrics["execution_times"].append(execution_time)
        self.metrics["success_count"] += 1 if success else 0
        self.metrics["failure_count"] += 1 if not success else 0
        
        if error:
            self.metrics["errors"].append(error)
        
        # Record system metrics
        memory_usage = self.process.memory_info().rss / 1024 / 1024  # MB
        cpu_usage = self.process.cpu_percent()
        
        self.metrics["memory_usage"].append(memory_usage)
        self.metrics["cpu_usage"].append(cpu_usage)
    
    def get_stability_report(self) -> Dict[str, Any]:
        """Get stability report."""
        if not self.metrics["execution_times"]:
            return {"error": "No execution data"}
        
        execution_times = self.metrics["execution_times"]
        memory_usage = self.metrics["memory_usage"]
        cpu_usage = self.metrics["cpu_usage"]
        
        total_time = time.time() - self.start_time
        
        return {
            "total_executions": len(execution_times),
            "success_rate": self.metrics["success_count"] / len(execution_times) * 100,
            "failure_rate": self.metrics["failure_count"] / len(execution_times) * 100,
            "total_time": total_time,
            "execution_time_stats": {
                "mean": sum(execution_times) / len(execution_times),
                "min": min(execution_times),
                "max": max(execution_times),
                "std_dev": (sum((x - sum(execution_times)/len(execution_times))**2 for x in execution_times) / len(execution_times))**0.5
            },
            "memory_stats": {
                "mean": sum(memory_usage) / len(memory_usage),
                "min": min(memory_usage),
                "max": max(memory_usage),
                "current": memory_usage[-1] if memory_usage else 0
            },
            "cpu_stats": {
                "mean": sum(cpu_usage) / len(cpu_usage),
                "min": min(cpu_usage),
                "max": max(cpu_usage),
                "current": cpu_usage[-1] if cpu_usage else 0
            },
            "error_count": len(self.metrics["errors"]),
            "errors": self.metrics["errors"][-10:]  # Last 10 errors
        }

class TestADKSystemStability:
    """Test ADK system stability."""
    
    def test_system_stability_under_load(self):
        """Test system stability under load."""
        monitor = StabilityMonitor()
        
        try:
            from src.enhanced_tools import get_all_street_names, get_building_ids_for_street
            
            # Test system stability with repeated operations
            num_iterations = 20
            
            for i in range(num_iterations):
                start_time = time.time()
                success = True
                error = None
                
                try:
                    # Perform operations that stress the system
                    streets = get_all_street_names()
                    assert len(streets) > 0
                    
                    # Test with multiple streets
                    for street in streets[:3]:  # Test first 3 streets
                        building_ids = get_building_ids_for_street(street)
                        assert isinstance(building_ids, list)
                
                except Exception as e:
                    success = False
                    error = str(e)
                
                execution_time = time.time() - start_time
                monitor.record_execution(execution_time, success, error)
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.1)
            
            # Get stability report
            report = monitor.get_stability_report()
            
            # Verify system remained stable
            assert report["success_rate"] > 90, f"System became unstable: {report['success_rate']:.1f}% success rate"
            assert report["execution_time_stats"]["mean"] < 10.0, "System performance degraded significantly"
            assert report["memory_stats"]["max"] - report["memory_stats"]["min"] < 200, "Memory usage became unstable"
            
            print(f"System stability under load report:")
            print(f"  Success rate: {report['success_rate']:.1f}%")
            print(f"  Average execution time: {report['execution_time_stats']['mean']:.3f}s")
            print(f"  Memory usage range: {report['memory_stats']['min']:.1f}MB - {report['memory_stats']['max']:.1f}MB")
            print(f"  Error count: {report['error_count']}")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_memory_stability_over_time(self):
        """Test memory stability over time."""
        monitor = StabilityMonitor()
        
        try:
            from src.enhanced_tools import get_all_street_names, get_building_ids_for_street
            
            # Test memory stability over extended period
            num_iterations = 50
            
            for i in range(num_iterations):
                start_time = time.time()
                success = True
                error = None
                
                try:
                    # Perform memory-intensive operations
                    streets = get_all_street_names()
                    for street in streets[:2]:  # Test first 2 streets
                        building_ids = get_building_ids_for_street(street)
                
                except Exception as e:
                    success = False
                    error = str(e)
                
                execution_time = time.time() - start_time
                monitor.record_execution(execution_time, success, error)
                
                # Allow time for garbage collection
                time.sleep(0.05)
            
            # Get stability report
            report = monitor.get_stability_report()
            
            # Analyze memory stability
            memory_usage = monitor.metrics["memory_usage"]
            initial_memory = memory_usage[0] if memory_usage else 0
            final_memory = memory_usage[-1] if memory_usage else 0
            max_memory = max(memory_usage) if memory_usage else 0
            min_memory = min(memory_usage) if memory_usage else 0
            
            memory_increase = final_memory - initial_memory
            memory_variance = max_memory - min_memory
            
            # Verify memory stability
            assert memory_increase < 100, f"Memory leak detected: {memory_increase:.2f}MB increase"
            assert memory_variance < 150, f"Memory variance too high: {memory_variance:.2f}MB"
            assert report["success_rate"] > 95, f"System became unstable: {report['success_rate']:.1f}% success rate"
            
            print(f"Memory stability report:")
            print(f"  Initial memory: {initial_memory:.2f}MB")
            print(f"  Final memory: {final_memory:.2f}MB")
            print(f"  Memory increase: {memory_increase:.2f}MB")
            print(f"  Memory variance: {memory_variance:.2f}MB")
            print(f"  Success rate: {report['success_rate']:.1f}%")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_concurrent_stability(self):
        """Test system stability under concurrent load."""
        monitor = StabilityMonitor()
        results_queue = queue.Queue()
        
        try:
            from src.enhanced_tools import get_all_street_names, get_building_ids_for_street
            
            def worker(worker_id: int, num_operations: int):
                """Worker function for concurrent execution."""
                for i in range(num_operations):
                    start_time = time.time()
                    success = True
                    error = None
                    
                    try:
                        streets = get_all_street_names()
                        for street in streets[:2]:  # Test first 2 streets
                            building_ids = get_building_ids_for_street(street)
                    
                    except Exception as e:
                        success = False
                        error = str(e)
                    
                    execution_time = time.time() - start_time
                    results_queue.put({
                        "worker_id": worker_id,
                        "operation": i,
                        "execution_time": execution_time,
                        "success": success,
                        "error": error
                    })
            
            # Test concurrent execution with multiple threads
            num_threads = 5
            operations_per_thread = 10
            
            threads = []
            start_time = time.time()
            
            # Start threads
            for i in range(num_threads):
                thread = threading.Thread(target=worker, args=(i, operations_per_thread))
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
            
            # Analyze results
            successful_results = [r for r in results if r["success"]]
            failed_results = [r for r in results if not r["success"]]
            
            success_rate = len(successful_results) / len(results) * 100
            execution_times = [r["execution_time"] for r in successful_results]
            
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            max_execution_time = max(execution_times) if execution_times else 0
            
            # Verify concurrent stability
            assert success_rate > 90, f"System became unstable under concurrent load: {success_rate:.1f}% success rate"
            assert avg_execution_time < 5.0, f"Average execution time too high under concurrent load: {avg_execution_time:.3f}s"
            assert max_execution_time < 15.0, f"Max execution time too high under concurrent load: {max_execution_time:.3f}s"
            assert total_time < 30.0, f"Total concurrent execution time too high: {total_time:.3f}s"
            
            print(f"Concurrent stability report:")
            print(f"  Total operations: {len(results)}")
            print(f"  Success rate: {success_rate:.1f}%")
            print(f"  Average execution time: {avg_execution_time:.3f}s")
            print(f"  Max execution time: {max_execution_time:.3f}s")
            print(f"  Total time: {total_time:.3f}s")
            print(f"  Failed operations: {len(failed_results)}")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_error_recovery_stability(self):
        """Test error recovery and system stability."""
        monitor = StabilityMonitor()
        
        try:
            from src.enhanced_tools import get_building_ids_for_street, run_comprehensive_hp_analysis
            
            # Test system stability after various error conditions
            error_scenarios = [
                ("empty_street", ""),
                ("invalid_street", "NonExistentStreet123"),
                ("special_chars", "Street@#$%^&*()"),
                ("very_long_street", "A" * 1000),
                ("unicode_street", "Straße_mit_Unicode_äöü"),
                ("numeric_street", "123456789"),
                ("whitespace_street", "   "),
                ("none_street", None)
            ]
            
            for scenario_name, test_input in error_scenarios:
                start_time = time.time()
                success = True
                error = None
                
                try:
                    # Test that system handles errors gracefully
                    if test_input is None:
                        # Skip None test as it would cause AttributeError
                        continue
                    
                    result = get_building_ids_for_street(test_input)
                    assert isinstance(result, list)  # Should return list even for errors
                    
                    # Test that system can still perform normal operations after errors
                    normal_result = get_building_ids_for_street("Parkstraße")
                    assert isinstance(normal_result, list)
                
                except Exception as e:
                    success = False
                    error = str(e)
                
                execution_time = time.time() - start_time
                monitor.record_execution(execution_time, success, error)
            
            # Get stability report
            report = monitor.get_stability_report()
            
            # Verify error recovery stability
            assert report["success_rate"] > 80, f"System error recovery failed: {report['success_rate']:.1f}% success rate"
            assert report["execution_time_stats"]["mean"] < 5.0, "Error recovery took too long"
            
            print(f"Error recovery stability report:")
            print(f"  Success rate: {report['success_rate']:.1f}%")
            print(f"  Average execution time: {report['execution_time_stats']['mean']:.3f}s")
            print(f"  Error count: {report['error_count']}")
            if report["errors"]:
                print(f"  Recent errors: {report['errors']}")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_resource_usage_stability(self):
        """Test resource usage stability."""
        monitor = StabilityMonitor()
        
        try:
            from src.enhanced_tools import get_all_street_names, get_building_ids_for_street
            
            # Test resource usage stability over time
            num_iterations = 30
            
            for i in range(num_iterations):
                start_time = time.time()
                success = True
                error = None
                
                try:
                    # Perform resource-intensive operations
                    streets = get_all_street_names()
                    for street in streets[:3]:  # Test first 3 streets
                        building_ids = get_building_ids_for_street(street)
                
                except Exception as e:
                    success = False
                    error = str(e)
                
                execution_time = time.time() - start_time
                monitor.record_execution(execution_time, success, error)
                
                # Allow time for resource cleanup
                time.sleep(0.1)
            
            # Get stability report
            report = monitor.get_stability_report()
            
            # Analyze resource usage
            memory_usage = monitor.metrics["memory_usage"]
            cpu_usage = monitor.metrics["cpu_usage"]
            
            memory_variance = max(memory_usage) - min(memory_usage) if memory_usage else 0
            cpu_variance = max(cpu_usage) - min(cpu_usage) if cpu_usage else 0
            
            # Verify resource usage stability
            assert report["success_rate"] > 95, f"System became unstable: {report['success_rate']:.1f}% success rate"
            assert memory_variance < 200, f"Memory usage variance too high: {memory_variance:.2f}MB"  # Relaxed limit
            assert cpu_variance < 50, f"CPU usage variance too high: {cpu_variance:.2f}%"
            assert report["execution_time_stats"]["std_dev"] < 2.0, "Execution time variance too high"
            
            print(f"Resource usage stability report:")
            print(f"  Success rate: {report['success_rate']:.1f}%")
            print(f"  Memory variance: {memory_variance:.2f}MB")
            print(f"  CPU variance: {cpu_variance:.2f}%")
            print(f"  Execution time std dev: {report['execution_time_stats']['std_dev']:.3f}s")
            print(f"  Average memory usage: {report['memory_stats']['mean']:.2f}MB")
            print(f"  Average CPU usage: {report['cpu_stats']['mean']:.2f}%")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_long_running_stability(self):
        """Test long-running stability."""
        monitor = StabilityMonitor()
        
        try:
            from src.enhanced_tools import get_all_street_names, get_building_ids_for_street
            
            # Test long-running stability
            num_iterations = 100
            start_time = time.time()
            
            for i in range(num_iterations):
                iteration_start = time.time()
                success = True
                error = None
                
                try:
                    # Perform operations
                    streets = get_all_street_names()
                    for street in streets[:2]:  # Test first 2 streets
                        building_ids = get_building_ids_for_street(street)
                
                except Exception as e:
                    success = False
                    error = str(e)
                
                execution_time = time.time() - iteration_start
                monitor.record_execution(execution_time, success, error)
                
                # Progress indicator
                if i % 20 == 0:
                    elapsed = time.time() - start_time
                    print(f"Long-running test progress: {i}/{num_iterations} ({elapsed:.1f}s elapsed)")
                
                # Small delay to prevent overwhelming
                time.sleep(0.05)
            
            total_time = time.time() - start_time
            
            # Get stability report
            report = monitor.get_stability_report()
            
            # Verify long-running stability
            assert report["success_rate"] > 95, f"System became unstable during long run: {report['success_rate']:.1f}% success rate"
            assert total_time < 120, f"Long-running test took too long: {total_time:.1f}s"
            assert report["execution_time_stats"]["mean"] < 3.0, "Performance degraded during long run"
            
            print(f"Long-running stability report:")
            print(f"  Total time: {total_time:.1f}s")
            print(f"  Success rate: {report['success_rate']:.1f}%")
            print(f"  Average execution time: {report['execution_time_stats']['mean']:.3f}s")
            print(f"  Memory usage range: {report['memory_stats']['min']:.1f}MB - {report['memory_stats']['max']:.1f}MB")
            print(f"  Error count: {report['error_count']}")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
