"""
Placeholder Heat Pump Electrical Simulator.

This module provides a fallback simulator that returns reasonable dummy data
when real pandapower simulations are not available or fail. It implements
the same interface as the real simulator for seamless fallback.
"""

from pathlib import Path
from typing import Dict, Any
import geopandas as gpd

from .base import (
    HPSimulatorInterface,
    SimulationResult,
    SimulationType,
    SimulationMode,
)


class PlaceholderHPSimulator(HPSimulatorInterface):
    """
    Placeholder heat pump electrical simulator that returns dummy data.
    
    Used as fallback when:
    - pandapower is not installed
    - Real simulation fails
    - Testing without dependencies
    
    Returns realistic-looking but fake KPIs based on simple estimates.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize placeholder simulator."""
        super().__init__(config)
        self._num_buildings = 0
        self._total_load_kw = 0
    
    def set_hp_parameters(self, thermal_kw: float, cop: float, three_phase: bool) -> None:
        """Set heat pump parameters."""
        self.hp_thermal_kw = thermal_kw
        self.hp_cop = cop
        self.hp_three_phase = three_phase
    
    def create_network(self, buildings_gdf: gpd.GeoDataFrame, **kwargs) -> Any:
        """
        'Create' placeholder network (just count buildings).
        
        Args:
            buildings_gdf: Building data
        
        Returns:
            None (no real network created)
        """
        self._num_buildings = len(buildings_gdf)
        
        # Add base load if missing
        if "base_electric_load_kw" not in buildings_gdf.columns:
            buildings_gdf["base_electric_load_kw"] = 2.0
        
        # Calculate total load
        base_load_kw = buildings_gdf["base_electric_load_kw"].sum()
        hp_load_kw = self._num_buildings * (self.hp_thermal_kw / self.hp_cop)
        self._total_load_kw = base_load_kw + hp_load_kw
        
        print(f"  Placeholder: {self._num_buildings} buildings, "
              f"{self._total_load_kw:.1f} kW total load")
        
        return None
    
    def run_simulation(self) -> SimulationResult:
        """
        'Run' placeholder simulation (generate dummy KPIs).
        
        Returns:
            SimulationResult with fake but realistic KPIs
        """
        self._start_timer()
        
        # Generate fake KPIs
        kpis = self.extract_kpis()
        
        result = SimulationResult(
            success=True,
            scenario_name=self.config.get("scenario_name", "HP_placeholder"),
            simulation_type=SimulationType.HEAT_PUMP,
            simulation_mode=SimulationMode.PLACEHOLDER,
            kpi=kpis,
            metadata={
                "num_buildings": self._num_buildings,
                "total_load_kw": self._total_load_kw,
                "hp_thermal_kw": self.hp_thermal_kw,
                "hp_cop": self.hp_cop,
                "note": "These are placeholder values, not real simulation results"
            },
            execution_time_s=self._get_execution_time()
        )
        
        result.add_warning("Using placeholder HP simulator - results are estimates only!")
        
        return result
    
    def extract_kpis(self) -> Dict[str, float]:
        """
        Generate fake KPIs based on simple rules of thumb.
        
        Returns:
            Dictionary with all required HP KPIs (fake values)
        """
        # Simple voltage estimates (assume mild voltage drop)
        min_voltage_pu = 0.95  # 5% drop
        max_voltage_pu = 1.00
        avg_voltage_pu = 0.98
        
        # Loading estimates (assume moderate loading)
        max_line_loading_pct = 75.0
        avg_line_loading_pct = 45.0
        trafo_loading_pct = 60.0
        
        # Losses (estimate 3% of total load)
        total_load_mw = self._total_load_kw / 1000
        losses_mw = total_load_mw * 0.03
        
        return {
            # Voltage
            "min_voltage_pu": min_voltage_pu,
            "max_voltage_pu": max_voltage_pu,
            "avg_voltage_pu": avg_voltage_pu,
            "voltage_violations": 0,  # Assume no violations in placeholder
            
            # Loading
            "max_line_loading_pct": max_line_loading_pct,
            "avg_line_loading_pct": avg_line_loading_pct,
            "overloaded_lines": 0,
            
            # Transformer
            "transformer_loading_pct": trafo_loading_pct,
            "transformer_overloaded": False,
            
            # Load & Losses
            "total_load_mw": round(total_load_mw, 4),
            "total_losses_mw": round(losses_mw, 4),
            "loss_percentage": 3.0,
            
            # Network
            "num_buses": self._num_buildings + 1,  # Buildings + MV bus
            "num_lines": self._num_buildings,
            "num_loads": self._num_buildings,
        }
    
    def get_voltage_violations(self, min_pu: float = 0.9, max_pu: float = 1.1) -> gpd.GeoDataFrame:
        """Return empty GeoDataFrame (no real results)."""
        return gpd.GeoDataFrame()
    
    def get_line_overloads(self, threshold_pct: float = 100.0) -> gpd.GeoDataFrame:
        """Return empty GeoDataFrame (no real results)."""
        return gpd.GeoDataFrame()
    
    def export_results(self, output_dir: Path, format: str = "geojson") -> Dict[str, Path]:
        """No real results to export."""
        return {}
    
    def get_network_summary(self) -> Dict[str, int]:
        """Return summary based on estimates."""
        return {
            "num_buses": self._num_buildings + 1,
            "num_lines": self._num_buildings,
            "num_loads": self._num_buildings,
            "num_transformers": 1,
            "num_ext_grids": 1,
        }

