# 🔧 Enhanced CHA (Centralized Heating Agent) - Detailed Constraints Guide

## 🎯 **Overview**
This document provides a comprehensive overview of all constraints, limitations, and validation criteria used in the Enhanced Centralized Heating Agent (CHA) with intelligent pipe sizing capabilities.

---

## 🌡️ **Thermal Constraints**

### **Temperature Constraints**
```yaml
# Supply and Return Temperature Limits
supply_temperature_c: 70      # Supply water temperature (°C)
return_temperature_c: 40      # Return water temperature (°C)
temperature_difference_k: 30  # ΔT between supply and return (K)

# Temperature Range Constraints
min_supply_temperature_c: 65  # Minimum supply temperature
max_supply_temperature_c: 90  # Maximum supply temperature
min_return_temperature_c: 35  # Minimum return temperature
max_return_temperature_c: 45  # Maximum return temperature

# Temperature-Dependent Properties
water_density_kg_m3: 1000     # Water density at 40°C
specific_heat_capacity_j_kgk: 4180  # Water specific heat capacity
thermal_conductivity_w_mk: 0.6      # Water thermal conductivity
```

### **Heat Transfer Constraints**
```python
def validate_thermal_constraints(self, network_data: dict) -> dict:
    """Validate thermal constraints for the district heating network."""
    
    violations = []
    warnings = []
    
    # Temperature difference validation
    delta_t = network_data['supply_temperature'] - network_data['return_temperature']
    if delta_t < 25:  # Minimum 25°C difference
        violations.append(f"Temperature difference too small: {delta_t}°C (minimum 25°C)")
    elif delta_t > 40:  # Maximum 40°C difference
        warnings.append(f"Large temperature difference: {delta_t}°C (maximum 40°C)")
    
    # Supply temperature validation
    supply_temp = network_data['supply_temperature']
    if supply_temp < 65 or supply_temp > 90:
        violations.append(f"Supply temperature outside range: {supply_temp}°C (65-90°C)")
    
    # Return temperature validation
    return_temp = network_data['return_temperature']
    if return_temp < 35 or return_temp > 45:
        violations.append(f"Return temperature outside range: {return_temp}°C (35-45°C)")
    
    return {
        'compliant': len(violations) == 0,
        'violations': violations,
        'warnings': warnings,
        'thermal_efficiency': delta_t / 30.0  # Normalized efficiency
    }
```

---

## 💨 **Pressure Constraints**

### **Pressure Limits**
```yaml
# Operating Pressure Constraints
supply_pressure_bar: 6.0      # Supply pressure at plant (bar)
return_pressure_bar: 2.0      # Return pressure at plant (bar)
pressure_difference_bar: 4.0  # Pressure difference (bar)

# Pressure Range Constraints
min_supply_pressure_bar: 4.0  # Minimum supply pressure
max_supply_pressure_bar: 8.0  # Maximum supply pressure
min_return_pressure_bar: 1.5  # Minimum return pressure
max_return_pressure_bar: 3.0  # Maximum return pressure

# Pressure Drop Constraints
max_pressure_drop_pa_per_m: 50    # Maximum pressure drop per meter
max_total_pressure_drop_bar: 2.0  # Maximum total pressure drop
min_operating_pressure_bar: 2.0   # Minimum operating pressure
```

### **Pressure Validation**
```python
def validate_pressure_constraints(self, simulation_results: dict) -> dict:
    """Validate pressure constraints for the network."""
    
    violations = []
    warnings = []
    
    pressures = simulation_results['pressures']
    pressure_drops = simulation_results['pressure_drops']
    
    # Minimum pressure validation
    min_pressure = min(pressures)
    if min_pressure < 2.0:
        violations.append(f"Pressure below minimum: {min_pressure:.2f} bar (minimum 2.0 bar)")
    elif min_pressure < 2.5:
        warnings.append(f"Low pressure warning: {min_pressure:.2f} bar")
    
    # Maximum pressure validation
    max_pressure = max(pressures)
    if max_pressure > 8.0:
        violations.append(f"Pressure exceeds maximum: {max_pressure:.2f} bar (maximum 8.0 bar)")
    elif max_pressure > 7.0:
        warnings.append(f"High pressure warning: {max_pressure:.2f} bar")
    
    # Pressure drop validation
    max_pressure_drop = max(pressure_drops)
    if max_pressure_drop > 2.0:
        violations.append(f"Total pressure drop too high: {max_pressure_drop:.2f} bar (maximum 2.0 bar)")
    
    # Pressure drop per meter validation
    max_drop_per_m = max([dp/length for dp, length in zip(pressure_drops, pipe_lengths)])
    if max_drop_per_m > 50:  # Pa/m
        violations.append(f"Pressure drop per meter too high: {max_drop_per_m:.1f} Pa/m (maximum 50 Pa/m)")
    
    return {
        'compliant': len(violations) == 0,
        'violations': violations,
        'warnings': warnings,
        'pressure_margin': min_pressure - 2.0,  # Safety margin
        'pressure_drop_efficiency': 2.0 - max_pressure_drop  # Efficiency metric
    }
```

---

## 🌊 **Hydraulic Constraints**

### **Velocity Constraints (EN 13941)**
```yaml
# Velocity Limits
max_velocity_ms: 3.0          # Maximum fluid velocity (m/s)
min_velocity_ms: 0.5          # Minimum velocity for turbulent flow (m/s)
optimal_velocity_range_ms: [1.0, 2.5]  # Optimal velocity range

# Velocity-Dependent Constraints
turbulent_flow_reynolds_min: 4000    # Minimum Reynolds number for turbulent flow
cavitation_velocity_ms: 4.0          # Velocity threshold for cavitation risk
erosion_velocity_ms: 2.5             # Velocity threshold for erosion risk
```

### **Flow Regime Constraints**
```yaml
# Reynolds Number Constraints
min_reynolds_number: 4000     # Minimum for turbulent flow
max_reynolds_number: 100000   # Maximum for stable flow
transition_reynolds: 2300     # Transition from laminar to turbulent

# Flow Characteristics
flow_uniformity_min: 0.8      # Minimum flow uniformity across network
flow_balance_tolerance: 0.05  # 5% tolerance for flow balance
```

### **Hydraulic Validation**
```python
def validate_hydraulic_constraints(self, simulation_results: dict) -> dict:
    """Validate hydraulic constraints for the network."""
    
    violations = []
    warnings = []
    
    velocities = simulation_results['velocities']
    reynolds_numbers = simulation_results['reynolds_numbers']
    flows = simulation_results['flows']
    
    # Velocity constraint validation
    max_velocity = max(velocities)
    min_velocity = min(velocities)
    
    if max_velocity > 3.0:
        violations.append(f"Velocity exceeds maximum: {max_velocity:.2f} m/s (maximum 3.0 m/s)")
    elif max_velocity > 2.5:
        warnings.append(f"Velocity approaching limit: {max_velocity:.2f} m/s")
    
    if min_velocity < 0.5:
        violations.append(f"Velocity below minimum: {min_velocity:.2f} m/s (minimum 0.5 m/s)")
    elif min_velocity < 0.8:
        warnings.append(f"Low velocity warning: {min_velocity:.2f} m/s")
    
    # Reynolds number validation
    laminar_pipes = [i for i, re in enumerate(reynolds_numbers) if re < 4000]
    if laminar_pipes:
        warnings.append(f"Laminar flow detected in {len(laminar_pipes)} pipes (Re < 4000)")
    
    # Flow uniformity validation
    flow_uniformity = min(flows) / max(flows) if max(flows) > 0 else 0
    if flow_uniformity < 0.8:
        warnings.append(f"Low flow uniformity: {flow_uniformity:.2f} (minimum 0.8)")
    
    return {
        'compliant': len(violations) == 0,
        'violations': violations,
        'warnings': warnings,
        'turbulent_flow_percentage': (len(reynolds_numbers) - len(laminar_pipes)) / len(reynolds_numbers) * 100,
        'velocity_uniformity': min_velocity / max_velocity if max_velocity > 0 else 0
    }
```

---

## 📏 **Pipe Sizing Constraints**

### **Standard Diameter Constraints**
```yaml
# Available Standard Diameters (EN 13941)
standard_diameters_mm: [50, 80, 100, 125, 150, 200, 250, 300, 400]

# Pipe Type Classification
main_pipes:
  min_diameter_mm: 200
  max_diameter_mm: 400
  flow_threshold_kg_s: 2.0
  min_flow_kg_s: 1.5
  max_flow_kg_s: 10.0

distribution_pipes:
  min_diameter_mm: 100
  max_diameter_mm: 200
  flow_threshold_kg_s: 0.5
  min_flow_kg_s: 0.3
  max_flow_kg_s: 2.0

service_connections:
  min_diameter_mm: 50
  max_diameter_mm: 100
  flow_threshold_kg_s: 0.1
  min_flow_kg_s: 0.05
  max_flow_kg_s: 0.5
```

### **Diameter Selection Constraints**
```python
def validate_pipe_sizing_constraints(self, pipe_data: dict) -> dict:
    """Validate pipe sizing constraints."""
    
    violations = []
    warnings = []
    
    diameter_mm = pipe_data['diameter_mm']
    flow_rate_kg_s = pipe_data['flow_rate_kg_s']
    pipe_type = pipe_data['pipe_type']
    
    # Standard diameter validation
    if diameter_mm not in self.standard_diameters:
        violations.append(f"Non-standard diameter: {diameter_mm}mm (not in standard range)")
    
    # Pipe type classification validation
    if pipe_type == 'main':
        if diameter_mm < 200 or diameter_mm > 400:
            violations.append(f"Main pipe diameter out of range: {diameter_mm}mm (200-400mm)")
        if flow_rate_kg_s < 1.5 or flow_rate_kg_s > 10.0:
            warnings.append(f"Main pipe flow rate unusual: {flow_rate_kg_s:.2f} kg/s")
    
    elif pipe_type == 'distribution':
        if diameter_mm < 100 or diameter_mm > 200:
            violations.append(f"Distribution pipe diameter out of range: {diameter_mm}mm (100-200mm)")
        if flow_rate_kg_s < 0.3 or flow_rate_kg_s > 2.0:
            warnings.append(f"Distribution pipe flow rate unusual: {flow_rate_kg_s:.2f} kg/s")
    
    elif pipe_type == 'service':
        if diameter_mm < 50 or diameter_mm > 100:
            violations.append(f"Service connection diameter out of range: {diameter_mm}mm (50-100mm)")
        if flow_rate_kg_s < 0.05 or flow_rate_kg_s > 0.5:
            warnings.append(f"Service connection flow rate unusual: {flow_rate_kg_s:.2f} kg/s")
    
    # Diameter utilization validation
    required_diameter = self.calculate_required_diameter(flow_rate_kg_s)
    utilization = required_diameter / (diameter_mm / 1000)
    
    if utilization < 0.5:
        warnings.append(f"Underutilized pipe: {utilization:.2f} (diameter too large)")
    elif utilization > 0.95:
        warnings.append(f"Overutilized pipe: {utilization:.2f} (diameter too small)")
    
    return {
        'compliant': len(violations) == 0,
        'violations': violations,
        'warnings': warnings,
        'diameter_utilization': utilization,
        'sizing_efficiency': min(1.0, utilization / 0.8)  # Efficiency metric
    }
```

---

## 🏗️ **Geometric Constraints**

### **Network Geometry Constraints**
```yaml
# Building Connection Constraints
max_building_distance_m: 50           # Maximum distance building to street
min_building_distance_m: 1            # Minimum distance building to street
connectivity_fix_distance_m: 100      # Maximum distance for connectivity fixes

# Street Following Constraints
max_pipe_deviation_m: 5               # Maximum deviation from street centerline
min_street_width_m: 3                 # Minimum street width for pipe installation
max_pipe_length_m: 500                # Maximum single pipe segment length
min_pipe_length_m: 1                  # Minimum pipe segment length

# Network Topology Constraints
max_network_depth: 10                 # Maximum network depth (hops from plant)
min_branching_factor: 1.2             # Minimum branching factor
max_branching_factor: 5.0             # Maximum branching factor
```

### **Spatial Validation**
```python
def validate_geometric_constraints(self, network_data: dict) -> dict:
    """Validate geometric constraints for the network."""
    
    violations = []
    warnings = []
    
    # Building connection distance validation
    for connection in network_data['service_connections']:
        distance = connection['distance_to_street_m']
        if distance > 50:
            violations.append(f"Building too far from street: {distance:.1f}m (maximum 50m)")
        elif distance > 40:
            warnings.append(f"Building far from street: {distance:.1f}m")
    
    # Pipe length validation
    for pipe in network_data['pipes']:
        length = pipe['length_m']
        if length > 500:
            violations.append(f"Pipe segment too long: {length:.1f}m (maximum 500m)")
        elif length < 1:
            violations.append(f"Pipe segment too short: {length:.1f}m (minimum 1m)")
    
    # Network depth validation
    max_depth = self.calculate_network_depth(network_data)
    if max_depth > 10:
        violations.append(f"Network too deep: {max_depth} levels (maximum 10)")
    elif max_depth > 8:
        warnings.append(f"Deep network: {max_depth} levels")
    
    # Street deviation validation
    for pipe in network_data['pipes']:
        deviation = pipe['deviation_from_street_m']
        if deviation > 5:
            violations.append(f"Pipe deviates too much from street: {deviation:.1f}m (maximum 5m)")
    
    return {
        'compliant': len(violations) == 0,
        'violations': violations,
        'warnings': warnings,
        'network_depth': max_depth,
        'average_building_distance': np.mean([c['distance_to_street_m'] for c in network_data['service_connections']]),
        'geometric_efficiency': self.calculate_geometric_efficiency(network_data)
    }
```

---

## 💰 **Economic Constraints**

### **Cost Constraints**
```yaml
# Cost Limits
max_cost_per_building_eur: 2000       # Maximum cost per connected building
max_cost_per_kw_eur: 500              # Maximum cost per kW of heat demand
max_total_network_cost_eur: 100000    # Maximum total network cost

# Economic Efficiency Constraints
min_cost_efficiency_score: 0.7        # Minimum cost efficiency (0-1)
max_payback_period_years: 15          # Maximum payback period
min_internal_rate_return: 0.08        # Minimum internal rate of return (8%)
```

### **Economic Validation**
```python
def validate_economic_constraints(self, network_data: dict) -> dict:
    """Validate economic constraints for the network."""
    
    violations = []
    warnings = []
    
    total_cost = network_data['total_cost_eur']
    total_buildings = network_data['total_buildings']
    total_heat_demand_kw = network_data['total_heat_demand_kw']
    
    # Cost per building validation
    cost_per_building = total_cost / total_buildings
    if cost_per_building > 2000:
        violations.append(f"Cost per building too high: {cost_per_building:.0f} EUR (maximum 2000 EUR)")
    elif cost_per_building > 1500:
        warnings.append(f"High cost per building: {cost_per_building:.0f} EUR")
    
    # Cost per kW validation
    cost_per_kw = total_cost / total_heat_demand_kw
    if cost_per_kw > 500:
        violations.append(f"Cost per kW too high: {cost_per_kw:.0f} EUR/kW (maximum 500 EUR/kW)")
    elif cost_per_kw > 400:
        warnings.append(f"High cost per kW: {cost_per_kw:.0f} EUR/kW")
    
    # Total cost validation
    if total_cost > 100000:
        violations.append(f"Total cost exceeds limit: {total_cost:.0f} EUR (maximum 100000 EUR)")
    
    # Economic efficiency validation
    efficiency_score = self.calculate_cost_efficiency(network_data)
    if efficiency_score < 0.7:
        warnings.append(f"Low cost efficiency: {efficiency_score:.2f} (minimum 0.7)")
    
    return {
        'compliant': len(violations) == 0,
        'violations': violations,
        'warnings': warnings,
        'cost_per_building_eur': cost_per_building,
        'cost_per_kw_eur': cost_per_kw,
        'total_cost_eur': total_cost,
        'efficiency_score': efficiency_score,
        'economic_viability': efficiency_score >= 0.7
    }
```

---

## 🔍 **Standards Compliance Constraints**

### **EN 13941 District Heating Standards**
```yaml
# EN 13941 Requirements
velocity_limits:
  min_ms: 0.5
  max_ms: 3.0
  recommended_ms: [1.0, 2.5]

pressure_requirements:
  min_operating_pressure_bar: 2.0
  max_operating_pressure_bar: 8.0
  pressure_drop_limit_bar: 2.0

temperature_requirements:
  supply_temp_range_c: [65, 90]
  return_temp_range_c: [35, 45]
  min_temp_difference_c: 25

pipe_material_requirements:
  min_wall_thickness_mm: 3.0
  corrosion_protection: required
  insulation_required: true
```

### **DIN 1988 Water Supply Standards**
```yaml
# DIN 1988 Requirements
flow_requirements:
  min_reynolds_number: 4000
  max_reynolds_number: 100000
  flow_uniformity_min: 0.8

pressure_requirements:
  max_pressure_drop_pa_per_m: 50
  min_operating_pressure_bar: 2.0
  pressure_surge_limit_bar: 1.5

pipe_requirements:
  standard_diameters_mm: [50, 80, 100, 125, 150, 200, 250, 300, 400]
  min_pipe_length_m: 1.0
  max_pipe_length_m: 500
```

### **Comprehensive Standards Validation**
```python
def validate_standards_compliance(self, network_data: dict) -> dict:
    """Comprehensive validation against engineering standards."""
    
    violations = []
    warnings = []
    
    # EN 13941 compliance
    en13941_results = self.validate_en13941_compliance(network_data)
    violations.extend(en13941_results['violations'])
    warnings.extend(en13941_results['warnings'])
    
    # DIN 1988 compliance
    din1988_results = self.validate_din1988_compliance(network_data)
    violations.extend(din1988_results['violations'])
    warnings.extend(din1988_results['warnings'])
    
    # Calculate overall compliance score
    total_checks = len(self.get_all_standards_checks())
    failed_checks = len(violations)
    compliance_score = max(0, (total_checks - failed_checks) / total_checks * 100)
    
    # Generate recommendations
    recommendations = self.generate_improvement_recommendations(network_data)
    
    return {
        'overall_compliant': len(violations) == 0,
        'compliance_score': compliance_score,
        'en13941_compliant': en13941_results['compliant'],
        'din1988_compliant': din1988_results['compliant'],
        'violations': violations,
        'warnings': warnings,
        'violation_count': len(violations),
        'warning_count': len(warnings),
        'recommendations': recommendations,
        'standards_summary': {
            'en13941_status': 'compliant' if en13941_results['compliant'] else 'non_compliant',
            'din1988_status': 'compliant' if din1988_results['compliant'] else 'non_compliant',
            'overall_status': 'compliant' if len(violations) == 0 else 'non_compliant'
        }
    }
```

---

## ⚡ **Performance Constraints**

### **Simulation Performance Constraints**
```yaml
# Convergence Requirements
max_iterations: 20                    # Maximum pandapipes iterations
convergence_tolerance: 1e-6           # Convergence tolerance
max_simulation_time_s: 60             # Maximum simulation time

# Performance Requirements
min_convergence_rate: 0.95            # Minimum convergence rate
max_memory_usage_mb: 1024             # Maximum memory usage
max_calculation_time_s: 300           # Maximum calculation time
```

### **Performance Validation**
```python
def validate_performance_constraints(self, simulation_results: dict) -> dict:
    """Validate performance constraints for the simulation."""
    
    violations = []
    warnings = []
    
    # Convergence validation
    if not simulation_results['converged']:
        violations.append("Simulation failed to converge")
    elif simulation_results['iterations'] > 15:
        warnings.append(f"Slow convergence: {simulation_results['iterations']} iterations")
    
    # Performance validation
    runtime = simulation_results['runtime_s']
    if runtime > 60:
        violations.append(f"Simulation too slow: {runtime:.1f}s (maximum 60s)")
    elif runtime > 30:
        warnings.append(f"Slow simulation: {runtime:.1f}s")
    
    # Memory usage validation
    memory_usage = simulation_results.get('memory_usage_mb', 0)
    if memory_usage > 1024:
        violations.append(f"High memory usage: {memory_usage}MB (maximum 1024MB)")
    
    return {
        'compliant': len(violations) == 0,
        'violations': violations,
        'warnings': warnings,
        'performance_score': self.calculate_performance_score(simulation_results),
        'convergence_rate': 1.0 if simulation_results['converged'] else 0.0,
        'efficiency_rating': self.calculate_efficiency_rating(simulation_results)
    }
```

---

## 🎯 **Constraint Integration & Validation**

### **Master Constraint Validator**
```python
class CHAConstraintValidator:
    """Master validator for all CHA constraints."""
    
    def __init__(self, config: dict):
        self.config = config
        self.validators = {
            'thermal': ThermalConstraintValidator(config),
            'pressure': PressureConstraintValidator(config),
            'hydraulic': HydraulicConstraintValidator(config),
            'sizing': PipeSizingConstraintValidator(config),
            'geometric': GeometricConstraintValidator(config),
            'economic': EconomicConstraintValidator(config),
            'standards': StandardsConstraintValidator(config),
            'performance': PerformanceConstraintValidator(config)
        }
    
    def validate_all_constraints(self, network_data: dict) -> dict:
        """Validate all constraints for the network."""
        
        validation_results = {}
        all_violations = []
        all_warnings = []
        
        # Run all validators
        for validator_name, validator in self.validators.items():
            result = validator.validate(network_data)
            validation_results[validator_name] = result
            all_violations.extend(result.get('violations', []))
            all_warnings.extend(result.get('warnings', []))
        
        # Calculate overall compliance
        overall_compliant = len(all_violations) == 0
        
        # Generate summary
        summary = {
            'overall_compliant': overall_compliant,
            'total_violations': len(all_violations),
            'total_warnings': len(all_warnings),
            'compliance_score': self.calculate_overall_compliance_score(validation_results),
            'critical_issues': [v for v in all_violations if 'critical' in v.lower()],
            'recommendations': self.generate_overall_recommendations(validation_results)
        }
        
        return {
            'summary': summary,
            'detailed_results': validation_results,
            'all_violations': all_violations,
            'all_warnings': all_warnings
        }
```

This comprehensive constraints guide ensures that the Enhanced CHA system meets all engineering standards, performance requirements, and operational constraints for district heating network design and analysis.
