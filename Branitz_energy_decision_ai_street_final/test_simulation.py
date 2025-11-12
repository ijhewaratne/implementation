# test_simulation.py
import os
import subprocess
import sys
import yaml
import json
from pathlib import Path

# Import the placeholder functions we are going to develop
from src.simulation_runner import run_pandapipes_simulation, run_pandapower_simulation


def get_building_ids(street_name: str, geojson_path: str) -> list:
    """A helper function to get building IDs for our test case."""
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    selected_ids = []
    street_lower = street_name.strip().lower()
    for feature in data["features"]:
        for adr in feature.get("adressen", []):
            street_val = adr.get("str")
            if street_val and street_val.strip().lower() == street_lower:
                oi = feature.get("gebaeude", {}).get("oi")
                if oi:
                    selected_ids.append(oi)
                break
    return list(set(selected_ids))


def setup_test_environment(street_name: str, base_config_file: str) -> bool:
    """
    Runs the main data preparation pipeline for a specific street to ensure
    all necessary input files for the simulation are available.
    """
    print("--- [Setup] Preparing test environment ---")

    # 1. Get building IDs for the test street
    main_data_file = "data/geojson/hausumringe_mit_adressenV3.geojson"
    building_ids = get_building_ids(street_name, main_data_file)
    if not building_ids:
        print(f"Error: No buildings found for '{street_name}'. Cannot set up test.")
        return False

    print(f"Found {len(building_ids)} buildings for '{street_name}'.")

    # 2. Create a temporary config YAML for the main pipeline
    with open(base_config_file, "r") as f:
        config = yaml.safe_load(f)

    config["selected_buildings"] = building_ids

    # --- FIX STARTS HERE: Disable irrelevant pipeline steps for this test ---
    # We only want to test the simulation, so we disable the final reporting steps.
    config["run_kpi_calculator"] = False
    config["run_llm_reporter"] = False
    # --- FIX ENDS HERE ---

    temp_config_path = "temp_test_config.yaml"
    with open(temp_config_path, "w") as f:
        yaml.dump(config, f)

    print(f"Temporary config created at '{temp_config_path}'")

    # 3. Run the main data preparation pipeline
    print("Running main.py to generate input files (buildings_prepared.geojson, etc.)...")
    try:
        # We run the main pipeline which will use our temporary config
        # to generate the necessary input files for the simulation.
        subprocess.run(
            [sys.executable, "main.py", "--config", temp_config_path],
            check=True,
            capture_output=True,  # Suppress verbose output unless there's an error
            text=True,
        )
        print("Main pipeline completed successfully.")
        os.remove(temp_config_path)  # Clean up
        return True
    except subprocess.CalledProcessError as e:
        print("--- ERROR during main pipeline setup ---")
        print(e.stderr)  # Print the actual error from the subprocess
        os.remove(temp_config_path)  # Clean up
        return False


def main():
    """
    Main function to run an isolated simulation test.
    """
    # --- CONFIGURE YOUR TEST CASE HERE ---
    TEST_STREET = "Parkstraße"
    TEST_SCENARIO_TYPE = "DH"  # Change to "HP" to test the other simulation
    # -------------------------------------

    # First, run the pre-processing pipeline to get the necessary files
    if not setup_test_environment(TEST_STREET, "run_all_test.yaml"):
        print("\nAborting test due to setup failure.")
        return

    print(f"\n--- [Test] Running isolated {TEST_SCENARIO_TYPE} simulation for '{TEST_STREET}' ---")

    # Now, we manually create the 'scenario' dictionary that the real agent
    # workflow would generate. This is the input to our function-under-test.
    output_dir = "results_test/"
    scenario = {
        "name": f"test_{TEST_STREET.lower()}_{TEST_SCENARIO_TYPE.lower()}",
        "type": TEST_SCENARIO_TYPE,
        # The building file should have the calculated demand values
        "building_file": os.path.join(output_dir, "buildings_with_demand.geojson"),
        "network_file": os.path.join(output_dir, "branitz_network.graphml"),
        "params": {
            "supply_temp": 70,
            "return_temp": 40,
        },
    }

    # Call the actual simulation function you are developing
    if TEST_SCENARIO_TYPE == "DH":
        results = run_pandapipes_simulation(scenario)
    elif TEST_SCENARIO_TYPE == "HP":
        results = run_pandapower_simulation(scenario)
    else:
        print(f"Invalid TEST_SCENARIO_TYPE: {TEST_SCENARIO_TYPE}")
        return

    print("\n--- [Result] ---")
    print(json.dumps(results, indent=2))
    print("\nTest finished. Check the results above.")


if __name__ == "__main__":
    main()
