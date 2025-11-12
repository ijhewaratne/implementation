# 🔧 ADK Troubleshooting Guide - Enhanced Multi-Agent System

## 📋 **Overview**

This comprehensive troubleshooting guide provides solutions for common issues encountered when using the Enhanced Multi-Agent System with Google ADK. It covers ADK-specific problems, agent issues, tool failures, and system performance problems.

---

## 🚨 **Quick Diagnosis**

### **System Health Check**
```bash
# Quick system health check
make health-check

# Detailed system status
make status

# Check deployment report
cat deployment_report.json | python -m json.tool
```

### **ADK Availability Check**
```python
# Check ADK availability
python -c "
try:
    from adk.api.adk import ADK
    print('✅ ADK is available')
except ImportError:
    print('❌ ADK is not available - using fallback mode')
"
```

### **Configuration Validation**
```bash
# Validate configuration
python scripts/validate_config.py

# Check specific environment
python scripts/validate_config.py --environment production
```

---

## 🔍 **Common Issues and Solutions**

### **1. ADK Import and Installation Issues**

#### **Issue: ModuleNotFoundError: No module named 'adk'**
```bash
# Error message
ModuleNotFoundError: No module named 'adk'
```

**Solutions:**
```bash
# Solution 1: Install ADK package
pip install adk>=0.1.0

# Solution 2: Use fallback mode
export ADK_ENABLED="false"
export FALLBACK_ENABLED="true"

# Solution 3: Reinstall with specific version
pip uninstall adk
pip install adk==0.1.0

# Solution 4: Check Python environment
which python
pip list | grep adk
```

**Verification:**
```python
# Test ADK import
try:
    from adk.api.adk import ADK
    adk = ADK()
    print("✅ ADK imported and initialized successfully")
except ImportError as e:
    print(f"❌ ADK import failed: {e}")
except Exception as e:
    print(f"❌ ADK initialization failed: {e}")
```

#### **Issue: ADK Version Compatibility**
```bash
# Error message
ImportError: cannot import name 'ADK' from 'adk.api.adk'
```

**Solutions:**
```bash
# Check ADK version
pip show adk

# Update to latest version
pip install --upgrade adk

# Install specific compatible version
pip install adk==0.1.0
```

### **2. API Key and Authentication Issues**

#### **Issue: API key not configured**
```bash
# Error message
ValueError: API key not configured
```

**Solutions:**
```bash
# Solution 1: Set environment variable
export GEMINI_API_KEY="your_gemini_api_key_here"

# Solution 2: Update configuration file
echo "api_key: your_gemini_api_key_here" >> configs/gemini_config.yml

# Solution 3: Check configuration file
cat configs/gemini_config.yml | grep api_key
```

**Verification:**
```python
# Test API key configuration
import os
import yaml

# Check environment variable
api_key_env = os.getenv("GEMINI_API_KEY")
print(f"API key from environment: {'✅ Set' if api_key_env else '❌ Not set'}")

# Check configuration file
try:
    with open("configs/gemini_config.yml", 'r') as f:
        config = yaml.safe_load(f)
    api_key_config = config.get("api_key")
    print(f"API key from config: {'✅ Set' if api_key_config else '❌ Not set'}")
except Exception as e:
    print(f"❌ Configuration file error: {e}")
```

#### **Issue: Invalid API key**
```bash
# Error message
google.api_core.exceptions.Unauthenticated: 401 The request is not properly authenticated
```

**Solutions:**
```bash
# Solution 1: Verify API key
curl -H "Authorization: Bearer your_gemini_api_key_here" \
     https://generativelanguage.googleapis.com/v1/models

# Solution 2: Regenerate API key
# Go to Google AI Studio and generate a new API key

# Solution 3: Check API key format
echo $GEMINI_API_KEY | wc -c  # Should be around 39 characters
```

### **3. Agent Initialization Issues**

#### **Issue: Agent initialization failed**
```python
# Error message
RuntimeError: Failed to initialize ADKAgentRunner
```

**Solutions:**
```python
# Solution 1: Check ADK availability
from agents.copy.run_enhanced_agent_system import ADKAgentRunner

try:
    runner = ADKAgentRunner()
    print("✅ ADKAgentRunner initialized successfully")
except Exception as e:
    print(f"❌ ADKAgentRunner initialization failed: {e}")
    
    # Check individual components
    try:
        from adk.api.adk import ADK
        adk = ADK()
        print("✅ ADK initialized")
    except Exception as adk_error:
        print(f"❌ ADK initialization failed: {adk_error}")
    
    try:
        from src.enhanced_agents import load_gemini_config
        config = load_gemini_config()
        print("✅ Configuration loaded")
    except Exception as config_error:
        print(f"❌ Configuration loading failed: {config_error}")
```

#### **Issue: Agent delegation failed**
```python
# Error message
KeyError: 'Unknown agent: XYZ'
```

**Solutions:**
```python
# Solution 1: Check available agents
from agents.copy.run_enhanced_agent_system import ADKAgentRunner

runner = ADKAgentRunner()
print(f"Available agents: {list(runner.agent_map.keys())}")

# Valid agents: CHA, DHA, CA, AA, DEA, EGPT

# Solution 2: Check delegation logic
def test_delegation():
    test_cases = [
        "analyze district heating for Parkstraße",  # Should delegate to CHA
        "analyze heat pump feasibility for Parkstraße",  # Should delegate to DHA
        "compare heating scenarios for Parkstraße",  # Should delegate to CA
        "show me all available streets",  # Should delegate to DEA
    ]
    
    for test_input in test_cases:
        result = runner.delegate_to_agent(test_input)
        print(f"Input: {test_input}")
        print(f"Delegated to: {result.get('delegated_agent', 'Unknown')}")
        print(f"Success: {result.get('success', False)}")
        print()

test_delegation()
```

### **4. Tool Execution Issues**

#### **Issue: Tool execution failed**
```python
# Error message
AttributeError: 'NoneType' object has no attribute 'run'
```

**Solutions:**
```python
# Solution 1: Check tool availability
from src.enhanced_tools import (
    run_comprehensive_dh_analysis,
    run_comprehensive_hp_analysis,
    compare_comprehensive_scenarios
)

# Test individual tools
try:
    result = run_comprehensive_dh_analysis("Parkstraße")
    print("✅ DH analysis tool working")
except Exception as e:
    print(f"❌ DH analysis tool failed: {e}")

try:
    result = run_comprehensive_hp_analysis("Parkstraße")
    print("✅ HP analysis tool working")
except Exception as e:
    print(f"❌ HP analysis tool failed: {e}")

# Solution 2: Check tool dependencies
import sys
print(f"Python path: {sys.path}")

# Check if required modules are available
required_modules = ['pandas', 'geopandas', 'pandapipes', 'pandapower']
for module in required_modules:
    try:
        __import__(module)
        print(f"✅ {module} available")
    except ImportError:
        print(f"❌ {module} not available")
```

#### **Issue: Tool timeout**
```python
# Error message
TimeoutError: Tool execution timed out
```

**Solutions:**
```python
# Solution 1: Increase timeout
from src.enhanced_tools import run_comprehensive_dh_analysis
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Tool execution timed out")

# Set timeout to 60 seconds
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)

try:
    result = run_comprehensive_dh_analysis("Parkstraße")
    signal.alarm(0)  # Cancel timeout
    print("✅ Tool execution completed")
except TimeoutError:
    print("❌ Tool execution timed out")
    signal.alarm(0)  # Cancel timeout

# Solution 2: Check system resources
import psutil

cpu_percent = psutil.cpu_percent()
memory_percent = psutil.virtual_memory().percent

print(f"CPU usage: {cpu_percent}%")
print(f"Memory usage: {memory_percent}%")

if cpu_percent > 90 or memory_percent > 90:
    print("⚠️ High resource usage detected - may cause timeouts")
```

### **5. Performance Issues**

#### **Issue: Slow response times**
```python
# Performance issue: Response time > 30 seconds
```

**Solutions:**
```python
# Solution 1: Monitor performance
from src.cha_performance_monitoring import CHAPerformanceMonitor
import time

monitor = CHAPerformanceMonitor()
monitor.start_monitoring()

start_time = time.time()
result = runner.delegate_to_agent("analyze district heating for Parkstraße")
end_time = time.time()

monitor.stop_monitoring()

response_time = (end_time - start_time) * 1000  # Convert to milliseconds
print(f"Response time: {response_time:.2f}ms")

if response_time > 30000:  # 30 seconds
    print("⚠️ Slow response time detected")
    
    # Get performance summary
    summary = monitor.get_metrics_summary()
    print(f"Performance summary: {summary}")

# Solution 2: Optimize configuration
config = {
    "model": "gemini-1.5-flash-latest",  # Use faster model
    "temperature": 0.7,  # Lower temperature for faster responses
    "timeout": 30,  # Set appropriate timeout
    "max_retries": 3  # Limit retries
}
```

#### **Issue: High memory usage**
```python
# Memory issue: Memory usage > 80%
```

**Solutions:**
```python
# Solution 1: Monitor memory usage
import psutil
import gc

def monitor_memory():
    memory = psutil.virtual_memory()
    print(f"Memory usage: {memory.percent}%")
    
    if memory.percent > 80:
        print("⚠️ High memory usage detected")
        
        # Force garbage collection
        gc.collect()
        
        # Check memory after cleanup
        memory_after = psutil.virtual_memory()
        print(f"Memory usage after cleanup: {memory_after.percent}%")

# Solution 2: Optimize data processing
def optimize_data_processing():
    # Process data in chunks
    chunk_size = 1000
    
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        # Process chunk
        process_chunk(chunk)
        
        # Clean up
        del chunk
        gc.collect()

monitor_memory()
```

### **6. Network and Connectivity Issues**

#### **Issue: Network timeout**
```bash
# Error message
requests.exceptions.ConnectTimeout: HTTPSConnectionPool timeout
```

**Solutions:**
```bash
# Solution 1: Check network connectivity
ping google.com
curl -I https://generativelanguage.googleapis.com

# Solution 2: Configure proxy (if needed)
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"

# Solution 3: Increase timeout
export GEMINI_TIMEOUT="60"
```

#### **Issue: SSL certificate errors**
```bash
# Error message
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**Solutions:**
```bash
# Solution 1: Update certificates
pip install --upgrade certifi

# Solution 2: Check system certificates
python -c "import ssl; print(ssl.get_default_verify_paths())"

# Solution 3: Disable SSL verification (not recommended for production)
export PYTHONHTTPSVERIFY=0
```

### **7. Configuration Issues**

#### **Issue: Invalid configuration file**
```bash
# Error message
yaml.YAMLError: while parsing a block mapping
```

**Solutions:**
```bash
# Solution 1: Validate YAML syntax
python -c "
import yaml
try:
    with open('configs/gemini_config.yml', 'r') as f:
        yaml.safe_load(f)
    print('✅ YAML syntax is valid')
except yaml.YAMLError as e:
    print(f'❌ YAML syntax error: {e}')
"

# Solution 2: Check configuration structure
python -c "
import yaml
with open('configs/gemini_config.yml', 'r') as f:
    config = yaml.safe_load(f)
    
required_keys = ['api_key', 'model', 'temperature']
for key in required_keys:
    if key in config:
        print(f'✅ {key}: {config[key]}')
    else:
        print(f'❌ Missing key: {key}')
"
```

#### **Issue: Configuration validation failed**
```bash
# Error message
ValidationError: Invalid configuration value
```

**Solutions:**
```python
# Solution 1: Validate configuration values
def validate_config():
    config_path = "configs/gemini_config.yml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate API key
    api_key = config.get("api_key")
    if not api_key or len(api_key) < 20:
        print("❌ Invalid API key")
        return False
    
    # Validate model
    model = config.get("model")
    valid_models = ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest"]
    if model not in valid_models:
        print(f"❌ Invalid model: {model}")
        return False
    
    # Validate temperature
    temperature = config.get("temperature")
    if not isinstance(temperature, (int, float)) or not 0 <= temperature <= 1:
        print(f"❌ Invalid temperature: {temperature}")
        return False
    
    print("✅ Configuration is valid")
    return True

validate_config()
```

---

## 🔧 **Advanced Troubleshooting**

### **1. Debug Mode**

#### **Enable Debug Mode**
```bash
# Enable debug mode
export DEBUG="true"
export LOG_LEVEL="DEBUG"

# Run with debug output
python -u start_adk_system.py --debug
```

#### **Debug Information Collection**
```python
# Collect debug information
def collect_debug_info():
    debug_info = {
        "system": {},
        "python": {},
        "packages": {},
        "configuration": {},
        "adk": {}
    }
    
    # System information
    import platform
    debug_info["system"] = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "architecture": platform.architecture()
    }
    
    # Python path
    import sys
    debug_info["python"] = {
        "path": sys.path,
        "executable": sys.executable
    }
    
    # Package versions
    import pkg_resources
    packages = ["adk", "google-generativeai", "pandas", "geopandas"]
    for package in packages:
        try:
            version = pkg_resources.get_distribution(package).version
            debug_info["packages"][package] = version
        except:
            debug_info["packages"][package] = "Not installed"
    
    # Configuration
    try:
        import yaml
        with open("configs/gemini_config.yml", 'r') as f:
            config = yaml.safe_load(f)
        debug_info["configuration"] = config
    except Exception as e:
        debug_info["configuration"] = {"error": str(e)}
    
    # ADK status
    try:
        from adk.api.adk import ADK
        adk = ADK()
        debug_info["adk"] = {"status": "available", "version": "unknown"}
    except Exception as e:
        debug_info["adk"] = {"status": "unavailable", "error": str(e)}
    
    return debug_info

# Collect and display debug information
debug_info = collect_debug_info()
import json
print(json.dumps(debug_info, indent=2))
```

### **2. Log Analysis**

#### **Log Collection**
```bash
# Collect all logs
mkdir -p logs/analysis
cp deployment.log logs/analysis/
cp logs/*.log logs/analysis/ 2>/dev/null || true

# Analyze logs
grep "ERROR" logs/analysis/*.log > logs/analysis/errors.log
grep "WARNING" logs/analysis/*.log > logs/analysis/warnings.log
grep "SUCCESS" logs/analysis/*.log > logs/analysis/success.log
```

#### **Log Analysis Script**
```python
# Analyze logs for patterns
def analyze_logs():
    import re
    from collections import Counter
    
    # Read log files
    log_files = ["deployment.log", "logs/system.log"]
    all_logs = []
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                all_logs.extend(f.readlines())
        except FileNotFoundError:
            continue
    
    # Analyze error patterns
    error_patterns = []
    for line in all_logs:
        if "ERROR" in line:
            # Extract error message
            error_match = re.search(r"ERROR.*?:(.*)", line)
            if error_match:
                error_patterns.append(error_match.group(1).strip())
    
    # Count error patterns
    error_counts = Counter(error_patterns)
    print("Most common errors:")
    for error, count in error_counts.most_common(5):
        print(f"  {count}x: {error}")
    
    # Analyze warning patterns
    warning_patterns = []
    for line in all_logs:
        if "WARNING" in line:
            warning_match = re.search(r"WARNING.*?:(.*)", line)
            if warning_match:
                warning_patterns.append(warning_match.group(1).strip())
    
    warning_counts = Counter(warning_patterns)
    print("\nMost common warnings:")
    for warning, count in warning_counts.most_common(5):
        print(f"  {count}x: {warning}")

analyze_logs()
```

### **3. Performance Profiling**

#### **Performance Profiling**
```python
# Profile system performance
import cProfile
import pstats
import io

def profile_analysis():
    # Profile the analysis function
    pr = cProfile.Profile()
    pr.enable()
    
    # Run analysis
    result = runner.delegate_to_agent("analyze district heating for Parkstraße")
    
    pr.disable()
    
    # Get profiling results
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats()
    
    print("Performance profile:")
    print(s.getvalue())

profile_analysis()
```

#### **Memory Profiling**
```python
# Profile memory usage
from memory_profiler import profile

@profile
def memory_intensive_analysis():
    result = runner.delegate_to_agent("analyze district heating for Parkstraße")
    return result

# Run with memory profiling
result = memory_intensive_analysis()
```

---

## 🆘 **Emergency Recovery**

### **1. System Recovery**

#### **Reset to Default Configuration**
```bash
# Backup current configuration
cp configs/gemini_config.yml configs/gemini_config.yml.backup

# Reset to default configuration
cat > configs/gemini_config.yml << EOF
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
EOF
```

#### **Clean Installation**
```bash
# Clean installation
make clean
rm -rf venv/
rm -rf dev/
rm -rf staging/
rm -rf prod/

# Reinstall
make deploy-adk
```

### **2. Data Recovery**

#### **Backup and Restore**
```bash
# Backup data
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz processed/ configs/ logs/

# Restore from backup
tar -xzf backup_20240101_120000.tar.gz
```

#### **Configuration Recovery**
```bash
# Restore configuration from backup
cp configs/gemini_config.yml.backup configs/gemini_config.yml

# Validate restored configuration
python scripts/validate_config.py
```

---

## 📞 **Getting Help**

### **1. Self-Help Resources**

#### **Documentation**
- [User Guide - ADK Enhanced](USER_GUIDE_ADK_ENHANCED.md)
- [System Architecture - ADK Integration](SYSTEM_ARCHITECTURE_ADK_INTEGRATION.md)
- [API Documentation - ADK Agents](API_DOCUMENTATION_ADK_AGENTS.md)
- [ADK Deployment Guide](ADK_DEPLOYMENT_GUIDE.md)

#### **Diagnostic Tools**
```bash
# Run diagnostic suite
make health-check
make status
python scripts/validate_config.py
```

### **2. Community Support**

#### **Issue Reporting**
When reporting issues, include:
- **System Information**: OS, Python version, package versions
- **Error Messages**: Complete error messages and stack traces
- **Configuration**: Relevant configuration files (sanitized)
- **Logs**: Relevant log files
- **Steps to Reproduce**: Detailed steps to reproduce the issue

#### **Debug Information**
```bash
# Collect debug information
python -c "
import json
import platform
import sys
import pkg_resources

debug_info = {
    'system': platform.platform(),
    'python': sys.version,
    'packages': {}
}

packages = ['adk', 'google-generativeai', 'pandas', 'geopandas']
for pkg in packages:
    try:
        debug_info['packages'][pkg] = pkg_resources.get_distribution(pkg).version
    except:
        debug_info['packages'][pkg] = 'Not installed'

print(json.dumps(debug_info, indent=2))
"
```

### **3. Professional Support**

#### **Enterprise Support**
For enterprise users, professional support is available including:
- **Priority Support**: Faster response times
- **Custom Solutions**: Tailored solutions for specific needs
- **Training**: Comprehensive training programs
- **Consulting**: Expert consulting services

---

## 📋 **Troubleshooting Checklist**

### **Before Reporting Issues**

- [ ] **System Requirements**: Verify system meets requirements
- [ ] **Dependencies**: Check all dependencies are installed
- [ ] **Configuration**: Validate configuration files
- [ ] **API Keys**: Verify API keys are correct and valid
- [ ] **Network**: Check network connectivity
- [ ] **Logs**: Review relevant log files
- [ ] **Documentation**: Check documentation for solutions
- [ ] **Community**: Search community forums for similar issues

### **Issue Reporting Template**

```
**Issue Description:**
[Brief description of the issue]

**Environment:**
- OS: [Operating system and version]
- Python: [Python version]
- ADK: [ADK version]
- Other packages: [Relevant package versions]

**Error Messages:**
[Complete error messages and stack traces]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What you expected to happen]

**Actual Behavior:**
[What actually happened]

**Configuration:**
[Relevant configuration files - sanitized]

**Logs:**
[Relevant log entries]

**Additional Information:**
[Any other relevant information]
```

---

## 🎉 **Conclusion**

This troubleshooting guide provides comprehensive solutions for common issues encountered with the Enhanced Multi-Agent System with Google ADK. By following the diagnostic steps and solutions provided, most issues can be resolved quickly and effectively.

**Key Points:**
- **Systematic Approach**: Follow the diagnostic steps in order
- **Log Analysis**: Always check logs for detailed error information
- **Configuration Validation**: Ensure configuration files are correct
- **Performance Monitoring**: Monitor system performance regularly
- **Community Support**: Use community resources for additional help
- **Professional Support**: Consider professional support for complex issues

**Remember**: Most issues are configuration-related and can be resolved by following the solutions in this guide. For persistent issues, don't hesitate to seek community or professional support.

**Happy troubleshooting!** 🔧
