#!/usr/bin/env python3
"""
Example usage of the Branitz DH framework.

This script demonstrates basic functionality of the DH pipeline system.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dh_core.config import Config, DHDesign, Paths
from dh_core.data_adapters import DataAdapter, load_network_from_json, load_addresses_geojson
from dh_core.ppipe_builder import build_and_run
from dh_core.viz import Visualizer, gradient_layer, repaint_with_results
from dh_core.costs import CostCalculator


def create_sample_data():
    """Create sample data for demonstration."""
    np.random.seed(42)
    
    # Create sample timeline data
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    values = np.cumsum(np.random.randn(100)) + 100
    
    timeline_df = pd.DataFrame({
        'date': dates,
        'value': values,
        'category': np.random.choice(['A', 'B', 'C'], 100)
    })
    
    # Create sample correlation data
    n_samples = 200
    correlation_data = pd.DataFrame({
        'feature_1': np.random.randn(n_samples),
        'feature_2': np.random.randn(n_samples) + 0.5,
        'feature_3': np.random.randn(n_samples) - 0.3,
        'feature_4': np.random.randn(n_samples) + 0.8,
        'target': np.random.randn(n_samples)
    })
    
    return timeline_df, correlation_data


def example_data_processing():
    """Example of data processing with the framework."""
    print("=== Data Processing Example ===")
    
    # Initialize components
    config = Config()
    data_adapter = DataAdapter(config)
    
    # Create sample data
    timeline_df, correlation_data = create_sample_data()
    
    # Save sample data
    data_adapter.save_csv(timeline_df, "sample_timeline.csv")
    data_adapter.save_csv(correlation_data, "sample_correlation.csv")
    
    print("Sample data saved to inputs directory")
    
    # Load data back
    loaded_timeline = data_adapter.load_csv("sample_timeline.csv")
    loaded_correlation = data_adapter.load_csv("sample_correlation.csv")
    
    print(f"Loaded timeline data: {loaded_timeline.shape}")
    print(f"Loaded correlation data: {loaded_correlation.shape}")
    
    return loaded_timeline, loaded_correlation


def example_dh_simulation():
    """Example of district heating network simulation."""
    print("\n=== District Heating Simulation Example ===")
    
    # Initialize components
    paths = Paths()
    design = DHDesign(supply_c=75.0, return_c=45.0, u_w_per_m2k=0.35, sections=8)
    
    try:
        # Load network data
        pipes = load_network_from_json(f"{paths.inputs}/network_data.json")
        print(f"Loaded {len(pipes)} pipes from network data")
        
        # Load address data
        addr = load_addresses_geojson(f"{paths.inputs}/adressen_branitzer_siedlung.json")
        print(f"Loaded {len(addr)} address points")
        
        # Load building loads
        from dh_core.load_binding import load_design_loads_csv, match_loads_to_addresses_by_roundrobin
        loads = load_design_loads_csv(f"{paths.inputs}/building_loads_design_mittleres.csv")
        addr_with_loads = match_loads_to_addresses_by_roundrobin(loads, addr)
        
        print(f"Matched {len(loads)} loads to {addr_with_loads['Q_design_kW'].gt(0).sum()} address points")
        
        # Run pandapipes simulation
        print("Running pandapipes simulation...")
        net = build_and_run(
            pipes, addr_with_loads, 
            design.supply_c, design.return_c, 
            design.u_w_per_m2k, sections=design.sections
        )
        
        print("Simulation completed successfully!")
        print(f"Network has {len(net.pipe)} pipes and {len(net.junction)} junctions")
        
        # Show some results
        if hasattr(net, 'res_pipe') and len(net.res_pipe) > 0:
            print(f"Temperature range: {net.res_pipe['t_from_k'].min():.1f}K - {net.res_pipe['t_from_k'].max():.1f}K")
            print(f"Pressure range: {net.res_pipe['p_from_bar'].min():.2f} - {net.res_pipe['p_from_bar'].max():.2f} bar")
        
        return net
        
    except FileNotFoundError as e:
        print(f"Data file not found: {e}")
        print("Make sure you have the required data files in data/inputs/")
        return None
    except Exception as e:
        print(f"Simulation failed: {e}")
        return None


def example_visualization():
    """Example of visualization capabilities."""
    print("\n=== Visualization Example ===")
    
    config = Config()
    visualizer = Visualizer(config)
    
    # Create sample data
    timeline_df, correlation_data = create_sample_data()
    
    # Create visualizations
    print("Creating timeline plot...")
    fig1 = visualizer.plot_timeline(
        timeline_df, 
        'date', 
        'value', 
        'Sample Timeline',
        save_path="sample_timeline"
    )
    
    print("Creating distribution plot...")
    fig2 = visualizer.plot_distribution(
        correlation_data['feature_1'],
        'Feature 1 Distribution',
        save_path="sample_distribution"
    )
    
    print("Creating correlation heatmap...")
    fig3 = visualizer.plot_correlation_heatmap(
        correlation_data,
        'Feature Correlations',
        save_path="sample_correlations"
    )
    
    print("Visualizations saved to outputs directory")
    
    return fig1, fig2, fig3


def example_cost_tracking():
    """Example of cost tracking."""
    print("\n=== Cost Tracking Example ===")
    
    config = Config()
    cost_calc = CostCalculator(config)
    
    # Track some costs
    cost_calc.track_api_call(
        tokens_used=1500, 
        model="gpt-3.5-turbo",
        operation="text_analysis"
    )
    
    cost_calc.track_computation(
        duration_seconds=45,
        operation="data_processing"
    )
    
    cost_calc.track_storage(
        size_bytes=1024*1024*10,  # 10 MB
        operation="data_caching"
    )
    
    # Get cost summary
    summary = cost_calc.get_cost_summary(days=30)
    print(f"Total cost: ${summary['total_cost']:.4f} {summary['currency']}")
    print(f"Operation breakdown: {summary['operation_breakdown']}")
    
    # Save cost report
    report_path = cost_calc.save_cost_report("example_cost_report")
    print(f"Cost report saved to: {report_path}")
    
    return summary


def main():
    """Run all examples."""
    print("Branitz DH Framework - Example Usage")
    print("===================================")
    
    try:
        # Run examples
        example_data_processing()
        example_dh_simulation()
        example_visualization()
        example_cost_tracking()
        
        print("\n=== All Examples Completed Successfully! ===")
        print("\nCheck the following directories for outputs:")
        print("- data/outputs/: Generated visualizations and reports")
        print("- data/inputs/: Sample data files")
        print("- data/cache/: Cached results (if caching was used)")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
