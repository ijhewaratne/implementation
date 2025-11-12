# run_agent_system.py
from adk.api.adk import ADK
from agents import EnergyPlannerAgent, CentralHeatingAgent, DecentralizedHeatingAgent, EnergyGPT
import re
from typing import Union

# Initialize the ADK. This manages agents and tool calls.
adk = ADK()

def extract_kpi_path(message: str) -> Union[str, None]:
    """Helper function to find a file path in a message."""
    match = re.search(r"([a-zA-Z0-9\/_\\.-]+scenario_kpis\.csv)", message)
    if match:
        return match.group(1)
    return None

def test_complete_pipeline():
    """Test the complete end-to-end pipeline with full agent workflow."""
    print("=== COMPLETE END-TO-END PIPELINE TEST ===")
    
    test_input = "analyze central heating for Parkstraße"
    print(f"Testing complete pipeline with input: '{test_input}'")
    
    try:
        # Step 1: Test the EnergyPlannerAgent
        print("\n--- Step 1: EnergyPlannerAgent Delegation ---")
        planner_response = adk.run(EnergyPlannerAgent, test_input)
        print(f"Planner Response: {planner_response.agent_response}")
        
        # Determine which agent to use based on planner response
        if "CHA" in planner_response.agent_response.upper():
            active_agent = CentralHeatingAgent
            scenario_type = "DH"
            print("Selected CentralHeatingAgent (CHA) for District Heating analysis")
        elif "DHA" in planner_response.agent_response.upper():
            active_agent = DecentralizedHeatingAgent
            scenario_type = "HP"
            print("Selected DecentralizedHeatingAgent (DHA) for Heat Pump analysis")
        else:
            print("Planner response unclear, defaulting to CHA")
            active_agent = CentralHeatingAgent
            scenario_type = "DH"
        
        # Step 2: Run the complete specialist agent pipeline
        print(f"\n--- Step 2: {active_agent.config.name} Complete Pipeline ---")
        print("This will execute all tools in sequence:")
        print("1. get_building_ids_for_street")
        print("2. create_network_graph") 
        print("3. run_simulation_pipeline")
        
        simulation_response = adk.run(active_agent, test_input)
        print(f"\nAgent Response: {simulation_response.agent_response}")
        
        # Step 3: Extract KPI path and run analysis
        print(f"\n--- Step 3: KPI Analysis with EnergyGPT ---")
        kpi_path = extract_kpi_path(simulation_response.agent_response)
        
        if kpi_path:
            print(f"Found KPI report at: {kpi_path}")
            analysis_response = adk.run(EnergyGPT, f"Please analyze the KPI report located at {kpi_path}")
            print(f"\n--- FINAL ANALYSIS REPORT ---")
            print(analysis_response.agent_response)
        else:
            print("Could not find KPI report path in the simulation response.")
            print("Checking for existing KPI files...")
            
            # Check for existing KPI files
            import os
            possible_kpi_paths = [
                "results_test/scenario_kpis.csv",
                "results/scenario_kpis.csv"
            ]
            
            for path in possible_kpi_paths:
                if os.path.exists(path):
                    print(f"Found existing KPI file: {path}")
                    analysis_response = adk.run(EnergyGPT, f"Please analyze the KPI report located at {path}")
                    print(f"\n--- FINAL ANALYSIS REPORT ---")
                    print(analysis_response.agent_response)
                    break
            else:
                print("No KPI files found.")
        
        # Step 4: Check generated files
        print(f"\n--- Step 4: Generated Files Summary ---")
        import os
        import glob
        
        # Check for network graph files
        network_files = glob.glob("results_test/network_graph_*.json")
        if network_files:
            print(f"Network graph files generated: {len(network_files)}")
            for file in network_files:
                print(f"  - {file}")
        
        # Check for service connection files
        service_files = glob.glob("results_test/service_connections_*.geojson")
        if service_files:
            print(f"Service connection files generated: {len(service_files)}")
            for file in service_files:
                print(f"  - {file}")
        
        # Check for KPI files
        kpi_files = glob.glob("results_test/scenario_kpis.*")
        if kpi_files:
            print(f"KPI files generated: {len(kpi_files)}")
            for file in kpi_files:
                print(f"  - {file}")
        
        # Check for LLM report files
        report_files = glob.glob("results_test/llm_*.md")
        if report_files:
            print(f"LLM report files generated: {len(report_files)}")
            for file in report_files:
                print(f"  - {file}")
        
        print(f"\n=== END-TO-END PIPELINE TEST COMPLETE ===")
        
    except Exception as e:
        print(f"Error during end-to-end test: {e}")
        import traceback
        traceback.print_exc()

def test_agent_system():
    """Test function to run a sample request without interactive input."""
    print("=== TESTING AGENT SYSTEM ===")
    
    # Test the EnergyPlannerAgent
    test_input = "analyze central heating for Parkstraße"
    print(f"Testing with input: '{test_input}'")
    
    try:
        # Test the planner agent
        print("\n--- Testing EnergyPlannerAgent ---")
        planner_response = adk.run(EnergyPlannerAgent, test_input)
        print(f"Planner Response: {planner_response.agent_response}")
        
        # Test the specialist agents with tool execution
        print("\n--- Testing CentralHeatingAgent with Tool Execution ---")
        cha_response = adk.run(CentralHeatingAgent, test_input)
        print(f"CHA Response: {cha_response.agent_response}")
        
        print("\n--- Testing DecentralizedHeatingAgent with Tool Execution ---")
        dha_response = adk.run(DecentralizedHeatingAgent, test_input)
        print(f"DHA Response: {dha_response.agent_response}")
        
        # Test the building extraction tool directly
        print("\n--- Testing Building Extraction Tool Directly ---")
        from energy_tools import get_building_ids_for_street
        buildings = get_building_ids_for_street.func("Parkstraße")
        print(f"Buildings found for Parkstraße: {buildings}")
        print(f"Number of buildings: {len(buildings)}")
        
        # Test the network graph creation tool directly
        print("\n--- Testing Network Graph Creation Tool Directly ---")
        from energy_tools import create_network_graph
        graph_result = create_network_graph.func(buildings, "results_test")
        print(f"Graph creation result: {graph_result}")
        
        # Test EnergyGPT with existing KPI report
        print("\n--- Testing EnergyGPT ---")
        egpt_response = adk.run(EnergyGPT, "Please analyze the KPI report at results_test/scenario_kpis.csv")
        print(f"EnergyGPT Response: {egpt_response.agent_response}")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

def main():
    """The main conversation loop for orchestrating the agents."""
    
    print("Starting Branitz Energy Planning Assistant...")
    print("You are now talking to the EnergyPlannerAgent. Ask for an analysis (e.g., 'Analyze central heating for Parkstraße').")

    # The main loop, the user interacts with the orchestrator.
    while True:
        try:
            user_input = input("\nYour request: ")
            if user_input.lower() in ["exit", "quit"]:
                break

            # --- Step 1: Delegation by the Planner Agent ---
            print("\n--- Planner Agent is thinking... ---")
            planner_response = adk.run(EnergyPlannerAgent, user_input)
            
            # The planner's response should be 'CHA' or 'DHA'.
            delegate_agent_name = planner_response.agent_response.strip().upper()
            
            if delegate_agent_name == "CHA":
                active_agent = CentralHeatingAgent
                print(f"--- Planner delegated to CentralHeatingAgent (CHA). ---")
            elif delegate_agent_name == "DHA":
                active_agent = DecentralizedHeatingAgent
                print(f"--- Planner delegated to DecentralizedHeatingAgent (DHA). ---")
            else:
                print(f"Planner response was unclear. Please try again. Response: {planner_response.agent_response}")
                continue

            # --- Step 2: Execution by the Specialist Agent ---
            print(f"--- {active_agent.config.name} is running the simulation... ---")
            # Pass the original user query to the specialist agent.
            simulation_response = adk.run(active_agent, user_input)
            print("--- Simulation agent finished. ---")
            print(f"Agent Log: {simulation_response.agent_response}")
            
            # --- Step 3: Analysis by EnergyGPT ---
            # Find the path to the KPI report in the specialist's final message.
            kpi_path = extract_kpi_path(simulation_response.agent_response)
            
            if kpi_path:
                print("\n--- KPI report found. Handing off to EnergyGPT for analysis... ---")
                # Pass the KPI path directly to the EnergyGPT agent.
                analysis_response = adk.run(
                    EnergyGPT, 
                    f"Please analyze the KPI report located at {kpi_path}"
                )
                print("\n--- FINAL REPORT ---")
                print(analysis_response.agent_response)
            else:
                print("\nCould not find the KPI report path in the simulation agent's response. Cannot proceed to analysis.")

        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    # Run the complete end-to-end pipeline test
    test_complete_pipeline()
