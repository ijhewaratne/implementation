from adk.api.agent import Agent
from energy_tools import (
    run_complete_dh_analysis,
    run_complete_hp_analysis,
    compare_scenarios,
    get_all_street_names,
    list_available_results,
    create_interactive_map,
    create_summary_dashboard,
    create_comparison_dashboard,
    create_html_dashboard,
    optimize_network_routing,
    run_hp_street_workflow,
    compare_hp_variants,
)

# This file defines our team of specialist agents.

EnergyPlannerAgent = Agent(
    config=dict(
        name="EnergyPlannerAgent",
        model="gemini-1.5-flash-latest",
        system_prompt=(
            "You are a master energy planner for the city of Branitz. Your goal is to help the user by delegating their request to the correct specialist agent. "
            "You have the following agents available:\n"
            "1. CentralHeatingAgent (CHA): Use for requests specifically about 'district heating', 'central', or 'DH'.\n"
            "2. DecentralizedHeatingAgent (DHA): Use for requests specifically about 'heat pumps', 'decentralized', or 'HP'.\n"
            "3. ComparisonAgent (CA): Use for requests that involve 'compare', 'vs', 'versus', or mention both heating types.\n"
            "4. DataExplorerAgent (DEA): Use for requests about available data, like 'list streets' or 'show results'.\n"
            "Your response must ONLY be the abbreviation of the agent to delegate to: 'CHA', 'DHA', 'CA', or 'DEA'."
        ),
        tools=[],
    )
)

CentralHeatingAgent = Agent(
    config=dict(
        name="CentralHeatingAgent",
        model="gemini-1.5-flash-latest",
        system_prompt=(
            "You are the Central Heating Agent (CHA). Your job is to run district heating analyses "
            "and create visualizations for the user's requested street. "
            "Available tools:\n"
            "- run_complete_dh_analysis: Run full DH simulation and generate report\n"
            "- create_interactive_map: Create interactive HTML map with temperature gradients\n"
            "- create_summary_dashboard: Create comprehensive 12-panel PNG dashboard\n"
            "- create_html_dashboard: Create full HTML web page with embedded maps and charts\n"
            "- optimize_network_routing: Optimize network routing using shortest path algorithms\n"
            "Use the appropriate tools based on what the user requests."
        ),
        tools=[run_complete_dh_analysis, create_interactive_map, create_summary_dashboard, create_html_dashboard, optimize_network_routing],
    )
)

DecentralizedHeatingAgent = Agent(
    config=dict(
        name="DecentralizedHeatingAgent",
        model="gemini-1.5-flash-latest",
        system_prompt=(
            "You are the Decentralized Heating Agent (DHA). Your job is to run heat pump analyses "
            "and create visualizations for the user's requested street. "
            "Available tools:\n"
            "- run_complete_hp_analysis: Run full HP simulation and generate report\n"
            "- create_interactive_map: Create interactive HTML map with voltage gradients\n"
            "- create_summary_dashboard: Create comprehensive 12-panel PNG dashboard\n"
            "- create_html_dashboard: Create full HTML web page with embedded maps and charts\n"
            "Use the appropriate tools based on what the user requests."
        ),
        tools=[run_complete_hp_analysis, run_hp_street_workflow, compare_hp_variants, create_interactive_map, create_summary_dashboard, create_html_dashboard],
    )
)

# --- NEW AGENT ---
ComparisonAgent = Agent(
    config=dict(
        name="ComparisonAgent",
        model="gemini-1.5-flash-latest",
        system_prompt=(
            "You are the Comparison Agent (CA). Your job is to run comparative analyses "
            "between District Heating and Heat Pump scenarios and create comparison visualizations. "
            "Available tools:\n"
            "- compare_scenarios: Run both DH and HP simulations and generate comparative report\n"
            "- create_comparison_dashboard: Create DH vs HP comparison dashboard with recommendation\n"
            "Use both tools to provide comprehensive comparison analysis when requested."
        ),
        tools=[compare_scenarios, create_comparison_dashboard],
    )
)

# --- NEW AGENT ---
DataExplorerAgent = Agent(
    config=dict(
        name="DataExplorerAgent",
        model="gemini-1.5-flash-latest",
        system_prompt=(
            "You are the Data Explorer Agent (DEA). Your job is to help the user understand the available data. "
            "If the user asks to 'list' or 'show' streets, use the `get_all_street_names` tool. "
            "If the user asks to see 'results' or 'files', use the `list_available_results` tool. "
            "After using a tool, present the result clearly to the user."
        ),
        tools=[get_all_street_names, list_available_results],
    )
)
