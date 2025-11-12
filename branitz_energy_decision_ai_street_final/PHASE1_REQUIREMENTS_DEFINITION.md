# 📋 Phase 1.2: Requirements Definition - Pipe Sizing Standards & Constraints

## 🎯 **Executive Summary**
This document defines the engineering standards, constraints, and requirements for implementing intelligent pipe sizing in the CHA system, based on European standards and best practices.

---

## 🏗️ **1.2.1 Pipe Sizing Standards Definition**

### **EN 13941: District Heating Pipes**

#### **Scope and Application**
- **Standard**: EN 13941 "District heating pipes - Preinsulated bonded pipe systems for directly buried hot water networks"
- **Application**: Preinsulated pipe systems for district heating networks
- **Temperature Range**: -50°C to +140°C
- **Pressure Range**: Up to 25 bar

#### **Key Requirements**
```yaml
EN_13941_Requirements:
  velocity_limits:
    maximum_velocity: 2.0  # m/s
    minimum_velocity: 0.1  # m/s (prevent sedimentation)
    recommended_velocity: 1.0-1.5  # m/s
  
  pressure_drop_limits:
    maximum_pressure_drop: 0.5  # bar/100m
    recommended_pressure_drop: 0.2-0.3  # bar/100m
  
  temperature_requirements:
    supply_temperature_range: [40, 90]  # °C
    return_temperature_range: [30, 60]  # °C
    temperature_difference_minimum: 20  # °C
  
  pressure_requirements:
    working_pressure_range: [2, 16]  # bar
    test_pressure_multiplier: 1.5  # x working pressure
  
  material_requirements:
    pipe_material: "steel"
    insulation_material: "polyurethane"
    outer_jacket: "HDPE"
    minimum_insulation_thickness: 30  # mm
```

#### **Design Criteria**
```python
# EN 13941 Design Criteria
EN_13941_CRITERIA = {
    'hydraulic_design': {
        'velocity_constraint': 'v ≤ 2.0 m/s',
        'pressure_drop_constraint': 'Δp ≤ 0.5 bar/100m',
        'flow_regime': 'turbulent',
        'reynolds_number_minimum': 4000
    },
    'thermal_design': {
        'heat_loss_maximum': '≤ 25 W/m·K',
        'temperature_drop_maximum': '≤ 5°C per km',
        'insulation_efficiency': '≥ 95%'
    },
    'mechanical_design': {
        'safety_factor': 2.0,
        'fatigue_consideration': True,
        'corrosion_protection': 'cathodic_protection'
    }
}
```

### **DIN 1988: Water Supply Systems**

#### **Scope and Application**
- **Standard**: DIN 1988 "Technical rules for drinking water installations"
- **Application**: Water supply systems and district heating
- **Temperature Range**: 5°C to 95°C
- **Pressure Range**: Up to 10 bar

#### **Key Requirements**
```yaml
DIN_1988_Requirements:
  velocity_limits:
    main_pipes: 2.0  # m/s
    distribution_pipes: 2.0  # m/s
    service_connections: 1.5  # m/s
    minimum_velocity: 0.1  # m/s
  
  pressure_drop_limits:
    main_pipes: 0.3  # bar/100m
    distribution_pipes: 0.4  # bar/100m
    service_connections: 0.5  # bar/100m
  
  pipe_sizing_method:
    method: "velocity_based"
    calculation_basis: "peak_demand"
    safety_factors:
      peak_factor: 1.2
      future_growth: 1.1
      safety_margin: 1.1
```

#### **Pipe Category Requirements**
```python
# DIN 1988 Pipe Category Requirements
DIN_1988_CATEGORIES = {
    'main_pipes': {
        'diameter_range': [0.200, 0.400],  # m
        'velocity_limit': 2.0,  # m/s
        'pressure_drop_limit': 0.3,  # bar/100m
        'typical_flow_range': [10, 100],  # kg/s
        'material': 'steel',
        'insulation': 'required'
    },
    'distribution_pipes': {
        'diameter_range': [0.080, 0.150],  # m
        'velocity_limit': 2.0,  # m/s
        'pressure_drop_limit': 0.4,  # bar/100m
        'typical_flow_range': [2, 20],  # kg/s
        'material': 'steel',
        'insulation': 'required'
    },
    'service_connections': {
        'diameter_range': [0.025, 0.050],  # m
        'velocity_limit': 1.5,  # m/s
        'pressure_drop_limit': 0.5,  # bar/100m
        'typical_flow_range': [0.1, 2],  # kg/s
        'material': 'steel_or_plastic',
        'insulation': 'required'
    }
}
```

---

## ⚙️ **1.2.2 Velocity Constraints Definition**

### **Velocity Limits by Pipe Category**

#### **Main Pipes (DN 200-400)**
```yaml
Main_Pipes_Velocity_Constraints:
  maximum_velocity: 2.0  # m/s (EN 13941 limit)
  minimum_velocity: 0.1  # m/s (prevent sedimentation)
  recommended_velocity: 1.0-1.5  # m/s
  design_velocity: 1.2  # m/s (optimal for most cases)
  
  rationale:
    - "High flow rates require larger diameters"
    - "Lower velocities reduce pressure drop"
    - "Economic optimization between pipe cost and pumping cost"
    - "Prevent erosion and noise"
```

#### **Distribution Pipes (DN 80-150)**
```yaml
Distribution_Pipes_Velocity_Constraints:
  maximum_velocity: 2.0  # m/s (EN 13941 limit)
  minimum_velocity: 0.1  # m/s (prevent sedimentation)
  recommended_velocity: 1.0-1.5  # m/s
  design_velocity: 1.2  # m/s (optimal for most cases)
  
  rationale:
    - "Medium flow rates with moderate pressure drop"
    - "Balance between pipe cost and hydraulic performance"
    - "Suitable for residential and commercial areas"
```

#### **Service Connections (DN 25-50)**
```yaml
Service_Connections_Velocity_Constraints:
  maximum_velocity: 1.5  # m/s (DIN 1988 limit)
  minimum_velocity: 0.1  # m/s (prevent sedimentation)
  recommended_velocity: 0.8-1.2  # m/s
  design_velocity: 1.0  # m/s (optimal for service connections)
  
  rationale:
    - "Lower flow rates allow higher velocities"
    - "Shorter lengths reduce pressure drop impact"
    - "Cost optimization for individual connections"
    - "Prevent water hammer in service lines"
```

### **Velocity Calculation Method**
```python
def calculate_velocity(mass_flow_kg_s: float, diameter_m: float) -> float:
    """
    Calculate flow velocity in pipe.
    
    Args:
        mass_flow_kg_s: Mass flow rate in kg/s
        diameter_m: Pipe inner diameter in meters
    
    Returns:
        velocity_ms: Flow velocity in m/s
    """
    import math
    
    # Water density at 70°C
    density_water_kg_m3 = 977.8
    
    # Calculate cross-sectional area
    area_m2 = math.pi * (diameter_m / 2) ** 2
    
    # Calculate volume flow rate
    volume_flow_m3_s = mass_flow_kg_s / density_water_kg_m3
    
    # Calculate velocity
    velocity_ms = volume_flow_m3_s / area_m2
    
    return velocity_ms
```

---

## 📊 **1.2.3 Pressure Drop Limits Definition**

### **Pressure Drop Limits by Pipe Category**

#### **Main Pipes (DN 200-400)**
```yaml
Main_Pipes_Pressure_Drop_Limits:
  maximum_pressure_drop: 0.3  # bar/100m
  recommended_pressure_drop: 0.2  # bar/100m
  design_pressure_drop: 0.25  # bar/100m
  
  rationale:
    - "Low pressure drop to minimize pumping costs"
    - "Large diameters reduce velocity and pressure drop"
    - "Critical for system efficiency"
    - "Allow for future expansion"
```

#### **Distribution Pipes (DN 80-150)**
```yaml
Distribution_Pipes_Pressure_Drop_Limits:
  maximum_pressure_drop: 0.4  # bar/100m
  recommended_pressure_drop: 0.3  # bar/100m
  design_pressure_drop: 0.35  # bar/100m
  
  rationale:
    - "Moderate pressure drop acceptable"
    - "Balance between pipe cost and hydraulic performance"
    - "Suitable for medium-distance distribution"
```

#### **Service Connections (DN 25-50)**
```yaml
Service_Connections_Pressure_Drop_Limits:
  maximum_pressure_drop: 0.5  # bar/100m
  recommended_pressure_drop: 0.4  # bar/100m
  design_pressure_drop: 0.45  # bar/100m
  
  rationale:
    - "Higher pressure drop acceptable for short connections"
    - "Cost optimization for individual buildings"
    - "Short lengths minimize total pressure drop"
```

### **Pressure Drop Calculation Method**
```python
def calculate_pressure_drop(mass_flow_kg_s: float, diameter_m: float, 
                          length_m: float, roughness_mm: float = 0.1) -> float:
    """
    Calculate pressure drop using Darcy-Weisbach equation.
    
    Args:
        mass_flow_kg_s: Mass flow rate in kg/s
        diameter_m: Pipe inner diameter in meters
        length_m: Pipe length in meters
        roughness_mm: Pipe roughness in mm
    
    Returns:
        pressure_drop_bar: Pressure drop in bar
    """
    import math
    
    # Water properties at 70°C
    density_water_kg_m3 = 977.8
    dynamic_viscosity_pa_s = 0.000404
    
    # Calculate velocity
    velocity_ms = calculate_velocity(mass_flow_kg_s, diameter_m)
    
    # Calculate Reynolds number
    reynolds = (density_water_kg_m3 * velocity_ms * diameter_m) / dynamic_viscosity_pa_s
    
    # Calculate friction factor (Colebrook-White equation)
    friction_factor = calculate_friction_factor(reynolds, roughness_mm, diameter_m)
    
    # Calculate pressure drop (Darcy-Weisbach)
    pressure_drop_pa = friction_factor * (length_m / diameter_m) * (density_water_kg_m3 * velocity_ms**2) / 2
    
    # Convert to bar
    pressure_drop_bar = pressure_drop_pa / 100000
    
    return pressure_drop_bar

def calculate_friction_factor(reynolds: float, roughness_mm: float, diameter_m: float) -> float:
    """Calculate friction factor using Colebrook-White equation."""
    import math
    
    # Relative roughness
    relative_roughness = (roughness_mm / 1000) / diameter_m
    
    # Colebrook-White equation (iterative solution)
    # Initial guess
    friction_factor = 0.01
    
    for _ in range(10):  # Iterative solution
        friction_factor_new = 1 / (2 * math.log10(relative_roughness/3.7 + 2.51/(reynolds * math.sqrt(friction_factor))))
        if abs(friction_factor_new - friction_factor) < 0.001:
            break
        friction_factor = friction_factor_new
    
    return friction_factor
```

---

## 📏 **1.2.4 Standard Pipe Diameters Specification**

### **Standard Pipe Diameters (50-400mm Range)**

#### **Complete Standard Diameter Series**
```python
# Standard pipe diameters in meters (DN series)
STANDARD_PIPE_DIAMETERS = {
    'DN_25': 0.025,   # 25mm - Service connections
    'DN_32': 0.032,   # 32mm - Service connections
    'DN_40': 0.040,   # 40mm - Service connections
    'DN_50': 0.050,   # 50mm - Service connections
    'DN_63': 0.063,   # 63mm - Small distribution
    'DN_80': 0.080,   # 80mm - Distribution pipes
    'DN_100': 0.100,  # 100mm - Distribution pipes
    'DN_125': 0.125,  # 125mm - Distribution pipes
    'DN_150': 0.150,  # 150mm - Distribution pipes
    'DN_200': 0.200,  # 200mm - Main pipes
    'DN_250': 0.250,  # 250mm - Main pipes
    'DN_300': 0.300,  # 300mm - Main pipes
    'DN_400': 0.400   # 400mm - Main pipes
}

# Diameter ranges by pipe category
PIPE_CATEGORY_DIAMETERS = {
    'service_connections': [0.025, 0.032, 0.040, 0.050],
    'distribution_pipes': [0.063, 0.080, 0.100, 0.125, 0.150],
    'main_pipes': [0.200, 0.250, 0.300, 0.400]
}
```

#### **Pipe Material Specifications**
```yaml
Pipe_Material_Specifications:
  steel_pipes:
    material_grade: "S235JR"
    wall_thickness_standard: "EN 10220"
    corrosion_protection: "cathodic_protection"
    insulation: "polyurethane_foam"
    outer_jacket: "HDPE"
    
  plastic_pipes:
    material: "PE-RT"
    pressure_rating: "PN16"
    temperature_rating: "95°C"
    insulation: "polyurethane_foam"
    outer_jacket: "HDPE"
    
  cost_factors:
    steel_vs_plastic: 1.2  # Steel is 20% more expensive
    insulation_cost_per_m: 15  # EUR/m
    installation_cost_per_m: 25  # EUR/m
```

#### **Diameter Selection Algorithm**
```python
def select_standard_diameter(required_diameter_m: float, 
                           pipe_category: str) -> float:
    """
    Select standard diameter closest to required diameter.
    
    Args:
        required_diameter_m: Calculated required diameter
        pipe_category: 'service_connections', 'distribution_pipes', 'main_pipes'
    
    Returns:
        standard_diameter_m: Selected standard diameter
    """
    available_diameters = PIPE_CATEGORY_DIAMETERS[pipe_category]
    
    # Find closest standard diameter
    closest_diameter = min(available_diameters, 
                          key=lambda x: abs(x - required_diameter_m))
    
    # Ensure minimum diameter for category
    min_diameter = min(available_diameters)
    if closest_diameter < min_diameter:
        closest_diameter = min_diameter
    
    return closest_diameter
```

---

## 🔄 **1.2.5 Data Flow Analysis**

### **Heat Demand → Mass Flow Rate Calculations**

#### **Conversion Formula**
```python
def heat_demand_to_mass_flow(heat_demand_kw: float, 
                           supply_temp_c: float, 
                           return_temp_c: float) -> float:
    """
    Convert heat demand to mass flow rate.
    
    Formula: Q = m * cp * ΔT
    Therefore: m = Q / (cp * ΔT)
    
    Args:
        heat_demand_kw: Heat demand in kW
        supply_temp_c: Supply temperature in °C
        return_temp_c: Return temperature in °C
    
    Returns:
        mass_flow_kg_s: Mass flow rate in kg/s
    """
    # Water specific heat capacity at 70°C
    cp_water_j_per_kgk = 4180
    
    # Temperature difference
    delta_t_k = supply_temp_c - return_temp_c
    
    # Mass flow rate calculation
    mass_flow_kg_s = (heat_demand_kw * 1000) / (cp_water_j_per_kgk * delta_t_k)
    
    return mass_flow_kg_s
```

#### **Flow Aggregation Through Network**
```python
def aggregate_network_flows(network_topology: dict, 
                          building_flows: dict) -> dict:
    """
    Aggregate flows through network hierarchy.
    
    Args:
        network_topology: Network structure with pipe connections
        building_flows: Heat demand per building
    
    Returns:
        pipe_flows: Mass flow rate per pipe segment
    """
    pipe_flows = {}
    
    # Start from service connections and work upstream
    for building_id, heat_demand_kw in building_flows.items():
        # Convert to mass flow
        mass_flow_kg_s = heat_demand_to_mass_flow(
            heat_demand_kw, 70, 40  # Supply 70°C, Return 40°C
        )
        
        # Trace flow path through network
        flow_path = trace_flow_path(building_id, network_topology)
        
        # Aggregate flows along path
        for pipe_id in flow_path:
            if pipe_id in pipe_flows:
                pipe_flows[pipe_id] += mass_flow_kg_s
            else:
                pipe_flows[pipe_id] = mass_flow_kg_s
    
    return pipe_flows
```

---

## 🎯 **1.2.6 Requirements Summary**

### **Engineering Standards Compliance**
```yaml
Standards_Compliance_Requirements:
  EN_13941:
    velocity_limit: 2.0  # m/s
    pressure_drop_limit: 0.5  # bar/100m
    temperature_range: [40, 90]  # °C
    pressure_range: [2, 16]  # bar
  
  DIN_1988:
    main_pipes_velocity: 2.0  # m/s
    distribution_velocity: 2.0  # m/s
    service_velocity: 1.5  # m/s
    main_pipes_pressure_drop: 0.3  # bar/100m
    distribution_pressure_drop: 0.4  # bar/100m
    service_pressure_drop: 0.5  # bar/100m
```

### **Pipe Sizing Constraints**
```yaml
Pipe_Sizing_Constraints:
  velocity_constraints:
    maximum: 2.0  # m/s
    minimum: 0.1  # m/s
    recommended: 1.0-1.5  # m/s
  
  pressure_drop_constraints:
    maximum: 0.5  # bar/100m
    recommended: 0.2-0.3  # bar/100m
  
  diameter_constraints:
    minimum: 0.025  # m (DN 25)
    maximum: 0.400  # m (DN 400)
    standard_series: [0.025, 0.032, 0.040, 0.050, 0.063, 0.080, 0.100, 0.125, 0.150, 0.200, 0.250, 0.300, 0.400]
```

### **Network Hierarchy Requirements**
```yaml
Network_Hierarchy_Requirements:
  main_pipes:
    diameter_range: [0.200, 0.400]  # m
    velocity_limit: 2.0  # m/s
    pressure_drop_limit: 0.3  # bar/100m
    typical_flow_range: [10, 100]  # kg/s
  
  distribution_pipes:
    diameter_range: [0.080, 0.150]  # m
    velocity_limit: 2.0  # m/s
    pressure_drop_limit: 0.4  # bar/100m
    typical_flow_range: [2, 20]  # kg/s
  
  service_connections:
    diameter_range: [0.025, 0.050]  # m
    velocity_limit: 1.5  # m/s
    pressure_drop_limit: 0.5  # bar/100m
    typical_flow_range: [0.1, 2]  # kg/s
```

---

## 📊 **Phase 1.2 Completion Status**

### **✅ Completed Tasks**
- [x] **1.2.1**: Define pipe sizing standards (EN 13941, DIN 1988)
- [x] **1.2.2**: Set velocity constraints (1-3 m/s)
- [x] **1.2.3**: Define pressure drop limits (max 50 Pa/m)
- [x] **1.2.4**: Specify standard pipe diameters (50-400mm range)
- [x] **1.2.5**: Map heat demand → mass flow rate calculations

### **📋 Key Requirements Defined**
1. **Standards Compliance**: EN 13941 and DIN 1988 requirements
2. **Velocity Constraints**: 2.0 m/s max for main/distribution, 1.5 m/s for service
3. **Pressure Drop Limits**: 0.3-0.5 bar/100m depending on pipe category
4. **Standard Diameters**: Complete DN series from 25mm to 400mm
5. **Flow Calculations**: Heat demand to mass flow rate conversion

### **🎯 Next Steps for Phase 1.3**
1. Trace building connections to pipe segments
2. Identify flow aggregation points in network
3. Complete data flow analysis

---

## 📝 **Conclusion**

**Phase 1.2** has successfully defined comprehensive requirements for intelligent pipe sizing, including:

✅ **Engineering Standards**: EN 13941 and DIN 1988 compliance requirements  
✅ **Velocity Constraints**: Category-specific velocity limits  
✅ **Pressure Drop Limits**: Graduated pressure drop constraints  
✅ **Standard Diameters**: Complete DN series specification  
✅ **Flow Calculations**: Heat demand to mass flow rate conversion  

These requirements provide the foundation for implementing intelligent pipe sizing in subsequent phases.

**Status**: ✅ **Phase 1.2 Complete** - Ready for Phase 1.3 Data Flow Analysis
