# 👨‍💻 Developer Guide - Enhanced Multi-Agent System with Google ADK

## 🎯 **Overview**

This developer guide provides comprehensive information for developers working with the Enhanced Multi-Agent System with Google ADK. It covers architecture, development workflows, testing, and contribution guidelines.

---

## 🏗️ **Architecture Overview**

### **System Architecture**
```
Enhanced Multi-Agent System with Google ADK
├── ADK Framework (Google Agent Development Kit)
├── 7 Specialized ADK Agents
├── Enhanced Tools Integration
├── ADK Agent Runner
├── Configuration Management
├── Performance Monitoring
└── Fallback Support (SimpleAgent)
```

### **Agent Hierarchy**
```python
# Agent delegation flow
EnergyPlannerAgent (EPA) → Specialist Agents
├── CentralHeatingAgent (CHA) - District Heating
├── DecentralizedHeatingAgent (DHA) - Heat Pumps
├── ComparisonAgent (CA) - Scenario Comparison
├── AnalysisAgent (AA) - Comprehensive Analysis
├── DataExplorerAgent (DEA) - Data Exploration
└── EnergyGPT (EGPT) - AI Analysis
```

---

## 🚀 **Development Setup**

### **Prerequisites**
- Python 3.8+ (3.9+ recommended)
- Google ADK package
- Google Gemini API Key
- Git for version control

### **Development Environment Setup**
```bash
# Clone repository
git clone <repository-url>
cd branitz_energy_decision_ai_street_final

# Create development environment
make deploy-dev

# Activate virtual environment
source dev/venv/bin/activate  # Linux/macOS
# or
dev\venv\Scripts\activate     # Windows

# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black ruff jupyter ipython
```

### **Configuration Setup**
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

## 🤖 **Agent Development**

### **Creating New Agents**

#### **1. Agent Definition**
```python
# src/enhanced_agents.py
from adk.api.agent import Agent
from src.enhanced_tools import custom_tool_function

# Create new agent
CustomAgent = Agent(
    config=create_agent_config(
        name="CustomAgent",
        system_prompt=(
            "You are a Custom Agent. Your job is to perform custom analysis. "
            "You MUST use the `custom_tool_function` tool with appropriate parameters. "
            "IMPORTANT: When you need to use a tool, ALWAYS output ONLY the function call "
            "in the format: custom_tool_function(param1='value1', param2='value2') "
            "on a single line, and nothing else."
        ),
        tools=[custom_tool_function]
    )
)
```

#### **2. Tool Implementation**
```python
# src/enhanced_tools.py
def custom_tool_function(param1: str, param2: str) -> str:
    """
    Custom tool function for analysis.
    
    Args:
        param1: First parameter
        param2: Second parameter
        
    Returns:
        Analysis results
    """
    try:
        # Your custom analysis logic here
        result = perform_custom_analysis(param1, param2)
        
        return f"Custom analysis completed for {param1} and {param2}. Results: {result}"
        
    except Exception as e:
        return f"Error in custom analysis: {str(e)}"
```

#### **3. Agent Registration**
```python
# src/enhanced_agents.py
# Add to agent map
agent_map = {
    "CHA": CentralHeatingAgent,
    "DHA": DecentralizedHeatingAgent,
    "CA": ComparisonAgent,
    "AA": AnalysisAgent,
    "DEA": DataExplorerAgent,
    "EGPT": EnergyGPT,
    "CUSTOM": CustomAgent  # Add new agent
}

# Add to exports
__all__ = [
    "EnergyPlannerAgent",
    "CentralHeatingAgent", 
    "DecentralizedHeatingAgent",
    "ComparisonAgent",
    "AnalysisAgent",
    "DataExplorerAgent",
    "EnergyGPT",
    "CustomAgent"  # Add new agent
]
```

### **Agent Configuration**

#### **Configuration Structure**
```python
def create_agent_config(name: str, system_prompt: str, tools: List[Any] = None) -> Dict[str, Any]:
    """Creates a standardized agent configuration dictionary."""
    config = {
        "name": name,
        "model": gemini_config.get("model", "gemini-1.5-flash-latest"),
        "system_prompt": system_prompt,
        "tools": tools if tools is not None else [],
        "temperature": gemini_config.get("temperature", 0.7),
        "api_key": gemini_config.get("api_key", os.getenv("GEMINI_API_KEY")),
    }
    return config
```

#### **System Prompt Guidelines**
```python
# Good system prompt structure
system_prompt = (
    "You are the [Agent Name] ([Agent Code]). Your job is to [primary function]. "
    "You MUST use the `[tool_name]` tool with [parameters]. "
    "This tool will automatically: "
    "1. [Step 1] "
    "2. [Step 2] "
    "3. [Step 3] "
    ""
    "IMPORTANT: When you need to use a tool, ALWAYS output ONLY the function call "
    "in the format: [tool_name](param1='value1', param2='value2') "
    "on a single line, and nothing else. "
    "After the tool call, wait for the result and present it clearly to the user."
)
```

---

## 🛠️ **Tool Development**

### **Tool Implementation Guidelines**

#### **1. Tool Function Structure**
```python
def tool_function_name(param1: str, param2: str = "default") -> str:
    """
    Tool function description.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2 (optional)
        
    Returns:
        Detailed description of return value
    """
    try:
        # Input validation
        if not param1:
            return "Error: param1 is required"
        
        # Main logic
        result = perform_analysis(param1, param2)
        
        # Format output
        return format_results(result)
        
    except Exception as e:
        return f"Error in tool execution: {str(e)}"
```

#### **2. Error Handling**
```python
def robust_tool_function(param1: str) -> str:
    """Tool with comprehensive error handling."""
    try:
        # Validate inputs
        if not param1 or not isinstance(param1, str):
            return "Error: Invalid parameter type or value"
        
        # Check prerequisites
        if not check_prerequisites():
            return "Error: Prerequisites not met"
        
        # Execute main logic
        result = execute_main_logic(param1)
        
        # Validate results
        if not validate_results(result):
            return "Error: Invalid results generated"
        
        return format_success_result(result)
        
    except FileNotFoundError as e:
        return f"Error: Required file not found: {str(e)}"
    except PermissionError as e:
        return f"Error: Permission denied: {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error occurred: {str(e)}"
```

#### **3. Performance Optimization**
```python
def optimized_tool_function(param1: str) -> str:
    """Tool with performance optimization."""
    import time
    import psutil
    
    start_time = time.time()
    start_memory = psutil.virtual_memory().used
    
    try:
        # Use efficient data structures
        data = load_data_efficiently(param1)
        
        # Process in chunks if large dataset
        if len(data) > 10000:
            result = process_in_chunks(data)
        else:
            result = process_data(data)
        
        # Clean up resources
        del data
        import gc
        gc.collect()
        
        # Log performance metrics
        end_time = time.time()
        end_memory = psutil.virtual_memory().used
        
        duration = (end_time - start_time) * 1000  # Convert to milliseconds
        memory_used = (end_memory - start_memory) / 1024 / 1024  # Convert to MB
        
        return f"Analysis completed in {duration:.2f}ms using {memory_used:.2f}MB. Results: {result}"
        
    except Exception as e:
        return f"Error in optimized tool execution: {str(e)}"
```

---

## 🧪 **Testing**

### **Unit Testing**

#### **Agent Testing**
```python
# tests/test_custom_agent.py
import pytest
from src.enhanced_agents import CustomAgent
from adk.api.adk import ADK

class TestCustomAgent:
    def test_agent_initialization(self):
        """Test agent initialization."""
        assert CustomAgent is not None
        assert CustomAgent.name == "CustomAgent"
    
    def test_agent_configuration(self):
        """Test agent configuration."""
        config = CustomAgent.config
        assert config["name"] == "CustomAgent"
        assert "custom_tool_function" in [tool.__name__ for tool in config["tools"]]
    
    def test_agent_delegation(self):
        """Test agent delegation."""
        adk = ADK()
        response = adk.run(CustomAgent, "test custom analysis")
        assert response is not None
        assert hasattr(response, 'agent_response')
```

#### **Tool Testing**
```python
# tests/test_custom_tools.py
import pytest
from src.enhanced_tools import custom_tool_function

class TestCustomTool:
    def test_tool_function_success(self):
        """Test successful tool execution."""
        result = custom_tool_function("param1", "param2")
        assert "Custom analysis completed" in result
        assert "param1" in result
        assert "param2" in result
    
    def test_tool_function_error_handling(self):
        """Test tool error handling."""
        result = custom_tool_function("", "param2")
        assert "Error" in result
    
    def test_tool_function_performance(self):
        """Test tool performance."""
        import time
        start_time = time.time()
        result = custom_tool_function("param1", "param2")
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000
        assert duration < 5000  # Should complete within 5 seconds
```

### **Integration Testing**

#### **End-to-End Testing**
```python
# tests/test_integration.py
import pytest
from agents.copy.run_enhanced_agent_system import ADKAgentRunner

class TestIntegration:
    def test_custom_agent_integration(self):
        """Test custom agent integration."""
        runner = ADKAgentRunner()
        
        # Test delegation to custom agent
        result = runner.delegate_to_agent("test custom analysis")
        
        assert "error" not in result
        assert result.get("delegated_agent") == "CUSTOM"
        assert result.get("success") is True
    
    def test_custom_tool_integration(self):
        """Test custom tool integration."""
        runner = ADKAgentRunner()
        
        # Test tool execution
        result = runner.delegate_to_agent("run custom analysis with param1 and param2")
        
        assert "error" not in result
        assert result.get("tools_executed") is True
        assert "Custom analysis completed" in result.get("agent_response", "")
```

### **Performance Testing**

#### **Performance Benchmarks**
```python
# tests/test_performance.py
import pytest
import time
import psutil
from agents.copy.run_enhanced_agent_system import ADKAgentRunner

class TestPerformance:
    def test_agent_response_time(self):
        """Test agent response time."""
        runner = ADKAgentRunner()
        
        start_time = time.time()
        result = runner.delegate_to_agent("test custom analysis")
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000
        assert response_time < 30000  # Should respond within 30 seconds
    
    def test_memory_usage(self):
        """Test memory usage."""
        initial_memory = psutil.virtual_memory().used
        
        runner = ADKAgentRunner()
        result = runner.delegate_to_agent("test custom analysis")
        
        final_memory = psutil.virtual_memory().used
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        assert memory_increase < 100  # Should not increase memory by more than 100MB
```

---

## 🔧 **Development Workflow**

### **Code Quality**

#### **Linting and Formatting**
```bash
# Run linting
ruff check src/ tests/

# Run formatting
black src/ tests/

# Run type checking
mypy src/
```

#### **Pre-commit Hooks**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.9
  
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.270
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.991
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### **Testing Workflow**

#### **Test Execution**
```bash
# Run all tests
make test-adk

# Run specific test categories
python -m pytest tests/test_adk_agents_unit.py -v
python -m pytest tests/test_adk_tools_unit.py -v
python -m pytest tests/test_adk_integration.py -v

# Run with coverage
python -m pytest --cov=src tests/

# Run performance tests
python -m pytest tests/test_adk_performance.py -v
```

#### **Continuous Integration**
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: |
          python -m pytest --cov=src tests/
      - name: Run linting
        run: |
          ruff check src/ tests/
          black --check src/ tests/
```

---

## 📚 **Documentation**

### **Code Documentation**

#### **Docstring Standards**
```python
def function_name(param1: str, param2: int = 10) -> str:
    """
    Brief description of the function.
    
    Detailed description of what the function does, including
    any important implementation details or considerations.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2 (default: 10)
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is invalid
        RuntimeError: When operation fails
        
    Example:
        >>> result = function_name("test", 20)
        >>> print(result)
        "Analysis completed"
    """
    pass
```

#### **Type Hints**
```python
from typing import Dict, List, Optional, Union, Any

def process_data(
    data: List[Dict[str, Any]], 
    options: Optional[Dict[str, Union[str, int]]] = None
) -> Dict[str, Any]:
    """Process data with optional configuration."""
    pass
```

### **API Documentation**

#### **Agent Documentation**
```python
# Document agent capabilities
class CustomAgent:
    """
    Custom Agent for specialized analysis.
    
    This agent provides custom analysis capabilities for specific use cases.
    It integrates with the ADK framework and provides comprehensive analysis
    through specialized tools.
    
    Attributes:
        name: Agent name
        config: Agent configuration
        tools: Available tools
        
    Example:
        >>> from src.enhanced_agents import CustomAgent
        >>> from adk.api.adk import ADK
        >>> adk = ADK()
        >>> response = adk.run(CustomAgent, "analyze custom data")
    """
    pass
```

---

## 🚀 **Deployment**

### **Development Deployment**
```bash
# Deploy development environment
make deploy-dev

# Start development services
cd dev
python start_dev.py
```

### **Production Deployment**
```bash
# Deploy production environment
make deploy-prod

# Start production services
cd prod
python start_adk_system.py
```

### **Docker Deployment**
```bash
# Build Docker images
make docker-build

# Start Docker services
make docker-up

# Check service status
docker-compose ps
```

---

## 🤝 **Contributing**

### **Contribution Guidelines**

#### **1. Fork and Clone**
```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/yourusername/branitz_energy_decision_ai_street_final.git
cd branitz_energy_decision_ai_street_final

# Add upstream remote
git remote add upstream https://github.com/original/branitz_energy_decision_ai_street_final.git
```

#### **2. Create Feature Branch**
```bash
# Create feature branch
git checkout -b feature/new-agent

# Make changes
# Add tests
# Update documentation

# Commit changes
git add .
git commit -m "Add new custom agent with comprehensive testing"
```

#### **3. Submit Pull Request**
```bash
# Push to your fork
git push origin feature/new-agent

# Create pull request on GitHub
# Include:
# - Description of changes
# - Tests added
# - Documentation updated
# - Breaking changes (if any)
```

### **Code Review Process**

#### **Review Checklist**
- [ ] **Code Quality**: Follows coding standards
- [ ] **Tests**: Comprehensive test coverage
- [ ] **Documentation**: Updated documentation
- [ ] **Performance**: No performance regressions
- [ ] **Security**: No security vulnerabilities
- [ ] **Compatibility**: Backward compatibility maintained

---

## 📋 **Best Practices**

### **Development Best Practices**

#### **1. Code Organization**
```python
# Organize code in logical modules
src/
├── enhanced_agents.py      # Agent definitions
├── enhanced_tools.py       # Tool implementations
├── cha_*.py               # CHA-specific modules
├── dha_*.py               # DHA-specific modules
└── utils/                 # Utility functions
    ├── config.py
    ├── logging.py
    └── validation.py
```

#### **2. Error Handling**
```python
# Use specific exception types
try:
    result = risky_operation()
except FileNotFoundError:
    return "Error: Required file not found"
except PermissionError:
    return "Error: Permission denied"
except Exception as e:
    return f"Error: Unexpected error occurred: {str(e)}"
```

#### **3. Performance Optimization**
```python
# Use efficient data structures
from collections import defaultdict
import numpy as np

# Process data in chunks
def process_large_dataset(data):
    chunk_size = 1000
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        yield process_chunk(chunk)
```

### **Testing Best Practices**

#### **1. Test Coverage**
```python
# Aim for high test coverage
# Test happy path
def test_successful_operation():
    result = function_under_test("valid_input")
    assert result == "expected_output"

# Test error cases
def test_error_handling():
    result = function_under_test("invalid_input")
    assert "Error" in result

# Test edge cases
def test_edge_cases():
    result = function_under_test("")
    assert result is not None
```

#### **2. Test Isolation**
```python
# Use fixtures for test setup
@pytest.fixture
def sample_data():
    return {"param1": "value1", "param2": "value2"}

def test_with_fixture(sample_data):
    result = function_under_test(sample_data["param1"])
    assert result is not None
```

---

## 🎉 **Conclusion**

This developer guide provides comprehensive information for developing with the Enhanced Multi-Agent System with Google ADK. By following the guidelines and best practices outlined here, developers can effectively contribute to and extend the system.

**Key Points:**
- **Architecture Understanding**: Understand the system architecture and agent hierarchy
- **Development Setup**: Proper development environment setup
- **Agent Development**: Guidelines for creating new agents and tools
- **Testing**: Comprehensive testing strategies
- **Code Quality**: Maintain high code quality standards
- **Documentation**: Keep documentation up to date
- **Contributing**: Follow contribution guidelines

**Happy developing!** 🚀
