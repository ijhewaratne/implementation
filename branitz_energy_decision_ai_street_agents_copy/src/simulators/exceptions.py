"""
Exception hierarchy for simulation errors.
"""


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
    
    def __str__(self):
        return f"{super().__str__()} (iteration={self.iteration}, residual={self.residual:.6f})"


class SimulationRuntimeError(SimulationError):
    """Runtime error during simulation execution."""
    pass

