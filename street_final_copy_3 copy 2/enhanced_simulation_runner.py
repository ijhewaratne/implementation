#!/usr/bin/env python3
"""
Enhanced Simulation Runner - Dual-Pipe District Heating Network

This enhanced version integrates our dual-pipe district heating network implementation
with the existing batch processing framework, providing:

1. Real pandapipes simulations for dual-pipe DH networks
2. Street-based scenario generation and selection
3. Comprehensive result reporting with interactive maps
4. Batch processing capabilities for large-scale analysis
5. Support for individual streets, multiple streets, and entire region
"""

import argparse
import json
import os
import sys
from pathlib import Path
import multiprocessing
import traceback
import yaml
import questionary
import geopandas as gpd
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

# Import our dual-pipe network classes
from create_complete_dual_pipe_dh_network_improved import ImprovedDualPipeDHNetwork
from simulate_dual_pipe_dh_network_final import FinalDualPipeDHSimulation

try:
    import folium

    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print("Warning: folium not available. Interactive maps will be skipped.")

RESULTS_DIR = Path("simulation_outputs")
RESULTS_DIR.mkdir(exist_ok=True)


class StreetBasedScenarioGenerator:
    """Generate scenarios for street-based dual-pipe DH analysis."""

    def __init__(self, data_geojson_path="data/geojson/hausumringe_mit_adressenV3.geojson"):
        self.data_geojson_path = data_geojson_path
        self.scenarios_dir = Path("scenarios")
        self.scenarios_dir.mkdir(exist_ok=True)

    def get_all_street_names(self):
        """Get all available street names from the data."""
        print(f"Reading all street names from {self.data_geojson_path}...")
        street_names = set()

        with open(self.data_geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for feature in data["features"]:
            for adr in feature.get("adressen", []):
                street_val = adr.get("str")
                if street_val:
                    street_names.add(street_val.strip())

        print(f"Found {len(street_names)} unique streets.")
        return sorted(list(street_names))

    def get_buildings_for_streets(self, selected_streets):
        """Get buildings for selected streets."""
        print(f"Fetching buildings for selected streets...")
        street_set = {s.lower() for s in selected_streets}
        selected_features = []

        with open(self.data_geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for feature in data["features"]:
            for adr in feature.get("adressen", []):
                street_val = adr.get("str")
                if street_val and street_val.strip().lower() in street_set:
                    selected_features.append(feature)
                    break

        print(f"Found {len(selected_features)} buildings.")
        return selected_features

    def get_all_buildings(self):
        """Get all buildings from the entire region."""
        print(f"Fetching all buildings from the entire region...")
        selected_features = []

        with open(self.data_geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for feature in data["features"]:
            selected_features.append(feature)

        print(f"Found {len(selected_features)} buildings in the entire region.")
        return selected_features

    def create_buildings_geojson(self, buildings_features, scenario_name):
        """Create GeoJSON file for buildings."""
        buildings_geojson = {"type": "FeatureCollection", "features": buildings_features}

        output_file = self.scenarios_dir / f"buildings_{scenario_name}.geojson"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(buildings_geojson, f, indent=2)

        print(f"Created building file: {output_file}")
        return str(output_file)

    def generate_street_scenarios(self, selection_type, selected_streets=None):
        """Generate scenarios based on selection type."""
        scenarios = []

        if selection_type == "individual_street":
            # Single street scenario
            street_name = selected_streets[0]
            clean_name = street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")

            buildings_features = self.get_buildings_for_streets([street_name])
            building_file = self.create_buildings_geojson(buildings_features, clean_name)

            scenario = {
                "name": f"dual_pipe_{clean_name}",
                "description": f"Dual-pipe DH network for {street_name}",
                "type": "DH",
                "params": {
                    "supply_temp": 70,
                    "return_temp": 40,
                    "tech": "dual_pipe_dh",
                    "street_name": street_name,
                    "num_buildings": len(buildings_features),
                    "selection_type": "individual_street",
                },
                "building_file": building_file,
                "network_file": "results_test/streets.geojson",
                "weather": {"file": "data/csv/TRY2015_517475143730_Jahr.dat"},
            }
            scenarios.append(scenario)

        elif selection_type == "multiple_streets":
            # Multiple streets scenario
            for street_name in selected_streets:
                clean_name = street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")

                buildings_features = self.get_buildings_for_streets([street_name])
                building_file = self.create_buildings_geojson(buildings_features, clean_name)

                scenario = {
                    "name": f"dual_pipe_{clean_name}",
                    "description": f"Dual-pipe DH network for {street_name}",
                    "type": "DH",
                    "params": {
                        "supply_temp": 70,
                        "return_temp": 40,
                        "tech": "dual_pipe_dh",
                        "street_name": street_name,
                        "num_buildings": len(buildings_features),
                        "selection_type": "multiple_streets",
                    },
                    "building_file": building_file,
                    "network_file": "results_test/streets.geojson",
                    "weather": {"file": "data/csv/TRY2015_517475143730_Jahr.dat"},
                }
                scenarios.append(scenario)

        elif selection_type == "entire_region":
            # Entire region scenario
            buildings_features = self.get_all_buildings()
            building_file = self.create_buildings_geojson(buildings_features, "entire_region")

            scenario = {
                "name": "dual_pipe_entire_region",
                "description": "Dual-pipe DH network for entire region",
                "type": "DH",
                "params": {
                    "supply_temp": 70,
                    "return_temp": 40,
                    "tech": "dual_pipe_dh",
                    "street_name": "entire_region",
                    "num_buildings": len(buildings_features),
                    "selection_type": "entire_region",
                },
                "building_file": building_file,
                "network_file": "results_test/streets.geojson",
                "weather": {"file": "data/csv/TRY2015_517475143730_Jahr.dat"},
            }
            scenarios.append(scenario)

        return scenarios


def run_dual_pipe_dh_simulation(scenario):
    """
    Run a complete dual-pipe DH simulation using our implementation.
    Returns comprehensive results including network statistics and pandapipes simulation.
    """
    try:
        print(f"🏗️ Running dual-pipe DH simulation for scenario: {scenario['name']}")

        # Create output directory for this scenario
        scenario_output_dir = RESULTS_DIR / scenario["name"]
        scenario_output_dir.mkdir(exist_ok=True)

        # Initialize dual-pipe network creator
        network_creator = ImprovedDualPipeDHNetwork(results_dir=str(scenario_output_dir))

        # Load data
        network_creator.load_data()

        # Build connected street network
        network_creator.build_connected_street_network()

        # Snap buildings to street network
        network_creator.snap_buildings_to_street_network()

        # Create dual-pipe network
        network_creator.create_dual_pipe_network()

        # Create dual service connections
        network_creator.create_dual_service_connections()

        # Calculate statistics
        network_creator.calculate_dual_network_statistics()

        # Create interactive map
        map_file = scenario_output_dir / f"dual_pipe_map_{scenario['name']}.html"
        network_creator.create_dual_pipe_interactive_map(save_path=str(map_file))

        # Save network results
        network_creator.save_dual_pipe_results(scenario["name"])

        # Run pandapipes simulation
        print(f"🔄 Running pandapipes simulation for {scenario['name']}...")
        simulator = FinalDualPipeDHSimulation(results_dir=str(scenario_output_dir))
        simulation_success = simulator.run_complete_simulation(scenario["name"])

        # Load simulation results
        simulation_results = {}
        sim_file = scenario_output_dir / f"pandapipes_simulation_results_{scenario['name']}.json"
        if sim_file.exists():
            with open(sim_file, "r") as f:
                simulation_results = json.load(f)

        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(v) for v in obj]
            elif hasattr(obj, "item"):  # numpy types
                return obj.item()
            else:
                return obj

        # Compile comprehensive results
        results = {
            "scenario": scenario["name"],
            "type": "DH",
            "success": True,
            "description": scenario.get("description", ""),
            "params": scenario.get("params", {}),
            "network_stats": convert_numpy_types(network_creator.network_stats),
            "simulation_results": convert_numpy_types(simulation_results),
            "kpi": {
                "total_heat_supplied_mwh": float(
                    network_creator.network_stats.get("total_heat_demand_mwh", 0)
                ),
                "total_pipe_length_km": float(
                    network_creator.network_stats.get("total_pipe_length_km", 0)
                ),
                "num_buildings": int(network_creator.network_stats.get("num_buildings", 0)),
                "service_connections": int(
                    network_creator.network_stats.get("service_connections", 0)
                ),
                "max_pressure_drop_bar": float(simulation_results.get("pressure_drop_bar", 0)),
                "total_flow_kg_per_s": float(simulation_results.get("total_flow_kg_per_s", 0)),
                "temperature_drop_c": float(simulation_results.get("temperature_drop_c", 0)),
                "hydraulic_success": bool(simulation_results.get("hydraulic_success", False)),
                "convergence_achieved": bool(simulation_results.get("convergence_achieved", False)),
            },
            "output_files": {
                "network_map": str(map_file),
                "network_stats": str(
                    scenario_output_dir / f"dual_network_stats_{scenario['name']}.json"
                ),
                "simulation_results": str(sim_file),
                "supply_pipes": str(
                    scenario_output_dir / f"dual_supply_pipes_{scenario['name']}.csv"
                ),
                "return_pipes": str(
                    scenario_output_dir / f"dual_return_pipes_{scenario['name']}.csv"
                ),
                "service_connections": str(
                    scenario_output_dir / f"dual_service_connections_{scenario['name']}.csv"
                ),
            },
            "timestamp": datetime.now().isoformat(),
        }

        print(f"✅ Dual-pipe DH simulation completed for {scenario['name']}")
        return results

    except Exception as e:
        traceback.print_exc()
        return {
            "scenario": scenario.get("name", ""),
            "type": "DH",
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def run_pandapower_simulation(scenario):
    """
    Placeholder: Run a single pandapower simulation for HP scenario.
    Returns dict of results/KPIs for this scenario.
    """
    try:
        print(f"Running HP simulation for scenario: {scenario['name']}")
        # TODO: Implement real pandapower simulation
        results = {
            "scenario": scenario["name"],
            "type": "HP",
            "success": True,
            "kpi": {"max_feeder_load_percent": 82, "transformer_overloads": 1},
        }
        return results
    except Exception as e:
        traceback.print_exc()
        return {
            "scenario": scenario.get("name", ""),
            "type": "HP",
            "success": False,
            "error": str(e),
        }


def run_scenario(scenario_file):
    """
    Load scenario JSON, call the correct simulation function, and save results.
    """
    try:
        with open(scenario_file, "r", encoding="utf-8") as f:
            scenario = json.load(f)

        if scenario.get("type", "DH").upper() == "DH":
            results = run_dual_pipe_dh_simulation(scenario)
        elif scenario.get("type", "DH").upper() == "HP":
            results = run_pandapower_simulation(scenario)
        else:
            raise ValueError(f"Unknown scenario type: {scenario.get('type')}")

        # Save results to output file
        out_file = RESULTS_DIR / f"{scenario['name']}_results.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved: {out_file}")
        return results
    except Exception as e:
        traceback.print_exc()
        return {"scenario_file": scenario_file, "success": False, "error": str(e)}


def run_simulation_scenarios(scenario_files, parallel=True):
    """
    Batch run all scenario files. Can use multiprocessing.
    """
    print(f"Running simulations for {len(scenario_files)} scenarios...")
    if parallel and len(scenario_files) > 1:
        with multiprocessing.Pool(processes=min(4, len(scenario_files))) as pool:
            results = pool.map(run_scenario, scenario_files)
    else:
        results = [run_scenario(sf) for sf in scenario_files]
    print("\nAll simulations complete.")
    return results


def interactive_scenario_generation():
    """Interactive scenario generation with street-based selection."""
    print("🏗️ ENHANCED SIMULATION RUNNER - DUAL-PIPE DISTRICT HEATING")
    print("=" * 80)
    print("🎯 STREET-BASED SCENARIO GENERATION")
    print("=" * 80)

    # Initialize scenario generator
    generator = StreetBasedScenarioGenerator()

    # Get selection type
    selection_type = questionary.select(
        "What type of analysis would you like to perform?",
        choices=[
            "🏠 Individual Street - Analyze one specific street",
            "🏘️ Multiple Streets - Analyze several selected streets",
            "🌍 Entire Region - Analyze all buildings in the region",
            "❌ Exit",
        ],
    ).ask()

    if selection_type == "❌ Exit":
        print("Exiting. Goodbye!")
        return []

    # Get street selection based on type
    if selection_type == "🏠 Individual Street - Analyze one specific street":
        all_streets = generator.get_all_street_names()
        selected_street = questionary.select(
            "Select the street you want to analyze:", choices=all_streets
        ).ask()
        selected_streets = [selected_street] if selected_street else []
        selection_type_key = "individual_street"

    elif selection_type == "🏘️ Multiple Streets - Analyze several selected streets":
        all_streets = generator.get_all_street_names()
        selected_streets = questionary.checkbox(
            "Select the streets you want to analyze (use space to select, enter to confirm):",
            choices=all_streets,
        ).ask()
        selection_type_key = "multiple_streets"

    elif selection_type == "🌍 Entire Region - Analyze all buildings in the region":
        selected_streets = []
        selection_type_key = "entire_region"

    else:
        print("Invalid selection. Exiting.")
        return []

    if not selected_streets and selection_type_key != "entire_region":
        print("No streets selected. Exiting.")
        return []

    # Generate scenarios
    print(f"\nGenerating scenarios for {selection_type_key}...")
    scenarios = generator.generate_street_scenarios(selection_type_key, selected_streets)

    # Save scenario files
    scenario_files = []
    for scenario in scenarios:
        scenario_file = generator.scenarios_dir / f"{scenario['name']}_scenario.json"
        with open(scenario_file, "w", encoding="utf-8") as f:
            json.dump(scenario, f, indent=2)
        scenario_files.append(str(scenario_file))
        print(f"✅ Scenario '{scenario['name']}' saved to {scenario_file}")

    return scenario_files


def generate_summary_report(results):
    """Generate a comprehensive summary report of all simulation results."""
    print("\n" + "=" * 80)
    print("📊 SIMULATION SUMMARY REPORT")
    print("=" * 80)

    successful_simulations = [r for r in results if r.get("success", False)]
    failed_simulations = [r for r in results if not r.get("success", False)]

    print(f"✅ Successful simulations: {len(successful_simulations)}")
    print(f"❌ Failed simulations: {len(failed_simulations)}")

    if successful_simulations:
        print("\n📈 SUCCESSFUL SIMULATIONS:")
        for result in successful_simulations:
            scenario_name = result.get("scenario", "Unknown")
            kpi = result.get("kpi", {})

            print(f"\n🏗️ {scenario_name}:")
            print(f"   • Buildings: {kpi.get('num_buildings', 'N/A')}")
            print(f"   • Heat Demand: {kpi.get('total_heat_supplied_mwh', 'N/A'):.1f} MWh/year")
            print(f"   • Pipe Length: {kpi.get('total_pipe_length_km', 'N/A'):.1f} km")
            print(f"   • Service Connections: {kpi.get('service_connections', 'N/A')}")
            print(f"   • Pressure Drop: {kpi.get('max_pressure_drop_bar', 'N/A'):.6f} bar")
            print(f"   • Total Flow: {kpi.get('total_flow_kg_per_s', 'N/A'):.1f} kg/s")
            print(
                f"   • Hydraulic Success: {'✅ Yes' if kpi.get('hydraulic_success', False) else '❌ No'}"
            )

    if failed_simulations:
        print("\n❌ FAILED SIMULATIONS:")
        for result in failed_simulations:
            scenario_name = result.get("scenario", "Unknown")
            error = result.get("error", "Unknown error")
            print(f"   • {scenario_name}: {error}")

    # Save summary report
    summary_file = RESULTS_DIR / "simulation_summary_report.json"
    summary_data = {
        "timestamp": datetime.now().isoformat(),
        "total_simulations": len(results),
        "successful_simulations": len(successful_simulations),
        "failed_simulations": len(failed_simulations),
        "results": results,
    }

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    print(f"\n📋 Summary report saved to: {summary_file}")
    print(f"📁 All results saved in: {RESULTS_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enhanced simulation runner for dual-pipe district heating networks."
    )
    parser.add_argument("--scenarios", nargs="+", help="List of scenario JSON files to run")
    parser.add_argument(
        "--interactive", action="store_true", help="Run interactive scenario generation"
    )
    parser.add_argument("--no_parallel", action="store_true", help="Disable multiprocessing")
    args = parser.parse_args()

    if args.interactive:
        # Interactive mode
        scenario_files = interactive_scenario_generation()
        if scenario_files:
            results = run_simulation_scenarios(scenario_files, parallel=not args.no_parallel)
            generate_summary_report(results)
    elif args.scenarios:
        # Batch mode with provided scenario files
        results = run_simulation_scenarios(args.scenarios, parallel=not args.no_parallel)
        generate_summary_report(results)
    else:
        print("Please provide either --scenarios or --interactive flag.")
        print("Example usage:")
        print("  python enhanced_simulation_runner.py --interactive")
        print(
            "  python enhanced_simulation_runner.py --scenarios scenarios/scenario1.json scenarios/scenario2.json"
        )
