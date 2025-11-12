"""
Base classes and interfaces for energy system simulators.

This module defines the abstract base classes that all simulators
(both real and placeholder) must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import time

import geopandas as gpd

from .exceptions import ValidationError, ConfigurationError


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
    
    All simulators must return results in this format to ensure
    consistency across the system.
    
    Attributes:
        success: Whether simulation completed successfully
        scenario_name: Name/identifier of the scenario
        simulation_type: Type of simulation (DH or HP)
        simulation_mode: Mode used (real or placeholder)
        kpi: Dictionary of key performance indicators
        metadata: Additional information (network size, parameters, etc.)
        error: Error message if success=False
        warnings: List of warning messages
        execution_time_s: Time taken to run simulation (seconds)
    """
    success: bool
    scenario_name: str
    simulation_type: SimulationType
    simulation_mode: SimulationMode
    kpi: Dict[str, float]
    metadata: Dict[str, Any]
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    execution_time_s: float = 0.0
    
    def to_dict(self) -> Dict:
        """
        Serialize to dictionary for JSON export.
        
        Returns:
            Dictionary representation suitable for JSON
        """
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
        """Add a warning message to the result."""
        self.warnings.append(message)


class BaseSimulator(ABC):
    """
    Abstract base class for all energy system simulators.
    
    This defines the interface that all concrete simulators
    (both real pandapipes/pandapower and placeholders) must implement.
    
    The workflow for using a simulator is:
        1. Create instance with configuration
        2. Call validate_inputs() to check data
        3. Call create_network() to build model
        4. Call run_simulation() to execute
        5. Optionally call export_results()
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
        self.network = None  # Will hold network object
        self._start_time = None
        self._validated = False
        
        # Validate that required config keys exist
        self._validate_config()
    
    def _validate_config(self):
        """
        Validate configuration dictionary.
        
        Subclasses can override to add specific validation.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not isinstance(self.config, dict):
            raise ConfigurationError("Configuration must be a dictionary")
    
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
            Network object (pandapipes.Net, pandapower.Net, or equivalent)
            
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
        See documentation for required KPIs per simulator type.
        
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
        """
        Internal: Get elapsed time in seconds.
        
        Returns:
            Elapsed time since _start_timer() was called
        """
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time


class DHSimulatorInterface(BaseSimulator):
    """
    Extended interface specific to district heating simulators.
    
    Adds DH-specific methods for temperature control and pressure analysis.
    All DH simulators (real and placeholder) must implement this interface.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # DH-specific attributes
        self.supply_temp_c = config.get("supply_temp_c", 85.0)
        self.return_temp_c = config.get("return_temp_c", 55.0)
        
        # Validate temperature settings
        if self.supply_temp_c <= self.return_temp_c:
            raise ConfigurationError(
                f"Supply temp ({self.supply_temp_c}°C) must be > "
                f"return temp ({self.return_temp_c}°C)"
            )
    
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


class HPSimulatorInterface(BaseSimulator):
    """
    Extended interface specific to heat pump electrical simulators.
    
    Adds HP-specific methods for electrical analysis and constraint checking.
    All HP simulators (real and placeholder) must implement this interface.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # HP-specific attributes
        self.hp_thermal_kw = config.get("hp_thermal_kw", 6.0)
        self.hp_cop = config.get("hp_cop", 2.8)
        self.hp_three_phase = config.get("hp_three_phase", True)
        
        # Validate HP parameters
        if self.hp_thermal_kw <= 0:
            raise ConfigurationError("HP thermal power must be > 0")
        if self.hp_cop <= 0:
            raise ConfigurationError("HP COP must be > 0")
    
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


# Required KPIs for each simulator type
DH_REQUIRED_KPIS = {
    # Heat Supply
    "total_heat_supplied_mwh": float,
    "peak_heat_load_kw": float,
    
    # Hydraulics
    "max_pressure_drop_bar": float,
    "avg_pressure_drop_bar": float,
    "pump_energy_kwh": float,
    
    # Thermal
    "min_supply_temp_c": float,
    "avg_supply_temp_c": float,
    "network_heat_loss_kwh": float,
    "heat_loss_percentage": float,
    
    # Network Size
    "num_junctions": int,
    "num_pipes": int,
    "num_consumers": int,
    "total_pipe_length_km": float,
}

HP_REQUIRED_KPIS = {
    # Voltage
    "min_voltage_pu": float,
    "max_voltage_pu": float,
    "avg_voltage_pu": float,
    "voltage_violations": int,
    
    # Line Loading
    "max_line_loading_pct": float,
    "avg_line_loading_pct": float,
    "overloaded_lines": int,
    
    # Transformer
    "transformer_loading_pct": float,
    "transformer_overloaded": bool,
    
    # Load & Losses
    "total_load_mw": float,
    "total_losses_mw": float,
    "loss_percentage": float,
    
    # Network Size
    "num_buses": int,
    "num_lines": int,
    "num_loads": int,
}

