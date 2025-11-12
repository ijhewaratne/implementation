"""
Placeholder District Heating Simulator.

This module provides a fallback simulator that returns reasonable dummy data
when real pandapipes simulations are not available or fail. It implements
the same interface as the real simulator for seamless fallback.
"""

from pathlib import Path
from typing import Dict, Any
import geopandas as gpd

from .base import (
    DHSimulatorInterface,
    SimulationResult,
    SimulationType,
    SimulationMode,
)


class PlaceholderDHSimulator(DHSimulatorInterface):
    """
    Placeholder district heating simulator that returns dummy data.
    
    Used as fallback when:
    - pandapipes is not installed
    - Real simulation fails
    - Testing without dependencies
    
    Returns realistic-looking but fake KPIs based on simple estimates.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize placeholder simulator."""
        super().__init__(config)
        self._num_buildings = 0
        self._total_demand_kw = 0
    
    def set_supply_temperature(self, temp_c: float) -> None:
        """Set supply temperature."""
        self.supply_temp_c = temp_c
    
    def set_return_temperature(self, temp_c: float) -> None:
        """Set return temperature."""
        self.return_temp_c = temp_c
    
    def create_network(self, buildings_gdf: gpd.GeoDataFrame, **kwargs) -> Any:
        """
        'Create' placeholder network (just count buildings).
        
        Args:
            buildings_gdf: Building data
        
        Returns:
            None (no real network created)
        """
        self._num_buildings = len(buildings_gdf)
        self._total_demand_kw = buildings_gdf["heating_load_kw"].sum()
        
        print(f"  Placeholder: {self._num_buildings} buildings, "
              f"{self._total_demand_kw:.1f} kW total demand")
        
        return None
    
    def run_simulation(self) -> SimulationResult:
        """
        'Run' placeholder simulation (generate dummy KPIs).
        
        Returns:
            SimulationResult with fake but realistic KPIs
        """
        self._start_timer()
        
        # Generate fake KPIs based on simple estimates
        kpis = self.extract_kpis()
        
        result = SimulationResult(
            success=True,
            scenario_name=self.config.get("scenario_name", "DH_placeholder"),
            simulation_type=SimulationType.DISTRICT_HEATING,
            simulation_mode=SimulationMode.PLACEHOLDER,
            kpi=kpis,
            metadata={
                "num_buildings": self._num_buildings,
                "total_demand_kw": self._total_demand_kw,
                "note": "These are placeholder values, not real simulation results"
            },
            execution_time_s=self._get_execution_time()
        )
        
        result.add_warning("Using placeholder DH simulator - results are estimates only!")
        
        return result
    
    def extract_kpis(self) -> Dict[str, float]:
        """
        Generate fake KPIs based on simple rules of thumb.
        
        Returns:
            Dictionary with all required DH KPIs (fake values)
        """
        # Simple estimates
        total_heat_mwh = self._total_demand_kw * 8760 / 1e6  # Assume constant load
        
        # Estimate network size
        num_junctions = self._num_buildings * 2  # Supply + return per building
        num_pipes = self._num_buildings * 2
        total_pipe_length_km = self._num_buildings * 0.05  # ~50m per building
        
        return {
            # Heat supply
            "total_heat_supplied_mwh": round(total_heat_mwh, 2),
            "peak_heat_load_kw": round(self._total_demand_kw, 1),
            
            # Hydraulics (dummy values)
            "max_pressure_drop_bar": 0.5,
            "avg_pressure_drop_bar": 0.3,
            "pump_energy_kwh": round(total_heat_mwh * 0.02 * 1000, 1),  # ~2% of heat
            
            # Thermal (dummy values)
            "min_supply_temp_c": self.supply_temp_c - 3.0,
            "avg_supply_temp_c": self.supply_temp_c - 1.5,
            "network_heat_loss_kwh": round(total_heat_mwh * 0.10 * 1000, 1),  # ~10% losses
            "heat_loss_percentage": 10.0,
            
            # Network
            "num_junctions": num_junctions,
            "num_pipes": num_pipes,
            "num_consumers": self._num_buildings,
            "total_pipe_length_km": round(total_pipe_length_km, 2),
        }
    
    def get_pressure_profile(self) -> gpd.GeoDataFrame:
        """Return empty GeoDataFrame (no real results)."""
        return gpd.GeoDataFrame()
    
    def get_temperature_profile(self) -> gpd.GeoDataFrame:
        """Return empty GeoDataFrame (no real results)."""
        return gpd.GeoDataFrame()
    
    def export_results(self, output_dir: Path, format: str = "geojson") -> Dict[str, Path]:
        """No real results to export."""
        return {}
    
    def get_network_summary(self) -> Dict[str, int]:
        """Return summary based on estimates."""
        return {
            "num_junctions": self._num_buildings * 2,
            "num_pipes": self._num_buildings * 2,
            "num_heat_exchangers": self._num_buildings,
            "num_sinks": 1,
            "num_ext_grids": 1,
        }

