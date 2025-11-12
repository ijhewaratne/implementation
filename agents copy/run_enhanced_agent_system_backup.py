# run_enhanced_agent_system_adk.py
"""
Enhanced Multi-Agent System Runner using Google ADK
Updated version with proper ADK integration and error handling
"""

import sys
import os
import re
from typing import Union, Optional
from pathlib import Path

# Add ADK to path
sys.path.insert(0, 'adk')

from adk.api.adk import ADK
from enhanced_agents import (
    EnergyPlannerAgent,
    CentralHeatingAgent,
    DecentralizedHeatingAgent,
    ComparisonAgent,
    AnalysisAgent,
    DataExplorerAgent,
    EnergyGPT,
    load_gemini_config
)

# Initialize the ADK with proper configuration
def initialize_adk() -> ADK:
    """Initialize ADK with proper configuration."""
    try:
        adk = ADK()
        print("✅ ADK initialized successfully")
        return adk
    except Exception as e:
        print(f"❌ Failed to initialize ADK: {e}")
        raise

# Initialize ADK
adk = initialize_adk()

def extract_kpi_path(message: str) -> Union[str, None]:
    """Helper function to find a file path in a message."""
    match = re.search(r"([a-zA-Z0-9\/_\\.-]+scenario_kpis\.csv)", message)
    if match:
        return match.group(1)
    return None

def validate_agent_config(agent) -> bool:
    """Validate that an agent has proper ADK configuration."""
    try:
        # Check if agent has required attributes
        required_attrs = ['name', 'model', 'system_prompt', 'tools']
        for attr in required_attrs:
            if not hasattr(agent.config, attr):
                print(f"❌ Agent {agent.name} missing required attribute: {attr}")
                return False
        
        # Check if API key is configured
        if not hasattr(agent.config, 'api_key') or not agent.config.api_key:
            print(f"⚠️ Agent {agent.name} missing API key - using fallback mode")
        
        print(f"✅ Agent {agent.name} configuration validated")
        return True
    except Exception as e:
        print(f"❌ Error validating agent {agent.name}: {e}")
        return False

def test_agent_initialization():
    """Test that all agents can be initialized properly."""
    print("=== AGENT INITIALIZATION TEST ===")
    
    agents = [
        EnergyPlannerAgent,
        CentralHeatingAgent,
        DecentralizedHeatingAgent,
        ComparisonAgent,
        AnalysisAgent,
        DataExplorerAgent,
        EnergyGPT
    ]
    
    for agent in agents:
        if validate_agent_config(agent):
            print(f"✅ {agent.name} initialized successfully")
        else:
            print(f"❌ {agent.name} initialization failed")
    
    print("=== AGENT INITIALIZATION TEST COMPLETED ===\n")

def test_comprehensive_pipeline():
    """Test the comprehensive end-to-end pipeline with enhanced agent workflow."""
    print("=== COMPREHENSIVE END-TO-END PIPELINE TEST ===")

    test_input = "analyze heat pump feasibility for Parkstraße with winter evening peak scenario"
    print(f"Testing comprehensive pipeline with input: '{test_input}'")

    try:
        # Step 1: Test the EnergyPlannerAgent
        print("\n--- Step 1: EnergyPlannerAgent Delegation ---")
        planner_response = adk.run(EnergyPlannerAgent, test_input)
        print(f"Planner Response: {planner_response.agent_response}")

        # Determine which agent to use based on planner response
        agent_map = {
            "CHA": CentralHeatingAgent,
            "DHA": DecentralizedHeatingAgent,
            "CA": ComparisonAgent,
            "AA": AnalysisAgent,
            "DEA": DataExplorerAgent,
        }

        delegate_agent_name = planner_response.agent_response.strip().upper()
        if delegate_agent_name in agent_map:
            delegate_agent = agent_map[delegate_agent_name]
            print(f"\n--- Step 2: Delegating to {delegate_agent_name} ---")
            
            # Test the delegated agent
            agent_response = adk.run(delegate_agent, test_input)
            print(f"Agent Response: {agent_response.agent_response}")
            
            # Check if there are tool calls in the response
            if hasattr(agent_response, 'tool_calls') and agent_response.tool_calls:
                print(f"Tool Calls: {agent_response.tool_calls}")
            
            return True
        else:
            print(f"❌ Unknown agent: {delegate_agent_name}")
            return False

    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        return False

def test_individual_agents():
    """Test individual agents with specific inputs."""
    print("=== INDIVIDUAL AGENT TESTING ===")
    
    test_cases = [
        (CentralHeatingAgent, "analyze district heating for Parkstraße"),
        (DecentralizedHeatingAgent, "analyze heat pump feasibility for Parkstraße"),
        (DataExplorerAgent, "show me all available streets"),
        (EnergyGPT, "analyze the KPI report")
    ]
    
    for agent, test_input in test_cases:
        print(f"\n--- Testing {agent.name} ---")
        print(f"Input: {test_input}")
        
        try:
            response = adk.run(agent, test_input)
            print(f"Response: {response.agent_response}")
            
            if hasattr(response, 'tool_calls') and response.tool_calls:
                print(f"Tool Calls: {response.tool_calls}")
            
            print(f"✅ {agent.name} test completed")
        except Exception as e:
            print(f"❌ {agent.name} test failed: {e}")

def test_tool_execution():
    """Test direct tool execution through agents."""
    print("=== TOOL EXECUTION TESTING ===")
    
    # Test tool execution through CentralHeatingAgent
    print("\n--- Testing tool execution through CentralHeatingAgent ---")
    try:
        # This should trigger the run_comprehensive_dh_analysis tool
        response = adk.run(CentralHeatingAgent, "run_comprehensive_dh_analysis(street_name='Parkstraße')")
        print(f"Tool execution response: {response.agent_response}")
        print("✅ Tool execution test completed")
    except Exception as e:
        print(f"❌ Tool execution test failed: {e}")

def main():
    """Main function to run all tests."""
    print("🚀 Enhanced Multi-Agent System with ADK")
    print("=" * 50)
    
    # Load and display configuration
    config = load_gemini_config()
    print(f"Model: {config.get('model', 'Unknown')}")
    print(f"API Key configured: {'Yes' if config.get('api_key') else 'No'}")
    print(f"Temperature: {config.get('temperature', 'Unknown')}")
    print()
    
    # Run tests
    test_agent_initialization()
    test_individual_agents()
    test_tool_execution()
    test_comprehensive_pipeline()
    
    print("\n🎉 All tests completed!")
    print("=" * 50)

def interactive_mode():
    """Interactive mode for testing the system."""
    print("🚀 Interactive Enhanced Multi-Agent System")
    print("Type 'quit' to exit, 'help' for available commands")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\nEnter your request: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            elif user_input.lower() == 'help':
                print("Available commands:")
                print("- Ask about district heating: 'analyze district heating for [street]'")
                print("- Ask about heat pumps: 'analyze heat pump feasibility for [street]'")
                print("- Compare scenarios: 'compare heating scenarios for [street]'")
                print("- Explore data: 'show me all available streets'")
                print("- Analyze results: 'analyze the KPI report'")
                continue
            elif not user_input:
                continue
            
            # Use the EnergyPlannerAgent to delegate
            print(f"\nProcessing: {user_input}")
            planner_response = adk.run(EnergyPlannerAgent, user_input)
            print(f"Delegating to: {planner_response.agent_response}")
            
            # Execute with the appropriate agent
            agent_map = {
                "CHA": CentralHeatingAgent,
                "DHA": DecentralizedHeatingAgent,
                "CA": ComparisonAgent,
                "AA": AnalysisAgent,
                "DEA": DataExplorerAgent,
            }
            
            delegate_agent_name = planner_response.agent_response.strip().upper()
            if delegate_agent_name in agent_map:
                delegate_agent = agent_map[delegate_agent_name]
                agent_response = adk.run(delegate_agent, user_input)
                print(f"\nResponse: {agent_response.agent_response}")
            else:
                print(f"❌ Unknown agent: {delegate_agent_name}")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Multi-Agent System with ADK")
    parser.add_argument("--test", action="store_true", help="Run all tests")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--input", type=str, help="Process a single input")
    
    args = parser.parse_args()
    
    if args.test:
        main()
    elif args.interactive:
        interactive_mode()
    elif args.input:
        print(f"Processing: {args.input}")
        planner_response = adk.run(EnergyPlannerAgent, args.input)
        print(f"Delegating to: {planner_response.agent_response}")
        
        agent_map = {
            "CHA": CentralHeatingAgent,
            "DHA": DecentralizedHeatingAgent,
            "CA": ComparisonAgent,
            "AA": AnalysisAgent,
            "DEA": DataExplorerAgent,
        }
        
        delegate_agent_name = planner_response.agent_response.strip().upper()
        if delegate_agent_name in agent_map:
            delegate_agent = agent_map[delegate_agent_name]
            agent_response = adk.run(delegate_agent, args.input)
            print(f"Response: {agent_response.agent_response}")
        else:
            print(f"❌ Unknown agent: {delegate_agent_name}")
    else:
        print("Use --test, --interactive, or --input to run the system")
        print("Example: python run_enhanced_agent_system_adk.py --input 'analyze district heating for Parkstraße'")
