# 🔧 CHA Hydraulic Simulation - Troubleshooting Guide

## 📋 **Overview**

This comprehensive troubleshooting guide provides solutions for common issues encountered when using the CHA (Centralized Heating Agent) system with enhanced hydraulic simulation capabilities. It covers Pandapipes integration, thermal simulation, auto-resize loops, validation systems, and performance optimization.

---

## 🚨 **Quick Diagnosis**

### **System Health Check**
```bash
# Quick system health check
python -c "
import sys
print(f'Python version: {sys.version}')

try:
    import pandapipes
    print(f'✅ Pandapipes version: {pandapipes.__version__}')
except ImportError:
    print('❌ Pandapipes not installed')

try:
    import numpy
    print(f'✅ NumPy version: {numpy.__version__}')
except ImportError:
    print('❌ NumPy not installed')

try:
    import pandas
    print(f'✅ Pandas version: {pandas.__version__}')
except ImportError:
    print('❌ Pandas not installed')
"
```

### **CHA Component Check**
```python
# Check CHA components availability
python -c "
try:
    from src.cha_enhanced_pandapipes import CHAEnhancedPandapipesSimulator
    print('✅ CHA Enhanced Pandapipes Simulator available')
except ImportError as e:
    print(f'❌ CHA Enhanced Pandapipes Simulator: {e}')

try:
    from src.cha_validation import CHAValidationSystem
    print('✅ CHA Validation System available')
except ImportError as e:
    print(f'❌ CHA Validation System: {e}')

try:
    from src.cha_schema_validator import CHASchemaValidator
    print('✅ CHA Schema Validator available')
except ImportError as e:
    print(f'❌ CHA Schema Validator: {e}')
"
```

### **Configuration Validation**
```bash
# Validate configuration
python -c "
import yaml
try:
    with open('configs/cha.yml', 'r') as f:
        config = yaml.safe_load(f)
    print('✅ Configuration file loaded successfully')
    
    # Check required parameters
    required_params = ['thermal_simulation_enabled', 'ground_temperature_c', 'pipe_sections']
    for param in required_params:
        if param in config:
            print(f'✅ {param}: {config[param]}')
        else:
            print(f'❌ Missing parameter: {param}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
"
```

---

## 🔍 **Common Issues and Solutions**

### **1. Pandapipes Integration Issues**

#### **Issue: ModuleNotFoundError: No module named 'pandapipes'**

**Symptoms:**
- Import error when trying to use CHAEnhancedPandapipesSimulator
- "Pandapipes not available" error messages

**Solutions:**
```bash
# Install Pandapipes
pip install pandapipes

# Or install with specific version
pip install pandapipes==0.8.0

# Verify installation
python -c "import pandapipes; print(f'Pandapipes version: {pandapipes.__version__}')"
```

#### **Issue: Pandapipes simulation fails with convergence errors**

**Symptoms:**
- "Simulation did not converge" error messages
- Unrealistic pressure or velocity values
- Network connectivity issues

**Solutions:**
```python
# Check network connectivity
def check_network_connectivity(network_data):
    """Check if network is properly connected."""
    # Check for isolated nodes
    isolated_nodes = []
    for node in network_data['junctions']:
        connected_pipes = [p for p in network_data['pipes'] 
                          if node['id'] in [p['from_node'], p['to_node']]]
        if len(connected_pipes) == 0:
            isolated_nodes.append(node['id'])
    
    if isolated_nodes:
        print(f"Warning: Isolated nodes found: {isolated_nodes}")
    
    return len(isolated_nodes) == 0

# Adjust simulation parameters
config = {
    'max_iter': 100,  # Increase max iterations
    'tol_p': 1e-4,    # Adjust pressure tolerance
    'tol_v': 1e-4,    # Adjust velocity tolerance
    'tol_T': 1e-4     # Adjust temperature tolerance
}
```

#### **Issue: Memory issues with large networks**

**Symptoms:**
- MemoryError during simulation
- Slow performance with large networks
- System becomes unresponsive

**Solutions:**
```python
import gc
import psutil

# Monitor memory usage
def monitor_memory():
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.1f} MB")
    return memory_mb

# Clean up after simulation
def cleanup_simulation():
    gc.collect()
    print("Memory cleaned up")

# Use smaller network chunks for large networks
def process_network_in_chunks(network_data, chunk_size=100):
    """Process large networks in smaller chunks."""
    pipes = network_data['pipes']
    for i in range(0, len(pipes), chunk_size):
        chunk = pipes[i:i + chunk_size]
        # Process chunk
        yield chunk
```

### **2. Thermal Simulation Issues**

#### **Issue: Thermal simulation produces unrealistic results**

**Symptoms:**
- Extremely high or low thermal losses
- Unrealistic temperature drops
- Negative thermal efficiency values

**Solutions:**
```python
# Validate thermal simulation parameters
def validate_thermal_config(config):
    """Validate thermal simulation configuration."""
    issues = []
    
    if config.get('ground_temperature_c', 0) < -50 or config.get('ground_temperature_c', 0) > 50:
        issues.append("Ground temperature should be between -50°C and 50°C")
    
    if config.get('pipe_sections', 1) < 1 or config.get('pipe_sections', 1) > 20:
        issues.append("Pipe sections should be between 1 and 20")
    
    if config.get('heat_transfer_coefficient', 0) < 0.1 or config.get('heat_transfer_coefficient', 0) > 2.0:
        issues.append("Heat transfer coefficient should be between 0.1 and 2.0 W/(m²·K)")
    
    return issues

# Check thermal calculation results
def validate_thermal_results(thermal_results):
    """Validate thermal calculation results."""
    issues = []
    
    if thermal_results['thermal_efficiency'] < 0 or thermal_results['thermal_efficiency'] > 1:
        issues.append(f"Thermal efficiency {thermal_results['thermal_efficiency']} is outside valid range [0,1]")
    
    if thermal_results['total_thermal_loss_kw'] < 0:
        issues.append("Negative thermal loss detected")
    
    if thermal_results['temperature_drop_c'] < 0 or thermal_results['temperature_drop_c'] > 50:
        issues.append(f"Temperature drop {thermal_results['temperature_drop_c']}°C is unrealistic")
    
    return issues
```

#### **Issue: Thermal simulation takes too long**

**Symptoms:**
- Thermal calculations run for hours
- System becomes unresponsive during thermal simulation
- High CPU usage during thermal calculations

**Solutions:**
```python
# Optimize thermal simulation parameters
config = {
    'pipe_sections': 4,  # Reduce from 8 to 4 for faster calculation
    'thermal_simulation_enabled': True,
    'ground_temperature_c': 10,
    'heat_transfer_coefficient': 0.6
}

# Use parallel processing for thermal calculations
from concurrent.futures import ThreadPoolExecutor
import numpy as np

def calculate_thermal_loss_parallel(pipe_data, num_workers=4):
    """Calculate thermal losses in parallel."""
    def calculate_single_pipe(pipe):
        # Thermal calculation for single pipe
        return calculate_pipe_thermal_loss(pipe)
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(calculate_single_pipe, pipe_data))
    
    return results
```

### **3. Auto-Resize Loop Issues**

#### **Issue: Auto-resize loop fails to converge**

**Symptoms:**
- "Auto-resize failed to converge" error messages
- Infinite loop in auto-resize process
- Pipes remain oversized after multiple iterations

**Solutions:**
```python
# Adjust auto-resize parameters
config = {
    'max_resize_iterations': 3,  # Reduce from 5 to 3
    'velocity_tolerance': 0.05,  # Tighten tolerance
    'pressure_tolerance': 25,    # Tighten pressure tolerance
    'resize_factor': 1.1         # Smaller resize steps
}

# Add convergence monitoring
def monitor_auto_resize_convergence(iteration_results):
    """Monitor auto-resize convergence."""
    if len(iteration_results) < 2:
        return True
    
    last_result = iteration_results[-1]
    prev_result = iteration_results[-2]
    
    velocity_improvement = abs(last_result['max_velocity_ms'] - prev_result['max_velocity_ms'])
    pressure_improvement = abs(last_result['max_pressure_drop_pa_per_m'] - prev_result['max_pressure_drop_pa_per_m'])
    
    # Check if improvement is too small (converged)
    if velocity_improvement < 0.01 and pressure_improvement < 5:
        return True
    
    return False
```

#### **Issue: Auto-resize produces extreme pipe sizes**

**Symptoms:**
- Very large or very small pipe diameters
- Unrealistic pipe sizing results
- System instability during auto-resize

**Solutions:**
```python
# Add pipe size constraints
def apply_pipe_size_constraints(pipe_data, min_diameter=0.05, max_diameter=1.0):
    """Apply constraints to pipe diameters."""
    constrained_data = pipe_data.copy()
    
    # Apply minimum diameter constraint
    constrained_data['diameter_m'] = constrained_data['diameter_m'].clip(lower=min_diameter)
    
    # Apply maximum diameter constraint
    constrained_data['diameter_m'] = constrained_data['diameter_m'].clip(upper=max_diameter)
    
    # Log constrained pipes
    constrained_pipes = pipe_data['diameter_m'] != constrained_data['diameter_m']
    if constrained_pipes.any():
        print(f"Warning: {constrained_pipes.sum()} pipes were constrained to valid diameter range")
    
    return constrained_data

# Validate pipe sizing results
def validate_pipe_sizing_results(pipe_data):
    """Validate pipe sizing results."""
    issues = []
    
    if pipe_data['diameter_m'].min() < 0.05:
        issues.append("Some pipes have diameters smaller than 50mm")
    
    if pipe_data['diameter_m'].max() > 1.0:
        issues.append("Some pipes have diameters larger than 1000mm")
    
    if pipe_data['diameter_m'].isna().any():
        issues.append("Some pipes have undefined diameters")
    
    return issues
```

### **4. Validation System Issues**

#### **Issue: Schema validation fails**

**Symptoms:**
- "Schema validation failed" error messages
- Invalid JSON structure errors
- Missing required fields errors

**Solutions:**
```python
# Check schema file
def validate_schema_file(schema_path):
    """Validate schema file."""
    try:
        import json
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        print("✅ Schema file is valid JSON")
        return True
    except Exception as e:
        print(f"❌ Schema file error: {e}")
        return False

# Fix common schema issues
def fix_common_schema_issues(data):
    """Fix common schema validation issues."""
    fixed_data = data.copy()
    
    # Ensure required fields exist
    required_fields = ['metadata', 'network_info', 'hydraulic_results', 'thermal_results', 'standards_compliance']
    for field in required_fields:
        if field not in fixed_data:
            fixed_data[field] = {}
    
    # Fix metadata issues
    if 'generated_at' not in fixed_data['metadata']:
        from datetime import datetime
        fixed_data['metadata']['generated_at'] = datetime.now().isoformat()
    
    # Fix numeric type issues
    if 'thermal_efficiency' in fixed_data['thermal_results']:
        fixed_data['thermal_results']['thermal_efficiency'] = float(fixed_data['thermal_results']['thermal_efficiency'])
    
    return fixed_data
```

#### **Issue: Standards compliance validation fails**

**Symptoms:**
- "Standards compliance failed" error messages
- Unexpected violations in standards checking
- False positive compliance failures

**Solutions:**
```python
# Debug standards compliance
def debug_standards_compliance(cha_output):
    """Debug standards compliance issues."""
    violations = []
    
    # Check EN 13941 compliance
    max_velocity = cha_output['hydraulic_results']['max_velocity_ms']
    if max_velocity > 2.0:
        violations.append(f"EN 13941: Velocity {max_velocity:.2f} m/s exceeds 2.0 m/s limit")
    
    max_pressure_drop = cha_output['hydraulic_results']['max_pressure_drop_pa_per_m']
    if max_pressure_drop > 500:
        violations.append(f"EN 13941: Pressure drop {max_pressure_drop:.0f} Pa/m exceeds 500 Pa/m limit")
    
    thermal_efficiency = cha_output['thermal_results']['thermal_efficiency']
    if thermal_efficiency < 0.85:
        violations.append(f"EN 13941: Thermal efficiency {thermal_efficiency:.2f} below 0.85 minimum")
    
    return violations

# Adjust standards thresholds
def adjust_standards_thresholds(config, standard='en_13941'):
    """Adjust standards compliance thresholds."""
    if standard == 'en_13941':
        config['max_velocity_ms'] = 2.0
        config['max_pressure_drop_pa_per_m'] = 500
        config['min_thermal_efficiency'] = 0.85
    elif standard == 'din_1988':
        config['max_velocity_ms'] = 2.0
        config['max_pressure_drop_pa_per_m'] = 400
        config['min_thermal_efficiency'] = 0.80
    elif standard == 'vdi_2067':
        config['max_velocity_ms'] = 1.5
        config['max_pressure_drop_pa_per_m'] = 300
        config['min_thermal_efficiency'] = 0.90
    
    return config
```

### **5. Performance Issues**

#### **Issue: Slow simulation performance**

**Symptoms:**
- Simulations take hours to complete
- High CPU usage during simulation
- Memory usage grows continuously

**Solutions:**
```python
# Optimize simulation performance
def optimize_simulation_performance(config):
    """Optimize simulation performance settings."""
    optimized_config = config.copy()
    
    # Reduce pipe sections for faster thermal calculation
    optimized_config['pipe_sections'] = 4  # Reduce from 8
    
    # Use simpler thermal model
    optimized_config['thermal_model'] = 'simplified'
    
    # Reduce convergence tolerance for faster convergence
    optimized_config['convergence_tolerance'] = 1e-4  # Less strict
    
    return optimized_config

# Profile simulation performance
import time
import cProfile

def profile_simulation(simulator, network_data):
    """Profile simulation performance."""
    start_time = time.time()
    
    # Run simulation with profiling
    cProfile.runctx('simulator.run_hydraulic_simulation()', 
                   globals(), locals(), 'simulation_profile.prof')
    
    end_time = time.time()
    print(f"Simulation completed in {end_time - start_time:.2f} seconds")
    
    # Analyze profile
    import pstats
    p = pstats.Stats('simulation_profile.prof')
    p.sort_stats('cumulative').print_stats(10)
```

#### **Issue: Memory leaks during simulation**

**Symptoms:**
- Memory usage increases with each simulation
- System becomes slow after multiple simulations
- Out of memory errors after extended use

**Solutions:**
```python
# Implement memory cleanup
def cleanup_after_simulation(simulator):
    """Clean up memory after simulation."""
    import gc
    
    # Clear simulation data
    if hasattr(simulator, 'network'):
        del simulator.network
    if hasattr(simulator, 'results'):
        del simulator.results
    
    # Force garbage collection
    gc.collect()
    
    print("Memory cleaned up after simulation")

# Monitor memory usage
def monitor_memory_usage():
    """Monitor memory usage during simulation."""
    import psutil
    import time
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024
    
    while True:
        current_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = current_memory - initial_memory
        
        if memory_increase > 1000:  # More than 1GB increase
            print(f"Warning: Memory usage increased by {memory_increase:.1f} MB")
            cleanup_after_simulation(simulator)
            break
        
        time.sleep(1)
```

---

## 🛠️ **Advanced Troubleshooting**

### **Debug Mode**

Enable debug mode for detailed logging:

```python
import logging

# Configure debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cha_debug.log'),
        logging.StreamHandler()
    ]
)

# Enable debug mode in configuration
config['debug_mode'] = True
config['verbose_logging'] = True
```

### **Performance Monitoring**

```python
# Monitor simulation performance
def monitor_simulation_performance(simulator):
    """Monitor simulation performance metrics."""
    import time
    import psutil
    
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    # Run simulation
    results = simulator.run_hydraulic_simulation()
    
    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    # Calculate metrics
    execution_time = end_time - start_time
    memory_usage = end_memory - start_memory
    
    print(f"Simulation Performance Metrics:")
    print(f"  Execution time: {execution_time:.2f} seconds")
    print(f"  Memory usage: {memory_usage:.1f} MB")
    print(f"  Peak memory: {end_memory:.1f} MB")
    
    return {
        'execution_time': execution_time,
        'memory_usage': memory_usage,
        'peak_memory': end_memory
    }
```

### **System Requirements Check**

```python
# Check system requirements
def check_system_requirements():
    """Check if system meets requirements."""
    import sys
    import psutil
    
    requirements = {
        'python_version': sys.version_info >= (3, 8),
        'memory_gb': psutil.virtual_memory().total / (1024**3) >= 4,
        'disk_space_gb': psutil.disk_usage('/').free / (1024**3) >= 2
    }
    
    print("System Requirements Check:")
    for requirement, met in requirements.items():
        status = "✅" if met else "❌"
        print(f"  {status} {requirement}: {met}")
    
    return all(requirements.values())
```

---

## 📞 **Getting Help**

### **Log Collection**

When reporting issues, collect the following logs:

```bash
# Collect system information
python -c "
import sys, platform, psutil
print(f'Python: {sys.version}')
print(f'Platform: {platform.platform()}')
print(f'Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB')
print(f'CPU: {psutil.cpu_count()} cores')
"

# Collect CHA logs
ls -la *.log
cat cha_debug.log | tail -50

# Collect configuration
cat configs/cha.yml
```

### **Common Error Codes**

| Error Code | Description | Solution |
|------------|-------------|----------|
| `CHA001` | Pandapipes not available | Install pandapipes: `pip install pandapipes` |
| `CHA002` | Configuration validation failed | Check config file syntax and required parameters |
| `CHA003` | Network connectivity issues | Verify network topology and node connections |
| `CHA004` | Simulation convergence failed | Adjust convergence parameters or check network |
| `CHA005` | Memory allocation failed | Reduce network size or optimize memory usage |
| `CHA006` | Schema validation failed | Check output data structure and required fields |
| `CHA007` | Standards compliance failed | Review network design against standards |

---

## 🎯 **Conclusion**

This troubleshooting guide covers the most common issues encountered with the CHA hydraulic simulation system. For additional support:

1. Check the logs for detailed error messages
2. Verify system requirements and dependencies
3. Test with smaller networks to isolate issues
4. Use debug mode for detailed logging
5. Contact support with collected logs and error details

Remember to always test changes in a development environment before applying them to production systems.
