"""
Energy System Simulators

This package contains real and placeholder simulators for:
- District Heating (DH) systems
- Heat Pump (HP) electrical systems
"""

from .base import (
    BaseSimulator,
    DHSimulatorInterface,
    HPSimulatorInterface,
    SimulationResult,
    SimulationType,
    SimulationMode,
)

from .exceptions import (
    SimulationError,
    ValidationError,
    ConfigurationError,
    NetworkCreationError,
    ConvergenceError,
    SimulationRuntimeError,
)

# Real simulators
from .pandapipes_dh_simulator import DistrictHeatingSimulator
from .pandapower_hp_simulator import HeatPumpElectricalSimulator

# Placeholder simulators
from .placeholder_dh import PlaceholderDHSimulator
from .placeholder_hp import PlaceholderHPSimulator

__all__ = [
    # Base classes
    "BaseSimulator",
    "DHSimulatorInterface",
    "HPSimulatorInterface",
    
    # Data structures
    "SimulationResult",
    "SimulationType",
    "SimulationMode",
    
    # Exceptions
    "SimulationError",
    "ValidationError",
    "ConfigurationError",
    "NetworkCreationError",
    "ConvergenceError",
    "SimulationRuntimeError",
    
    # Real simulators
    "DistrictHeatingSimulator",
    "HeatPumpElectricalSimulator",
    
    # Placeholder simulators
    "PlaceholderDHSimulator",
    "PlaceholderHPSimulator",
]

