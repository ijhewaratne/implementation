#!/usr/bin/env python3
"""
Demo: Automated DH Network Analysis Workflow

This script demonstrates the automated workflow for district heating network analysis.
It processes a predefined street and shows all the outputs generated.

Usage:
    python demo_automated_workflow.py
"""

import os
import sys
import json
from pathlib import Path


def demo_automated_workflow():
    """Demonstrate the automated workflow with a predefined street."""

    print("=" * 80)
    print("DEMO: AUTOMATED DH NETWORK ANALYSIS WORKFLOW")
    print("=" * 80)

    # Predefined street for demo
    demo_street = "Bleyerstraße"

    print(f"\n🎯 Demo Street: {demo_street}")
    print("\nThis demo will show the complete automated workflow:")
    print("1. Street selection and building extraction")
    print("2. Scenario creation")
    print("3. DH network simulation")
    print("4. LLM report generation")
    print("5. Interactive map creation")
    print("6. Consumer reports generation")
    print("7. Results summary")

    # Check if we have the required data
    data_file = "data/geojson/hausumringe_mit_adressenV3.geojson"
    if not os.path.exists(data_file):
        print(f"\n❌ Error: Required data file not found: {data_file}")
        print("Please ensure the data file is available.")
        return False

    print(f"\n✅ Data file found: {data_file}")

    # Import the interactive run functions
    try:
        from interactive_run_enhanced import (
            get_all_street_names,
            get_buildings_for_streets,
            create_street_buildings_geojson,
            create_street_scenario,
            run_simulation_for_street,
            generate_llm_report_for_street,
            generate_interactive_map_for_street,
            generate_consumer_reports_for_street,
        )
    except ImportError as e:
        print(f"\n❌ Error importing functions: {e}")
        return False

    # Create output directory
    output_dir = "street_analysis_outputs"
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n📁 Output directory: {output_dir}")

    # Step 1: Get buildings for the demo street
    print(f"\n{'='*60}")
    print(f"STEP 1: EXTRACTING BUILDINGS FOR {demo_street}")
    print(f"{'='*60}")

    buildings_features = get_buildings_for_streets(data_file, [demo_street])
    if not buildings_features:
        print(f"❌ No buildings found for {demo_street}")
        return False

    print(f"✅ Found {len(buildings_features)} buildings")

    # Step 2: Create building GeoJSON
    print(f"\n{'='*60}")
    print(f"STEP 2: CREATING BUILDING GEOJSON")
    print(f"{'='*60}")

    building_file = create_street_buildings_geojson(buildings_features, demo_street, output_dir)
    print(f"✅ Building file created: {building_file}")

    # Step 3: Create scenario
    print(f"\n{'='*60}")
    print(f"STEP 3: CREATING SCENARIO")
    print(f"{'='*60}")

    scenario_file = create_street_scenario(demo_street, building_file, output_dir)
    print(f"✅ Scenario file created: {scenario_file}")

    # Step 4: Run simulation
    print(f"\n{'='*60}")
    print(f"STEP 4: RUNNING DH NETWORK SIMULATION")
    print(f"{'='*60}")

    simulation_success = run_simulation_for_street(scenario_file, output_dir)
    if not simulation_success:
        print("❌ Simulation failed")
        return False

    print("✅ Simulation completed successfully")

    # Step 5: Generate LLM report
    print(f"\n{'='*60}")
    print(f"STEP 5: GENERATING LLM REPORT")
    print(f"{'='*60}")

    report_success = generate_llm_report_for_street(demo_street, output_dir)
    if report_success:
        print("✅ LLM report generated successfully")
    else:
        print("⚠️  LLM report generation failed")

    # Step 6: Generate interactive map
    print(f"\n{'='*60}")
    print(f"STEP 6: GENERATING INTERACTIVE MAP")
    print(f"{'='*60}")

    map_success = generate_interactive_map_for_street(demo_street, output_dir)
    if map_success:
        print("✅ Interactive map generated successfully")
    else:
        print("⚠️  Interactive map generation failed")

    # Step 7: Generate consumer reports
    print(f"\n{'='*60}")
    print(f"STEP 7: GENERATING CONSUMER REPORTS")
    print(f"{'='*60}")

    reports_success = generate_consumer_reports_for_street(demo_street, output_dir)
    if reports_success:
        print("✅ Consumer reports generated successfully")
    else:
        print("⚠️  Consumer reports generation failed")

    # Step 8: Show results summary
    print(f"\n{'='*80}")
    print("WORKFLOW COMPLETE - RESULTS SUMMARY")
    print(f"{'='*80}")

    clean_name = demo_street.replace(" ", "_").replace("/", "_").replace("\\", "_")

    # List all generated files
    generated_files = [
        f"Buildings: {output_dir}/buildings_{clean_name}.geojson",
        f"Scenario: {output_dir}/scenario_{clean_name}.json",
        f"Results: simulation_outputs/street_{clean_name}_results.json",
        f"Network Plot: simulation_outputs/dh_street_{clean_name}.png",
        f"LLM Report: {output_dir}/llm_report_{clean_name}.md",
        f"Interactive Map: {output_dir}/interactive_map_{clean_name}.html",
        f"Consumer Reports: {output_dir}/consumer_reports_{clean_name}.html",
    ]

    print(f"\n📋 Generated Files for {demo_street}:")
    for i, file_path in enumerate(generated_files, 1):
        status = "✅" if os.path.exists(file_path.split(": ")[1]) else "❌"
        print(f"  {i}. {status} {file_path}")

    # Show simulation results summary
    results_file = f"simulation_outputs/street_{clean_name}_results.json"
    if os.path.exists(results_file):
        try:
            with open(results_file, "r") as f:
                results = json.load(f)

            kpi = results.get("kpi", {})
            print(f"\n📊 Simulation Results Summary:")
            print(f"  • Number of Buildings: {kpi.get('num_buildings', 'N/A')}")
            print(f"  • Total Heat Demand: {kpi.get('heat_mwh', 'N/A')} MWh")
            print(f"  • Total Pipe Length: {kpi.get('total_pipe_length_km', 'N/A')} km")
            print(
                f"  • Network Density: {kpi.get('network_density_km_per_building', 'N/A')} km/building"
            )
            print(
                f"  • Hydraulic Success: {'✅ Yes' if kpi.get('hydraulic_success', False) else '❌ No'}"
            )
            print(f"  • Max Pressure Drop: {kpi.get('max_dp_bar', 'N/A')} bar")
        except Exception as e:
            print(f"⚠️  Could not read simulation results: {e}")

    print(f"\n🎉 Demo completed successfully!")
    print(f"\n💡 Next steps:")
    print(f"  1. Open the interactive map: {output_dir}/interactive_map_{clean_name}.html")
    print(f"  2. Review the LLM report: {output_dir}/llm_report_{clean_name}.md")
    print(f"  3. Check the consumer reports: {output_dir}/consumer_reports_{clean_name}.html")
    print(f"  4. Check the network plot: simulation_outputs/dh_street_{clean_name}.png")
    print(f"  5. Run the full interactive workflow: python interactive_run_enhanced.py")

    return True


if __name__ == "__main__":
    success = demo_automated_workflow()
    sys.exit(0 if success else 1)
