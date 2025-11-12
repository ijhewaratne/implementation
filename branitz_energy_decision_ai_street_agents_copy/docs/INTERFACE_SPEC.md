# Interface Specification
## Agent-Based Energy System - Real Simulations Integration

**Version:** 1.0  
**Date:** November 2025

---

## 1. Base Simulator Interface

### 1.1 Abstract Base Class

```python
# File: src/simulators/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import geopandas as gpd
from pathlib import Path
import time


class SimulationType(Enum):
    """Enumeration of simulation types."""
    DISTRICT_HEATING = "DH"
    HEAT_PUMP = "HP"


class SimulationMode(Enum):
    """Enumeration of simulation modes."""
    REAL = "real"
    PLACEHOLDER = "placeholder"


@dataclass
class SimulationResult:
    """
    Standardized container for simulation results.
    
    All simulators must return results in this format.
    """
    success: bool
    scenario_name: str
    simulation_type: SimulationType
    simulation_mode: SimulationMode
    kpi: Dict[str, float]
    metadata: Dict[str, Any]
    error: Optional[str] = None
    warnings: List[str] = None
    execution_time_s: float = 0.0
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary for JSON export."""
        return {
            "success": self.success,
            "scenario": self.scenario_name,
            "type": self.simulation_type.value,
            "mode": self.simulation_mode.value,
            "kpi": self.kpi,
            "metadata": self.metadata,
            "error": self.error,
            "warnings": self.warnings,
            "execution_time_s": self.execution_time_s
        }
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)


class BaseSimulator(ABC):
    """
    Abstract base class for all energy system simulators.
    
    All concrete simulators (real and placeholder) must implement this interface.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize simulator with configuration.
        
        Args:
            config: Dictionary containing simulation parameters.
                   Required keys depend on simulator type.
        
        Raises:
            ConfigurationError: If required config keys are missing
        """
        self.config = config
        self.network = None
        self._start_time = None
        self._validated = False
    
    @abstractmethod
    def validate_inputs(self, buildings_gdf: gpd.GeoDataFrame, **kwargs) -> bool:
        """
        Validate input data before simulation.
        
        Must check:
        - Required columns exist in buildings_gdf
        - Data types are correct
        - Values are in acceptable ranges
        - Geometries are valid
        - CRS is appropriate
        
        Args:
            buildings_gdf: GeoDataFrame with building data
            **kwargs: Additional inputs specific to simulator type
            
        Returns:
            True if all validations pass
            
        Raises:
            ValidationError: With detailed message if validation fails
        """
        pass
    
    @abstractmethod
    def create_network(self, buildings_gdf: gpd.GeoDataFrame, **kwargs) -> Any:
        """
        Create network model from building data.
        
        Must:
        - Transform geometries to appropriate CRS
        - Create network topology
        - Add all components (pipes/lines, consumers/loads, etc.)
        - Set boundary conditions
        - Validate network connectivity
        
        Args:
            buildings_gdf: GeoDataFrame with building geometries and demands
            **kwargs: Additional data (e.g., existing network, topology preference)
            
        Returns:
            Network object (pandapipes.Net or pandapower.Net or equivalent)
            
        Raises:
            NetworkCreationError: If network creation fails
        """
        pass
    
    @abstractmethod
    def run_simulation(self) -> SimulationResult:
        """
        Execute physics-based simulation.
        
        Must:
        - Ensure network is created
        - Run solver (pipeflow/powerflow)
        - Handle convergence failures gracefully
        - Extract results
        - Calculate KPIs
        - Measure execution time
        
        Returns:
            SimulationResult with all fields populated
            
        Raises:
            ConvergenceError: If simulation fails to converge
            SimulationError: For other simulation failures
        """
        pass
    
    @abstractmethod
    def extract_kpis(self) -> Dict[str, float]:
        """
        Extract key performance indicators from simulation results.
        
        Must return a dictionary with standardized KPI names.
        See section 2 and 3 for required KPIs per simulator type.
        
        Returns:
            Dictionary mapping KPI name (str) to value (float)
        """
        pass
    
    def export_results(self, 
                      output_dir: Path, 
                      format: str = "geojson") -> Dict[str, Path]:
        """
        Export simulation results to files.
        
        Optional method - default implementation returns empty dict.
        Simulators should override to provide visualization exports.
        
        Args:
            output_dir: Directory to save results
            format: Output format ("geojson", "json", "csv")
            
        Returns:
            Dictionary mapping result type to file path
            Example: {"junctions": Path(...), "pipes": Path(...)}
        """
        return {}
    
    def get_network_summary(self) -> Dict[str, int]:
        """
        Get summary statistics of the network.
        
        Optional method - default implementation returns empty dict.
        
        Returns:
            Dictionary with network element counts
            Example: {"num_junctions": 50, "num_pipes": 48}
        """
        return {}
    
    def _start_timer(self):
        """Internal: Start execution timer."""
        self._start_time = time.time()
    
    def _get_execution_time(self) -> float:
        """Internal: Get elapsed time in seconds."""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time
```

---

## 2. District Heating Simulator Interface

### 2.1 Extended Interface

```python
# File: src/simulators/base.py (continued)

class DHSimulatorInterface(BaseSimulator):
    """
    Extended interface specific to district heating simulators.
    
    Adds DH-specific methods for temperature control and pressure analysis.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # DH-specific attributes
        self.supply_temp_c = config.get("supply_temp_c", 85.0)
        self.return_temp_c = config.get("return_temp_c", 55.0)
    
    @abstractmethod
    def set_supply_temperature(self, temp_c: float) -> None:
        """
        Set supply temperature in Celsius.
        
        Args:
            temp_c: Supply temperature (typically 70-95°C)
            
        Raises:
            ValueError: If temperature is out of valid range
        """
        pass
    
    @abstractmethod
    def set_return_temperature(self, temp_c: float) -> None:
        """
        Set return temperature in Celsius.
        
        Args:
            temp_c: Return temperature (typically 40-60°C)
            
        Raises:
            ValueError: If temperature is out of valid range or >= supply temp
        """
        pass
    
    @abstractmethod
    def get_pressure_profile(self) -> gpd.GeoDataFrame:
        """
        Get pressure distribution along network.
        
        Returns:
            GeoDataFrame with columns:
            - junction_id: int
            - pressure_bar: float
            - geometry: Point
        """
        pass
    
    @abstractmethod
    def get_temperature_profile(self) -> gpd.GeoDataFrame:
        """
        Get temperature distribution along network.
        
        Returns:
            GeoDataFrame with columns:
            - junction_id: int
            - temperature_c: float
            - circuit: str ("supply" or "return")
            - geometry: Point
        """
        pass
    
    def validate_inputs(self, buildings_gdf: gpd.GeoDataFrame, **kwargs) -> bool:
        """
        Validate inputs for DH simulation.
        
        Required columns in buildings_gdf:
        - GebaeudeID or building_id: str
        - geometry: Polygon or Point
        - heating_load_kw: float (> 0)
        """
        required_cols = ["geometry", "heating_load_kw"]
        missing = [col for col in required_cols if col not in buildings_gdf.columns]
        
        if missing:
            raise ValidationError(f"Missing required columns: {missing}")
        
        if len(buildings_gdf) < 2:
            raise ValidationError("At least 2 buildings required for DH simulation")
        
        if (buildings_gdf["heating_load_kw"] <= 0).any():
            raise ValidationError("All buildings must have heating_load_kw > 0")
        
        if buildings_gdf.geometry.is_empty.any():
            raise ValidationError("All buildings must have valid geometry")
        
        self._validated = True
        return True
```

### 2.2 Required KPIs for DH Simulators

```python
# All DH simulators must return these KPIs in extract_kpis()

DH_REQUIRED_KPIS = {
    # Heat Supply
    "total_heat_supplied_mwh": float,      # Total heat delivered (MWh)
    "peak_heat_load_kw": float,            # Peak heat load (kW)
    
    # Hydraulics
    "max_pressure_drop_bar": float,        # Maximum pressure drop (bar)
    "avg_pressure_drop_bar": float,        # Average pressure drop (bar)
    "pump_energy_kwh": float,              # Pump energy consumption (kWh)
    
    # Thermal
    "min_supply_temp_c": float,            # Minimum supply temperature (°C)
    "avg_supply_temp_c": float,            # Average supply temperature (°C)
    "network_heat_loss_kwh": float,        # Heat losses in network (kWh)
    "heat_loss_percentage": float,         # Losses as % of supplied heat
    
    # Network Size
    "num_junctions": int,                  # Number of junctions
    "num_pipes": int,                      # Number of pipes
    "num_consumers": int,                  # Number of heat exchangers
    "total_pipe_length_km": float,         # Total pipe length (km)
}

# Optional KPIs (nice to have)
DH_OPTIONAL_KPIS = {
    "avg_flow_velocity_m_s": float,        # Average flow velocity (m/s)
    "max_flow_velocity_m_s": float,        # Maximum flow velocity (m/s)
    "mass_flow_kg_s": float,               # Mass flow rate (kg/s)
    "return_temp_c": float,                # Return temperature (°C)
}
```

---

## 3. Heat Pump Electrical Simulator Interface

### 3.1 Extended Interface

```python
# File: src/simulators/base.py (continued)

class HPSimulatorInterface(BaseSimulator):
    """
    Extended interface specific to heat pump electrical simulators.
    
    Adds HP-specific methods for electrical analysis and constraint checking.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # HP-specific attributes
        self.hp_thermal_kw = config.get("hp_thermal_kw", 6.0)
        self.hp_cop = config.get("hp_cop", 2.8)
        self.hp_three_phase = config.get("hp_three_phase", True)
    
    @abstractmethod
    def set_hp_parameters(self, 
                         thermal_kw: float, 
                         cop: float, 
                         three_phase: bool) -> None:
        """
        Set heat pump electrical parameters.
        
        Args:
            thermal_kw: Thermal power output (kW)
            cop: Coefficient of performance (typically 2.5-4.0)
            three_phase: True for 3-phase balanced, False for single-phase
            
        Raises:
            ValueError: If parameters are out of valid range
        """
        pass
    
    @abstractmethod
    def get_voltage_violations(self, 
                               min_pu: float = 0.9, 
                               max_pu: float = 1.1) -> gpd.GeoDataFrame:
        """
        Get buses with voltage violations.
        
        Args:
            min_pu: Minimum acceptable voltage (per-unit)
            max_pu: Maximum acceptable voltage (per-unit)
        
        Returns:
            GeoDataFrame with columns:
            - bus_id: int
            - voltage_pu: float
            - violation_type: str ("undervoltage" or "overvoltage")
            - geometry: Point
        """
        pass
    
    @abstractmethod
    def get_line_overloads(self, 
                          threshold_pct: float = 100.0) -> gpd.GeoDataFrame:
        """
        Get lines exceeding loading threshold.
        
        Args:
            threshold_pct: Loading threshold (% of max capacity)
        
        Returns:
            GeoDataFrame with columns:
            - line_id: int
            - loading_pct: float
            - max_i_ka: float (maximum allowed current)
            - current_i_ka: float (actual current)
            - geometry: LineString
        """
        pass
    
    def validate_inputs(self, buildings_gdf: gpd.GeoDataFrame, **kwargs) -> bool:
        """
        Validate inputs for HP electrical simulation.
        
        Required columns in buildings_gdf:
        - GebaeudeID or building_id: str
        - geometry: Polygon or Point
        - heating_load_kw: float (> 0)
        - base_electric_load_kw: float (optional, defaults to 2.0)
        """
        required_cols = ["geometry", "heating_load_kw"]
        missing = [col for col in required_cols if col not in buildings_gdf.columns]
        
        if missing:
            raise ValidationError(f"Missing required columns: {missing}")
        
        if len(buildings_gdf) < 2:
            raise ValidationError("At least 2 buildings required for HP simulation")
        
        # Add base load if missing
        if "base_electric_load_kw" not in buildings_gdf.columns:
            buildings_gdf["base_electric_load_kw"] = 2.0
        
        if buildings_gdf.geometry.is_empty.any():
            raise ValidationError("All buildings must have valid geometry")
        
        self._validated = True
        return True
```

### 3.2 Required KPIs for HP Simulators

```python
# All HP simulators must return these KPIs in extract_kpis()

HP_REQUIRED_KPIS = {
    # Voltage
    "min_voltage_pu": float,               # Minimum voltage (per-unit)
    "max_voltage_pu": float,               # Maximum voltage (per-unit)
    "avg_voltage_pu": float,               # Average voltage (per-unit)
    "voltage_violations": int,             # Count of buses with violations
    
    # Line Loading
    "max_line_loading_pct": float,         # Maximum line loading (%)
    "avg_line_loading_pct": float,         # Average line loading (%)
    "overloaded_lines": int,               # Count of overloaded lines
    
    # Transformer
    "transformer_loading_pct": float,      # Transformer loading (%)
    "transformer_overloaded": bool,        # True if transformer overloaded
    
    # Load & Losses
    "total_load_mw": float,                # Total electrical load (MW)
    "total_losses_mw": float,              # Total losses (MW)
    "loss_percentage": float,              # Losses as % of load
    
    # Network Size
    "num_buses": int,                      # Number of buses
    "num_lines": int,                      # Number of lines
    "num_loads": int,                      # Number of loads
}

# Optional KPIs
HP_OPTIONAL_KPIS = {
    "power_factor": float,                 # Average power factor
    "max_current_ka": float,               # Maximum line current (kA)
    "reactive_power_mvar": float,          # Total reactive power (Mvar)
}
```

---

## 4. Orchestrator Interface

### 4.1 Simulation Orchestrator

```python
# File: src/orchestration/simulation_orchestrator.py

from typing import Optional, Dict, Any
from pathlib import Path
from .cache_manager import CacheManager
from .progress_tracker import ProgressTracker
from ..simulators.base import BaseSimulator, SimulationResult, SimulationType

class SimulationOrchestrator:
    """
    Coordinates simulation execution with caching and progress tracking.
    
    Responsibilities:
    - Select appropriate simulator (real or placeholder)
    - Check cache before running simulation
    - Track progress during execution
    - Handle errors and fallbacks
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize orchestrator with configuration.
        
        Args:
            config: Configuration dictionary with keys:
                - use_real_simulations: bool
                - use_real_dh: bool
                - use_real_hp: bool
                - enable_caching: bool
                - fallback_on_error: bool
        """
        self.config = config
        self.cache_manager = CacheManager(config) if config.get("enable_caching") else None
        self.progress_tracker = ProgressTracker() if config.get("enable_progress_tracking") else None
    
    def run_simulation(self,
                      simulation_type: SimulationType,
                      buildings_gdf: gpd.GeoDataFrame,
                      scenario_name: str,
                      scenario_params: Dict[str, Any],
                      **kwargs) -> SimulationResult:
        """
        Execute simulation with caching and error handling.
        
        Workflow:
        1. Check cache
        2. Select simulator
        3. Run simulation
        4. Cache results
        5. Return results
        
        Args:
            simulation_type: DH or HP
            buildings_gdf: Building data
            scenario_name: Scenario identifier
            scenario_params: Simulation parameters
            **kwargs: Additional data (e.g., street_network)
            
        Returns:
            SimulationResult
        """
        # 1. Check cache
        if self.cache_manager:
            cached_result = self.cache_manager.get(
                simulation_type, buildings_gdf, scenario_params
            )
            if cached_result:
                print(f"[Cache HIT] Using cached results for {scenario_name}")
                return cached_result
        
        # 2. Select simulator
        simulator = self._select_simulator(simulation_type, scenario_params)
        
        # 3. Run simulation
        try:
            if self.progress_tracker:
                self.progress_tracker.start(scenario_name)
            
            simulator.validate_inputs(buildings_gdf, **kwargs)
            simulator.create_network(buildings_gdf, **kwargs)
            result = simulator.run_simulation()
            
            if self.progress_tracker:
                self.progress_tracker.complete()
            
        except Exception as e:
            if self.config.get("fallback_on_error"):
                print(f"[Fallback] Simulation failed, using placeholder: {e}")
                simulator = self._get_placeholder_simulator(simulation_type, scenario_params)
                result = simulator.run_simulation()
            else:
                raise
        
        # 4. Cache results
        if self.cache_manager and result.success:
            self.cache_manager.set(
                simulation_type, buildings_gdf, scenario_params, result
            )
        
        return result
    
    def _select_simulator(self, 
                         simulation_type: SimulationType,
                         params: Dict[str, Any]) -> BaseSimulator:
        """
        Select appropriate simulator based on configuration.
        
        Returns:
            Configured simulator instance
        """
        use_real = self.config.get("use_real_simulations", False)
        
        if simulation_type == SimulationType.DISTRICT_HEATING:
            use_real_dh = self.config.get("use_real_dh", True) and use_real
            if use_real_dh:
                from ..simulators.pandapipes_dh_simulator import DistrictHeatingSimulator
                return DistrictHeatingSimulator(params)
            else:
                from ..simulators.placeholder_dh import PlaceholderDHSimulator
                return PlaceholderDHSimulator(params)
        
        elif simulation_type == SimulationType.HEAT_PUMP:
            use_real_hp = self.config.get("use_real_hp", True) and use_real
            if use_real_hp:
                from ..simulators.pandapower_hp_simulator import HeatPumpElectricalSimulator
                return HeatPumpElectricalSimulator(params)
            else:
                from ..simulators.placeholder_hp import PlaceholderHPSimulator
                return PlaceholderHPSimulator(params)
        
        else:
            raise ValueError(f"Unknown simulation type: {simulation_type}")
```

---

## 5. Cache Manager Interface

```python
# File: src/orchestration/cache_manager.py

import hashlib
import json
import pickle
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import geopandas as gpd

class CacheManager:
    """
    Manages caching of simulation results.
    
    Cache key is generated from:
    - Building IDs (sorted)
    - Simulation type
    - Simulation parameters
    
    Cache entry includes:
    - Timestamp
    - Simulation result
    - Metadata (inputs hash, version)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize cache manager.
        
        Args:
            config: Configuration with keys:
                - cache_directory: str
                - cache_ttl_hours: int
        """
        self.cache_dir = Path(config.get("cache_directory", "simulation_cache"))
        self.cache_ttl = timedelta(hours=config.get("cache_ttl_hours", 24))
        self.cache_dir.mkdir(exist_ok=True)
        (self.cache_dir / "dh").mkdir(exist_ok=True)
        (self.cache_dir / "hp").mkdir(exist_ok=True)
    
    def _generate_cache_key(self,
                           simulation_type: str,
                           buildings_gdf: gpd.GeoDataFrame,
                           params: Dict[str, Any]) -> str:
        """
        Generate unique cache key from inputs.
        
        Returns:
            32-character hexadecimal hash
        """
        # Extract building IDs
        if "GebaeudeID" in buildings_gdf.columns:
            building_ids = sorted(buildings_gdf["GebaeudeID"].tolist())
        elif "building_id" in buildings_gdf.columns:
            building_ids = sorted(buildings_gdf["building_id"].tolist())
        else:
            building_ids = sorted(buildings_gdf.index.tolist())
        
        # Create cache key data
        cache_data = {
            "simulation_type": simulation_type,
            "building_ids": building_ids,
            "params": params
        }
        
        # Generate hash
        key_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self,
            simulation_type: str,
            buildings_gdf: gpd.GeoDataFrame,
            params: Dict[str, Any]) -> Optional[Any]:
        """
        Retrieve cached result if available and valid.
        
        Returns:
            SimulationResult if cache hit, None if cache miss
        """
        key = self._generate_cache_key(simulation_type, buildings_gdf, params)
        cache_file = self.cache_dir / simulation_type.lower() / f"{key}.pkl"
        meta_file = self.cache_dir / simulation_type.lower() / f"{key}_meta.json"
        
        if not cache_file.exists() or not meta_file.exists():
            return None
        
        # Check if cache is expired
        with open(meta_file, 'r') as f:
            metadata = json.load(f)
        
        cached_time = datetime.fromisoformat(metadata["timestamp"])
        if datetime.now() - cached_time > self.cache_ttl:
            print(f"[Cache EXPIRED] {key}")
            return None
        
        # Load cached result
        with open(cache_file, 'rb') as f:
            result = pickle.load(f)
        
        return result
    
    def set(self,
            simulation_type: str,
            buildings_gdf: gpd.GeoDataFrame,
            params: Dict[str, Any],
            result: Any):
        """
        Store simulation result in cache.
        """
        key = self._generate_cache_key(simulation_type, buildings_gdf, params)
        cache_file = self.cache_dir / simulation_type.lower() / f"{key}.pkl"
        meta_file = self.cache_dir / simulation_type.lower() / f"{key}_meta.json"
        
        # Save result
        with open(cache_file, 'wb') as f:
            pickle.dump(result, f)
        
        # Save metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "simulation_type": simulation_type,
            "cache_key": key
        }
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"[Cache SET] {key}")
    
    def clear(self, simulation_type: Optional[str] = None):
        """
        Clear cache for specific type or all types.
        """
        if simulation_type:
            cache_subdir = self.cache_dir / simulation_type.lower()
            for file in cache_subdir.glob("*"):
                file.unlink()
        else:
            for file in self.cache_dir.rglob("*"):
                if file.is_file():
                    file.unlink()
```

---

## 6. Progress Tracker Interface

```python
# File: src/orchestration/progress_tracker.py

from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
import time

@dataclass
class ProgressStage:
    """Represents a stage in the simulation process."""
    name: str
    percentage: float  # 0-100
    completed: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ProgressTracker:
    """
    Tracks and reports simulation progress.
    
    Provides feedback to users during long-running simulations.
    """
    
    # Define progress stages for each simulation type
    DH_STAGES = [
        ProgressStage("Loading building data", 5),
        ProgressStage("Creating network topology", 15),
        ProgressStage("Adding heat exchangers", 25),
        ProgressStage("Running hydraulic simulation", 50),
        ProgressStage("Running thermal simulation", 75),
        ProgressStage("Extracting results", 90),
        ProgressStage("Exporting GeoJSON", 100),
    ]
    
    HP_STAGES = [
        ProgressStage("Loading building data", 5),
        ProgressStage("Creating LV network", 20),
        ProgressStage("Adding loads", 35),
        ProgressStage("Running power flow", 70),
        ProgressStage("Checking constraints", 85),
        ProgressStage("Extracting results", 95),
        ProgressStage("Exporting GeoJSON", 100),
    ]
    
    def __init__(self):
        self.current_scenario = None
        self.stages: List[ProgressStage] = []
        self.current_stage_idx = 0
        self.start_time = None
    
    def start(self, scenario_name: str, simulation_type: str = "DH"):
        """Initialize progress tracking for a new simulation."""
        self.current_scenario = scenario_name
        self.stages = (self.DH_STAGES.copy() if simulation_type == "DH" 
                      else self.HP_STAGES.copy())
        self.current_stage_idx = 0
        self.start_time = time.time()
        print(f"\n[Progress] Starting: {scenario_name}")
    
    def update(self, stage_name: str):
        """Update progress to a specific stage."""
        for idx, stage in enumerate(self.stages):
            if stage.name == stage_name:
                self.current_stage_idx = idx
                stage.completed = True
                stage.end_time = datetime.now()
                progress_pct = stage.percentage
                print(f"[Progress] {progress_pct:.0f}% - {stage_name}")
                return
    
    def complete(self):
        """Mark simulation as complete."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        print(f"[Progress] 100% - Complete ({elapsed:.1f}s)")
        self.current_scenario = None
    
    def estimate_remaining_time(self) -> Optional[float]:
        """
        Estimate remaining time in seconds.
        
        Returns:
            Estimated seconds remaining, or None if cannot estimate
        """
        if self.current_stage_idx == 0 or not self.start_time:
            return None
        
        elapsed = time.time() - self.start_time
        current_progress = self.stages[self.current_stage_idx].percentage
        
        if current_progress == 0:
            return None
        
        total_estimated = (elapsed / current_progress) * 100
        remaining = total_estimated - elapsed
        
        return max(0, remaining)
```

---

## 7. Exception Hierarchy

```python
# File: src/simulators/exceptions.py

class SimulationError(Exception):
    """Base exception for all simulation errors."""
    pass

class ValidationError(SimulationError):
    """Input data validation failed."""
    pass

class ConfigurationError(SimulationError):
    """Invalid configuration parameters."""
    pass

class NetworkCreationError(SimulationError):
    """Failed to create network model."""
    pass

class ConvergenceError(SimulationError):
    """Simulation failed to converge."""
    
    def __init__(self, message: str, iteration: int = 0, residual: float = 0.0):
        super().__init__(message)
        self.iteration = iteration
        self.residual = residual

class SimulationRuntimeError(SimulationError):
    """Runtime error during simulation execution."""
    pass
```

---

## 8. Summary of Contracts

### 8.1 Method Signatures That MUST Match

All implementations must have identical signatures for:

1. **`__init__(self, config: Dict[str, Any])`**
2. **`validate_inputs(self, buildings_gdf: gpd.GeoDataFrame, **kwargs) -> bool`**
3. **`create_network(self, buildings_gdf: gpd.GeoDataFrame, **kwargs) -> Any`**
4. **`run_simulation(self) -> SimulationResult`**
5. **`extract_kpis(self) -> Dict[str, float]`**

### 8.2 Required Return Types

- `SimulationResult` must have all fields populated
- KPIs must include all required keys (see sections 2.2 and 3.2)
- GeoDataFrames must have specified columns

### 8.3 Configuration Keys

**DH Simulators require:**
- `supply_temp_c`: float
- `return_temp_c`: float

**HP Simulators require:**
- `hp_thermal_kw`: float
- `hp_cop`: float
- `hp_three_phase`: bool

---

**Document Status:** ✅ Complete  
**Next:** Implement base classes and concrete simulators

