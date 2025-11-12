# Agent-Based Energy System - Architecture Design
## Phase 1: Real Simulation Integration

**Version:** 1.0  
**Date:** November 2025  
**Status:** Design Phase  

---

## 1. Executive Summary

This document outlines the architecture for integrating **real pandapipes (DH) and pandapower (HP) simulations** into the existing Agent-Based Energy System, replacing placeholder implementations with physics-based calculations.

### Key Objectives
1. ✅ Maintain natural language AI interface
2. ✅ Add real physics simulations (pandapipes/pandapower)
3. ✅ Keep backward compatibility with placeholders
4. ✅ Enable modular, testable architecture
5. ✅ Support performance optimization (caching, async)

---

## 2. Current Architecture (Problematic)

```
┌─────────────┐
│  User Query │
│ "analyze DH │
│  for Park-  │
│   straße"   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│     EnergyPlannerAgent              │
│  (Gemini-1.5-flash)                 │
│  → Analyzes intent                  │
│  → Delegates to specialist          │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  CentralHeatingAgent (CHA)          │
│  → Calls energy_tools               │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  energy_tools.py                    │
│  run_simulation_pipeline()          │
│  → get_building_ids_for_street()    │
│  → run_simulation_pipeline()        │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  main.py (10-step pipeline)         │
│  Step 8: simulation_runner          │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  simulation_runner.py               │
│  ❌ PLACEHOLDER SIMULATIONS         │
│  → run_pandapipes_simulation()      │
│     Returns hardcoded: 1234 MWh     │
│  → run_pandapower_simulation()      │
│     Returns hardcoded: 82% load     │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Dummy KPIs (unrealistic)           │
│  → LLM generates report from fake   │
│     data                            │
└─────────────────────────────────────┘
```

### Problems
1. ❌ **No real physics** - results are meaningless
2. ❌ **Can't validate designs** - no constraint checking
3. ❌ **Can't compare scenarios** - fake data doesn't reflect reality
4. ❌ **Wasted AI capabilities** - LLM analyzes dummy data

---

## 3. Proposed Architecture (Solution)

```
┌─────────────┐
│  User Query │
│ "analyze DH │
│  for Park-  │
│   straße"   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│     EnergyPlannerAgent              │
│  (Gemini-1.5-flash)                 │
│  → Analyzes intent                  │
│  → Delegates to specialist          │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  CentralHeatingAgent (CHA)          │
│  → Calls energy_tools               │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  energy_tools.py (ENHANCED)         │
│  run_simulation_pipeline()          │
│  → get_building_ids_for_street()    │
│  → run_simulation_pipeline()        │
│  → NEW: pass simulation_config      │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  main.py (10-step pipeline)         │
│  Step 8: NEW real_simulation_runner│
└──────┬──────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  NEW: real_simulation_runner.py (Smart Router)       │
│  ┌────────────────────────────────────────────────┐  │
│  │  SimulationOrchestrator                        │  │
│  │  → Checks config: use_real_simulations         │  │
│  │  → Routes to real or placeholder               │  │
│  │  → Handles caching, progress tracking          │  │
│  └────────────┬───────────────────────────────────┘  │
└───────────────┼──────────────────────────────────────┘
                │
      ┌─────────┴─────────┐
      │                   │
      ▼                   ▼
┌─────────────────┐  ┌─────────────────┐
│  DH Simulator   │  │  HP Simulator   │
│  (Real/Stub)    │  │  (Real/Stub)    │
└─────────────────┘  └─────────────────┘
      │                   │
      ▼                   ▼
┌─────────────────┐  ┌─────────────────┐
│ pandapipes_dh_  │  │ pandapower_hp_  │
│ simulator.py    │  │ simulator.py    │
│                 │  │                 │
│ ✅ Real Physics │  │ ✅ Real Physics │
│ ✅ Network      │  │ ✅ 3-phase      │
│    Creation     │  │    Power Flow   │
│ ✅ Hydraulic +  │  │ ✅ Voltage      │
│    Thermal      │  │    Analysis     │
│    Simulation   │  │ ✅ Constraint   │
│ ✅ KPI Extract  │  │    Checking     │
└─────────────────┘  └─────────────────┘
      │                   │
      └─────────┬─────────┘
                ▼
┌─────────────────────────────────────┐
│  Real Physics-Based KPIs            │
│  → Pressure drops (bar)             │
│  → Temperatures (°C)                │
│  → Voltages (pu)                    │
│  → Line loadings (%)                │
│  → Constraint violations            │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  LLM Report Generation              │
│  → Analyzes REAL data               │
│  → Provides accurate insights       │
│  → Realistic recommendations        │
└─────────────────────────────────────┘
```

---

## 4. Directory Structure

```
branitz_energy_decision_ai_street_agents/
│
├── agents.py                          # Agent definitions (unchanged)
├── energy_tools.py                    # Agent tools (minor updates)
├── main.py                            # Pipeline orchestrator (unchanged)
├── run_agent_system.py                # Entry point (unchanged)
│
├── config/                            # ← NEW: Configuration directory
│   ├── __init__.py
│   ├── simulation_config.yaml         # Simulation parameters
│   └── feature_flags.yaml             # Feature toggles
│
├── src/
│   ├── __init__.py
│   │
│   ├── simulators/                    # ← NEW: Simulation modules
│   │   ├── __init__.py
│   │   ├── base.py                    # Abstract base classes
│   │   ├── pandapipes_dh_simulator.py # Real DH simulation
│   │   ├── pandapower_hp_simulator.py # Real HP simulation
│   │   ├── placeholder_dh.py          # Fallback DH
│   │   └── placeholder_hp.py          # Fallback HP
│   │
│   ├── orchestration/                 # ← NEW: Routing & coordination
│   │   ├── __init__.py
│   │   ├── simulation_orchestrator.py # Smart router
│   │   ├── cache_manager.py           # Result caching
│   │   └── progress_tracker.py        # Progress monitoring
│   │
│   ├── real_simulation_runner.py      # ← NEW: Main simulation router
│   ├── simulation_runner.py           # ← OLD: Keep for backward compat
│   │
│   ├── data_preparation.py            # Existing modules (unchanged)
│   ├── building_attributes.py
│   ├── envelope_and_uvalue.py
│   ├── demand_calculation.py
│   ├── profile_generation.py
│   ├── network_construction.py
│   ├── scenario_manager.py
│   ├── kpi_calculator.py              # Update to handle new KPIs
│   └── llm_reporter.py
│
├── tests/                             # ← NEW: Test suite
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_dh_simulator.py
│   │   ├── test_hp_simulator.py
│   │   └── test_orchestrator.py
│   ├── integration/
│   │   ├── test_agent_dh_flow.py
│   │   └── test_agent_hp_flow.py
│   └── fixtures/
│       ├── sample_buildings.geojson
│       └── sample_streets.geojson
│
├── simulation_cache/                  # ← NEW: Cached results
│   └── .gitkeep
│
├── docs/                              # ← NEW: Documentation
│   ├── ARCHITECTURE_DESIGN.md         # This file
│   ├── INTERFACE_SPEC.md              # Interface contracts
│   ├── DATA_FLOW.md                   # Data flow diagrams
│   └── MIGRATION_GUIDE.md             # Migration instructions
│
└── requirements.txt                   # Updated dependencies
```

---

## 5. Module Responsibilities

### 5.1 Core Simulation Modules

#### **`src/simulators/base.py`**
**Purpose:** Define abstract interfaces for all simulators  
**Responsibilities:**
- Define `BaseSimulator` abstract class
- Specify required methods: `create_network()`, `run_simulation()`, `extract_kpis()`
- Define standard data structures for inputs/outputs
- Type hints for all interfaces

#### **`src/simulators/pandapipes_dh_simulator.py`**
**Purpose:** Real district heating simulation  
**Responsibilities:**
- Create pandapipes network from building data
- Configure supply/return circuits
- Add heat exchangers for consumers
- Run hydraulic + thermal simulation
- Extract pressure, temperature, flow results
- Calculate pump energy, heat losses
- Export results to GeoJSON

#### **`src/simulators/pandapower_hp_simulator.py`**
**Purpose:** Real electrical grid simulation for heat pumps  
**Responsibilities:**
- Create pandapower LV network
- Add MV/LV transformer
- Model 3-phase or single-phase loads
- Run power flow calculation
- Extract voltage profiles, line loadings
- Detect constraint violations
- Calculate grid losses

#### **`src/simulators/placeholder_dh.py`** & **`placeholder_hp.py`**
**Purpose:** Fallback when real libraries unavailable  
**Responsibilities:**
- Implement same interface as real simulators
- Return reasonable dummy data
- Log warnings about placeholder usage
- Enable testing without full dependencies

### 5.2 Orchestration Modules

#### **`src/orchestration/simulation_orchestrator.py`**
**Purpose:** Intelligent routing and coordination  
**Responsibilities:**
- Read configuration (real vs placeholder)
- Select appropriate simulator
- Handle caching (check cache before simulation)
- Coordinate parallel simulations (multiple streets)
- Aggregate results
- Error handling and retry logic

#### **`src/orchestration/cache_manager.py`**
**Purpose:** Result caching for performance  
**Responsibilities:**
- Generate cache keys from inputs
- Check cache validity
- Store/retrieve simulation results
- Implement cache eviction policies
- Provide cache statistics

#### **`src/orchestration/progress_tracker.py`**
**Purpose:** User feedback during long simulations  
**Responsibilities:**
- Track simulation stages
- Provide progress updates to agents
- Estimate remaining time
- Log detailed progress for debugging

### 5.3 Updated Existing Modules

#### **`src/real_simulation_runner.py`** (NEW)
**Purpose:** Replace `simulation_runner.py` with real simulations  
**Responsibilities:**
- Entry point for all simulations
- Delegate to `SimulationOrchestrator`
- Maintain backward-compatible API
- Handle scenario files

#### **`src/kpi_calculator.py`** (UPDATED)
**Purpose:** Calculate KPIs from simulation results  
**Responsibilities:**
- Handle both placeholder and real simulation outputs
- Calculate economic metrics (LCoH, NPV)
- Calculate environmental metrics (CO2)
- Support new detailed KPIs (voltages, pressures)

---

## 6. Interface Contracts

### 6.1 Base Simulator Interface

```python
# src/simulators/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import geopandas as gpd
from pathlib import Path

class SimulationResult:
    """Standard result container for all simulations."""
    
    def __init__(self,
                 success: bool,
                 scenario_name: str,
                 simulation_type: str,  # "DH" or "HP"
                 simulation_mode: str,  # "real" or "placeholder"
                 kpi: Dict[str, float],
                 metadata: Optional[Dict[str, Any]] = None,
                 error: Optional[str] = None):
        self.success = success
        self.scenario_name = scenario_name
        self.simulation_type = simulation_type
        self.simulation_mode = simulation_mode
        self.kpi = kpi
        self.metadata = metadata or {}
        self.error = error
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "scenario": self.scenario_name,
            "type": self.simulation_type,
            "mode": self.simulation_mode,
            "kpi": self.kpi,
            "metadata": self.metadata,
            "error": self.error
        }


class BaseSimulator(ABC):
    """Abstract base class for all energy system simulators."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize simulator with configuration.
        
        Args:
            config: Dictionary containing simulation parameters
        """
        self.config = config
        self.network = None  # Will hold network object (pandapipes/pandapower)
    
    @abstractmethod
    def validate_inputs(self, buildings_gdf: gpd.GeoDataFrame, **kwargs) -> bool:
        """
        Validate input data before simulation.
        
        Args:
            buildings_gdf: GeoDataFrame with building data
            **kwargs: Additional inputs (e.g., street_network)
            
        Returns:
            True if inputs are valid
            
        Raises:
            ValueError: If inputs are invalid with detailed message
        """
        pass
    
    @abstractmethod
    def create_network(self, buildings_gdf: gpd.GeoDataFrame, **kwargs) -> Any:
        """
        Create network model from building data.
        
        Args:
            buildings_gdf: GeoDataFrame with building geometries and demands
            **kwargs: Additional data (topology, existing network, etc.)
            
        Returns:
            Network object (pandapipes.Net or pandapower.Net)
        """
        pass
    
    @abstractmethod
    def run_simulation(self) -> SimulationResult:
        """
        Execute physics-based simulation.
        
        Returns:
            SimulationResult with success status, KPIs, and metadata
            
        Raises:
            SimulationError: If simulation fails to converge
        """
        pass
    
    @abstractmethod
    def extract_kpis(self) -> Dict[str, float]:
        """
        Extract key performance indicators from simulation results.
        
        Returns:
            Dictionary of KPI name -> value
        """
        pass
    
    def export_results(self, output_dir: Path, format: str = "geojson") -> Dict[str, Path]:
        """
        Export simulation results to files.
        
        Args:
            output_dir: Directory to save results
            format: Output format ("geojson", "json", "csv")
            
        Returns:
            Dictionary mapping result type -> file path
        """
        # Default implementation - can be overridden
        return {}
    
    def get_network_summary(self) -> Dict[str, int]:
        """
        Get summary statistics of the network.
        
        Returns:
            Dictionary with counts of network elements
        """
        # Default implementation - can be overridden
        return {}
```

### 6.2 DH Simulator Specific Interface

```python
# src/simulators/base.py (continued)

class DHSimulatorInterface(BaseSimulator):
    """Extended interface specific to district heating simulators."""
    
    @abstractmethod
    def set_supply_temperature(self, temp_c: float) -> None:
        """Set supply temperature in Celsius."""
        pass
    
    @abstractmethod
    def set_return_temperature(self, temp_c: float) -> None:
        """Set return temperature in Celsius."""
        pass
    
    @abstractmethod
    def get_pressure_profile(self) -> gpd.GeoDataFrame:
        """
        Get pressure distribution along network.
        
        Returns:
            GeoDataFrame with junction pressures
        """
        pass
    
    @abstractmethod
    def get_temperature_profile(self) -> gpd.GeoDataFrame:
        """
        Get temperature distribution along network.
        
        Returns:
            GeoDataFrame with junction temperatures
        """
        pass


class HPSimulatorInterface(BaseSimulator):
    """Extended interface specific to heat pump electrical simulators."""
    
    @abstractmethod
    def set_hp_parameters(self, thermal_kw: float, cop: float, three_phase: bool) -> None:
        """Set heat pump electrical parameters."""
        pass
    
    @abstractmethod
    def get_voltage_violations(self, min_pu: float = 0.9, max_pu: float = 1.1) -> gpd.GeoDataFrame:
        """
        Get buses with voltage violations.
        
        Returns:
            GeoDataFrame with violated buses and voltage values
        """
        pass
    
    @abstractmethod
    def get_line_overloads(self, threshold_pct: float = 100.0) -> gpd.GeoDataFrame:
        """
        Get lines exceeding loading threshold.
        
        Returns:
            GeoDataFrame with overloaded lines
        """
        pass
```

---

## 7. Data Flow Specification

### 7.1 Input Data Structure

```python
class SimulationInput:
    """Standardized input for all simulations."""
    
    scenario_name: str                    # e.g., "Parkstraße_DH_85C"
    scenario_type: str                    # "DH" or "HP"
    buildings_gdf: gpd.GeoDataFrame       # Building geometries + demands
    street_network: gpd.GeoDataFrame      # Optional street geometry
    parameters: Dict[str, Any]            # Scenario-specific params
    
    # buildings_gdf required columns:
    #   - GebaeudeID: str (building identifier)
    #   - geometry: Polygon or Point
    #   - heating_load_kw: float
    #   - base_electric_load_kw: float (for HP)
    
    # parameters examples:
    # DH: {"supply_temp": 85, "return_temp": 55, "pipe_diameter_m": 0.065}
    # HP: {"hp_thermal_kw": 6.0, "hp_cop": 2.8, "hp_three_phase": True}
```

### 7.2 Output Data Structure

```python
class SimulationOutput:
    """Standardized output from all simulations."""
    
    result: SimulationResult              # Main result container
    geojson_files: Dict[str, Path]        # Exported visualization files
    network_summary: Dict[str, int]       # Network element counts
    execution_time: float                 # Simulation time (seconds)
    
    # result.kpi structure for DH:
    # {
    #     "total_heat_supplied_mwh": float,
    #     "pump_energy_kwh": float,
    #     "max_pressure_drop_bar": float,
    #     "avg_pressure_drop_bar": float,
    #     "min_supply_temp_c": float,
    #     "network_heat_loss_kwh": float,
    #     "num_junctions": int,
    #     "num_pipes": int
    # }
    
    # result.kpi structure for HP:
    # {
    #     "min_voltage_pu": float,
    #     "max_voltage_pu": float,
    #     "voltage_violations": int,
    #     "max_line_loading_pct": float,
    #     "overloaded_lines": int,
    #     "transformer_loading_pct": float,
    #     "total_load_mw": float,
    #     "total_losses_mw": float,
    #     "loss_percentage": float
    # }
```

---

## 8. Configuration Schema

### 8.1 Feature Flags (`config/feature_flags.yaml`)

```yaml
# Feature toggles for gradual rollout
features:
  use_real_simulations: true          # Master switch
  use_real_dh: true                   # Enable real DH simulations
  use_real_hp: false                  # Enable real HP simulations (staged rollout)
  
  enable_caching: true                # Cache simulation results
  cache_ttl_hours: 24                 # Cache validity period
  
  enable_progress_tracking: true      # Show progress bars
  enable_parallel_execution: false    # Run multiple streets in parallel
  
  fallback_on_error: true             # Use placeholder if simulation fails
  strict_mode: false                  # Fail fast on errors (for testing)

logging:
  level: "INFO"                       # DEBUG, INFO, WARNING, ERROR
  log_simulations: true               # Log detailed simulation steps
  log_cache_operations: true          # Log cache hits/misses
```

### 8.2 Simulation Parameters (`config/simulation_config.yaml`)

```yaml
# District Heating Configuration
district_heating:
  supply_temp_c: 85.0
  return_temp_c: 55.0
  
  network:
    pipe_roughness_mm: 0.1            # Steel pipe roughness
    default_diameter_m: 0.065         # DN65
    insulation_thickness_mm: 30
    ambient_temp_c: 10
  
  plant:
    supply_pressure_bar: 6.0
    min_pressure_bar: 2.0
  
  simulation:
    solver: "pipeflow"                # pandapipes solver
    mode: "all"                       # "hydraulic", "thermal", or "all"
    max_iterations: 100
    tolerance: 1e-6

# Heat Pump Electrical Configuration
heat_pump:
  hp_thermal_kw: 6.0                  # Thermal power per building
  hp_cop: 2.8                         # Coefficient of performance
  hp_three_phase: true                # 3-phase vs single-phase
  
  grid:
    mv_voltage_kv: 20.0               # Medium voltage
    lv_voltage_kv: 0.4                # Low voltage
    transformer_mva: 0.63             # Transformer capacity
    
  cables:
    default_type: "NAYY 4x150 SE"     # Standard LV cable
    max_length_m: 500                 # Max cable length
    
  limits:
    voltage_min_pu: 0.90              # Min voltage (per-unit)
    voltage_max_pu: 1.10              # Max voltage
    line_loading_max_pct: 100.0       # Max line loading
    transformer_loading_max_pct: 100.0
  
  simulation:
    solver: "nr"                      # Newton-Raphson
    use_3ph: true                     # Use 3-phase solver
    max_iterations: 100
    tolerance: 1e-6

# Performance Settings
performance:
  cache_directory: "simulation_cache"
  max_cache_size_mb: 1000
  
  parallel:
    max_workers: 4
    chunk_size: 10                    # Buildings per chunk
  
  timeouts:
    network_creation_s: 60
    simulation_s: 300
    total_s: 600

# Validation Rules
validation:
  min_buildings: 2                    # Minimum buildings for valid simulation
  max_buildings: 500                  # Maximum buildings (performance limit)
  
  dh:
    min_heat_demand_kw: 1.0           # Minimum building heat demand
    max_pipe_length_m: 1000           # Sanity check for pipe lengths
    
  hp:
    min_base_load_kw: 0.5
    max_total_load_mw: 2.0            # Maximum load for LV network
```

---

## 9. Error Handling Strategy

### 9.1 Error Hierarchy

```python
# src/simulators/exceptions.py

class SimulationError(Exception):
    """Base exception for simulation errors."""
    pass

class NetworkCreationError(SimulationError):
    """Failed to create network model."""
    pass

class ConvergenceError(SimulationError):
    """Simulation failed to converge."""
    pass

class ValidationError(SimulationError):
    """Input data validation failed."""
    pass

class ConfigurationError(SimulationError):
    """Invalid configuration parameters."""
    pass
```

### 9.2 Fallback Logic

```
┌─────────────────────────┐
│ Start Simulation        │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Check feature_flags:    │
│ use_real_simulations?   │
└───────────┬─────────────┘
            │
    ┌───────┴───────┐
    │ YES           │ NO
    ▼               ▼
┌─────────────┐ ┌─────────────┐
│ Try Real    │ │ Use         │
│ Simulator   │ │ Placeholder │
└──────┬──────┘ └─────────────┘
       │
       ▼
┌─────────────────────────┐
│ Real simulation         │
│ throws exception?       │
└───────────┬─────────────┘
            │
    ┌───────┴───────┐
    │ YES           │ NO
    ▼               ▼
┌─────────────┐ ┌─────────────┐
│ Check       │ │ Return      │
│ fallback_   │ │ Real        │
│ on_error?   │ │ Results     │
└──────┬──────┘ └─────────────┘
       │
   ┌───┴───┐
   │YES    │NO
   ▼       ▼
┌────────┐ ┌────────┐
│Use     │ │Re-raise│
│Placeholder│ │Error   │
└────────┘ └────────┘
```

---

## 10. Performance Optimization Strategy

### 10.1 Caching

**Cache Key Generation:**
```
cache_key = hash(
    building_ids (sorted),
    scenario_type,
    simulation_parameters
)
```

**Cache Location:**
```
simulation_cache/
├── dh/
│   ├── {cache_key}.pkl         # Pickled SimulationResult
│   └── {cache_key}_meta.json   # Metadata (timestamp, inputs)
└── hp/
    ├── {cache_key}.pkl
    └── {cache_key}_meta.json
```

**Cache Invalidation:**
- Time-based: 24 hours (configurable)
- Manual: Clear cache command
- Automatic: If simulation code version changes

### 10.2 Parallel Execution

For multi-street analysis:
```python
# Example: Analyze 10 streets in parallel
streets = ["Parkstraße", "Liebermannstraße", ...]

with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(run_simulation_for_street, street)
        for street in streets
    ]
    results = [f.result() for f in futures]
```

### 10.3 Progress Tracking

```python
# Progress stages for DH simulation:
stages = [
    "Loading building data",       # 5%
    "Creating network topology",   # 15%
    "Adding heat exchangers",      # 25%
    "Running hydraulic simulation",# 50%
    "Running thermal simulation",  # 75%
    "Extracting results",          # 90%
    "Exporting GeoJSON",           # 100%
]
```

---

## 11. Testing Strategy

### 11.1 Test Pyramid

```
        ┌─────────┐
        │   E2E   │  ← 5% (Agent → Real Sim → Report)
        ├─────────┤
        │         │
      ┌─┴─────────┴─┐
      │ Integration │  ← 25% (Module interactions)
      ├─────────────┤
      │             │
    ┌─┴─────────────┴─┐
    │  Unit Tests     │  ← 70% (Individual functions)
    └─────────────────┘
```

### 11.2 Test Coverage Goals

- Unit tests: 80%+ coverage
- Integration tests: Key flows covered
- E2E tests: Happy paths + error scenarios

### 11.3 Test Data

```
tests/fixtures/
├── sample_buildings_small.geojson     # 5 buildings (fast)
├── sample_buildings_medium.geojson    # 25 buildings (typical)
├── sample_buildings_large.geojson     # 100 buildings (stress test)
└── sample_streets.geojson
```

---

## 12. Migration Path

### Phase 1: Architecture Design (Current)
✅ Define interfaces  
✅ Create directory structure  
✅ Document data flows  
✅ Design configuration  

### Phase 2: Implementation (Next)
□ Create base classes  
□ Implement DH simulator  
□ Implement HP simulator  
□ Create orchestrator  
□ Add caching  

### Phase 3: Testing
□ Write unit tests  
□ Write integration tests  
□ Validate against standalone simulators  
□ Performance benchmarking  

### Phase 4: Deployment
□ Gradual rollout with feature flags  
□ Monitor performance  
□ Collect user feedback  
□ Full production deployment  

---

## 13. Success Metrics

### Functional Metrics
- ✅ Real simulations produce results within 5% of standalone tools
- ✅ 95%+ simulation success rate
- ✅ Zero data loss (all simulations cached/logged)

### Performance Metrics
- ✅ < 30s for typical street (15-30 buildings)
- ✅ < 2 minutes for large street (100+ buildings)
- ✅ 50%+ cache hit rate after warmup

### Quality Metrics
- ✅ 80%+ code coverage
- ✅ Zero critical bugs in production
- ✅ < 1% simulation convergence failures

---

## 14. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Simulation convergence failures** | High | Medium | • Implement robust fallbacks<br>• Add network simplification<br>• Cache successful configs |
| **Performance degradation** | Medium | Low | • Implement caching<br>• Profile and optimize<br>• Add progress indicators |
| **Breaking changes to Agent API** | High | Low | • Maintain backward compatibility<br>• Version interfaces<br>• Comprehensive testing |
| **Dependency conflicts** (pandapipes/pandapower) | Medium | Medium | • Pin dependency versions<br>• Test in isolated environment<br>• Document requirements |
| **Incorrect results from real simulations** | High | Low | • Validate against known cases<br>• Cross-check with standalone tools<br>• Add sanity checks |

---

## 15. Next Steps

1. **Review this architecture** with stakeholders
2. **Create interface contracts** (`src/simulators/base.py`)
3. **Set up directory structure**
4. **Implement DH simulator** (Phase 2, Step 1)
5. **Write unit tests** for DH simulator
6. **Integrate into agent system**
7. **Test end-to-end** with single street
8. **Iterate and improve**

---

**Document Status:** ✅ Complete - Ready for Phase 2 Implementation  
**Last Updated:** November 2025  
**Author:** AI Architecture Team

