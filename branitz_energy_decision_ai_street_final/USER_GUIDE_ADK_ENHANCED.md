# 👥 Enhanced Multi-Agent System with Google ADK - User Guide

## 🎯 **Welcome to the Enhanced Multi-Agent System**

The Enhanced Multi-Agent System with Google ADK is a powerful, intelligent system for analyzing energy infrastructure and heating strategies. This user guide will help you get started with the ADK-enhanced agents and understand how to use their advanced features.

---

## 🚀 **Quick Start**

### **Prerequisites**

Before using the Enhanced Multi-Agent System, ensure you have:

- **Python 3.8 or higher** (3.9+ recommended)
- **Google ADK package** (optional, with fallback support)
- **Google Gemini API Key** (for ADK functionality)
- **Required dependencies** installed
- **Input data files** (streets, buildings, heat demand)
- **Configuration files** properly set up

### **Installation**

#### **Method 1: Interactive Deployment (Recommended)**
```bash
# Clone the repository
git clone <repository-url>
cd branitz_energy_decision_ai_street_final

# Run interactive deployment
make deploy-adk

# Follow the prompts:
# 1. Select environment (development/staging/production)
# 2. Configure API keys
# 3. Install dependencies
# 4. Run tests
# 5. Setup ADK environment
```

#### **Method 2: Manual Installation**
```bash
# Install dependencies
pip install -r requirements.txt

# Install ADK package (optional)
pip install adk>=0.1.0

# Verify installation
python -c "from agents.copy.run_enhanced_agent_system import ADKAgentRunner; print('ADK System installed successfully!')"
```

#### **Method 3: Docker Installation**
```bash
# Build Docker images
make docker-build

# Start Docker services
make docker-up

# Verify Docker deployment
docker-compose ps
```

### **Configuration Setup**

#### **1. API Key Configuration**
```bash
# Set environment variable
export GEMINI_API_KEY="your_gemini_api_key_here"

# Or update configuration file
echo "api_key: your_gemini_api_key_here" >> configs/gemini_config.yml
```

#### **2. ADK Configuration**
```yaml
# configs/gemini_config.yml
api_key: "your_gemini_api_key_here"
model: "gemini-1.5-flash-latest"
temperature: 0.7
timeout: 30
max_retries: 3

# ADK-specific configuration
adk:
  available: true
  fallback_to_simpleagent: true
  quota_retry_delay: 60
  max_retries: 3
  error_handling: "comprehensive"
```

---

## 🤖 **ADK-Enhanced Agents Overview**

### **Agent Hierarchy**

The Enhanced Multi-Agent System consists of 7 specialized ADK agents:

```
EnergyPlannerAgent (EPA) - Master Orchestrator
├── CentralHeatingAgent (CHA) - District Heating Expert
├── DecentralizedHeatingAgent (DHA) - Heat Pump Expert
├── ComparisonAgent (CA) - Scenario Comparison Expert
├── AnalysisAgent (AA) - Comprehensive Analysis Expert
├── DataExplorerAgent (DEA) - Data & Results Expert
└── EnergyGPT (EGPT) - AI-Powered Analysis Expert
```

### **Agent Capabilities**

#### **1. EnergyPlannerAgent (EPA) - Master Orchestrator**
- **Purpose**: Intelligent delegation to specialist agents
- **Capabilities**: 
  - Understands user requests
  - Delegates to appropriate specialist agents
  - Coordinates multi-agent workflows
  - Provides system overview and guidance

#### **2. CentralHeatingAgent (CHA) - District Heating Expert**
- **Purpose**: Comprehensive district heating analysis
- **Capabilities**:
  - Dual-pipe network design (supply + return)
  - Pandapipes hydraulic simulation
  - Interactive dashboard generation
  - Intelligent pipe sizing
  - Network optimization

#### **3. DecentralizedHeatingAgent (DHA) - Heat Pump Expert**
- **Purpose**: Heat pump feasibility analysis
- **Capabilities**:
  - Power flow simulation with Pandapower
  - Electrical infrastructure assessment
  - Proximity analysis
  - Feasibility evaluation
  - Performance optimization

#### **4. ComparisonAgent (CA) - Scenario Comparison Expert**
- **Purpose**: Compare DH vs HP scenarios
- **Capabilities**:
  - Side-by-side scenario comparison
  - Comprehensive metrics analysis
  - AI-powered recommendations
  - Economic analysis integration
  - Decision support

#### **5. AnalysisAgent (AA) - Comprehensive Analysis Expert**
- **Purpose**: Multi-scenario comprehensive analysis
- **Capabilities**:
  - Heat pump analysis
  - District heating analysis
  - Scenario comparison
  - KPI report generation
  - Interactive visualizations

#### **6. DataExplorerAgent (DEA) - Data & Results Expert**
- **Purpose**: Data exploration and results management
- **Capabilities**:
  - Street and building data access
  - Results exploration
  - KPI report analysis
  - Data visualization
  - Information retrieval

#### **7. EnergyGPT (EGPT) - AI-Powered Analysis Expert**
- **Purpose**: AI-powered analysis and insights
- **Capabilities**:
  - Advanced data analysis
  - AI-driven insights
  - Recommendation generation
  - Pattern recognition
  - Predictive analysis

---

## 🎮 **Basic Usage**

### **Starting the System**

#### **Method 1: Interactive Mode**
```bash
# Start the ADK system
make start-adk

# Or use the generated start script
python start_adk_system.py
```

#### **Method 2: Command Line Interface**
```bash
# Process a single input
python start_adk_system.py --input "analyze district heating for Parkstraße"

# Run analysis for a specific street
python start_adk_system.py --analyze Parkstraße --type dh

# Run comprehensive analysis
python start_adk_system.py --analyze Parkstraße --type auto
```

#### **Method 3: Programmatic Usage**
```python
from agents.copy.run_enhanced_agent_system import ADKAgentRunner

# Initialize the runner
runner = ADKAgentRunner()

# Process a request
result = runner.delegate_to_agent("analyze district heating for Parkstraße")

# Check results
if "error" in result:
    print(f"Error: {result['error']}")
else:
    print(f"Agent: {result.get('delegated_agent_name')}")
    print(f"Response: {result.get('agent_response')}")
```

### **Interactive Commands**

#### **Available Commands**
- **`help`** - Show available commands
- **`quit`** or **`exit`** - Exit the system
- **`analyze district heating for [street]`** - Analyze district heating
- **`analyze heat pump feasibility for [street]`** - Analyze heat pumps
- **`compare heating scenarios for [street]`** - Compare scenarios
- **`show me all available streets`** - List available streets
- **`analyze the available results`** - Analyze existing results

#### **Example Interactive Session**
```
🚀 Enhanced Interactive Multi-Agent System
Type 'quit' to exit, 'help' for available commands
==================================================

Enter your request: help

Available commands:
- Ask about district heating: 'analyze district heating for [street]'
- Ask about heat pumps: 'analyze heat pump feasibility for [street]'
- Compare scenarios: 'compare heating scenarios for [street]'
- Explore data: 'show me all available streets'
- Analyze results: 'analyze the available results'
- Quick analysis: 'analyze [street]' (auto-selects best option)

Enter your request: analyze district heating for Parkstraße

🔄 Processing: analyze district heating for Parkstraße
📋 Step 1: Determining appropriate agent...
✅ Delegating to: CHA
📋 Step 2: Executing with CentralHeatingAgent...

📊 Analysis Results:
Agent: CentralHeatingAgent
Response: [Comprehensive district heating analysis results...]
✅ Tools executed successfully
```

---

## 🔧 **ADK-Specific Features**

### **1. Enhanced Agent Communication**

#### **ADK Agent Delegation**
The system uses intelligent delegation to route requests to the most appropriate agent:

```python
# The EnergyPlannerAgent analyzes the request and delegates
user_input = "analyze district heating for Parkstraße"
result = runner.delegate_to_agent(user_input)

# Result contains delegation information
print(f"Delegated to: {result['delegated_agent']}")  # CHA
print(f"Agent name: {result['delegated_agent_name']}")  # CentralHeatingAgent
```

#### **Multi-Agent Coordination**
Agents can work together for complex analyses:

```python
# Comprehensive analysis using multiple agents
result = runner.run_comprehensive_analysis("Parkstraße", "compare")

# This will:
# 1. Use DHA for heat pump analysis
# 2. Use CHA for district heating analysis
# 3. Use CA for scenario comparison
# 4. Provide comprehensive results
```

### **2. Advanced Error Handling**

#### **Quota Management**
The system includes built-in quota management for API calls:

```python
# Automatic quota retry with exponential backoff
runner = ADKAgentRunner()
runner.quota_retry_delay = 60  # seconds
runner.max_retries = 3

# The system will automatically retry on quota exceeded errors
result = runner.delegate_to_agent("analyze district heating for Parkstraße")
```

#### **Fallback Support**
If ADK is unavailable, the system automatically falls back to SimpleAgent:

```python
# Automatic fallback configuration
config = {
    "adk_enabled": True,
    "fallback_enabled": True,
    "fallback_to_simpleagent": True
}

# The system will use SimpleAgent if ADK fails
```

### **3. Performance Optimization**

#### **Response Time Optimization**
The system is optimized for fast response times:

```python
# Performance monitoring
from src.cha_performance_monitoring import CHAPerformanceMonitor

monitor = CHAPerformanceMonitor()
monitor.start_monitoring()

# Run operations
result = runner.delegate_to_agent("analyze district heating for Parkstraße")

monitor.stop_monitoring()
print(monitor.get_metrics_summary())
```

#### **Memory Management**
Efficient memory usage with automatic cleanup:

```python
# Memory monitoring
import psutil

# Check memory usage
memory = psutil.virtual_memory()
print(f"Memory usage: {memory.percent}%")

# The system automatically manages memory for large operations
```

### **4. Enhanced Tool Integration**

#### **Comprehensive Analysis Tools**
Each agent has access to specialized tools:

```python
# CHA tools
cha_tools = ["run_comprehensive_dh_analysis"]

# DHA tools  
dha_tools = ["run_comprehensive_hp_analysis"]

# CA tools
ca_tools = ["compare_comprehensive_scenarios"]

# AA tools
aa_tools = [
    "run_comprehensive_hp_analysis",
    "run_comprehensive_dh_analysis", 
    "compare_comprehensive_scenarios",
    "generate_comprehensive_kpi_report"
]

# DEA tools
dea_tools = [
    "get_all_street_names",
    "list_available_results",
    "analyze_kpi_report"
]

# EGPT tools
egpt_tools = ["analyze_kpi_report"]
```

#### **Tool Execution Results**
Tools provide comprehensive results with detailed information:

```python
# Tool execution results
result = runner.delegate_to_agent("analyze district heating for Parkstraße")

if result.get('tools_executed'):
    print("✅ Tools executed successfully")
    print(f"Tool results: {result.get('tool_results')}")
    
    # Results include:
    # - Network design
    # - Hydraulic simulation
    # - Interactive dashboard
    # - Performance metrics
    # - Recommendations
```

---

## 📊 **Advanced Usage**

### **1. Comprehensive Analysis**

#### **Multi-Scenario Analysis**
```python
# Run comprehensive analysis for a street
result = runner.run_comprehensive_analysis("Parkstraße", "auto")

# Analysis types:
# - "auto": Let the system decide
# - "dh": District heating analysis
# - "hp": Heat pump analysis  
# - "compare": Scenario comparison
```

#### **Data Exploration**
```python
# Explore available data
result = runner.explore_data("show me all available streets")

# Analyze existing results
result = runner.analyze_results("processed/kpi/kpi_summary.json")
```

### **2. Custom Agent Configuration**

#### **Agent Configuration**
```python
# Custom agent configuration
from src.enhanced_agents import create_agent_config

config = create_agent_config(
    name="CustomAgent",
    system_prompt="You are a custom agent for specific analysis...",
    tools=[custom_tool_function]
)
```

#### **Tool Integration**
```python
# Add custom tools
def custom_analysis_tool(street_name: str) -> str:
    """Custom analysis tool."""
    # Your custom analysis logic
    return "Custom analysis results"

# Register with agent
agent = Agent(config=create_agent_config(
    name="CustomAgent",
    system_prompt="...",
    tools=[custom_analysis_tool]
))
```

### **3. Performance Monitoring**

#### **System Performance**
```python
# Monitor system performance
from src.cha_performance_monitoring import CHAPerformanceMonitor

monitor = CHAPerformanceMonitor()
monitor.start_monitoring()

# Run operations
for i in range(10):
    result = runner.delegate_to_agent(f"analyze street_{i}")

monitor.stop_monitoring()

# Get performance summary
summary = monitor.get_metrics_summary()
print(f"Average response time: {summary['response_time']['mean']}ms")
print(f"Memory usage: {summary['memory_usage']['mean']}MB")
```

#### **Health Monitoring**
```python
# System health check
def health_check():
    try:
        runner = ADKAgentRunner()
        result = runner.delegate_to_agent("health check")
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

# Run health check
if health_check():
    print("✅ System healthy")
else:
    print("❌ System unhealthy")
```

---

## 🧪 **Testing and Validation**

### **1. System Testing**

#### **Run All Tests**
```bash
# Run comprehensive test suite
make test-adk

# Run specific test categories
python -m pytest tests/test_adk_agents_unit.py -v
python -m pytest tests/test_adk_tools_unit.py -v
python -m pytest tests/test_adk_integration.py -v
python -m pytest tests/test_adk_performance.py -v
```

#### **Test Individual Components**
```bash
# Test ADK agents
python -m pytest tests/test_adk_agents_unit.py::TestEnergyPlannerAgent -v

# Test ADK tools
python -m pytest tests/test_adk_tools_unit.py::TestRunComprehensiveDHAnalysis -v

# Test integration
python -m pytest tests/test_adk_integration.py::TestEndToEndPipeline -v
```

### **2. Performance Testing**

#### **Performance Benchmarks**
```bash
# Run performance tests
python -m pytest tests/test_adk_performance.py -v

# Run system stability tests
python -m pytest tests/test_adk_system_stability.py -v

# Run performance comparison tests
python -m pytest tests/test_adk_vs_simpleagent_performance.py -v
```

#### **Load Testing**
```python
# Load testing example
import concurrent.futures
import time

def load_test():
    runner = ADKAgentRunner()
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(10):
            future = executor.submit(
                runner.delegate_to_agent, 
                f"analyze district heating for Street_{i}"
            )
            futures.append(future)
        
        results = [future.result() for future in futures]
    
    end_time = time.time()
    print(f"Load test completed in {end_time - start_time:.2f} seconds")
    print(f"Success rate: {sum(1 for r in results if 'error' not in r) / len(results) * 100:.1f}%")

# Run load test
load_test()
```

### **3. Validation**

#### **Configuration Validation**
```bash
# Validate configuration
python scripts/validate_config.py

# Validate specific environment
python scripts/validate_config.py --environment production
```

#### **System Validation**
```bash
# System health check
make health-check

# System status
make status

# Check deployment report
cat deployment_report.json | python -m json.tool
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. ADK Import Error**
```bash
# Error: ModuleNotFoundError: No module named 'adk'
# Solution: Install ADK package
pip install adk>=0.1.0

# Or use fallback mode
export ADK_ENABLED="false"
export FALLBACK_ENABLED="true"
```

#### **2. API Key Issues**
```bash
# Error: API key not configured
# Solution: Set API key
export GEMINI_API_KEY="your_api_key_here"

# Or update configuration file
echo "api_key: your_api_key_here" >> configs/gemini_config.yml
```

#### **3. Agent Delegation Issues**
```python
# Error: Unknown agent delegation
# Solution: Check agent map
from agents.copy.run_enhanced_agent_system import ADKAgentRunner

runner = ADKAgentRunner()
print(f"Available agents: {list(runner.agent_map.keys())}")

# Valid agents: CHA, DHA, CA, AA, DEA, EGPT
```

#### **4. Tool Execution Issues**
```python
# Error: Tool execution failed
# Solution: Check tool availability
from src.enhanced_tools import run_comprehensive_dh_analysis

try:
    result = run_comprehensive_dh_analysis("Parkstraße")
    print("Tool execution successful")
except Exception as e:
    print(f"Tool execution failed: {e}")
```

#### **5. Performance Issues**
```python
# Error: Slow response times
# Solution: Monitor performance
from src.cha_performance_monitoring import CHAPerformanceMonitor

monitor = CHAPerformanceMonitor()
monitor.start_monitoring()

# Run operations
result = runner.delegate_to_agent("analyze district heating for Parkstraße")

monitor.stop_monitoring()
summary = monitor.get_metrics_summary()

# Check performance metrics
if summary['response_time']['mean'] > 30000:  # 30 seconds
    print("⚠️ Response time is slow, consider optimization")
```

### **Debug Mode**

#### **Enable Debug Mode**
```bash
# Enable debug mode
export DEBUG="true"
export LOG_LEVEL="DEBUG"

# Run with debug output
python -u start_adk_system.py --debug
```

#### **Debug Information**
```python
# Get debug information
from agents.copy.run_enhanced_agent_system import ADKAgentRunner

runner = ADKAgentRunner()

# Check ADK availability
print(f"ADK available: {runner.adk is not None}")

# Check configuration
print(f"Configuration: {runner.config}")

# Check agent map
print(f"Agent map: {runner.agent_map}")
```

### **Log Analysis**

#### **View Logs**
```bash
# View deployment logs
tail -f deployment.log

# View system logs
tail -f logs/system.log

# View error logs
grep "ERROR" logs/*.log
```

#### **Log Analysis**
```bash
# Analyze deployment logs
grep "ERROR" deployment.log
grep "WARNING" deployment.log
grep "SUCCESS" deployment.log

# Analyze test results
grep "FAILED" test_results.log
grep "PASSED" test_results.log
```

---

## 📚 **Best Practices**

### **1. System Usage**

#### **Optimal Request Format**
```python
# Good: Specific and clear requests
"analyze district heating for Parkstraße"
"compare heating scenarios for Hauptstraße"
"show me all available streets"

# Avoid: Vague or unclear requests
"analyze something"
"help me"
"what can you do"
```

#### **Efficient Analysis**
```python
# Use appropriate analysis types
result = runner.run_comprehensive_analysis("Parkstraße", "dh")  # District heating
result = runner.run_comprehensive_analysis("Parkstraße", "hp")  # Heat pumps
result = runner.run_comprehensive_analysis("Parkstraße", "compare")  # Comparison
result = runner.run_comprehensive_analysis("Parkstraße", "auto")  # Auto-select
```

### **2. Performance Optimization**

#### **Batch Processing**
```python
# Process multiple streets efficiently
streets = ["Parkstraße", "Hauptstraße", "Bahnhofstraße"]

for street in streets:
    result = runner.delegate_to_agent(f"analyze district heating for {street}")
    # Process results
```

#### **Resource Management**
```python
# Monitor resource usage
import psutil

# Check system resources
cpu_percent = psutil.cpu_percent()
memory_percent = psutil.virtual_memory().percent

if cpu_percent > 80 or memory_percent > 80:
    print("⚠️ High resource usage detected")
```

### **3. Error Handling**

#### **Robust Error Handling**
```python
# Implement robust error handling
def safe_analysis(street_name: str):
    try:
        result = runner.delegate_to_agent(f"analyze district heating for {street_name}")
        
        if "error" in result:
            print(f"Analysis failed: {result['error']}")
            return None
        
        return result
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Use safe analysis
result = safe_analysis("Parkstraße")
```

#### **Retry Logic**
```python
# Implement retry logic
import time

def retry_analysis(street_name: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            result = runner.delegate_to_agent(f"analyze district heating for {street_name}")
            
            if "error" not in result:
                return result
            
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed: {e}, retrying...")
                time.sleep(2 ** attempt)
            else:
                print(f"All attempts failed: {e}")
    
    return None

# Use retry analysis
result = retry_analysis("Parkstraße")
```

---

## 📋 **Quick Reference**

### **Available Commands**
```bash
# System management
make start-adk          # Start ADK system
make test-adk           # Test ADK system
make health-check       # Health check
make status             # System status

# Deployment
make deploy-adk         # Interactive deployment
make deploy-dev         # Development deployment
make deploy-staging     # Staging deployment
make deploy-prod        # Production deployment

# Docker
make docker-build       # Build Docker images
make docker-up          # Start Docker services
make docker-down        # Stop Docker services
make docker-logs        # View Docker logs
```

### **Agent Quick Reference**
```python
# Agent delegation
"analyze district heating for [street]"     → CHA (CentralHeatingAgent)
"analyze heat pump feasibility for [street]" → DHA (DecentralizedHeatingAgent)
"compare heating scenarios for [street]"    → CA (ComparisonAgent)
"analyze heating options for [street]"      → AA (AnalysisAgent)
"show me all available streets"             → DEA (DataExplorerAgent)
"analyze the available results"             → EGPT (EnergyGPT)
```

### **Configuration Quick Reference**
```yaml
# configs/gemini_config.yml
api_key: "your_gemini_api_key_here"
model: "gemini-1.5-flash-latest"
temperature: 0.7
timeout: 30
max_retries: 3

adk:
  available: true
  fallback_to_simpleagent: true
  quota_retry_delay: 60
  max_retries: 3
  error_handling: "comprehensive"
```

---

## 🆘 **Support and Resources**

### **Documentation**
- [System Architecture - ADK Integration](SYSTEM_ARCHITECTURE_ADK_INTEGRATION.md)
- [API Documentation - ADK Agents](API_DOCUMENTATION_ADK_AGENTS.md)
- [ADK Integration Changes](ADK_INTEGRATION_CHANGES.md)
- [ADK Deployment Guide](ADK_DEPLOYMENT_GUIDE.md)

### **Getting Help**
- **Issues**: Report issues in the project repository
- **Documentation**: Check the comprehensive documentation
- **Community**: Join the project community discussions
- **Updates**: Follow project updates and releases

### **Best Practices**
- **Security**: Keep API keys secure and rotate regularly
- **Performance**: Monitor system performance and optimize as needed
- **Testing**: Run tests before and after changes
- **Documentation**: Keep user documentation updated
- **Backup**: Regular backup of configuration and data

---

## 🎉 **Conclusion**

The Enhanced Multi-Agent System with Google ADK provides powerful, intelligent analysis capabilities for energy infrastructure. With its 7 specialized agents, comprehensive tool integration, and robust error handling, it offers a complete solution for district heating and heat pump analysis.

**Key Benefits:**
- **Intelligent Delegation**: Automatic routing to appropriate specialist agents
- **Comprehensive Analysis**: Multi-scenario analysis with detailed results
- **Robust Error Handling**: Quota management and fallback support
- **Performance Optimization**: Fast response times and efficient resource usage
- **Easy Integration**: Simple API and comprehensive documentation
- **Flexible Deployment**: Multiple deployment options for different needs

**Ready to analyze your energy infrastructure with the Enhanced Multi-Agent System!** 🚀
