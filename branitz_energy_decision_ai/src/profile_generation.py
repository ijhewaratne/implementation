import json
from pathlib import Path
from load_profile_phase_generator import ParallelLoadProfileGenerator


building_data_file="data/json/output_branitzer_siedlungV11.json"
household_data_file="data/json/building_population_resultsV6.json"
output_file="results/building_load_profiles.json"

def generate_all_profiles(building_data_file, household_data_file, output_file):
    """
    Wrapper function to generate all load profiles using robust, phase-aware logic.
    Arguments:
        building_data_file: Path to the JSON with building attributes (including GebaeudeID, etc.)
        household_data_file: Path to the JSON with demographic/household data
        output_file: Path to save the resulting load profiles as JSON
    Returns:
        Results dict (typically, all load profiles by building ID)
    """
    generator = ParallelLoadProfileGenerator(building_data_file, household_data_file)
    results = generator.generate_all_profiles(output_file)
    return results

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate all building load profiles using robust phase-aware logic.")
    parser.add_argument("--buildings", required=True, help="Path to building data JSON (attributes per building)")
    parser.add_argument("--households", required=True, help="Path to household data JSON (demographics, etc)")
    parser.add_argument("--output", default="results/building_load_profiles.json", help="Output file for load profiles")
    args = parser.parse_args()

    Path("results").mkdir(exist_ok=True)
    print(f"Running full robust load profile generation...\nBuildings: {args.buildings}\nHouseholds: {args.households}\nOutput: {args.output}")
    generate_all_profiles(args.buildings, args.households, args.output)
