# ⚡ Decentralized Heating Agent (DHA) - Comprehensive Guide

## 🎯 **Overview**
The **Decentralized Heating Agent (DHA)** is a sophisticated system that analyzes the **electrical grid impact** of decentralized heating solutions (primarily heat pumps) by converting heat demand to electrical loads and evaluating grid constraints. It operates in parallel with the CHA (Centralized Heating Agent) as part of the fork-join architecture.

---

## 🏗️ **System Architecture**

### **Core Components**
```
DHA System
├── 📊 Input Data Processing
│   ├── LFA Heat Demand (8760h profiles)
│   ├── Feeder Topology (building-to-feeder mapping)
│   └── Weather Data (temperature-dependent COP)
├── 🔄 Heat-to-Electric Conversion
│   ├── COP Calculation (temperature-dependent)
│   ├── Heat Pump Efficiency Modeling
│   └── Electrical Load Generation
├── 🔌 Grid Impact Analysis
│   ├── Feeder Load Aggregation
│   ├── Utilization Analysis
│   └── Voltage Drop Calculation
├── ⚡ Power Flow Simulation (Optional)
│   ├── Pandapower Integration
│   ├── Load Flow Analysis
│   └── Voltage Constraint Validation
└── 📈 Output Generation
    ├── Feeder Load Profiles
    ├── Violation Analysis
    └── Grid Performance KPIs
```

### **Data Flow Architecture**
```
LFA Heat Demand → COP Calculation → Electrical Load → Feeder Aggregation → Grid Analysis → KPIs
     ↓              ↓                 ↓               ↓                ↓           ↓
8760h profiles  Temperature bins  P_el = Q_th/COP  Per-feeder sums  Utilization  Violations
```

---

## 🔧 **Configuration & Constraints**

### **Configuration File: `configs/dha.yml`**
```yaml
# COP bins by outdoor temperature (inclusive ranges)
cop_bins:
  - { t_min: -50, t_max: -10, cop: 2.0 }  # Very cold weather
  - { t_min: -10, t_max: 0,  cop: 2.5 }  # Cold weather
  - { t_min: 0,   t_max: 10, cop: 3.0 }  # Moderate weather
  - { t_min: 10,  t_max: 50, cop: 3.5 }  # Warm weather

# Fallback constant COP if no weather data
cop_default: 3.0

# Grid constraint thresholds
utilization_threshold: 0.8         # 80% feeder utilization limit
v_min_pu: 0.90                    # Minimum voltage (per unit)
v_max_pu: 1.10                    # Maximum voltage (per unit)

# Input data paths
lfa_glob: processed/lfa/*.json                    # LFA heat demand files
feeder_topology: data/processed/feeder_topology.parquet  # Building-feeder mapping
weather_parquet: data/processed/weather.parquet           # Optional weather data

# Output directories
out_dir: processed/dha
eval_dir: eval/dha

# Analysis settings
pandapower_enabled: true          # Enable Pandapower load flow analysis
top_n_hours: 10                   # Analyze top N peak hours
```

### **Key Constraints**

#### **1. Heat Pump Performance Constraints**
- **COP Range**: 2.0 - 3.5 (temperature-dependent)
- **Default COP**: 3.0 (when weather data unavailable)
- **Temperature Bins**: 4 ranges for COP calculation
- **Efficiency Limits**: Heat pump efficiency decreases with lower temperatures

#### **2. Electrical Grid Constraints**
- **Feeder Utilization**: Maximum 80% (configurable)
- **Voltage Limits**: 0.90 - 1.10 per unit (±10%)
- **Power Factor**: Assumed 0.98 (configurable)
- **Grid Capacity**: Based on feeder ratings

#### **3. Analysis Constraints**
- **Peak Hour Analysis**: Top N hours only (default: 10)
- **Building Coverage**: All buildings must be mapped to feeders
- **Data Completeness**: 8760-hour heat profiles required

---

## 🔥 **Heat Demand to Electrical Load Conversion**

### **COP (Coefficient of Performance) Calculation**
The DHA converts heat demand to electrical load using temperature-dependent COP values:

```python
def calculate_electrical_load(heat_demand_kw: float, outdoor_temp_c: float, cop_bins: list) -> float:
    """Calculate electrical load from heat demand using temperature-dependent COP."""
    
    # Find appropriate COP for temperature
    cop = cop_default  # Fallback
    for bin_info in cop_bins:
        if bin_info['t_min'] <= outdoor_temp_c <= bin_info['t_max']:
            cop = bin_info['cop']
            break
    
    # Convert heat to electrical power: P_el = Q_th / COP
    electrical_load_kw = heat_demand_kw / cop
    
    return electrical_load_kw
```

### **Temperature-Dependent COP Modeling**
```yaml
# COP Performance Curve
Temperature Range (°C) | COP Value | Efficiency
----------------------|-----------|------------
-50 to -10           | 2.0       | 200% (very cold)
-10 to 0             | 2.5       | 250% (cold)
0 to 10              | 3.0       | 300% (moderate)
10 to 50             | 3.5       | 350% (warm)
```

### **Electrical Load Profile Generation**
```python
def generate_electrical_profiles(heat_profiles: dict, weather_data: dict) -> dict:
    """Generate 8760-hour electrical load profiles."""
    
    electrical_profiles = {}
    
    for building_id, heat_profile in heat_profiles.items():
        electrical_profile = []
        
        for hour, heat_demand_kw in enumerate(heat_profile):
            outdoor_temp = weather_data.get(hour, {}).get('temperature_c', 5.0)
            cop = calculate_cop(outdoor_temp)
            electrical_load = heat_demand_kw / cop
            
            electrical_profile.append({
                'hour': hour,
                'heat_demand_kw': heat_demand_kw,
                'electrical_load_kw': electrical_load,
                'cop': cop,
                'temperature_c': outdoor_temp
            })
        
        electrical_profiles[building_id] = electrical_profile
    
    return electrical_profiles
```

---

## 🔌 **Feeder Load Aggregation & Analysis**

### **Building-to-Feeder Mapping**
```python
def aggregate_feeder_loads(electrical_profiles: dict, feeder_topology: dict) -> dict:
    """Aggregate electrical loads by feeder and hour."""
    
    feeder_loads = {}
    
    for building_id, profile in electrical_profiles.items():
        feeder_id = feeder_topology[building_id]['feeder_id']
        feeder_rating_kw = feeder_topology[building_id]['feeder_rating_kw']
        
        if feeder_id not in feeder_loads:
            feeder_loads[feeder_id] = {
                'rating_kw': feeder_rating_kw,
                'buildings': [],
                'hourly_loads': [0.0] * 8760
            }
        
        feeder_loads[feeder_id]['buildings'].append(building_id)
        
        # Aggregate hourly loads
        for hour_data in profile:
            hour = hour_data['hour']
            electrical_load = hour_data['electrical_load_kw']
            feeder_loads[feeder_id]['hourly_loads'][hour] += electrical_load
    
    return feeder_loads
```

### **Feeder Utilization Analysis**
```python
def analyze_feeder_utilization(feeder_loads: dict) -> dict:
    """Analyze feeder utilization and identify constraints."""
    
    utilization_analysis = {}
    
    for feeder_id, data in feeder_loads.items():
        rating_kw = data['rating_kw']
        hourly_loads = data['hourly_loads']
        
        # Calculate utilization percentages
        utilization_percentages = [(load / rating_kw) * 100 for load in hourly_loads]
        
        # Find peak utilization
        max_utilization = max(utilization_percentages)
        peak_hour = utilization_percentages.index(max_utilization)
        
        # Check for violations
        violations = [util > 80.0 for util in utilization_percentages]  # 80% threshold
        
        utilization_analysis[feeder_id] = {
            'rating_kw': rating_kw,
            'max_utilization_pct': max_utilization,
            'peak_hour': peak_hour,
            'violation_count': sum(violations),
            'violation_hours': [i for i, v in enumerate(violations) if v],
            'average_utilization_pct': sum(utilization_percentages) / len(utilization_percentages)
        }
    
    return utilization_analysis
```

---

## ⚡ **Power Flow Analysis**

### **Heuristic Voltage Calculation**
When Pandapower is not available, DHA uses heuristic voltage drop calculations:

```python
def calculate_heuristic_voltage_drops(utilization_pct: float) -> dict:
    """Calculate voltage drops using heuristic method."""
    
    # Voltage drop based on utilization (simplified model)
    # At 0% utilization: 0% voltage drop
    # At 100% utilization: 10% voltage drop
    # At 200% utilization: 15% voltage drop (capped)
    
    utilization_capped = min(utilization_pct, 200.0)
    voltage_drop_pu = (utilization_capped / 100) * 0.1
    
    # Additional penalty for overloading
    if utilization_pct > 100:
        overloading_penalty = ((utilization_pct - 100) / 100) * 0.05
        voltage_drop_pu += overloading_penalty
    
    # Cap total voltage drop at 20%
    voltage_drop_pu = min(voltage_drop_pu, 0.2)
    
    # Calculate voltage at feeder end
    voltage_end_pu = 1.0 - voltage_drop_pu
    
    return {
        'voltage_drop_pu': voltage_drop_pu,
        'voltage_end_pu': voltage_end_pu,
        'voltage_violation': voltage_end_pu < 0.90 or voltage_end_pu > 1.10
    }
```

### **Pandapower Integration**
For more accurate analysis, DHA can use Pandapower for detailed load flow calculations:

```python
def run_pandapower_analysis(feeder_loads: dict, voltage_limits: tuple) -> dict:
    """Run detailed load flow analysis using Pandapower."""
    
    try:
        import pandapower as pp
        
        results = {}
        v_min_pu, v_max_pu = voltage_limits
        
        for feeder_id, data in feeder_loads.items():
            # Create simple network model
            net = pp.create_empty_network()
            
            # Create buses (HV and LV)
            pp.create_bus(net, vn_kv=0.4, name=f"HV_{feeder_id}")
            pp.create_bus(net, vn_kv=0.4, name=f"LV_{feeder_id}")
            
            # Create external grid (infinite bus)
            pp.create_ext_grid(net, bus=0, vm_pu=1.0)
            
            # Create line (typical LV cable parameters)
            pp.create_line_from_parameters(
                net, from_bus=0, to_bus=1,
                length_km=0.1,  # 100m line
                r_ohm_per_km=0.1,  # Resistance
                x_ohm_per_km=0.08, # Reactance
                c_nf_per_km=250,   # Capacitance
                max_i_ka=0.5       # Current rating
            )
            
            # Analyze peak hour
            peak_hour = data['peak_hour']
            peak_load_kw = data['hourly_loads'][peak_hour]
            
            # Create load
            pp.create_load(net, bus=1, p_mw=peak_load_kw/1000, name=f"Load_{feeder_id}")
            
            # Run load flow
            pp.runpp(net, algorithm='nr', max_iteration=20)
            
            # Extract results
            voltage_pu = net.res_bus.vm_pu.iloc[1]  # LV bus voltage
            
            results[feeder_id] = {
                'voltage_pu': voltage_pu,
                'voltage_violation': voltage_pu < v_min_pu or voltage_pu > v_max_pu,
                'converged': net.converged,
                'load_mw': peak_load_kw / 1000
            }
        
        return results
        
    except ImportError:
        print("⚠️ Pandapower not available, using heuristic analysis")
        return run_heuristic_analysis(feeder_loads)
```

---

## 📊 **Key Performance Indicators (KPIs)**

### **Feeder Performance KPIs**
```python
def calculate_feeder_kpis(feeder_analysis: dict) -> dict:
    """Calculate comprehensive feeder performance KPIs."""
    
    kpis = {
        # Feeder Statistics
        'feeder_statistics': {
            'total_feeders': len(feeder_analysis),
            'overloaded_feeders': len([f for f in feeder_analysis.values() if f['max_utilization_pct'] > 80]),
            'avg_utilization_pct': np.mean([f['max_utilization_pct'] for f in feeder_analysis.values()]),
            'max_utilization_pct': max([f['max_utilization_pct'] for f in feeder_analysis.values()]),
            'total_capacity_kw': sum([f['rating_kw'] for f in feeder_analysis.values()])
        },
        
        # Grid Performance
        'grid_performance': {
            'total_violations': sum([f['violation_count'] for f in feeder_analysis.values()]),
            'violation_feeders': len([f for f in feeder_analysis.values() if f['violation_count'] > 0]),
            'avg_violation_hours': np.mean([f['violation_count'] for f in feeder_analysis.values()]),
            'peak_system_load_kw': sum([f['rating_kw'] * f['max_utilization_pct'] / 100 for f in feeder_analysis.values()])
        },
        
        # Heat Pump Performance
        'heat_pump_performance': {
            'avg_cop': calculate_average_cop(),
            'cop_range': [2.0, 3.5],
            'temperature_impact': calculate_temperature_impact(),
            'efficiency_rating': calculate_efficiency_rating()
        },
        
        # Economic Impact
        'economic_impact': {
            'total_electrical_demand_mwh': sum([f['rating_kw'] * f['avg_utilization_pct'] / 100 * 8760 / 1000 for f in feeder_analysis.values()]),
            'grid_upgrade_required': len([f for f in feeder_analysis.values() if f['max_utilization_pct'] > 100]),
            'estimated_upgrade_cost_eur': estimate_grid_upgrade_costs(feeder_analysis)
        }
    }
    
    return kpis
```

### **System-Level KPIs**
```python
def calculate_system_kpis(dha_results: dict) -> dict:
    """Calculate system-level performance KPIs."""
    
    return {
        # Overall System Performance
        'system_performance': {
            'total_buildings_analyzed': dha_results['buildings_analyzed'],
            'total_feeders': dha_results['feeders'],
            'system_utilization_max': dha_results['max_utilization'],
            'voltage_compliance': check_voltage_compliance(dha_results),
            'grid_stability_rating': calculate_grid_stability_rating(dha_results)
        },
        
        # Heat Pump Integration Success
        'heat_pump_integration': {
            'feasibility_score': calculate_feasibility_score(dha_results),
            'grid_impact_rating': calculate_grid_impact_rating(dha_results),
            'deployment_recommendation': generate_deployment_recommendation(dha_results),
            'constraint_summary': summarize_constraints(dha_results)
        },
        
        # Comparison with CHA
        'comparison_metrics': {
            'electrical_vs_thermal_efficiency': compare_efficiency_metrics(),
            'infrastructure_requirements': compare_infrastructure_requirements(),
            'deployment_complexity': compare_deployment_complexity(),
            'operational_flexibility': compare_operational_flexibility()
        }
    }
```

---

## 📁 **Output Files & Artifacts**

### **Primary Output Files**
1. **`processed/dha/feeder_loads.csv`**
   ```csv
   feeder_id,hour,p_kw,utilization_pct,feeder_rating_kw,v_end_pu,v_violation
   F1,1245,45.2,90.4,50.0,0.91,false
   F2,1245,38.7,77.4,50.0,0.94,false
   ```

2. **`eval/dha/violations.csv`**
   ```csv
   feeder_id,hour,p_kw,utilization_pct,feeder_rating_kw,v_end_pu,v_violation,violation_type
   F3,1245,52.1,104.2,50.0,0.89,true,utilization_and_voltage
   ```

3. **`processed/dha/dha_summary.json`**
   ```json
   {
     "analysis_summary": {
       "buildings_analyzed": 14,
       "feeders": 3,
       "peak_hours_analyzed": 10,
       "max_utilization_pct": 104.2,
       "total_violations": 2
     },
     "feeder_performance": {
       "F1": {"max_utilization_pct": 90.4, "violations": 0},
       "F2": {"max_utilization_pct": 77.4, "violations": 0},
       "F3": {"max_utilization_pct": 104.2, "violations": 2}
     },
     "heat_pump_analysis": {
       "avg_cop": 2.8,
       "temperature_impact": "moderate",
       "efficiency_rating": "good"
     }
   }
   ```

### **Analysis Reports**
4. **`eval/dha/grid_impact_report.html`** - Interactive grid impact visualization
5. **`eval/dha/feeder_analysis.html`** - Detailed feeder performance dashboard
6. **`processed/dha/electrical_profiles.parquet`** - 8760-hour electrical load profiles

---

## 🔍 **Technical Details**

### **Heat Pump Modeling**
- **COP Calculation**: Temperature-dependent efficiency curves
- **Load Conversion**: P_el = Q_th / COP
- **Auxiliary Loads**: Not explicitly modeled (can be added)
- **Diversity Factors**: Not applied (conservative analysis)

### **Electrical Grid Modeling**
- **Feeder Topology**: Simplified radial network model
- **Voltage Levels**: 0.4 kV (low voltage)
- **Cable Parameters**: Typical LV cable characteristics
- **Load Flow**: Newton-Raphson algorithm (Pandapower)

### **Analysis Methodology**
- **Peak Hour Focus**: Top N hours for detailed analysis
- **Violation Detection**: Utilization and voltage constraint checking
- **Scaling**: Analysis can be scaled to full 8760-hour simulation

---

## 🚀 **Execution Workflow**

### **Command Line Usage**
```bash
# Run complete DHA analysis
make dha

# Run with specific configuration
python src/dha.py --config configs/dha.yml

# Run with custom settings
python src/dha.py --config configs/dha.yml --top-n 20 --util-threshold 0.75
```

### **Programmatic Usage**
```python
from src.dha import run as run_dha

# Run DHA analysis
result = run_dha("configs/dha.yml")

# Access results
print(f"Buildings analyzed: {result['buildings_analyzed']}")
print(f"Max utilization: {result['max_utilization']}%")
print(f"Violations: {result['violations']}")
```

---

## ⚠️ **Limitations & Future Enhancements**

### **Current Limitations**
1. **Simplified Grid Model**: Basic radial network topology
2. **No Load Diversity**: Conservative peak load analysis
3. **Limited Heat Pump Types**: Single COP model
4. **No Demand Response**: Fixed load profiles
5. **Basic Economic Analysis**: Limited cost modeling

### **Future Enhancements**
1. **Advanced Grid Models**: Meshed network topology
2. **Load Diversity Factors**: Realistic load aggregation
3. **Multiple Heat Pump Types**: Various technologies and sizes
4. **Demand Response Integration**: Flexible load management
5. **Detailed Economic Analysis**: Comprehensive cost-benefit analysis
6. **Grid Upgrade Planning**: Infrastructure investment recommendations

---

## 📊 **Integration with System Architecture**

### **Fork-Join DAG Position**
```
LFA (Heat Demand) ──┬──→ CHA (District Heating)
                    │
                    └──→ DHA (Heat Pumps) ──→ EAA (Economics) ──→ TCA (Decision)
```

### **Data Exchange**
- **Input from LFA**: 8760-hour heat demand profiles
- **Output to EAA**: Electrical load profiles, grid constraints, upgrade costs
- **Parallel with CHA**: Both analyze different heating solutions

### **Decision Support**
DHA provides critical information for the TCA (Techno-Economic Analysis Agent):
- **Grid Feasibility**: Can the grid handle heat pump loads?
- **Upgrade Requirements**: What infrastructure investments are needed?
- **Performance Comparison**: How do heat pumps compare to district heating?
- **Deployment Strategy**: Which areas are suitable for heat pumps?

---

## 🎯 **Summary**

The DHA is a sophisticated system that:

✅ **Converts heat demand to electrical loads** using temperature-dependent COP modeling  
✅ **Analyzes electrical grid constraints** through feeder utilization and voltage analysis  
✅ **Provides detailed grid impact assessment** for heat pump deployment  
✅ **Generates comprehensive KPIs** for decision support  
✅ **Integrates with the overall system** for comparative analysis  
✅ **Supports both heuristic and detailed analysis** with Pandapower integration  

This makes DHA an essential component for evaluating decentralized heating solutions and their impact on the electrical grid infrastructure! ⚡
