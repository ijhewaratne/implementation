# Physics-Enhanced Multi-Agent System for District Heating Analysis

## 🎯 Overview

This enhanced multi-agent system integrates sophisticated physics models and pipe catalog extraction capabilities to provide advanced district heating network analysis and optimization. The agents utilize real-world physics calculations, actual pipe specifications, and comprehensive economic analysis to deliver accurate, actionable insights.

## 🏗️ Architecture

### Core Components

1. **Physics Models** (`optimize/physics_models.py`)
   - Fluid dynamics calculations (Reynolds number, friction factors)
   - Heat transfer analysis (pipe heat losses)
   - Hydraulic network analysis (pressure drops, head losses)

2. **Pipe Catalog Extraction** (`scripts/build_pipe_catalog.py`)
   - Excel file parsing with heuristic header detection
   - Keyword-based column mapping
   - EU/US number format normalization
   - Standardized data schema output

3. **Enhanced Tools** (`enhanced_tools_with_physics.py`)
   - Integration layer between agents and physics models
   - Specialized analysis functions
   - Economic comparison tools

4. **Specialized Agents** (`enhanced_agents_with_physics.py`)
   - Domain-specific agents for different analysis types
   - Orchestrated workflow management
   - Comprehensive system integration

## 🤖 Agent Specializations

### 1. PhysicsEnhancedEnergyPlannerAgent (Orchestrator)
**Role**: Master coordinator that delegates to specialist agents
**Capabilities**:
- Understands user requests and routes to appropriate specialists
- Manages complex multi-step analysis workflows
- Provides integrated recommendations

**Delegation Options**:
- `PCA` → Pipe catalog extraction and analysis
- `PMA` → Physics modeling and calculations
- `NOA` → Network optimization and design
- `TCA` → Technology comparison and economic analysis
- `CAA` → Comprehensive system analysis

### 2. PipeCatalogAgent (PCA)
**Role**: Excel data extraction and pipe specification analysis
**Tools**:
- `extract_pipe_catalog_from_excel()` - Extract pipe data from Excel files
- `analyze_pipe_catalog()` - Analyze extracted data and provide insights

**Use Cases**:
```python
# Extract pipe catalog from Excel
extract_pipe_catalog_from_excel(
    excel_file_path="Technikkatalog_Wärmeplanung_Version_1.1_August24_CC-BY.xlsx",
    output_path="data/catalogs/pipe_catalog.csv"
)

# Analyze available pipe specifications
analyze_pipe_catalog(catalog_path="data/catalogs/pipe_catalog.csv")
```

### 3. PhysicsModelingAgent (PMA)
**Role**: Advanced fluid dynamics and heat transfer calculations
**Tools**:
- `calculate_pipe_hydraulics()` - Hydraulic parameter calculations
- `calculate_pipe_heat_loss()` - Thermal loss analysis

**Physics Models Used**:
- **Reynolds Number**: `Re = ρ * v * d / μ`
- **Swamee-Jain Friction Factor**: For turbulent flow analysis
- **Darcy-Weisbach Equation**: Pressure drop calculations
- **Heat Transfer Equations**: Thermal loss analysis

**Use Cases**:
```python
# Hydraulic analysis
calculate_pipe_hydraulics(
    flow_rate_m3s=0.01,
    pipe_diameter_mm=100,
    pipe_length_m=200,
    fluid_density_kgm3=1000,
    fluid_viscosity_Pas=0.001
)

# Heat loss analysis
calculate_pipe_heat_loss(
    pipe_diameter_mm=150,
    pipe_length_m=300,
    fluid_temperature_c=80,
    soil_temperature_c=10,
    u_value_Wm2K=0.4
)
```

### 4. NetworkOptimizationAgent (NOA)
**Role**: District heating network design and optimization
**Tools**:
- `optimize_district_heating_network()` - Comprehensive network optimization

**Analysis Includes**:
- Heat demand calculations and flow rate determination
- Pipe diameter optimization based on hydraulic constraints
- Cost-performance analysis using real pipe catalog data
- Heat loss calculations and energy efficiency assessment
- Pressure drop analysis and pump requirements

**Use Cases**:
```python
# Optimize network design
optimize_district_heating_network(
    street_name="Branitzer Straße",
    total_heat_demand_kW=500,
    supply_temperature_c=80,
    return_temperature_c=60,
    max_pressure_drop_kPa=50
)
```

### 5. TechnologyComparisonAgent (TCA)
**Role**: Economic analysis and technology comparison
**Tools**:
- `compare_heating_technologies()` - Comprehensive technology comparison

**Analysis Includes**:
- Life-cycle cost analysis (20-year period)
- Operating cost calculations with real energy prices
- Installation cost estimates
- Technology-specific efficiency considerations
- Environmental impact assessment

**Use Cases**:
```python
# Compare heating technologies
compare_heating_technologies(
    street_name="Branitzer Straße",
    heat_demand_kW=500,
    electricity_price_eur_kwh=0.30,
    gas_price_eur_kwh=0.08,
    heat_pump_cop=3.5
)
```

### 6. ComprehensiveAnalysisAgent (CAA)
**Role**: End-to-end energy system analysis
**Tools**: All available tools combined
**Capabilities**:
- Data extraction and validation
- Physics-based modeling and calculations
- Network optimization and design recommendations
- Economic analysis and technology comparison
- Integrated insights and actionable recommendations

## 🔧 How Agents Utilize the New Files

### 1. Pipe Catalog Integration

**Extraction Process**:
1. **Excel Scanning**: Agents use `PipeCatalogBuilder` to scan Excel files
2. **Header Detection**: Heuristic algorithms identify data headers
3. **Column Mapping**: Keyword-based mapping finds relevant columns
4. **Data Normalization**: EU/US number formats are standardized
5. **Schema Output**: Data is converted to standardized CSV format

**Analysis Process**:
1. **Data Loading**: Agents load extracted pipe specifications
2. **Statistical Analysis**: Diameter ranges, cost analysis, technical specifications
3. **Recommendations**: Design guidance based on available options
4. **Integration**: Results feed into network optimization

### 2. Physics Models Integration

**Hydraulic Calculations**:
1. **Input Validation**: Agents validate all input parameters
2. **Flow Regime Determination**: Reynolds number calculations
3. **Friction Analysis**: Swamee-Jain or laminar friction factors
4. **Pressure Drop**: Darcy-Weisbach equation application
5. **Head Loss**: Conversion to hydraulic head

**Heat Transfer Analysis**:
1. **Mode Selection**: U-value or direct W/m mode
2. **Surface Area**: Pipe surface area calculations
3. **Temperature Difference**: Thermal driving force
4. **Heat Loss**: Thermal transfer calculations
5. **Energy Impact**: Annual energy loss assessment

### 3. Network Optimization Workflow

**Step-by-Step Process**:
1. **Demand Analysis**: Heat demand → flow rate calculations
2. **Pipe Selection**: Catalog-based diameter optimization
3. **Hydraulic Analysis**: Physics-based pressure drop calculations
4. **Thermal Analysis**: Heat loss assessment
5. **Cost Analysis**: Economic optimization
6. **Recommendations**: Integrated design guidance

## 📊 Example Workflows

### Workflow 1: New District Heating Network Design

```python
# 1. Extract pipe catalog data
extract_pipe_catalog_from_excel()

# 2. Analyze available pipe specifications
analyze_pipe_catalog()

# 3. Optimize network design
optimize_district_heating_network(
    street_name="Branitzer Straße",
    total_heat_demand_kW=500
)

# 4. Compare with alternative technologies
compare_heating_technologies(
    street_name="Branitzer Straße",
    heat_demand_kW=500
)
```

### Workflow 2: Existing Network Analysis

```python
# 1. Calculate hydraulic parameters for existing pipes
calculate_pipe_hydraulics(
    flow_rate_m3s=0.015,
    pipe_diameter_mm=150,
    pipe_length_m=500
)

# 2. Assess heat losses
calculate_pipe_heat_loss(
    pipe_diameter_mm=150,
    pipe_length_m=500,
    fluid_temperature_c=85,
    soil_temperature_c=12
)

# 3. Optimize for efficiency improvements
optimize_district_heating_network(
    street_name="Existing Network",
    total_heat_demand_kW=750,
    max_pressure_drop_kPa=30
)
```

### Workflow 3: Technology Decision Support

```python
# 1. Comprehensive technology comparison
compare_heating_technologies(
    street_name="Decision Analysis",
    heat_demand_kW=300,
    electricity_price_eur_kwh=0.35,
    gas_price_eur_kwh=0.10
)

# 2. Network optimization for district heating option
optimize_district_heating_network(
    street_name="Decision Analysis",
    total_heat_demand_kW=300
)

# 3. Detailed physics analysis
calculate_pipe_hydraulics(
    flow_rate_m3s=0.008,
    pipe_diameter_mm=100,
    pipe_length_m=300
)
```

## 🎯 Key Benefits

### 1. **Real-World Accuracy**
- Physics-based calculations using validated models
- Real pipe specifications from actual catalogs
- Industry-standard equations and methodologies

### 2. **Comprehensive Analysis**
- Multi-disciplinary approach (technical + economic)
- Life-cycle cost analysis
- Environmental impact assessment

### 3. **Specialized Expertise**
- Domain-specific agents for different analysis types
- Orchestrated workflow for complex projects
- Integrated recommendations

### 4. **Scalability**
- Modular design allows easy extension
- Reusable physics models
- Standardized data formats

### 5. **User-Friendly Interface**
- Natural language interaction
- Automated delegation to specialists
- Clear, actionable recommendations

## 🚀 Getting Started

### 1. Setup Requirements
```bash
# Install required packages
pip install pandas numpy scipy matplotlib geopandas folium

# Ensure physics models and pipe catalog modules are available
python -c "from optimize.physics_models import *; print('Physics models loaded')"
python -c "from scripts.build_pipe_catalog import PipeCatalogBuilder; print('Pipe catalog builder loaded')"
```

### 2. Run Demonstrations
```bash
# Run the comprehensive demonstration
python demo_physics_enhanced_agents.py
```

### 3. Use Individual Agents
```python
from enhanced_agents_with_physics import PipeCatalogAgent, PhysicsModelingAgent

# Create agents
pca = PipeCatalogAgent()
pma = PhysicsModelingAgent()

# Use agents for analysis
await pca.run("Extract pipe catalog data from Excel")
await pma.run("Calculate hydraulic parameters for DN100 pipe")
```

## 📈 Future Enhancements

### Planned Features
1. **Advanced Network Simulation**: Integration with pandapipes for complex networks
2. **Machine Learning Optimization**: AI-driven pipe selection and routing
3. **Real-Time Data Integration**: Live sensor data for operational analysis
4. **3D Visualization**: Interactive 3D network visualization
5. **Scenario Planning**: Multiple scenario comparison and optimization

### Extension Points
1. **Additional Physics Models**: More sophisticated thermal and hydraulic models
2. **Economic Models**: Advanced cost modeling and financial analysis
3. **Environmental Models**: Carbon footprint and sustainability analysis
4. **Regulatory Compliance**: Building codes and standards integration

## 🤝 Contributing

The physics-enhanced agent system is designed for extensibility. Key areas for contribution:

1. **Physics Models**: Additional fluid dynamics and heat transfer models
2. **Economic Analysis**: Enhanced cost modeling and financial tools
3. **Data Integration**: New data sources and formats
4. **Agent Specializations**: New domain-specific agents
5. **Visualization**: Enhanced reporting and visualization tools

## 📚 References

- **Fluid Dynamics**: Swamee-Jain friction factor approximation
- **Heat Transfer**: Standard thermal conductivity and heat loss equations
- **District Heating**: EN standards for district heating networks
- **Economic Analysis**: Life-cycle cost analysis methodologies

---

This physics-enhanced multi-agent system represents a significant advancement in district heating analysis, combining real-world physics with practical engineering applications to deliver accurate, actionable insights for energy infrastructure planning and optimization. 