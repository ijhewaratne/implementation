"""
Real Heat Pump Electrical Simulator using pandapower.

This module implements physics-based 3-phase electrical grid simulation
for heat pump scenarios using the pandapower library. It extends 
HPSimulatorInterface and provides realistic power flow calculations.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import json
import math
import pyproj

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString
from pyproj import Transformer

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False

from src.hp.lv_network import load_nodes_ways, nearest_node_id

from .base import (
    HPSimulatorInterface,
    SimulationResult,
    SimulationType,
    SimulationMode,
    HP_REQUIRED_KPIS,
)
from .exceptions import (
    NetworkCreationError,
    ConvergenceError,
    ValidationError,
    ConfigurationError,
)


class HeatPumpElectricalSimulator(HPSimulatorInterface):
    """
    Real pandapower-based 3-phase electrical grid simulator for heat pumps.
    
    This simulator creates a low-voltage electrical distribution network,
    adds heat pump loads to existing base loads, runs 3-phase power flow,
    and checks for constraint violations (voltage, line loading).
    
    Features:
    - MV/LV transformer modeling
    - 3-phase balanced or single-phase unbalanced loads
    - Voltage profile analysis
    - Line loading and overload detection
    - Grid loss calculation
    
    Example:
        >>> config = {"hp_thermal_kw": 6.0, "hp_cop": 2.8, "hp_three_phase": True}
        >>> simulator = HeatPumpElectricalSimulator(config)
        >>> simulator.validate_inputs(buildings_gdf)
        >>> simulator.create_network(buildings_gdf)
        >>> result = simulator.run_simulation()
        >>> print(result.kpi["min_voltage_pu"])
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize HP electrical simulator with configuration.
        
        Args:
            config: Configuration dictionary with keys:
                - hp_thermal_kw: Heat pump thermal power (kW)
                - hp_cop: Coefficient of performance
                - hp_three_phase: True for balanced 3-phase, False for single-phase
                - lv_voltage_kv: Low voltage level (default 0.4 kV)
                - mv_voltage_kv: Medium voltage level (default 20 kV)
                - voltage_min_pu: Minimum voltage limit (pu)
                - voltage_max_pu: Maximum voltage limit (pu)
        
        Raises:
            ConfigurationError: If pandapower not available
        """
        if not PANDAPOWER_AVAILABLE:
            raise ConfigurationError(
                "pandapower is required for HP simulations. "
                "Install with: pip install pandapower"
            )
        
        super().__init__(config)
        
        # Additional HP-specific config
        self.lv_voltage_kv = config.get("lv_voltage_kv", 0.4)
        self.mv_voltage_kv = config.get("mv_voltage_kv", 20.0)
        self.voltage_min_pu = config.get("voltage_min_pu", 0.90)
        self.voltage_max_pu = config.get("voltage_max_pu", 1.10)
        self.line_loading_max_pct = config.get("line_loading_max_pct", 100.0)
        
        # Storage for results
        self._simulation_metadata = {}
        self._input_buildings: Optional[gpd.GeoDataFrame] = None
    
    def set_hp_parameters(self, thermal_kw: float, cop: float, three_phase: bool) -> None:
        """Set heat pump electrical parameters."""
        if thermal_kw <= 0:
            raise ValueError(f"HP thermal power must be > 0, got {thermal_kw}")
        if cop <= 0:
            raise ValueError(f"HP COP must be > 0, got {cop}")
        
        self.hp_thermal_kw = thermal_kw
        self.hp_cop = cop
        self.hp_three_phase = three_phase
    
    def validate_inputs(self, buildings_gdf: gpd.GeoDataFrame, **kwargs) -> bool:
        """
        Validate building dataset before simulation.
        
        Extends the base validation with geometry cleaning and identifier checks.
        """
        if not super().validate_inputs(buildings_gdf, **kwargs):
            return False

        if buildings_gdf.geometry.isna().any():
            raise ValidationError("All buildings must include geometry.")

        valid_gdf = buildings_gdf[~buildings_gdf.geometry.is_empty].copy()
        if valid_gdf.empty:
            raise ValidationError("No buildings with valid geometry available.")

        if "GebaeudeID" not in valid_gdf.columns and "building_id" not in valid_gdf.columns:
            valid_gdf["GebaeudeID"] = [f"B{idx}" for idx in range(len(valid_gdf))]

        if (valid_gdf["heating_load_kw"] < 0).any():
            raise ValidationError("Heating loads must be non-negative.")

        # Ensure base load column exists (super() may have added default)
        if "base_electric_load_kw" not in valid_gdf.columns:
            default_base = kwargs.get("default_base_load_kw", 2.0)
            valid_gdf["base_electric_load_kw"] = default_base

        self._input_buildings = valid_gdf
        self._validated = True
        return True
    
    def create_network(self, buildings_gdf: gpd.GeoDataFrame, **kwargs) -> Any:
        """Create pandapower LV electrical network from buildings."""
        try:
            if buildings_gdf is None:
                if not self._validated or self._input_buildings is None:
                    raise ValidationError("No validated building dataset available.")
                buildings_gdf = self._input_buildings
            elif not self._validated or not buildings_gdf.equals(self._input_buildings):
                self.validate_inputs(buildings_gdf)
                buildings_gdf = self._input_buildings

            nodes_ways_path = kwargs.get("nodes_ways_path")
            nodes_data = kwargs.get("nodes_data")
            if buildings_gdf.crs is None:
                buildings_gdf = buildings_gdf.set_crs("EPSG:4326")
            projected_gdf, target_crs = self._to_projected(buildings_gdf)
            building_id_col = "GebaeudeID" if "GebaeudeID" in projected_gdf.columns else "building_id"

            nodes_tuple = None
            nodes_file_path = None
            if nodes_ways_path:
                nodes_file_path = Path(nodes_ways_path)
                nodes_tuple = load_nodes_ways(nodes_file_path)
            elif nodes_data:
                nodes_tuple = nodes_data

            if nodes_tuple:
                net, building_buses, trafo_bus, trafo_identifier = self._create_network_from_nodes(
                    projected_gdf,
                    nodes_tuple,
                    target_crs,
                    building_id_col,
                )
                network_mode = "branched"
            else:
                net, building_buses, trafo_bus, trafo_identifier = self._create_star_network(
                    projected_gdf,
                    building_id_col,
                )
                network_mode = "star"

            total_load_kw, hp_kw, loads_attached = self._attach_loads(
                net,
                projected_gdf,
                building_buses,
                building_id_col,
            )
            unmatched = len(projected_gdf) - loads_attached

            self.network = net
            metadata = {
                "num_buildings": len(projected_gdf),
                "transformer_location": trafo_identifier,
                "total_load_kw": total_load_kw,
                "hp_electrical_kw_per_building": hp_kw,
                "base_load_kw_avg": float(projected_gdf["base_electric_load_kw"].mean()),
                "network_construction": network_mode,
                "num_buses": int(len(net.bus)),
                "num_lines": int(len(net.line)),
                "loads_attached": loads_attached,
                "unmatched_buildings": unmatched,
                "transformer_bus_index": int(trafo_bus),
            }
            if nodes_tuple:
                metadata["nodes_file"] = str(nodes_file_path) if nodes_file_path else "in-memory"
                metadata["building_to_bus_count"] = loads_attached

            self._simulation_metadata = metadata

            if unmatched > 0:
                print(
                    f"  ⚠️  {unmatched} buildings could not be attached to the LV network and were skipped."
                )

            print(
                f"  Network created: {len(net.bus)} buses, {len(net.line)} lines, {loads_attached} loads"
            )
            print(
                f"  Total load: {total_load_kw:.1f} kW ({hp_kw:.1f} kW HP per building)"
            )

            return net
        except Exception as e:
            raise NetworkCreationError(f"Failed to create HP network: {e}") from e

    def _to_projected(self, gdf: gpd.GeoDataFrame) -> Tuple[gpd.GeoDataFrame, pyproj.CRS]:
        if gdf.crs.is_projected:
            return gdf, gdf.crs
        try:
            target_crs = gdf.estimate_utm_crs()
        except Exception:
            target_crs = pyproj.CRS("EPSG:32633")
        return gdf.to_crs(target_crs), target_crs

    def _create_star_network(
        self,
        buildings_gdf: gpd.GeoDataFrame,
        building_id_col: str,
    ) -> Tuple[pp.pandapowerNet, Dict[int, int], int, Any]:
        net = pp.create_empty_network()
        mv_bus = pp.create_bus(net, vn_kv=self.mv_voltage_kv, name="MV_bus")
        pp.create_ext_grid(net, bus=mv_bus, vm_pu=1.02, name="MV_slack", s_sc_max_mva=500.0, rx_max=0.1)

        building_buses: Dict[int, int] = {}
        geodata_records = []

        for idx, building in buildings_gdf.iterrows():
            centroid = building.geometry.centroid
            bus = pp.create_bus(
                net,
                vn_kv=self.lv_voltage_kv,
                name=f"LV_{building.get(building_id_col, idx)}",
            )
            building_buses[idx] = bus
            geodata_records.append({"bus": bus, "x": float(centroid.x), "y": float(centroid.y)})

        if geodata_records:
            net.bus_geodata = pd.DataFrame(geodata_records).set_index("bus")

        geom_union = (
            buildings_gdf.geometry.union_all()
            if hasattr(buildings_gdf.geometry, "union_all")
            else buildings_gdf.geometry.unary_union
        )
        centroid = geom_union.centroid
        distances = buildings_gdf.geometry.centroid.distance(centroid)
        trafo_building_idx = distances.idxmin()
        trafo_bus = building_buses[trafo_building_idx]
        trafo_building_id = buildings_gdf.loc[trafo_building_idx].get(building_id_col, trafo_building_idx)

        pp.create_transformer_from_parameters(
            net,
            hv_bus=mv_bus,
            lv_bus=trafo_bus,
            sn_mva=0.63,
            vn_hv_kv=self.mv_voltage_kv,
            vn_lv_kv=self.lv_voltage_kv,
            vk_percent=6.0,
            vkr_percent=0.5,
            pfe_kw=1.0,
            i0_percent=0.1,
            vector_group="Dyn",
            name="Trafo_1",
        )

        trafo_coords = buildings_gdf.loc[trafo_building_idx].geometry.centroid
        for idx, bus in building_buses.items():
            if idx == trafo_building_idx:
                continue
            building_coords = buildings_gdf.loc[idx].geometry.centroid
            length_km = math.hypot(building_coords.x - trafo_coords.x, building_coords.y - trafo_coords.y) / 1000.0
            length_km = max(length_km, 0.001)
            building_id = buildings_gdf.loc[idx].get(building_id_col, idx)
            pp.create_line_from_parameters(
                net,
                from_bus=trafo_bus,
                to_bus=bus,
                length_km=length_km,
                r_ohm_per_km=0.206,
                x_ohm_per_km=0.080,
                c_nf_per_km=210,
                max_i_ka=0.27,
                r0_ohm_per_km=0.206,
                x0_ohm_per_km=0.080,
                c0_nf_per_km=210,
                name=f"Cable_to_{building_id}",
            )

        return net, building_buses, trafo_bus, trafo_building_id

    def _create_network_from_nodes(
        self,
        buildings_gdf: gpd.GeoDataFrame,
        nodes_data: Tuple[Dict[int, Dict[str, Any]], List[Dict[str, Any]]],
        target_crs,
        building_id_col: str,
    ) -> Tuple[pp.pandapowerNet, Dict[int, int], int, Any]:
        id_to_node, ways = nodes_data
        transformer = Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)

        node_coords_proj: Dict[int, Tuple[float, float]] = {}
        for nid, node in id_to_node.items():
            try:
                lon = float(node["lon"])  # type: ignore[index]
                lat = float(node["lat"])  # type: ignore[index]
            except (KeyError, TypeError, ValueError):
                continue
            x, y = transformer.transform(lon, lat)
            node_coords_proj[nid] = (x, y)

        if not node_coords_proj:
            raise NetworkCreationError("Nodes data is empty or invalid.")

        net = pp.create_empty_network()
        mv_bus = pp.create_bus(net, vn_kv=self.mv_voltage_kv, name="MV_bus")
        pp.create_ext_grid(net, bus=mv_bus, vm_pu=1.02, name="MV_slack", s_sc_max_mva=500.0, rx_max=0.1)

        node_to_bus: Dict[int, int] = {}
        geodata_records = []
        for nid, (x, y) in node_coords_proj.items():
            bus = pp.create_bus(net, vn_kv=self.lv_voltage_kv, name=f"node_{nid}")
            node_to_bus[nid] = bus
            geodata_records.append({"bus": bus, "x": float(x), "y": float(y)})

        if geodata_records:
            net.bus_geodata = pd.DataFrame(geodata_records).set_index("bus")

        union_geom = (
            buildings_gdf.geometry.union_all()
            if hasattr(buildings_gdf.geometry, "union_all")
            else buildings_gdf.geometry.unary_union
        )
        building_centroid = union_geom.centroid

        trafo_node = min(
            node_coords_proj.keys(),
            key=lambda nid: math.hypot(
                node_coords_proj[nid][0] - building_centroid.x,
                node_coords_proj[nid][1] - building_centroid.y,
            ),
        )
        trafo_bus = node_to_bus[trafo_node]
        trafo_building_id = trafo_node

        pp.create_transformer_from_parameters(
            net,
            hv_bus=mv_bus,
            lv_bus=trafo_bus,
            sn_mva=0.63,
            vn_hv_kv=self.mv_voltage_kv,
            vn_lv_kv=self.lv_voltage_kv,
            vk_percent=6.0,
            vkr_percent=0.5,
            pfe_kw=1.0,
            i0_percent=0.1,
            vector_group="Dyn",
            name="Trafo_1",
        )

        seen_edges = set()
        for way in ways:
            tags = way.get("tags", {})
            if tags.get("power") not in {"line", "cable", "minor_line"}:
                continue
            nodes = way.get("nodes", [])
            for u, v in zip(nodes, nodes[1:]):
                if u not in node_to_bus or v not in node_to_bus:
                    continue
                edge = tuple(sorted((u, v)))
                if edge in seen_edges:
                    continue
                seen_edges.add(edge)
                x1, y1 = node_coords_proj[u]
                x2, y2 = node_coords_proj[v]
                length_km = math.hypot(x2 - x1, y2 - y1) / 1000.0
                length_km = max(length_km, 0.001)
                pp.create_line_from_parameters(
                    net,
                    from_bus=node_to_bus[u],
                    to_bus=node_to_bus[v],
                    length_km=length_km,
                    r_ohm_per_km=0.206,
                    x_ohm_per_km=0.080,
                    c_nf_per_km=210,
                    max_i_ka=0.27,
                    r0_ohm_per_km=0.206,
                    x0_ohm_per_km=0.080,
                    c0_nf_per_km=210,
                    name=f"edge_{u}_{v}",
                )

        building_buses: Dict[int, int] = {}
        for idx, building in buildings_gdf.iterrows():
            centroid = building.geometry.centroid
            best_node = min(
                node_coords_proj.keys(),
                key=lambda nid: math.hypot(
                    node_coords_proj[nid][0] - centroid.x,
                    node_coords_proj[nid][1] - centroid.y,
                ),
            )
            building_buses[idx] = node_to_bus[best_node]

        return net, building_buses, trafo_bus, trafo_building_id

    def _attach_loads(
        self,
        net: pp.pandapowerNet,
        buildings_gdf: gpd.GeoDataFrame,
        building_buses: Dict[int, int],
        building_id_col: str,
    ) -> Tuple[float, float, int]:
        hp_electrical_kw = self.hp_thermal_kw / self.hp_cop
        total_load_kw = 0.0
        loads_attached = 0

        for idx, building in buildings_gdf.iterrows():
            bus = building_buses.get(idx)
            if bus is None:
                continue

            base_load_kw = float(building.get("base_electric_load_kw", 2.0))
            total_building_load_kw = base_load_kw + hp_electrical_kw
            total_load_kw += total_building_load_kw

            name = f"Load_{building.get(building_id_col, idx)}"

            if self.hp_three_phase:
                pp.create_load(
                    net,
                    bus=bus,
                    p_mw=total_building_load_kw / 1000.0,
                    q_mvar=0.0,
                    name=name,
                )
            else:
                pp.create_asymmetric_load(
                    net,
                    bus=bus,
                    p_a_mw=total_building_load_kw / 1000.0,
                    p_b_mw=0.0,
                    p_c_mw=0.0,
                    q_a_mvar=0.0,
                    q_b_mvar=0.0,
                    q_c_mvar=0.0,
                    name=name,
                )

            loads_attached += 1

        return total_load_kw, hp_electrical_kw, loads_attached
 
    def run_simulation(self) -> SimulationResult:
        """
        Run pandapower 3-phase power flow simulation.
        
        Executes power flow calculation to determine:
        - Voltage magnitudes and angles at all buses
        - Power flows and losses in all lines
        - Transformer loading
        - System losses
        
        Returns:
            SimulationResult with success status, KPIs, and metadata
        
        Raises:
            ConvergenceError: If power flow fails to converge
        """
        if self.network is None:
            raise ValueError("Network not created. Call create_network() first.")
        
        self._start_timer()
        
        try:
            print("  Running pandapower power flow...")
            
            if self.hp_three_phase:
                # Standard power flow for balanced loads
                pp.runpp(self.network)
            else:
                # 3-phase power flow for unbalanced loads
                pp.runpp_3ph(self.network)
            
            print("  Power flow converged successfully!")
            
            # Extract KPIs
            kpis = self.extract_kpis()
            
            # Create result
            result = SimulationResult(
                success=True,
                scenario_name=self.config.get("scenario_name", "HP_scenario"),
                simulation_type=SimulationType.HEAT_PUMP,
                simulation_mode=SimulationMode.REAL,
                kpi=kpis,
                metadata={
                    **self._simulation_metadata,
                    "hp_thermal_kw": self.hp_thermal_kw,
                    "hp_cop": self.hp_cop,
                    "hp_three_phase": self.hp_three_phase,
                    "network_summary": self.get_network_summary(),
                },
                execution_time_s=self._get_execution_time()
            )
            
            # Add warnings for violations
            if kpis["voltage_violations"] > 0:
                result.add_warning(
                    f"{kpis['voltage_violations']} buses have voltage violations"
                )
            if kpis["overloaded_lines"] > 0:
                result.add_warning(
                    f"{kpis['overloaded_lines']} lines are overloaded"
                )
            if kpis["transformer_overloaded"]:
                result.add_warning("Transformer is overloaded!")
            
            return result
            
        except Exception as e:
            # Power flow failed
            error_msg = f"Pandapower power flow failed: {str(e)}"
            print(f"  ❌ {error_msg}")
            
            return SimulationResult(
                success=False,
                scenario_name=self.config.get("scenario_name", "HP_scenario"),
                simulation_type=SimulationType.HEAT_PUMP,
                simulation_mode=SimulationMode.REAL,
                kpi={},
                metadata=self._simulation_metadata,
                error=error_msg,
                execution_time_s=self._get_execution_time()
            )
    
    def extract_kpis(self) -> Dict[str, float]:
        """
        Extract all required KPIs from power flow results.
        
        Returns dictionary with all 13 required HP KPIs:
        - Voltage metrics (min/max/avg, violations)
        - Line loading metrics (max/avg, overloads)
        - Transformer metrics (loading, overloaded)
        - Load and loss metrics
        - Network metrics (element counts)
        
        Returns:
            Dictionary with all required KPI keys
        """
        net = self.network
        kpis = {}
        
        # --- Voltage Metrics ---
        bus_voltages = net.res_bus.vm_pu
        kpis["min_voltage_pu"] = bus_voltages.min()
        kpis["max_voltage_pu"] = bus_voltages.max()
        kpis["avg_voltage_pu"] = bus_voltages.mean()
        
        # Voltage violations (outside limits)
        violations = (
            (bus_voltages < self.voltage_min_pu) | 
            (bus_voltages > self.voltage_max_pu)
        )
        kpis["voltage_violations"] = int(violations.sum())
        
        # --- Line Loading Metrics ---
        if hasattr(net, 'res_line') and len(net.res_line) > 0:
            line_loadings = net.res_line.loading_percent
            kpis["max_line_loading_pct"] = line_loadings.max()
            kpis["avg_line_loading_pct"] = line_loadings.mean()
            kpis["overloaded_lines"] = int((line_loadings > self.line_loading_max_pct).sum())
        else:
            kpis["max_line_loading_pct"] = 0.0
            kpis["avg_line_loading_pct"] = 0.0
            kpis["overloaded_lines"] = 0
        
        # --- Transformer Metrics ---
        if hasattr(net, 'res_trafo') and len(net.res_trafo) > 0:
            trafo_loading = net.res_trafo.loading_percent.max()
            kpis["transformer_loading_pct"] = trafo_loading
            kpis["transformer_overloaded"] = bool(trafo_loading > 100.0)
        else:
            kpis["transformer_loading_pct"] = 0.0
            kpis["transformer_overloaded"] = False
        
        # --- Load and Loss Metrics ---
        # Total load (from bus results, excluding slack)
        kpis["total_load_mw"] = net.res_bus.p_mw.sum()
        
        # Losses
        line_losses = net.res_line.pl_mw.sum() if hasattr(net, 'res_line') else 0.0
        trafo_losses = net.res_trafo.pl_mw.sum() if hasattr(net, 'res_trafo') else 0.0
        kpis["total_losses_mw"] = line_losses + trafo_losses
        
        # Loss percentage
        if kpis["total_load_mw"] > 0:
            kpis["loss_percentage"] = (kpis["total_losses_mw"] / kpis["total_load_mw"]) * 100
        else:
            kpis["loss_percentage"] = 0.0
        
        # --- Network Metrics ---
        kpis["num_buses"] = len(net.bus)
        kpis["num_lines"] = len(net.line) if hasattr(net, 'line') else 0
        kpis["num_loads"] = len(net.load) if hasattr(net, 'load') else 0
        
        return kpis
    
    def get_voltage_violations(self, 
                               min_pu: float = 0.9, 
                               max_pu: float = 1.1) -> gpd.GeoDataFrame:
        """Get buses with voltage violations as GeoDataFrame."""
        if not hasattr(self.network, 'res_bus'):
            return gpd.GeoDataFrame()
        
        data = []
        for idx, bus in self.network.bus.iterrows():
            voltage_pu = self.network.res_bus.loc[idx, 'vm_pu']
            
            if voltage_pu < min_pu:
                violation_type = "undervoltage"
            elif voltage_pu > max_pu:
                violation_type = "overvoltage"
            else:
                continue  # No violation
            
            # Get coordinates
            if hasattr(self.network, 'bus_geodata') and idx in self.network.bus_geodata.index:
                geo = self.network.bus_geodata.loc[idx]
                geometry = Point(geo.x, geo.y)
            else:
                continue
            
            data.append({
                "bus_id": idx,
                "voltage_pu": voltage_pu,
                "violation_type": violation_type,
                "geometry": geometry
            })
        
        if data:
            return gpd.GeoDataFrame(data, crs="EPSG:25833")  # Adjust CRS as needed
        else:
            return gpd.GeoDataFrame()
    
    def get_line_overloads(self, threshold_pct: float = 100.0) -> gpd.GeoDataFrame:
        """Get overloaded lines as GeoDataFrame."""
        if not hasattr(self.network, 'res_line'):
            return gpd.GeoDataFrame()
        
        data = []
        for idx, line in self.network.line.iterrows():
            loading_pct = self.network.res_line.loc[idx, 'loading_percent']
            
            if loading_pct <= threshold_pct:
                continue  # No overload
            
            # Get line geometry from bus coordinates
            from_bus = line.from_bus
            to_bus = line.to_bus
            
            if (hasattr(self.network, 'bus_geodata') and 
                from_bus in self.network.bus_geodata.index and
                to_bus in self.network.bus_geodata.index):
                
                from_geo = self.network.bus_geodata.loc[from_bus]
                to_geo = self.network.bus_geodata.loc[to_bus]
                geometry = LineString([
                    (from_geo.x, from_geo.y),
                    (to_geo.x, to_geo.y)
                ])
            else:
                continue
            
            # Get current
            i_ka = self.network.res_line.loc[idx, 'i_ka']
            max_i_ka = line.get('max_i_ka', 0.0)
            
            data.append({
                "line_id": idx,
                "loading_pct": loading_pct,
                "current_i_ka": i_ka,
                "max_i_ka": max_i_ka,
                "geometry": geometry
            })
        
        if data:
            return gpd.GeoDataFrame(data, crs="EPSG:25833")
        else:
            return gpd.GeoDataFrame()
    
    def export_results(
        self,
        output_dir: Path,
        format: str = "geojson",
        *,
        prefix: Optional[str] = None,
        kpi_summary: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Path]:
        """Export simulation results to files."""
        if self.network is None:
            return {}

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exported_files: Dict[str, Path] = {}
        scenario_slug = self.config.get("scenario_name", "hp_scenario")
        default_slug = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in scenario_slug).strip("_")
        base_name = prefix.strip() if prefix else default_slug or "hp_scenario"
        safe_name = base_name.replace("/", "_").replace(" ", "_")

        if format.lower() != "geojson":
            return exported_files

        net = self.network

        load_kw_by_bus: Dict[int, float] = {}
        if hasattr(net, "load") and len(net.load) > 0:
            res_table = getattr(net, "res_load", None)
            for load_idx, load_row in net.load.iterrows():
                bus_id = int(load_row.bus)
                p_mw = 0.0
                if res_table is not None and load_idx in res_table.index:
                    p_mw = float(res_table.loc[load_idx, "p_mw"])
                elif hasattr(load_row, "p_mw"):
                    p_mw = float(load_row.p_mw)
                load_kw_by_bus[bus_id] = load_kw_by_bus.get(bus_id, 0.0) + abs(p_mw) * 1000.0
        if hasattr(net, "asymmetric_load") and len(net.asymmetric_load) > 0:
            res_asym = getattr(net, "res_asymmetric_load", None)
            res_asym_3ph = getattr(net, "res_asymmetric_load_3ph", None)
            for load_idx, load_row in net.asymmetric_load.iterrows():
                bus_id = int(load_row.bus)
                p_total_mw = 0.0
                if res_asym is not None and load_idx in res_asym.index:
                    row = res_asym.loc[load_idx]
                    p_total_mw = float(row.get("p_a_mw", 0.0)) + float(row.get("p_b_mw", 0.0)) + float(row.get("p_c_mw", 0.0))
                elif res_asym_3ph is not None and load_idx in res_asym_3ph.index:
                    row = res_asym_3ph.loc[load_idx]
                    p_total_mw = (
                        float(row.get("p_a_mw", 0.0))
                        + float(row.get("p_b_mw", 0.0))
                        + float(row.get("p_c_mw", 0.0))
                    )
                load_kw_by_bus[bus_id] = load_kw_by_bus.get(bus_id, 0.0) + abs(p_total_mw) * 1000.0

        transformer_bus_idx = self._simulation_metadata.get("transformer_bus_index")

        def classify_voltage(value: float) -> str:
            if value < 0.92 or value > 1.08:
                return "critical"
            if value < 0.95 or value > 1.05:
                return "warning"
            return "normal"

        def classify_loading(value: float) -> str:
            if value >= 120.0:
                return "critical"
            if value >= 100.0:
                return "warning"
            return "normal"

        # Export buses GeoJSON
        buses_features = []
        if hasattr(net, "bus_geodata") and len(net.bus_geodata) > 0:
            for idx, bus in net.bus.iterrows():
                if idx not in net.bus_geodata.index:
                    continue

                geo = net.bus_geodata.loc[idx]
                voltage = 0.0
                if hasattr(net, "res_bus_3ph") and idx in net.res_bus_3ph.index:
                    res = net.res_bus_3ph.loc[idx]
                    voltage = float(min(res.get("vm_a_pu", 0), res.get("vm_b_pu", 0), res.get("vm_c_pu", 0)))
                elif hasattr(net, "res_bus") and idx in net.res_bus.index:
                    voltage = float(net.res_bus.loc[idx, "vm_pu"])

                load_kw = load_kw_by_bus.get(int(idx), 0.0)
                properties = {
                    "id": int(idx),
                    "name": str(bus.get("name", f"bus{idx}")),
                    "voltage_pu": voltage,
                    "voltage_kv": float(getattr(bus, "vn_kv", bus.get("vn_kv", 0.4))),
                    "load_kw": load_kw,
                    "has_load": load_kw > 1e-3,
                    "voltage_status": classify_voltage(voltage) if voltage else "unknown",
                }
                if transformer_bus_idx is not None and int(idx) == int(transformer_bus_idx):
                    properties["is_transformer"] = True
                feature = {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [float(geo.x), float(geo.y)]},
                    "properties": properties,
                }
                buses_features.append(feature)

        if buses_features:
            buses_file = output_dir / f"{safe_name}_buses_results.geojson"
            with buses_file.open("w", encoding="utf-8") as f:
                json.dump({"type": "FeatureCollection", "features": buses_features}, f, indent=2)
            exported_files["buses_results"] = buses_file
            print(f"  Exported: {buses_file}")

        # Export lines GeoJSON
        line_features = []
        if hasattr(net, "line") and len(net.line) > 0 and hasattr(net, "bus_geodata"):
            for idx, line in net.line.iterrows():
                from_bus = int(line.from_bus)
                to_bus = int(line.to_bus)
                if (
                    from_bus not in net.bus_geodata.index
                    or to_bus not in net.bus_geodata.index
                ):
                    continue

                from_geo = net.bus_geodata.loc[from_bus]
                to_geo = net.bus_geodata.loc[to_bus]

                if hasattr(net, "res_line") and idx in net.res_line.index:
                    loading_pct = float(net.res_line.loc[idx, "loading_percent"])
                    current_i_ka = float(net.res_line.loc[idx, "i_ka"])
                elif hasattr(net, "res_line_3ph") and idx in net.res_line_3ph.index:
                    res_line = net.res_line_3ph.loc[idx]
                    currents = [float(res_line.get(col, 0.0)) for col in ("i_a_ka", "i_b_ka", "i_c_ka")]
                    current_i_ka = max(currents) if currents else 0.0
                    max_i_ka = float(line.get("max_i_ka", 0.0)) or 0.0
                    loading_pct = (
                        (current_i_ka / max_i_ka) * 100.0 if max_i_ka > 0 else 0.0
                    )
                else:
                    loading_pct = 0.0
                    current_i_ka = 0.0

                status = "normal"
                if from_bus == transformer_bus_idx or to_bus == transformer_bus_idx:
                    status = "transformer"
                elif from_bus in load_kw_by_bus or to_bus in load_kw_by_bus:
                    status = "load"

                length_km = float(line.get("length_km", 0.0))
                loading_status = classify_loading(loading_pct)
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [float(from_geo.x), float(from_geo.y)],
                            [float(to_geo.x), float(to_geo.y)],
                        ],
                    },
                    "properties": {
                        "id": int(idx),
                        "name": str(line.get("name", f"line{idx}")),
                        "length_km": length_km,
                        "length_m": length_km * 1000.0,
                        "loading_pct": float(loading_pct),
                        "loading_status": loading_status,
                        "current_i_ka": current_i_ka,
                        "max_i_ka": float(line.get("max_i_ka", 0.0)),
                    },
                }
                line_features.append(feature)

        if line_features:
            lines_file = output_dir / f"{safe_name}_lines_results.geojson"
            with lines_file.open("w", encoding="utf-8") as f:
                json.dump({"type": "FeatureCollection", "features": line_features}, f, indent=2)
            exported_files["lines_results"] = lines_file
            print(f"  Exported: {lines_file}")

        # Export violations CSV
        voltage_violations = self.get_voltage_violations(
            min_pu=self.voltage_min_pu, max_pu=self.voltage_max_pu
        )
        line_overloads = self.get_line_overloads(threshold_pct=self.line_loading_max_pct)

        violation_rows = []
        for _, row in voltage_violations.iterrows():
            violation_rows.append(
                {
                    "type": row.get("violation_type", "voltage"),
                    "element": f"bus_{row.get('bus_id')}",
                    "value": f"{row.get('voltage_pu', 0):.3f} pu",
                    "limit": f"{self.voltage_min_pu:.3f}-{self.voltage_max_pu:.3f} pu",
                    "severity": "critical"
                    if row.get("voltage_pu", 0) < self.voltage_min_pu - 0.05
                    else "warning",
                }
            )

        for _, row in line_overloads.iterrows():
            violation_rows.append(
                {
                    "type": "line_overload",
                    "element": f"line_{row.get('line_id')}",
                    "value": f"{row.get('loading_pct', 0):.1f}%",
                    "limit": f"{self.line_loading_max_pct:.1f}%",
                    "severity": "critical"
                    if row.get("loading_pct", 0) > self.line_loading_max_pct + 20
                    else "warning",
                }
            )

        if violation_rows:
            import csv

            violations_file = output_dir / f"{safe_name}_violations.csv"
            with violations_file.open("w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(
                    csvfile, fieldnames=["type", "element", "value", "limit", "severity"]
                )
                writer.writeheader()
                writer.writerows(violation_rows)
            exported_files["violations"] = violations_file
            print(f"  Exported: {violations_file}")

        if kpi_summary:
            kpi_file = output_dir / f"{safe_name}_kpis.json"
            with kpi_file.open("w", encoding="utf-8") as f:
                json.dump(kpi_summary, f, indent=2)
            exported_files["kpis"] = kpi_file
            print(f"  Exported: {kpi_file}")

        return exported_files
    
    def get_network_summary(self) -> Dict[str, int]:
        """Get summary statistics of the network."""
        if self.network is None:
            return {}
        
        return {
            "num_buses": len(self.network.bus),
            "num_lines": len(self.network.line) if hasattr(self.network, 'line') else 0,
            "num_loads": len(self.network.load) if hasattr(self.network, 'load') else 0,
            "num_transformers": len(self.network.trafo) if hasattr(self.network, 'trafo') else 0,
            "num_ext_grids": len(self.network.ext_grid) if hasattr(self.network, 'ext_grid') else 0,
        }

