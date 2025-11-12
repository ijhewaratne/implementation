# 📚 API Documentation - ADK Agents

## 🎯 **Overview**

This document provides comprehensive API documentation for the Enhanced Multi-Agent System with Google ADK integration. The system includes 7 specialized agents that work together to provide comprehensive energy infrastructure analysis.

---

## 🤖 **Agent Architecture**

### **Agent Hierarchy**
```
EnergyPlannerAgent (EPA) - Master Orchestrator
├── CentralHeatingAgent (CHA) - District Heating Expert
├── DecentralizedHeatingAgent (DHA) - Heat Pump Expert
├── ComparisonAgent (CA) - Scenario Comparison Expert
├── AnalysisAgent (AA) - Comprehensive Analysis Expert
├── DataExplorerAgent (DEA) - Data & Results Expert
└── EnergyGPT (EGPT) - AI-Powered Analysis Expert
```

---

## 🎯 **EnergyPlannerAgent (EPA)**

### **Purpose**
Master orchestrator that delegates user requests to appropriate specialist agents.

### **Configuration**
```python
{
    "name": "EnergyPlannerAgent",
    "model": "gemini-1.5-flash-latest",
    "temperature": 0.7,
    "system_prompt": "You are a master energy planner for the city of Branitz...",
    "tools": []  # Delegates to specialist agents
}
```

### **System Prompt**
```
You are a master energy planner for the city of Branitz. Your goal is to help the user analyze different heating strategies with comprehensive infrastructure assessment. You have several specialist agents available:

1. CentralHeatingAgent (CHA): An expert on district heating networks with dual-pipe analysis and hydraulic simulation.
2. DecentralizedHeatingAgent (DHA): An expert on heat pumps with power flow analysis and electrical infrastructure assessment.
3. ComparisonAgent (CA): An expert at comparing both scenarios with comprehensive metrics.
4. AnalysisAgent (AA): An expert at comprehensive analysis with interactive visualizations.
5. DataExplorerAgent (DEA): An expert at exploring available data and results.
6. EnergyGPT (EGPT): An expert AI analyst for energy infrastructure, capable of analyzing results and providing insights.

First, understand the user's request. Then, clearly state which specialist agent you will delegate to:
'CHA' for district heating analysis,
'DHA' for heat pump analysis,
'CA' for comparing both scenarios,
'AA' for comprehensive analysis,
'DEA' for exploring data and results,
'EGPT' for general energy analysis and insights.

Your response should ONLY be the name of the agent to delegate to: 'CHA', 'DHA', 'CA', 'AA', 'DEA', or 'EGPT'.
```

### **Usage**
```python
from src.enhanced_agents import EnergyPlannerAgent

# Initialize agent
agent = EnergyPlannerAgent

# Use with ADK
from adk.api.adk import ADK
adk = ADK()
response = adk.run(agent, "analyze heating options for Parkstraße")
```

### **Expected Output**
- **Input**: "analyze heating options for Parkstraße"
- **Output**: "AA" (delegates to AnalysisAgent)

---

## 🔥 **CentralHeatingAgent (CHA)**

### **Purpose**
Expert on district heating networks with dual-pipe analysis and hydraulic simulation.

### **Configuration**
```python
{
    "name": "CentralHeatingAgent",
    "model": "gemini-1.5-flash-latest",
    "temperature": 0.7,
    "system_prompt": "You are the Central Heating Agent (CHA)...",
    "tools": ["run_comprehensive_dh_analysis"]
}
```

### **System Prompt**
```
You are the Central Heating Agent (CHA). Your job is to execute comprehensive district heating analysis including dual-pipe network design, hydraulic simulation, and interactive visualization. You MUST use the `run_comprehensive_dh_analysis` tool with the street name. This tool will automatically:

1. Extract buildings for the specified street
2. Create complete dual-pipe district heating network (supply + return)
3. Run pandapipes hydraulic simulation
4. Generate interactive dashboard with metrics
5. Provide comprehensive analysis summary

IMPORTANT: When you need to use a tool, ALWAYS output ONLY the function call in the format:
run_comprehensive_dh_analysis(street_name='street_name') on a single line, and nothing else.
Do not explain, do not add extra text.
After the tool call, wait for the result and present it clearly to the user.
```

### **Available Tools**

#### **run_comprehensive_dh_analysis(street_name: str)**
- **Purpose**: Execute comprehensive district heating analysis
- **Parameters**:
  - `street_name` (str): Name of the street to analyze
- **Returns**: Comprehensive analysis results including network design, simulation results, and visualizations
- **Example**:
  ```python
  result = run_comprehensive_dh_analysis("Parkstraße")
  ```

### **Usage**
```python
from src.enhanced_agents import CentralHeatingAgent

# Initialize agent
agent = CentralHeatingAgent

# Use with ADK
from adk.api.adk import ADK
adk = ADK()
response = adk.run(agent, "analyze district heating for Parkstraße")
```

### **Expected Output**
- **Input**: "analyze district heating for Parkstraße"
- **Output**: Tool call `run_comprehensive_dh_analysis(street_name='Parkstraße')` followed by analysis results

---

## ❄️ **DecentralizedHeatingAgent (DHA)**

### **Purpose**
Expert on heat pumps with power flow analysis and electrical infrastructure assessment.

### **Configuration**
```python
{
    "name": "DecentralizedHeatingAgent",
    "model": "gemini-1.5-flash-latest",
    "temperature": 0.7,
    "system_prompt": "You are the Decentralized Heating Agent (DHA)...",
    "tools": ["run_comprehensive_hp_analysis"]
}
```

### **System Prompt**
```
You are the Decentralized Heating Agent (DHA). Your job is to execute comprehensive heat pump feasibility analysis including power flow simulation, proximity assessment, and electrical infrastructure analysis. You MUST use the `run_comprehensive_hp_analysis` tool with the street name and optionally a scenario. This tool will automatically:

1. Extract buildings for the specified street
2. Analyze proximity to power infrastructure
3. Run pandapower power flow simulation
4. Generate interactive dashboard with metrics
5. Provide comprehensive feasibility assessment

Available scenarios: 'winter_werktag_abendspitze', 'summer_sonntag_abendphase', 'winter_werktag_mittag', 'summer_werktag_abendspitze'

IMPORTANT: When you need to use a tool, ALWAYS output ONLY the function call in the format:
run_comprehensive_hp_analysis(street_name='street_name', scenario='scenario_name') on a single line, and nothing else.
Do not explain, do not add extra text.
After the tool call, wait for the result and present it clearly to the user.
```

### **Available Tools**

#### **run_comprehensive_hp_analysis(street_name: str, scenario: str = 'winter_werktag_abendspitze')**
- **Purpose**: Execute comprehensive heat pump feasibility analysis
- **Parameters**:
  - `street_name` (str): Name of the street to analyze
  - `scenario` (str): Analysis scenario (optional, defaults to 'winter_werktag_abendspitze')
- **Returns**: Comprehensive heat pump analysis results including feasibility assessment, electrical impact, and visualizations
- **Example**:
  ```python
  result = run_comprehensive_hp_analysis("Parkstraße", "winter_werktag_abendspitze")
  ```

### **Usage**
```python
from src.enhanced_agents import DecentralizedHeatingAgent

# Initialize agent
agent = DecentralizedHeatingAgent

# Use with ADK
from adk.api.adk import ADK
adk = ADK()
response = adk.run(agent, "analyze heat pump feasibility for Parkstraße")
```

### **Expected Output**
- **Input**: "analyze heat pump feasibility for Parkstraße"
- **Output**: Tool call `run_comprehensive_hp_analysis(street_name='Parkstraße')` followed by analysis results

---

## ⚖️ **ComparisonAgent (CA)**

### **Purpose**
Expert at comparing both DH and HP scenarios with comprehensive metrics.

### **Configuration**
```python
{
    "name": "ComparisonAgent",
    "model": "gemini-1.5-flash-latest",
    "temperature": 0.7,
    "system_prompt": "You are the Comparison Agent (CA)...",
    "tools": ["compare_comprehensive_scenarios"]
}
```

### **System Prompt**
```
You are the Comparison Agent (CA). Your job is to compare both DH and HP scenarios for a given street with comprehensive analysis. You MUST use the `compare_comprehensive_scenarios` tool. This tool will automatically:

1. Run comprehensive heat pump feasibility analysis
2. Run comprehensive district heating network analysis
3. Provide side-by-side comparison with metrics
4. Generate recommendations based on technical and economic factors

IMPORTANT: When you need to use a tool, ALWAYS output ONLY the function call in the format:
compare_comprehensive_scenarios(street_name='street_name', hp_scenario='scenario_name') on a single line, and nothing else.
Do not explain, do not add extra text.
After the tool call, wait for the result and present it clearly to the user.
```

### **Available Tools**

#### **compare_comprehensive_scenarios(street_name: str, hp_scenario: str = 'winter_werktag_abendspitze')**
- **Purpose**: Compare DH and HP scenarios with comprehensive analysis
- **Parameters**:
  - `street_name` (str): Name of the street to analyze
  - `hp_scenario` (str): Heat pump analysis scenario (optional, defaults to 'winter_werktag_abendspitze')
- **Returns**: Comprehensive scenario comparison including metrics, recommendations, and visualizations
- **Example**:
  ```python
  result = compare_comprehensive_scenarios("Parkstraße", "winter_werktag_abendspitze")
  ```

### **Usage**
```python
from src.enhanced_agents import ComparisonAgent

# Initialize agent
agent = ComparisonAgent

# Use with ADK
from adk.api.adk import ADK
adk = ADK()
response = adk.run(agent, "compare heating scenarios for Parkstraße")
```

### **Expected Output**
- **Input**: "compare heating scenarios for Parkstraße"
- **Output**: Tool call `compare_comprehensive_scenarios(street_name='Parkstraße')` followed by comparison results

---

## 📊 **AnalysisAgent (AA)**

### **Purpose**
Expert at comprehensive analysis with interactive visualizations.

### **Configuration**
```python
{
    "name": "AnalysisAgent",
    "model": "gemini-1.5-flash-latest",
    "temperature": 0.7,
    "system_prompt": "You are the Analysis Agent (AA)...",
    "tools": [
        "run_comprehensive_hp_analysis",
        "run_comprehensive_dh_analysis",
        "compare_comprehensive_scenarios",
        "generate_comprehensive_kpi_report"
    ]
}
```

### **System Prompt**
```
You are the Analysis Agent (AA). Your job is to run comprehensive analysis for a given street with enhanced capabilities. You can choose between:

1. Heat pump analysis: `run_comprehensive_hp_analysis(street_name='street_name', scenario='scenario_name')`
2. District heating analysis: `run_comprehensive_dh_analysis(street_name='street_name')`
3. Scenario comparison: `compare_comprehensive_scenarios(street_name='street_name', hp_scenario='scenario_name')`
4. KPI report generation: `generate_comprehensive_kpi_report(street_name='street_name')`

Choose the most appropriate analysis based on the user's request.
IMPORTANT: When you need to use a tool, ALWAYS output ONLY the function call on a single line, and nothing else.
Do not explain, do not add extra text.
After the tool call, wait for the result and present it clearly to the user.
```

### **Available Tools**

#### **run_comprehensive_hp_analysis(street_name: str, scenario: str = 'winter_werktag_abendspitze')**
- **Purpose**: Execute comprehensive heat pump feasibility analysis
- **Parameters**:
  - `street_name` (str): Name of the street to analyze
  - `scenario` (str): Analysis scenario (optional, defaults to 'winter_werktag_abendspitze')
- **Returns**: Comprehensive heat pump analysis results

#### **run_comprehensive_dh_analysis(street_name: str)**
- **Purpose**: Execute comprehensive district heating analysis
- **Parameters**:
  - `street_name` (str): Name of the street to analyze
- **Returns**: Comprehensive district heating analysis results

#### **compare_comprehensive_scenarios(street_name: str, hp_scenario: str = 'winter_werktag_abendspitze')**
- **Purpose**: Compare DH and HP scenarios with comprehensive analysis
- **Parameters**:
  - `street_name` (str): Name of the street to analyze
  - `hp_scenario` (str): Heat pump analysis scenario (optional, defaults to 'winter_werktag_abendspitze')
- **Returns**: Comprehensive scenario comparison results

#### **generate_comprehensive_kpi_report(street_name: str)**
- **Purpose**: Generate comprehensive KPI report
- **Parameters**:
  - `street_name` (str): Name of the street to analyze
- **Returns**: Comprehensive KPI report with metrics and visualizations

### **Usage**
```python
from src.enhanced_agents import AnalysisAgent

# Initialize agent
agent = AnalysisAgent

# Use with ADK
from adk.api.adk import ADK
adk = ADK()
response = adk.run(agent, "analyze heating options for Parkstraße")
```

### **Expected Output**
- **Input**: "analyze heating options for Parkstraße"
- **Output**: Tool call based on analysis type followed by comprehensive results

---

## 🔍 **DataExplorerAgent (DEA)**

### **Purpose**
Expert at exploring available data and results.

### **Configuration**
```python
{
    "name": "DataExplorerAgent",
    "model": "gemini-1.5-flash-latest",
    "temperature": 0.7,
    "system_prompt": "You are the Data Explorer Agent (DEA)...",
    "tools": [
        "get_all_street_names",
        "list_available_results",
        "analyze_kpi_report"
    ]
}
```

### **System Prompt**
```
You are the Data Explorer Agent (DEA). Your job is to help users explore available data and results. You can use the following tools:

1. `get_all_street_names` to show all available streets in the dataset.
2. `list_available_results` to show all available result files including dashboards and visualizations.
3. `analyze_kpi_report` to analyze existing KPI reports.

IMPORTANT: When you need to use a tool, ALWAYS output ONLY the function call in the format:
tool_name(arg1='value1', ...) on a single line, and nothing else.
Do not explain, do not add extra text.
After each tool call, wait for the result before proceeding to the next step.
```

### **Available Tools**

#### **get_all_street_names()**
- **Purpose**: Retrieve all available street names from the dataset
- **Parameters**: None
- **Returns**: List of all available street names
- **Example**:
  ```python
  streets = get_all_street_names()
  ```

#### **list_available_results()**
- **Purpose**: List all available result files including dashboards and visualizations
- **Parameters**: None
- **Returns**: List of all available result files and their descriptions
- **Example**:
  ```python
  results = list_available_results()
  ```

#### **analyze_kpi_report(report_path: str = None)**
- **Purpose**: Analyze existing KPI reports
- **Parameters**:
  - `report_path` (str): Path to the KPI report (optional, defaults to latest report)
- **Returns**: Analysis of KPI report with insights and recommendations
- **Example**:
  ```python
  analysis = analyze_kpi_report("processed/kpi/kpi_summary.json")
  ```

### **Usage**
```python
from src.enhanced_agents import DataExplorerAgent

# Initialize agent
agent = DataExplorerAgent

# Use with ADK
from adk.api.adk import ADK
adk = ADK()
response = adk.run(agent, "show me all available streets")
```

### **Expected Output**
- **Input**: "show me all available streets"
- **Output**: Tool call `get_all_street_names()` followed by list of streets

---

## 🧠 **EnergyGPT (EGPT)**

### **Purpose**
Expert AI analyst for energy infrastructure, capable of analyzing results and providing insights.

### **Configuration**
```python
{
    "name": "EnergyGPT",
    "model": "gemini-1.5-flash-latest",
    "temperature": 0.7,
    "system_prompt": "You are EnergyGPT, an expert AI analyst...",
    "tools": ["analyze_kpi_report"]
}
```

### **System Prompt**
```
You are EnergyGPT, an expert AI analyst for energy infrastructure. Your job is to analyze results and provide insights. You can use the `analyze_kpi_report` tool to analyze KPI reports. Present the results clearly to the user with actionable insights and recommendations.
```

### **Available Tools**

#### **analyze_kpi_report(report_path: str = None)**
- **Purpose**: Analyze existing KPI reports with AI-powered insights
- **Parameters**:
  - `report_path` (str): Path to the KPI report (optional, defaults to latest report)
- **Returns**: AI-powered analysis of KPI report with insights and recommendations
- **Example**:
  ```python
  analysis = analyze_kpi_report("processed/kpi/kpi_summary.json")
  ```

### **Usage**
```python
from src.enhanced_agents import EnergyGPT

# Initialize agent
agent = EnergyGPT

# Use with ADK
from adk.api.adk import ADK
adk = ADK()
response = adk.run(agent, "analyze the available results")
```

### **Expected Output**
- **Input**: "analyze the available results"
- **Output**: Tool call `analyze_kpi_report()` followed by AI-powered analysis

---

## 🚀 **ADK Agent Runner**

### **Purpose**
Enhanced ADK Agent Runner with improved error handling, quota management, and ADK communication.

### **Class**: `ADKAgentRunner`

### **Location**: `agents copy/run_enhanced_agent_system.py`

### **Key Methods**

#### **`__init__()`**
- **Purpose**: Initialize the ADK Agent Runner
- **Returns**: ADKAgentRunner instance
- **Example**:
  ```python
  runner = ADKAgentRunner()
  ```

#### **`delegate_to_agent(user_input: str)`**
- **Purpose**: Enhanced delegation logic with better error handling
- **Parameters**:
  - `user_input` (str): User input to process
- **Returns**: Dictionary with delegation results
- **Example**:
  ```python
  result = runner.delegate_to_agent("analyze heating options for Parkstraße")
  ```

#### **`run_comprehensive_analysis(street_name: str, analysis_type: str = 'auto')`**
- **Purpose**: Run comprehensive analysis for a specific street
- **Parameters**:
  - `street_name` (str): Name of the street to analyze
  - `analysis_type` (str): Type of analysis ('auto', 'dh', 'hp', 'compare')
- **Returns**: Dictionary with analysis results
- **Example**:
  ```python
  result = runner.run_comprehensive_analysis("Parkstraße", "auto")
  ```

#### **`explore_data(query: str)`**
- **Purpose**: Explore available data and results
- **Parameters**:
  - `query` (str): Data exploration query
- **Returns**: Dictionary with exploration results
- **Example**:
  ```python
  result = runner.explore_data("show me all available streets")
  ```

#### **`analyze_results(result_path: str = None)`**
- **Purpose**: Analyze existing results
- **Parameters**:
  - `result_path` (str): Path to results (optional, defaults to latest)
- **Returns**: Dictionary with analysis results
- **Example**:
  ```python
  result = runner.analyze_results()
  ```

### **Usage**
```python
from agents.copy.run_enhanced_agent_system import ADKAgentRunner

# Initialize runner
runner = ADKAgentRunner()

# Use delegation
result = runner.delegate_to_agent("analyze heating options for Parkstraße")

# Use comprehensive analysis
result = runner.run_comprehensive_analysis("Parkstraße", "auto")

# Use data exploration
result = runner.explore_data("show me all available streets")
```

---

## 🔧 **Configuration Management**

### **Gemini Configuration**
```yaml
# configs/gemini_config.yml
api_key: "your_gemini_api_key"
model: "gemini-1.5-flash-latest"
temperature: 0.7
timeout: 30
max_retries: 3
```

### **Agent Configuration**
```python
# Individual agent configuration
{
    "name": "AgentName",
    "model": "gemini-1.5-flash-latest",
    "temperature": 0.7,
    "system_prompt": "Agent-specific system prompt...",
    "tools": ["tool1", "tool2", ...],
    "api_key": "your_gemini_api_key"
}
```

### **ADK Configuration**
```python
# ADK-specific configuration
{
    "adk_available": True,
    "fallback_to_simpleagent": True,
    "quota_retry_delay": 60,
    "max_retries": 3,
    "error_handling": "comprehensive"
}
```

---

## 🧪 **Testing**

### **Unit Tests**
```bash
# Run unit tests
python -m pytest tests/test_adk_agents_unit.py -v

# Run tool tests
python -m pytest tests/test_adk_tools_unit.py -v

# Run delegation tests
python -m pytest tests/test_adk_agent_delegation_unit.py -v
```

### **Integration Tests**
```bash
# Run integration tests
python -m pytest tests/test_adk_integration.py -v

# Run runner tests
python -m pytest tests/test_adk_runner_integration.py -v

# Run end-to-end tests
python -m pytest tests/test_adk_end_to_end_integration.py -v
```

### **Performance Tests**
```bash
# Run performance tests
python -m pytest tests/test_adk_performance.py -v

# Run comparison tests
python -m pytest tests/test_adk_vs_simpleagent_performance.py -v

# Run stability tests
python -m pytest tests/test_adk_system_stability.py -v
```

---

## 🚀 **Usage Examples**

### **Basic Usage**
```python
from src.enhanced_agents import EnergyPlannerAgent, CentralHeatingAgent
from adk.api.adk import ADK

# Initialize ADK
adk = ADK()

# Use EnergyPlannerAgent for delegation
response = adk.run(EnergyPlannerAgent, "analyze heating options for Parkstraße")
print(response.agent_response)  # Output: "AA"

# Use CentralHeatingAgent for district heating analysis
response = adk.run(CentralHeatingAgent, "analyze district heating for Parkstraße")
print(response.agent_response)  # Output: Tool call and results
```

### **Advanced Usage with Runner**
```python
from agents.copy.run_enhanced_agent_system import ADKAgentRunner

# Initialize runner
runner = ADKAgentRunner()

# Comprehensive analysis
result = runner.run_comprehensive_analysis("Parkstraße", "auto")
print(f"Analysis completed: {result['success']}")
print(f"Agent used: {result['delegated_agent_name']}")
print(f"Results: {result['agent_response']}")

# Data exploration
result = runner.explore_data("show me all available streets")
print(f"Streets found: {result['agent_response']}")
```

### **Error Handling**
```python
try:
    result = runner.delegate_to_agent("invalid input")
    if "error" in result:
        print(f"Error occurred: {result['error']}")
    else:
        print(f"Success: {result['agent_response']}")
except Exception as e:
    print(f"Exception: {e}")
```

---

## 📋 **Best Practices**

### **Agent Usage**
1. **Use EnergyPlannerAgent** for initial delegation
2. **Use specialist agents** for specific analysis tasks
3. **Handle errors gracefully** with try-catch blocks
4. **Validate inputs** before processing
5. **Use appropriate tools** for each agent

### **Performance Optimization**
1. **Cache results** when possible
2. **Use appropriate scenarios** for analysis
3. **Monitor quota usage** and implement retry logic
4. **Optimize tool calls** to minimize API usage
5. **Use fallback mechanisms** when ADK is unavailable

### **Error Handling**
1. **Implement retry logic** for transient errors
2. **Handle quota exceeded** errors gracefully
3. **Provide fallback options** when ADK is unavailable
4. **Log errors** for debugging and monitoring
5. **Validate responses** before processing

---

## 🔗 **Related Documentation**

- [System Architecture - ADK Integration](SYSTEM_ARCHITECTURE_ADK_INTEGRATION.md)
- [Enhanced Tools Documentation](src/enhanced_tools.py)
- [Configuration Guide](configs/)
- [Testing Documentation](tests/)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)

---

## 📞 **Support**

For questions, issues, or contributions related to the ADK agents:

1. **Check the documentation** for common usage patterns
2. **Run the test suite** to verify functionality
3. **Review the examples** for implementation guidance
4. **Check the configuration** for proper setup
5. **Monitor the logs** for error details

The ADK integration provides a robust, scalable, and reliable multi-agent system for energy infrastructure analysis with comprehensive error handling and fallback support.
