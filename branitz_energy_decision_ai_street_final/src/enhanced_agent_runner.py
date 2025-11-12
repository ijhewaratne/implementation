#!/usr/bin/env python3
"""
Enhanced Multi-Agent Runner for Branitz Energy Decision AI
Based on the legacy ADK implementation with delegation capabilities.
"""

from src.enhanced_agents import (
    EnergyPlannerAgent,
    CentralHeatingAgent,
    DecentralizedHeatingAgent,
    ComparisonAgent,
    AnalysisAgent,
    DataExplorerAgent,
    EnergyGPT,
)
import re
from typing import Union
import os


def test_comprehensive_pipeline():
    """Test the comprehensive end-to-end pipeline with enhanced agent workflow."""
    print("=== COMPREHENSIVE END-TO-END PIPELINE TEST ===")

    test_input = "analyze heat pump feasibility for Parkstraße with winter evening peak scenario"
    print(f"Testing comprehensive pipeline with input: '{test_input}'")

    try:
        # Step 1: Test the EnergyPlannerAgent
        print("\n--- Step 1: EnergyPlannerAgent Delegation ---")
        planner_response_text = _safe_adk_run(EnergyPlannerAgent, test_input)
        print(f"Planner Response: {planner_response_text}")

        # Determine which agent to use based on planner response
        # normalize keys once
        agent_map = {k.upper(): v for k, v in {
            "CHA": CentralHeatingAgent,
            "DHA": DecentralizedHeatingAgent,
            "CA": ComparisonAgent,
            "AA": AnalysisAgent,
            "DEA": DataExplorerAgent,
            "ENERGYGPT": EnergyGPT,
            "EGPT": EnergyGPT,
            "ENERGY_GPT": EnergyGPT,
        }.items()}

        delegate_agent_name = planner_response_text.strip().upper()
        active_agent = agent_map.get(delegate_agent_name, DecentralizedHeatingAgent)

        print(f"Selected {active_agent.config.name} for analysis")

        # Step 2: Run the comprehensive specialist agent pipeline
        print(f"\n--- Step 2: {active_agent.config.name} Comprehensive Pipeline ---")

        simulation_response = _safe_adk_run(active_agent, test_input)
        print(f"\nAgent Response: {simulation_response}")

        # Step 3: Extract dashboard path and provide analysis
        print(f"\n--- Step 3: Results Analysis ---")

        # Look for dashboard links in the response
        dashboard_match = re.search(r"file://([^\s]+\.html)", simulation_response.agent_response)
        if dashboard_match:
            dashboard_path = dashboard_match.group(1)
            print(f"Found dashboard at: {dashboard_path}")
            print(f"Open this file in your browser to view the interactive dashboard")

        # Look for other generated files
        results_match = re.search(
            r"📁 GENERATED FILES:(.*?)(?=\n\n|\n===|\n🔗)",
            simulation_response.agent_response,
            re.DOTALL,
        )
        if results_match:
            print(f"Generated files summary: {results_match.group(1).strip()}")

        print(f"\n--- COMPREHENSIVE ANALYSIS COMPLETED ---")
        print(
            "The enhanced agent system has successfully executed comprehensive energy infrastructure analysis."
        )
        print("Check the generated files and dashboard for detailed results.")

    except Exception as e:
        print(f"Error in comprehensive pipeline test: {e}")


def interactive_mode():
    """Run the enhanced agent system in interactive mode."""
    print("🤖 ENHANCED BRANITZ ENERGY DECISION AI - MULTI-AGENT SYSTEM")
    print("=" * 80)
    print("🎯 COMPREHENSIVE ANALYSIS CAPABILITIES:")
    print("   • Heat Pump Feasibility Analysis (Power Flow + Proximity)")
    print("   • District Heating Network Design (Dual-Pipe + Hydraulic)")
    print("   • Scenario Comparison (HP vs DH)")
    print("   • Interactive Dashboards and Visualizations")
    print("   • Data Exploration and Results Management")
    print("   • AI-Powered Analysis and Insights")
    print("=" * 80)
    print("💡 EXAMPLE COMMANDS:")
    print("   • 'analyze heat pump feasibility for Parkstraße'")
    print("   • 'analyze district heating for Luciestraße'")
    print("   • 'compare both scenarios for Damaschkeallee'")
    print("   • 'show available streets'")
    print("   • 'show results'")
    print("   • 'generate KPI report for An der Bahn'")
    print("")
    print("🤖 ENERGYGPT SHORTCUTS:")
    print("   • 'egpt analyze_kpi_report(kpi_report_path=\"<path>\")'")
    print("   • 'analyze kpi <path>'")
    print("   • 'exit' to quit")
    print("=" * 80)

    while True:
        try:
            user_input = input("\n🎯 Your request: ").strip()

            if user_input.lower() in ["exit", "quit", "q"]:
                print("Goodbye! 👋")
                break

            if not user_input:
                continue

            # Quick route to EnergyGPT
            if user_input.lower().startswith("egpt "):
                prompt = user_input[5:].strip()
                run_agent_once(EnergyGPT, prompt)
                continue

            # Convenience: analyze KPI path without typing tool call
            # Example: analyze kpi processed/kpi/kpi_summary.json
            if user_input.lower().startswith("analyze kpi "):
                path = user_input.split(" ", 2)[2].strip()
                run_agent_once(EnergyGPT, f"analyze_kpi_report(kpi_report_path='{path}')")
                continue

            print("\n🤔 Planner Agent is thinking...")

            # Get planner delegation
            planner_response_text = _safe_adk_run(EnergyPlannerAgent, user_input)
            delegate_agent_name = planner_response_text.strip().upper()

            print(f"🎯 Planner delegated to {delegate_agent_name}.")

            # Map to appropriate agent
            # normalize keys once
            agent_map = {k.upper(): v for k, v in {
                "CHA": CentralHeatingAgent,
                "DHA": DecentralizedHeatingAgent,
                "CA": ComparisonAgent,
                "AA": AnalysisAgent,
                "DEA": DataExplorerAgent,
                "ENERGYGPT": EnergyGPT,
                "EGPT": EnergyGPT,
                "ENERGY_GPT": EnergyGPT,
            }.items()}

            active_agent = agent_map.get(delegate_agent_name, DataExplorerAgent)

            print(f"⚡ {active_agent.config.name} is executing your request...")

            # Run the analysis
            response_text = _safe_adk_run(active_agent, user_input)

            print(f"\n📊 {active_agent.config.name} Response:")
            print(response_text)

            # Check for dashboard links
            dashboard_match = re.search(r"file://([^\s]+\.html)", response_text)
            if dashboard_match:
                dashboard_path = dashboard_match.group(1)
                print(f"\n🔗 Interactive Dashboard: {dashboard_path}")
                print("   Open this file in your browser to view the interactive dashboard")

        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again with a different request.")


def batch_mode(requests: list[str]):
    """Run the enhanced agent system in batch mode for multiple requests."""
    print("🤖 ENHANCED BRANITZ ENERGY DECISION AI - BATCH MODE")
    print("=" * 80)
    print(f"Processing {len(requests)} requests...")

    results = []

    for i, request in enumerate(requests, 1):
        print(f"\n--- Processing Request {i}/{len(requests)} ---")
        print(f"Request: {request}")

        try:
            # Get planner delegation
            planner_response_text = _safe_adk_run(EnergyPlannerAgent, request)
            delegate_agent_name = planner_response_text.strip().upper()

            # Map to appropriate agent
            # normalize keys once
            agent_map = {k.upper(): v for k, v in {
                "CHA": CentralHeatingAgent,
                "DHA": DecentralizedHeatingAgent,
                "CA": ComparisonAgent,
                "AA": AnalysisAgent,
                "DEA": DataExplorerAgent,
                "ENERGYGPT": EnergyGPT,
                "EGPT": EnergyGPT,
                "ENERGY_GPT": EnergyGPT,
            }.items()}

            active_agent = agent_map.get(delegate_agent_name, DataExplorerAgent)

            # Run the analysis
            response_text = _safe_adk_run(active_agent, request)

            results.append({
                "request": request,
                "agent": active_agent.config.name,
                "response": response_text,
                "success": True
            })

            print(f"✅ Completed with {active_agent.config.name}")

        except Exception as e:
            results.append({
                "request": request,
                "agent": "Error",
                "response": str(e),
                "success": False
            })
            print(f"❌ Failed: {e}")

    # Summary
    print(f"\n--- BATCH PROCESSING COMPLETE ---")
    successful = sum(1 for r in results if r["success"])
    print(f"Successful: {successful}/{len(requests)}")
    
    return results


def _safe_adk_run(agent, prompt: str) -> str:
    """Run agent with ADK or SimpleAgent fallback."""
    try:
        from adk.api.adk import ADK
        # ADK is available, use it
        adk = ADK()
        res = adk.run(agent, prompt)
        return res.agent_response
    except Exception as e:
        # ADK not available, check if agent has run method (SimpleAgent)
        if hasattr(agent, 'run'):
            return agent.run(prompt)
        
        # Fallback: directly call tool when the prompt is a tool string
        if prompt.strip().startswith("analyze_kpi_report("):
            from src.enhanced_tools import analyze_kpi_report
            import re
            m = re.search(r"kpi_report_path\s*=\s*['\"](.+?)['\"]", prompt)
            if not m:
                return "❌ Missing kpi_report_path in prompt."
            return analyze_kpi_report(m.group(1))
        
        return f"❌ Neither ADK nor SimpleAgent available. Got: {prompt}"

def run_agent_once(agent, prompt: str):
    """Run a single agent with a prompt and return the result."""
    out = _safe_adk_run(agent, prompt)
    print(out)
    return out

def main():
    """Main function to run the enhanced agent system."""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "test":
            test_comprehensive_pipeline()
        elif command == "interactive":
            interactive_mode()
        elif command == "batch":
            # Example batch requests
            batch_requests = [
                "analyze heat pump feasibility for Parkstraße",
                "analyze district heating for Luciestraße",
                "compare both scenarios for Damaschkeallee",
                "show available streets",
                "show results"
            ]
            batch_mode(batch_requests)
        elif command == "egpt":
            # Usage: python enhanced_agent_runner.py egpt "analyze_kpi_report(kpi_report_path='processed/kpi/kpi_summary.json')"
            prompt = sys.argv[2] if len(sys.argv) > 2 else "help"
            run_agent_once(EnergyGPT, prompt)
            sys.exit(0)
        else:
            print("Usage: python enhanced_agent_runner.py [test|interactive|batch|egpt]")
            print("  test: Run comprehensive pipeline test")
            print("  interactive: Run in interactive mode")
            print("  batch: Run in batch mode with predefined requests")
            print("  egpt: Run EnergyGPT with a specific prompt")
            print("")
            print("EGPT usage:")
            print("  python enhanced_agent_runner.py egpt \"analyze_kpi_report(kpi_report_path='<path>')\"")
    else:
        # Default to interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
