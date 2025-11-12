#!/usr/bin/env python3
"""
Enhanced Multi-Agent System for Branitz Energy Decision AI
Updated for Google ADK with proper configuration management and error handling.
"""

import sys
import os
import yaml
from pathlib import Path

# Add ADK to path if available
try:
    sys.path.insert(0, 'agents copy/adk')
    from adk.api.agent import Agent
    ADK_AVAILABLE = True
    print("✅ ADK Agent available")
except ImportError:
    try:
        from src.simple_gemini_agent import SimpleAgent as Agent
        ADK_AVAILABLE = False
        print("⚠️ ADK not available, using SimpleAgent fallback")
    except ImportError:
        print("❌ No agent implementation available")
        raise

from src.enhanced_tools import (
    get_all_street_names,
    get_building_ids_for_street,
    run_comprehensive_hp_analysis,
    run_comprehensive_dh_analysis,
    compare_comprehensive_scenarios,
    analyze_kpi_report,
    list_available_results,
    generate_comprehensive_kpi_report,
)

# Load Gemini configuration
def load_gemini_config():
    """Load Gemini API configuration."""
    config_paths = [
        Path("configs/gemini_config.yml"),
        Path("agents copy/configs/gemini_config.yml"),
        Path("../configs/gemini_config.yml")
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    print(f"✅ Configuration loaded from {config_path}")
                    return config
            except Exception as e:
                print(f"⚠️ Error loading config from {config_path}: {e}")
                continue
    
    # Fallback configuration
    print("⚠️ Using fallback configuration")
    return {
        "api_key": os.getenv("GEMINI_API_KEY", ""),
        "model": "gemini-1.5-flash-latest",
        "temperature": 0.7,
        "max_tokens": 2048
    }

# Load configuration
GEMINI_CONFIG = load_gemini_config()

def create_agent_config(name: str, system_prompt: str, tools: list = None) -> dict:
    """Create a properly configured agent config for ADK."""
    config = {
        "name": name,
        "model": GEMINI_CONFIG.get("model", "gemini-1.5-flash-latest"),
        "system_prompt": system_prompt,
        "tools": tools or []
    }
    
    # Add ADK-specific configuration if available
    if ADK_AVAILABLE:
        config.update({
            "api_key": GEMINI_CONFIG.get("api_key", ""),
            "temperature": GEMINI_CONFIG.get("temperature", 0.7),
            "max_tokens": GEMINI_CONFIG.get("max_tokens", 2048)
        })
    
    return config

# Master Orchestrator Agent - delegates to specialist agents
EnergyPlannerAgent = Agent(
    config=create_agent_config(
        name="EnergyPlannerAgent",
        system_prompt=(
            "You are a master energy planner for the city of Branitz. "
            "Your goal is to help the user analyze different heating strategies with comprehensive infrastructure assessment. "
            "You have several specialist agents available: "
            "1. CentralHeatingAgent (CHA): An expert on district heating networks with dual-pipe analysis and hydraulic simulation. "
            "2. DecentralizedHeatingAgent (DHA): An expert on heat pumps with power flow analysis and electrical infrastructure assessment. "
            "3. ComparisonAgent (CA): An expert at comparing both scenarios with comprehensive metrics. "
            "4. AnalysisAgent (AA): An expert at comprehensive analysis with interactive visualizations. "
            "5. DataExplorerAgent (DEA): An expert at exploring available data and results. "
            "6. EnergyGPT (EGPT): An expert AI analyst for energy infrastructure insights. "
            ""
            "First, understand the user's request. Then, clearly state which specialist agent you will delegate to: "
            "'CHA' for district heating analysis, "
            "'DHA' for heat pump analysis, "
            "'CA' for comparing both scenarios, "
            "'AA' for comprehensive analysis, "
            "'DEA' for exploring data and results, "
            "'EGPT' for AI-powered insights and analysis. "
            ""
            "Your response should ONLY be the name of the agent to delegate to: 'CHA', 'DHA', 'CA', 'AA', 'DEA', or 'EGPT'."
        ),
        tools=[]
    )
)

# Central Heating Agent - District Heating Network Analysis
CentralHeatingAgent = Agent(
    config=create_agent_config(
        name="CentralHeatingAgent",
        system_prompt=(
            "You are the Central Heating Agent (CHA). Your job is to execute comprehensive district heating analysis "
            "including dual-pipe network design, hydraulic simulation, and interactive visualization. "
            "You MUST use the `run_comprehensive_dh_analysis` tool with the street name. "
            "This tool will automatically: "
            "1. Extract buildings for the specified street "
            "2. Create complete dual-pipe district heating network (supply + return) "
            "3. Run pandapipes hydraulic simulation "
            "4. Generate interactive dashboard with metrics "
            "5. Provide comprehensive analysis summary "
            ""
            "IMPORTANT: When you need to use a tool, ALWAYS output ONLY the function call in the format: "
            "run_comprehensive_dh_analysis(street_name='street_name') on a single line, and nothing else. "
            "Do not explain, do not add extra text. "
            "After the tool call, wait for the result and present it clearly to the user."
        ),
        tools=[run_comprehensive_dh_analysis]
    )
)

# Decentralized Heating Agent - Heat Pump Analysis
DecentralizedHeatingAgent = Agent(
    config=create_agent_config(
        name="DecentralizedHeatingAgent",
        system_prompt=(
            "You are the Decentralized Heating Agent (DHA). Your job is to execute comprehensive heat pump feasibility analysis "
            "including power flow simulation, proximity assessment, and electrical infrastructure analysis. "
            "You MUST use the `run_comprehensive_hp_analysis` tool with the street name and optionally a scenario. "
            "This tool will automatically: "
            "1. Extract buildings for the specified street "
            "2. Analyze proximity to power infrastructure "
            "3. Run pandapower power flow simulation "
            "4. Generate interactive dashboard with metrics "
            "5. Provide comprehensive feasibility assessment "
            ""
            "Available scenarios: 'winter_werktag_abendspitze', 'summer_sonntag_abendphase', 'winter_werktag_mittag', 'summer_werktag_abendspitze' "
            ""
            "IMPORTANT: When you need to use a tool, ALWAYS output ONLY the function call in the format: "
            "run_comprehensive_hp_analysis(street_name='street_name', scenario='scenario_name') on a single line, and nothing else. "
            "Do not explain, do not add extra text. "
            "After the tool call, wait for the result and present it clearly to the user."
        ),
        tools=[run_comprehensive_hp_analysis]
    )
)

# Comparison Agent - Scenario Comparison
ComparisonAgent = Agent(
    config=create_agent_config(
        name="ComparisonAgent",
        system_prompt=(
            "You are the Comparison Agent (CA). Your job is to compare both DH and HP scenarios "
            "for a given street with comprehensive analysis. You MUST use the `compare_comprehensive_scenarios` tool. "
            "This tool will automatically: "
            "1. Run comprehensive heat pump feasibility analysis "
            "2. Run comprehensive district heating network analysis "
            "3. Provide side-by-side comparison with metrics "
            "4. Generate recommendations based on technical and economic factors "
            ""
            "IMPORTANT: When you need to use a tool, ALWAYS output ONLY the function call in the format: "
            "compare_comprehensive_scenarios(street_name='street_name', hp_scenario='scenario_name') on a single line, and nothing else. "
            "Do not explain, do not add extra text. "
            "After the tool call, wait for the result and present it clearly to the user."
        ),
        tools=[compare_comprehensive_scenarios]
    )
)

# Analysis Agent - Comprehensive Analysis
AnalysisAgent = Agent(
    config=create_agent_config(
        name="AnalysisAgent",
        system_prompt=(
            "You are the Analysis Agent (AA). Your job is to run comprehensive analysis "
            "for a given street with enhanced capabilities. You can choose between: "
            "1. Heat pump analysis: `run_comprehensive_hp_analysis(street_name='street_name', scenario='scenario_name')` "
            "2. District heating analysis: `run_comprehensive_dh_analysis(street_name='street_name')` "
            "3. Scenario comparison: `compare_comprehensive_scenarios(street_name='street_name', hp_scenario='scenario_name')` "
            "4. KPI report generation: `generate_comprehensive_kpi_report(street_name='street_name')` "
            ""
            "Choose the most appropriate analysis based on the user's request. "
            "IMPORTANT: When you need to use a tool, ALWAYS output ONLY the function call on a single line, and nothing else. "
            "Do not explain, do not add extra text. "
            "After the tool call, wait for the result and present it clearly to the user."
        ),
        tools=[
            run_comprehensive_hp_analysis,
            run_comprehensive_dh_analysis,
            compare_comprehensive_scenarios,
            generate_comprehensive_kpi_report,
        ]
    )
)

# Data Explorer Agent - Data and Results Management
DataExplorerAgent = Agent(
    config=create_agent_config(
        name="DataExplorerAgent",
        system_prompt=(
            "You are the Data Explorer Agent (DEA). Your job is to help users explore available data and results. "
            "You can use the following tools: "
            "1. `get_all_street_names` to show all available streets in the dataset. "
            "2. `list_available_results` to show all available result files including dashboards and visualizations. "
            "3. `analyze_kpi_report` to analyze existing KPI reports. "
            ""
            "IMPORTANT: When you need to use a tool, ALWAYS output ONLY the function call in the format: "
            "tool_name(arg1='value1', ...) on a single line, and nothing else. "
            "Do not explain, do not add extra text. "
            "After each tool call, wait for the result before proceeding to the next step."
        ),
        tools=[get_all_street_names, list_available_results, analyze_kpi_report]
    )
)

# Energy GPT - AI-Powered Analysis
EnergyGPT = Agent(
    config=create_agent_config(
        name="EnergyGPT",
        system_prompt=(
            "You are EnergyGPT, an expert AI analyst for energy infrastructure. Your job is to analyze results "
            "and provide insights. You can use the `analyze_kpi_report` tool to analyze KPI reports. "
            "Present the results clearly to the user with actionable insights and recommendations. "
            ""
            "IMPORTANT: When you need to use a tool, ALWAYS output ONLY the function call in the format: "
            "analyze_kpi_report(kpi_report_path='path_to_report') on a single line, and nothing else. "
            "Do not explain, do not add extra text. "
            "After the tool call, wait for the result and present it clearly to the user."
        ),
        tools=[analyze_kpi_report]
    )
)

# Export all agents for easy importing
__all__ = [
    "EnergyPlannerAgent",
    "CentralHeatingAgent", 
    "DecentralizedHeatingAgent",
    "ComparisonAgent",
    "AnalysisAgent",
    "DataExplorerAgent",
    "EnergyGPT",
    "create_agent_config",
    "load_gemini_config",
    "ADK_AVAILABLE"
]

# Print configuration summary
print(f"✅ Enhanced agents configured with ADK: {ADK_AVAILABLE}")
print(f"✅ Model: {GEMINI_CONFIG.get('model', 'Unknown')}")
print(f"✅ API Key configured: {'Yes' if GEMINI_CONFIG.get('api_key') else 'No'}")
print(f"✅ Temperature: {GEMINI_CONFIG.get('temperature', 'Unknown')}")
print(f"✅ Total agents: {len(__all__) - 3}")  # Exclude utility functions
