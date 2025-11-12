"""
Integration Script: NPV Optimizer with Existing Dual-Pipe DH System

This script demonstrates how to integrate the NPV-based pipe diameter optimizer
with the existing dual-pipe district heating system.
"""

import sys
from pathlib import Path
import logging

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from npv_dh_integration import NPVDHIntegration
from npv_pipe_optimizer import PipeConstraints, EconomicParameters, PipeSegment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def integrate_with_existing_dh_system():
    """
    Demonstrate integration of NPV optimizer with existing DH system.
    """
    logger.info("Integrating NPV optimizer with existing dual-pipe DH system")

    # Initialize NPV DH integration
    pipe_catalog_path = "data/csv/pipe_catalog.csv"

    # Custom constraints for EN 13941 compliance
    constraints = PipeConstraints(
        max_velocity_m_s=1.5, min_temperature_difference_k=30.0, max_pressure_drop_bar_per_km=50.0
    )

    # Economic parameters for NPV calculation
    economic_params = EconomicParameters(
        discount_rate=0.05,  # 5% annual discount rate
        lifetime_years=30,
        electricity_cost_eur_mwh=80.0,
        heat_cost_eur_mwh=60.0,
        pump_efficiency=0.75,
        operation_hours_per_year=8760.0,
    )

    integration = NPVDHIntegration(pipe_catalog_path, constraints, economic_params)

    # Create sample pipe segments (simulating data from existing DH system)
    segments = [
        PipeSegment(
            length_m=100.0,
            heat_demand_kw=50.0,
            supply_temperature_c=80.0,
            return_temperature_c=50.0,
            flow_rate_m3_h=2.5,
            diameter_mm=50.0,  # Will be optimized
            cost_per_meter_eur=100.0,
        ),
        PipeSegment(
            length_m=150.0,
            heat_demand_kw=75.0,
            supply_temperature_c=80.0,
            return_temperature_c=50.0,
            flow_rate_m3_h=3.8,
            diameter_mm=65.0,  # Will be optimized
            cost_per_meter_eur=120.0,
        ),
        PipeSegment(
            length_m=200.0,
            heat_demand_kw=100.0,
            supply_temperature_c=80.0,
            return_temperature_c=50.0,
            flow_rate_m3_h=5.0,
            diameter_mm=80.0,  # Will be optimized
            cost_per_meter_eur=150.0,
        ),
    ]

    logger.info(f"Created {len(segments)} pipe segments for optimization")

    # Step 1: Optimize pipe diameters using NPV analysis
    logger.info("Step 1: Running NPV-based pipe diameter optimization")
    optimization_results = integration.optimize_pipe_diameters(segments)

    # Step 2: Create optimized pandapipes network
    logger.info("Step 2: Creating optimized pandapipes network")
    net = integration.create_optimized_pandapipes_network()

    # Step 3: Run hydraulic simulation
    logger.info("Step 3: Running hydraulic simulation")
    simulation_results = integration.run_hydraulic_simulation(net)

    # Step 4: Generate comprehensive reports
    logger.info("Step 4: Generating optimization reports")
    integration.generate_optimization_report("results_test/npv_dh_integration_report.txt")
    integration.save_optimization_results_csv("results_test/npv_dh_integration_results.csv")

    # Step 5: Print integration summary
    print("\n" + "=" * 80)
    print("NPV-BASED DH SYSTEM INTEGRATION SUMMARY")
    print("=" * 80)

    network_summary = optimization_results["network_summary"]
    print(f"✅ Network Optimization Complete:")
    print(f"   • Total Segments: {network_summary['total_segments']}")
    print(f"   • Network NPV: {network_summary['network_npv_eur']:.2f} EUR")
    print(f"   • Total Initial Cost: {network_summary['total_initial_cost_eur']:.2f} EUR")
    print(
        f"   • Total Annual Operating Cost: {network_summary['total_annual_operating_cost_eur']:.2f} EUR"
    )

    print(f"\n✅ Pandapipes Integration Complete:")
    print(f"   • Network Created: {len(net.pipe)} pipes")
    print(f"   • Junctions: {len(net.junction)}")
    print(f"   • External Grid: 1 heat source")

    print(f"\n✅ Hydraulic Simulation Complete:")
    print(f"   • Simulation Converged: {simulation_results['converged']}")
    print(f"   • Pipe Results: {len(simulation_results['pipe_results'])} pipes analyzed")
    print(
        f"   • Junction Results: {len(simulation_results['junction_results'])} junctions analyzed"
    )

    print(f"\n✅ EN 13941 Compliance:")
    for segment in integration.optimized_segments:
        print(
            f"   • {segment.segment_id}: Velocity={segment.velocity_m_s:.2f} m/s, "
            f"Pressure Drop={segment.pressure_drop_bar:.3f} bar"
        )

    print(f"\n✅ Reports Generated:")
    print(f"   • Optimization Report: results_test/npv_dh_integration_report.txt")
    print(f"   • Results CSV: results_test/npv_dh_integration_results.csv")

    print(f"\n🎯 Integration Benefits:")
    print(f"   • NPV-based optimal pipe diameter selection")
    print(f"   • EN 13941 constraint compliance (v ≤ 1.5 m/s, ΔT ≥ 30 K)")
    print(f"   • Economic analysis with 30-year lifetime")
    print(f"   • Seamless pandapipes integration")
    print(f"   • Comprehensive reporting and analysis")

    print("\n" + "=" * 80)
    print("Integration completed successfully! 🎉")
    print("=" * 80)

    return {
        "optimization_results": optimization_results,
        "network": net,
        "simulation_results": simulation_results,
        "optimized_segments": integration.optimized_segments,
    }


def demonstrate_agent_integration():
    """
    Demonstrate how the NPV optimizer can be integrated with the agent system.
    """
    logger.info("Demonstrating agent system integration")

    # This would be integrated into the existing agent tools
    print("\n🤖 AGENT SYSTEM INTEGRATION DEMONSTRATION")
    print("=" * 50)

    print("The NPV optimizer can be integrated into the existing agent system:")
    print("1. Add to tools/analysis_tools.py:")
    print("   - run_npv_optimized_dh_analysis()")
    print("   - integrate with existing run_comprehensive_dh_analysis()")

    print("\n2. Update simple_enhanced_agents.py:")
    print("   - Add NPV optimization capabilities to CentralHeatingAgent")
    print("   - Include economic analysis in agent responses")

    print("\n3. Enhance comparison tools:")
    print("   - Include NPV analysis in HP vs DH comparisons")
    print("   - Add economic metrics to comparison dashboards")

    print("\n4. Integration points:")
    print("   - Replace fixed pipe diameters with optimized diameters")
    print("   - Add economic analysis to existing DH network creation")
    print("   - Include NPV results in agent-generated reports")

    print("\n✅ Ready for full agent system integration!")


if __name__ == "__main__":
    try:
        # Run the integration demonstration
        results = integrate_with_existing_dh_system()

        # Demonstrate agent integration
        demonstrate_agent_integration()

        logger.info("NPV DH system integration demonstration completed successfully")

    except Exception as e:
        logger.error(f"Error in integration demonstration: {e}")
        raise
