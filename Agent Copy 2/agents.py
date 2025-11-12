from adk.api.agent import Agent
from energy_tools import (
    run_complete_dh_analysis,
    run_complete_hp_analysis,
    compare_scenarios,
    get_all_street_names,
    list_available_results,
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
            "You are the Central Heating Agent (CHA). Your only job is to run a complete "
            "district heating analysis for the user's requested street. "
            "To do this, you MUST call the `run_complete_dh_analysis` tool, "
            "passing the street name from the user's query as the `street_name` argument."
        ),
        tools=[run_complete_dh_analysis],
    )
)

DecentralizedHeatingAgent = Agent(
    config=dict(
        name="DecentralizedHeatingAgent",
        model="gemini-1.5-flash-latest",
        system_prompt=(
            "You are the Decentralized Heating Agent (DHA). Your only job is to run a complete "
            "heat pump analysis for the user's requested street. "
            "To do this, you MUST call the `run_complete_hp_analysis` tool, "
            "passing the street name from the user's query as the `street_name` argument."
        ),
        tools=[run_complete_hp_analysis],
    )
)

# --- NEW AGENT ---
ComparisonAgent = Agent(
    config=dict(
        name="ComparisonAgent",
        model="gemini-1.5-flash-latest",
        system_prompt=(
            "You are the Comparison Agent (CA). Your only job is to run a comparative analysis "
            "between District Heating and Heat Pump scenarios for the user's requested street. "
            "To do this, you MUST call the `compare_scenarios` tool, passing the street name from the user's query."
        ),
        tools=[compare_scenarios],
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
