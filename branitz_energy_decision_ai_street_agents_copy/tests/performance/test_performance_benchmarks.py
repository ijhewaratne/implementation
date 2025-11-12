"""
Performance Benchmarking Tests

Tests simulation performance with various network sizes to ensure
execution times remain acceptable for production use.

Benchmarks:
- Small networks (3-5 buildings): Should be < 10s
- Medium networks (10-20 buildings): Should be < 30s
- Large networks (50+ buildings): Should be < 60s
"""

import sys
from pathlib import Path
import time
import geopandas as gpd
from shapely.geometry import Point
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.simulators import (
    DistrictHeatingSimulator,
    HeatPumpElectricalSimulator,
    SimulationMode,
)


def create_test_buildings(num_buildings: int, seed: int = 42) -> gpd.GeoDataFrame:
    """
    Create test building dataset of specified size.
    
    Args:
        num_buildings: Number of buildings to create
        seed: Random seed for reproducibility
    
    Returns:
        GeoDataFrame with buildings
    """
    np.random.seed(seed)
    
    # Create buildings in a grid pattern
    grid_size = int(np.ceil(np.sqrt(num_buildings)))
    buildings_data = []
    
    for i in range(num_buildings):
        row = i // grid_size
        col = i % grid_size
        
        buildings_data.append({
            'GebaeudeID': f'BENCH_B{i:04d}',
            'heating_load_kw': np.random.uniform(30, 100),
            'base_electric_load_kw': np.random.uniform(1.5, 3.5),
            'geometry': Point(col * 60, row * 60).buffer(10)
        })
    
    return gpd.GeoDataFrame(buildings_data, crs='EPSG:25833')


def benchmark_dh_simulation(num_buildings: int) -> dict:
    """
    Benchmark DH simulation with specified network size.
    
    Args:
        num_buildings: Number of buildings to simulate
    
    Returns:
        Dictionary with benchmark results
    """
    print(f"\n{'='*60}")
    print(f"DH BENCHMARK: {num_buildings} buildings")
    print(f"{'='*60}")
    
    # Create test data
    buildings = create_test_buildings(num_buildings)
    total_demand = buildings['heating_load_kw'].sum()
    
    # Configure simulator
    config = {
        "supply_temp_c": 85.0,
        "return_temp_c": 55.0,
        "scenario_name": f"Benchmark_DH_{num_buildings}b"
    }
    
    try:
        # Create simulator
        simulator = DistrictHeatingSimulator(config)
        
        # Measure network creation
        start_time = time.time()
        simulator.validate_inputs(buildings)
        validation_time = time.time() - start_time
        
        start_time = time.time()
        simulator.create_network(buildings)
        network_time = time.time() - start_time
        
        # Measure simulation
        start_time = time.time()
        result = simulator.run_simulation()
        simulation_time = time.time() - start_time
        
        total_time = validation_time + network_time + simulation_time
        
        # Print results
        print(f"  Total demand: {total_demand:.1f} kW")
        print(f"  Validation time: {validation_time:.3f}s")
        print(f"  Network creation: {network_time:.3f}s")
        print(f"  Simulation time: {simulation_time:.3f}s")
        print(f"  Total time: {total_time:.3f}s")
        
        if result.success:
            print(f"  ✅ Success")
            print(f"  Network: {result.kpi.get('num_junctions', 0)} junctions, "
                  f"{result.kpi.get('num_pipes', 0)} pipes")
            print(f"  Pressure: {result.kpi.get('max_pressure_drop_bar', 0):.3f} bar")
        else:
            print(f"  ⚠️  Simulation failed: {result.error}")
            print(f"  Mode: {result.simulation_mode.value}")
        
        return {
            "num_buildings": num_buildings,
            "success": result.success,
            "mode": result.simulation_mode.value,
            "validation_time_s": validation_time,
            "network_time_s": network_time,
            "simulation_time_s": simulation_time,
            "total_time_s": total_time,
            "num_junctions": result.kpi.get('num_junctions', 0) if result.success else 0,
            "num_pipes": result.kpi.get('num_pipes', 0) if result.success else 0,
        }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {
            "num_buildings": num_buildings,
            "success": False,
            "error": str(e),
            "total_time_s": 0
        }


def benchmark_hp_simulation(num_buildings: int) -> dict:
    """
    Benchmark HP simulation with specified network size.
    
    Args:
        num_buildings: Number of buildings to simulate
    
    Returns:
        Dictionary with benchmark results
    """
    print(f"\n{'='*60}")
    print(f"HP BENCHMARK: {num_buildings} buildings")
    print(f"{'='*60}")
    
    # Create test data
    buildings = create_test_buildings(num_buildings)
    total_demand = buildings['heating_load_kw'].sum()
    
    # Configure simulator
    config = {
        "hp_thermal_kw": 6.0,
        "hp_cop": 2.8,
        "hp_three_phase": True,
        "scenario_name": f"Benchmark_HP_{num_buildings}b"
    }
    
    try:
        # Create simulator
        simulator = HeatPumpElectricalSimulator(config)
        
        # Measure network creation
        start_time = time.time()
        simulator.validate_inputs(buildings)
        validation_time = time.time() - start_time
        
        start_time = time.time()
        simulator.create_network(buildings)
        network_time = time.time() - start_time
        
        # Measure simulation
        start_time = time.time()
        result = simulator.run_simulation()
        simulation_time = time.time() - start_time
        
        total_time = validation_time + network_time + simulation_time
        
        # Print results
        print(f"  Total demand: {total_demand:.1f} kW")
        print(f"  Validation time: {validation_time:.3f}s")
        print(f"  Network creation: {network_time:.3f}s")
        print(f"  Simulation time: {simulation_time:.3f}s")
        print(f"  Total time: {total_time:.3f}s")
        
        if result.success:
            print(f"  ✅ Success")
            print(f"  Network: {result.kpi.get('num_buses', 0)} buses, "
                  f"{result.kpi.get('num_lines', 0)} lines")
            print(f"  Min voltage: {result.kpi.get('min_voltage_pu', 0):.3f} pu")
            print(f"  Max loading: {result.kpi.get('max_line_loading_pct', 0):.1f}%")
        else:
            print(f"  ⚠️  Simulation failed: {result.error}")
            print(f"  Mode: {result.simulation_mode.value}")
        
        return {
            "num_buildings": num_buildings,
            "success": result.success,
            "mode": result.simulation_mode.value,
            "validation_time_s": validation_time,
            "network_time_s": network_time,
            "simulation_time_s": simulation_time,
            "total_time_s": total_time,
            "num_buses": result.kpi.get('num_buses', 0) if result.success else 0,
            "num_lines": result.kpi.get('num_lines', 0) if result.success else 0,
        }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {
            "num_buildings": num_buildings,
            "success": False,
            "error": str(e),
            "total_time_s": 0
        }


def run_performance_benchmarks():
    """
    Run comprehensive performance benchmarks.
    
    Tests various network sizes to establish performance baseline.
    """
    print("\n" + "="*70)
    print("PERFORMANCE BENCHMARK SUITE")
    print("="*70)
    
    # Test sizes
    test_sizes = [3, 5, 10, 20]
    
    dh_results = []
    hp_results = []
    
    # DH Benchmarks
    print("\n" + "="*70)
    print("DISTRICT HEATING BENCHMARKS")
    print("="*70)
    
    for size in test_sizes:
        result = benchmark_dh_simulation(size)
        dh_results.append(result)
    
    # HP Benchmarks
    print("\n" + "="*70)
    print("HEAT PUMP BENCHMARKS")
    print("="*70)
    
    for size in test_sizes:
        result = benchmark_hp_simulation(size)
        hp_results.append(result)
    
    # Summary
    print("\n" + "="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)
    
    print("\nDistrict Heating Performance:")
    print(f"{'Buildings':<12} {'Time (s)':<10} {'Status':<10} {'Network Size':<20}")
    print("-" * 60)
    for r in dh_results:
        status = "✅ PASS" if r['success'] and r['total_time_s'] < 30 else "⚠️  SLOW"
        network = f"{r.get('num_junctions', 0)}j, {r.get('num_pipes', 0)}p"
        print(f"{r['num_buildings']:<12} {r['total_time_s']:<10.2f} {status:<10} {network:<20}")
    
    print("\nHeat Pump Performance:")
    print(f"{'Buildings':<12} {'Time (s)':<10} {'Status':<10} {'Network Size':<20}")
    print("-" * 60)
    for r in hp_results:
        status = "✅ PASS" if r['success'] and r['total_time_s'] < 30 else "⚠️  SLOW"
        network = f"{r.get('num_buses', 0)}b, {r.get('num_lines', 0)}l"
        print(f"{r['num_buildings']:<12} {r['total_time_s']:<10.2f} {status:<10} {network:<20}")
    
    # Performance criteria
    print("\n" + "="*70)
    print("PERFORMANCE CRITERIA")
    print("="*70)
    
    all_pass = True
    
    # Check if all simulations meet performance targets
    for r in dh_results + hp_results:
        if r['num_buildings'] <= 10 and r['total_time_s'] > 10:
            print(f"⚠️  Warning: {r['num_buildings']} buildings took {r['total_time_s']:.1f}s (target: <10s)")
            all_pass = False
        elif r['num_buildings'] <= 50 and r['total_time_s'] > 30:
            print(f"⚠️  Warning: {r['num_buildings']} buildings took {r['total_time_s']:.1f}s (target: <30s)")
            all_pass = False
    
    if all_pass:
        print("✅ All performance targets met!")
    
    # Calculate statistics
    dh_times = [r['total_time_s'] for r in dh_results if r['success']]
    hp_times = [r['total_time_s'] for r in hp_results if r['success']]
    
    if dh_times:
        print(f"\nDH Statistics:")
        print(f"  Average time: {np.mean(dh_times):.2f}s")
        print(f"  Min time: {np.min(dh_times):.2f}s")
        print(f"  Max time: {np.max(dh_times):.2f}s")
    
    if hp_times:
        print(f"\nHP Statistics:")
        print(f"  Average time: {np.mean(hp_times):.2f}s")
        print(f"  Min time: {np.min(hp_times):.2f}s")
        print(f"  Max time: {np.max(hp_times):.2f}s")
    
    return {"dh": dh_results, "hp": hp_results}


if __name__ == "__main__":
    """Run performance benchmarks."""
    results = run_performance_benchmarks()
    
    print("\n" + "="*70)
    print("BENCHMARK COMPLETE")
    print("="*70)
    
    # Check if all passed
    all_successful = all(
        r['success'] for r in results['dh'] + results['hp']
    )
    
    if all_successful:
        print("\n✅ All benchmarks completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Some benchmarks failed - check output above")
        sys.exit(1)

