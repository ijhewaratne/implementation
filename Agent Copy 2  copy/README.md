# Branitz Energy Decision AI - Agent System

A sophisticated multi-agent system for urban energy planning, providing the same comprehensive functionality as the main system but through intelligent agent delegation and specialized tools.

## 🤖 Agent Architecture

The system consists of **7 specialized agents** working together:

### **1. EnergyPlannerAgent** 🎯
- **Role**: Master orchestrator and delegation manager
- **Function**: Analyzes user requests and delegates to appropriate specialist agents
- **Tools**: None (delegation only)

### **2. CentralHeatingAgent (CHA)** 🔥
- **Role**: District Heating specialist
- **Function**: Executes complete DH scenario analysis
- **Tools**: Building extraction, network creation, simulation, visualization, analysis

### **3. DecentralizedHeatingAgent (DHA)** ❄️
- **Role**: Heat Pump specialist  
- **Function**: Executes complete HP scenario analysis
- **Tools**: Building extraction, network creation, simulation, visualization, analysis

### **4. ComparisonAgent (CA)** ⚖️
- **Role**: Scenario comparison expert
- **Function**: Runs both DH and HP scenarios and provides side-by-side comparison
- **Tools**: Scenario comparison

### **5. AnalysisAgent (AA)** 📊
- **Role**: Comprehensive analysis specialist
- **Function**: Runs complete end-to-end analysis with visualization
- **Tools**: Complete analysis pipeline

### **6. DataExplorerAgent (DEA)** 🔍
- **Role**: Data exploration and results management
- **Function**: Helps users explore available data and results
- **Tools**: Street listing, results listing, KPI analysis

### **7. EnergyGPT** 🧠
- **Role**: AI-powered analysis and reporting
- **Function**: Generates natural language insights from KPI data
- **Tools**: KPI analysis

## 🚀 Quick Start

### 1. Environment Setup
```bash
conda activate branitz_env
cd branitz_energy_decision_ai_street_agents
```

### 2. Run the Agent System
```bash
python run_agent_system.py
```

### 3. Interactive Usage
The system will present you with options:
- `analyze district heating for [street]` - Run DH scenario
- `analyze heat pumps for [street]` - Run HP scenario
- `compare scenarios for [street]` - Compare both DH and HP
- `comprehensive analysis for [street]` - Full analysis with visualization
- `show available streets` - List all streets in dataset
- `show results` - List all generated files

## 🛠️ Available Tools

### **Data Exploration Tools**
- `get_all_street_names()` - Lists all 27 available streets
- `get_building_ids_for_street(street_name)` - Extracts building IDs for a street
- `list_available_results()` - Shows all generated files

### **Network & Visualization Tools**
- `create_network_graph(building_ids, output_dir)` - Creates building network
- `create_network_visualization(output_dir)` - Generates high-quality plots (PNG + PDF)

### **Simulation & Analysis Tools**
- `run_simulation_pipeline(building_ids, scenario_type)` - Runs energy simulations
- `run_complete_analysis(street_name, scenario_type)` - Complete end-to-end analysis
- `compare_scenarios(street_name)` - Compares DH vs HP scenarios
- `analyze_kpi_report(kpi_path)` - AI-powered KPI analysis

## 📋 Example Usage

### **District Heating Analysis**
```
🎯 Your request: analyze district heating for Parkstraße

🤔 Planner Agent is thinking...
🎯 Planner delegated to CentralHeatingAgent.

⚡ CentralHeatingAgent is executing your request...
TOOL: Searching for buildings on 'Parkstraße'...
TOOL: Found 15 buildings.
TOOL: Creating network graph for 15 buildings...
TOOL: Starting pipeline for 15 buildings. Scenario type: DH
TOOL: Creating network visualization...
TOOL: Analyzing KPI report...

📊 CentralHeatingAgent Response:
[Complete analysis results]

🔍 Running additional analysis...
📈 Analyzing KPI report...
📋 AI Analysis:
[AI-generated insights]

✅ Request completed successfully!
```

### **Scenario Comparison**
```
🎯 Your request: compare scenarios for Liebermannstraße

🤔 Planner Agent is thinking...
🎯 Planner delegated to ComparisonAgent.

⚡ ComparisonAgent is executing your request...
TOOL: Comparing DH and HP scenarios for 'Liebermannstraße'...

📊 ComparisonAgent Response:
=== SCENARIO COMPARISON FOR LIEBERMANNSTRASSE ===
Buildings Analyzed: 105

DISTRICT HEATING (DH) SCENARIO:
[DH results]

HEAT PUMP (HP) SCENARIO:
[HP results]

KPI COMPARISON:
[Detailed comparison table]

RECOMMENDATION:
• Cost: Heat Pumps are 37.6% cheaper (€110.37 vs €176.88/MWh)
• Emissions: District Heating produces 12.18 fewer tons CO₂/year
• Recommendation: Heat Pumps based on cost priority

✅ Request completed successfully!
```

## 🎯 Agent Capabilities

### **Intelligent Delegation**
- Automatically routes requests to appropriate specialists
- Handles natural language queries
- Provides clear feedback on agent selection

### **Comprehensive Analysis**
- Building extraction and validation
- Network graph creation with minimum spanning trees
- Energy demand calculation
- Load profile generation
- Multi-scenario simulation
- KPI calculation and comparison
- AI-powered insights and recommendations

### **High-Quality Visualization**
- Network topology maps
- Building-to-street connections
- Service line layouts
- Multiple output formats (PNG, PDF, GeoJSON)

### **Data Management**
- Automatic file organization
- Result tracking and listing
- Error handling and recovery
- Progress feedback

## 🔧 Technical Features

### **Multi-Agent Coordination**
- Specialized agent roles
- Tool sharing and coordination
- Error handling and recovery
- Progress tracking

### **Comprehensive Toolset**
- 9 specialized tools
- Automatic tool chaining
- Result validation
- File management

### **User Experience**
- Natural language interface
- Clear progress indicators
- Comprehensive error messages
- Helpful suggestions

## 📊 Output Files

The system generates the same comprehensive outputs as the main system:

### **Network Files**
- `network_graph_*.json` - Building network topology
- `service_connections_*.geojson` - Building-to-street connections
- `buildings_projected_*.geojson` - Building geometries

### **Analysis Files**
- `scenario_kpis.csv` - Key performance indicators
- `scenario_kpis.json` - KPI data in JSON format
- `llm_final_report.md` - AI-generated analysis report

### **Visualization Files**
- `network_visualization.png` - High-resolution network map
- `network_visualization.pdf` - Vector format for printing

## 🚀 Advanced Usage

### **Testing Mode**
```bash
# Test individual agents
python run_agent_system.py test

# Test complete pipeline
python run_agent_system.py pipeline
```

### **Custom Analysis**
The agents can handle various request formats:
- "analyze central heating for Parkstraße"
- "run heat pump simulation for Liebermannstraße"
- "compare district heating vs heat pumps for Petzoldstraße"
- "show me all available streets"
- "what results do we have?"

## 🔍 Troubleshooting

### **Common Issues**
1. **Missing Dependencies**: Ensure `branitz_env` is activated
2. **File Not Found**: Check data file paths in configuration
3. **Agent Errors**: Review agent responses for specific issues
4. **Tool Failures**: Check tool output for detailed error messages

### **Error Recovery**
- Agents automatically handle most errors
- System provides clear error messages
- Failed operations can be retried
- Partial results are preserved

## 🎯 Key Advantages

### **vs. Main System**
- **Intelligent Delegation**: Automatically routes to appropriate specialists
- **Natural Language Interface**: More user-friendly interaction
- **Specialized Expertise**: Each agent has deep knowledge in their domain
- **Better Error Handling**: More robust error recovery
- **Enhanced Visualization**: Automatic plot generation and saving

### **vs. Traditional Tools**
- **AI-Powered Analysis**: Natural language insights and recommendations
- **Comprehensive Coverage**: End-to-end analysis pipeline
- **Multi-Scenario Comparison**: Side-by-side DH vs HP analysis
- **Interactive Exploration**: Easy data and result exploration

## 📈 Performance

- **Speed**: Optimized agent delegation reduces processing time
- **Accuracy**: Specialized agents provide more focused analysis
- **Reliability**: Robust error handling and recovery
- **Scalability**: Modular design supports easy expansion

The agent system provides the same comprehensive energy analysis capabilities as the main system, but with enhanced user experience, intelligent delegation, and specialized expertise through its multi-agent architecture.
