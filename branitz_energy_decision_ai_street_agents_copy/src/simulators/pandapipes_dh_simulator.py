"""
Real District Heating Simulator using pandapipes.

This module implements physics-based district heating network simulation
using the pandapipes library. It extends DHSimulatorInterface and provides
realistic hydraulic and thermal calculations.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json

import geopandas as gpd
from shapely.geometry import Point, LineString

try:
    import pandapipes as pp
    PANDAPIPES_AVAILABLE = True
except ImportError:
    PANDAPIPES_AVAILABLE = False

from .base import (
    DHSimulatorInterface,
    SimulationResult,
    SimulationType,
    SimulationMode,
    DH_REQUIRED_KPIS,
)
from .exceptions import (
    NetworkCreationError,
    ConvergenceError,
    ValidationError,
    ConfigurationError,
)

# Import advanced routing (Phase 8.1)
try:
    from ..routing import (
        create_street_network_with_virtual_nodes,
        find_shortest_paths_from_plant,
        analyze_routing_results,
        transform_plant_coordinates,
        build_dual_pipe_topology,
    )
    ADVANCED_ROUTING_AVAILABLE = True
except ImportError:
    ADVANCED_ROUTING_AVAILABLE = False
    print("Warning: Advanced routing not available. Using basic radial topology.")


class DistrictHeatingSimulator(DHSimulatorInterface):
    """
    Real pandapipes-based district heating simulator.
    
    This simulator creates a radial district heating network topology,
    runs coupled hydraulic-thermal simulations, and extracts detailed
    performance indicators.
    
    Features:
    - Realistic pipe sizing based on flow requirements
    - Separate supply and return circuits
    - Heat exchangers for building connections
    - Pressure drop and temperature loss calculations
    - Pump energy estimation
    
    Example:
        >>> config = {"supply_temp_c": 85, "return_temp_c": 55}
        >>> simulator = DistrictHeatingSimulator(config)
        >>> simulator.validate_inputs(buildings_gdf)
        >>> simulator.create_network(buildings_gdf)
        >>> result = simulator.run_simulation()
        >>> print(result.kpi["total_heat_supplied_mwh"])
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize DH simulator with configuration.
        
        Args:
            config: Configuration dictionary with keys:
                - supply_temp_c: Supply temperature (°C)
                - return_temp_c: Return temperature (°C)
                - default_diameter_m: Default pipe diameter (m)
                - pipe_roughness_mm: Pipe roughness (mm)
                - supply_pressure_bar: Plant supply pressure (bar)
        
        Raises:
            ConfigurationError: If pandapipes not available
        """
        if not PANDAPIPES_AVAILABLE:
            raise ConfigurationError(
                "pandapipes is required for DH simulations. "
                "Install with: pip install pandapipes"
            )
        
        super().__init__(config)
        
        # Additional DH-specific config
        self.default_diameter_m = config.get("default_diameter_m", 0.065)
        self.pipe_roughness_mm = config.get("pipe_roughness_mm", 0.1)
        self.supply_pressure_bar = config.get("supply_pressure_bar", 6.0)
        self.topology = config.get("topology", "radial")
        
        # Storage for results
        self._simulation_metadata = {}
    
    def set_supply_temperature(self, temp_c: float) -> None:
        """Set supply temperature in Celsius."""
        if not 60 <= temp_c <= 120:
            raise ValueError(f"Supply temperature {temp_c}°C out of range [60, 120]°C")
        if temp_c <= self.return_temp_c:
            raise ValueError(
                f"Supply temp ({temp_c}°C) must be > return temp ({self.return_temp_c}°C)"
            )
        self.supply_temp_c = temp_c
    
    def set_return_temperature(self, temp_c: float) -> None:
        """Set return temperature in Celsius."""
        if not 30 <= temp_c <= 70:
            raise ValueError(f"Return temperature {temp_c}°C out of range [30, 70]°C")
        if temp_c >= self.supply_temp_c:
            raise ValueError(
                f"Return temp ({temp_c}°C) must be < supply temp ({self.supply_temp_c}°C)"
            )
        self.return_temp_c = temp_c
    
    def create_network(self, buildings_gdf: gpd.GeoDataFrame, **kwargs) -> Any:
        """
        Create pandapipes district heating network from buildings.
        
        Network topology:
        - Radial design with central heat plant
        - Supply and return circuits modeled separately
        - Heat exchangers at each consumer building
        - External grid at plant for boundary conditions
        - Sink at end of return circuit for mass flow
        
        Args:
            buildings_gdf: GeoDataFrame with columns:
                - geometry: Building footprints (Polygon or Point)
                - heating_load_kw: Heating demand (kW)
                - GebaeudeID or building_id: Building identifier
            **kwargs: Additional options (topology preference, etc.)
        
        Returns:
            pandapipes.Net object ready for simulation
        
        Raises:
            NetworkCreationError: If network creation fails
        """
        try:
            # Ensure projected CRS for accurate distances
            if buildings_gdf.crs.is_geographic:
                print("  Converting to projected CRS...")
                buildings_gdf = buildings_gdf.to_crs(buildings_gdf.estimate_utm_crs())
            
            # Create empty network
            net = pp.create_empty_network(fluid="water")
            
            # Calculate total demand
            total_demand_kw = buildings_gdf["heating_load_kw"].sum()
            print(f"  Total heat demand: {total_demand_kw:.1f} kW")
            
            # Select heat source (building closest to centroid)
            centroid = buildings_gdf.geometry.unary_union.centroid
            distances = buildings_gdf.geometry.centroid.distance(centroid)
            source_idx = distances.idxmin()
            source_building = buildings_gdf.loc[source_idx]
            
            building_id_col = "GebaeudeID" if "GebaeudeID" in buildings_gdf.columns else "building_id"
            source_id = source_building.get(building_id_col, source_idx)
            print(f"  Selected heat source: Building {source_id}")
            
            # Temperature in Kelvin
            supply_temp_k = self.supply_temp_c + 273.15
            return_temp_k = self.return_temp_c + 273.15
            
            # Create plant junctions
            source_coords = source_building.geometry.centroid
            
            plant_supply = pp.create_junction(
                net,
                pn_bar=self.supply_pressure_bar,
                tfluid_k=supply_temp_k,
                geodata=(source_coords.x, source_coords.y),
                name="plant_supply"
            )
            
            plant_return = pp.create_junction(
                net,
                pn_bar=self.supply_pressure_bar - 0.5,  # Slightly lower
                tfluid_k=return_temp_k,
                geodata=(source_coords.x, source_coords.y),
                name="plant_return"
            )
            
            # Add external grid (pressure & temperature boundary)
            pp.create_ext_grid(
                net,
                junction=plant_supply,
                p_bar=self.supply_pressure_bar,
                t_k=supply_temp_k,
                name="plant_ext_grid"
            )
            
            # Connect consumer buildings
            consumers = buildings_gdf[buildings_gdf.index != source_idx].copy()
            # Sort by demand (largest first for better hydraulics)
            consumers = consumers.sort_values("heating_load_kw", ascending=False)
            
            current_supply = plant_supply
            current_return = plant_return
            
            for idx, building in consumers.iterrows():
                building_id = building.get(building_id_col, idx)
                coords = building.geometry.centroid
                
                # Create supply and return junctions for this building
                bldg_supply = pp.create_junction(
                    net,
                    pn_bar=self.supply_pressure_bar,
                    tfluid_k=supply_temp_k,
                    geodata=(coords.x, coords.y),
                    name=f"supply_{building_id}"
                )
                
                bldg_return = pp.create_junction(
                    net,
                    pn_bar=self.supply_pressure_bar - 0.5,
                    tfluid_k=return_temp_k,
                    geodata=(coords.x, coords.y),
                    name=f"return_{building_id}"
                )
                
                # Calculate pipe length
                prev_supply_geo = net.junction_geodata.loc[current_supply]
                prev_return_geo = net.junction_geodata.loc[current_return]
                
                distance_supply_m = coords.distance(
                    Point(prev_supply_geo["x"], prev_supply_geo["y"])
                )
                distance_return_m = coords.distance(
                    Point(prev_return_geo["x"], prev_return_geo["y"])
                )
                
                # Create supply pipe
                pp.create_pipe_from_parameters(
                    net,
                    from_junction=current_supply,
                    to_junction=bldg_supply,
                    length_km=distance_supply_m / 1000,
                    diameter_m=self.default_diameter_m,
                    k_mm=self.pipe_roughness_mm,
                    name=f"pipe_supply_{building_id}"
                )
                
                # Create return pipe
                pp.create_pipe_from_parameters(
                    net,
                    from_junction=bldg_return,
                    to_junction=current_return,
                    length_km=distance_return_m / 1000,
                    diameter_m=self.default_diameter_m,
                    k_mm=self.pipe_roughness_mm,
                    name=f"pipe_return_{building_id}"
                )
                
                # Add heat exchanger
                heat_demand_w = building["heating_load_kw"] * 1000
                pp.create_heat_exchanger(
                    net,
                    from_junction=bldg_supply,
                    to_junction=bldg_return,
                    diameter_m=0.1,
                    qext_w=-heat_demand_w,  # Negative = heat extraction
                    name=f"he_{building_id}"
                )
                
                # Update current junctions for next building
                current_supply = bldg_supply
                current_return = bldg_return
            
            # Add sink at end of return line (mass flow boundary)
            delta_t_k = supply_temp_k - return_temp_k
            cp_water = 4186  # J/(kg·K)
            total_demand_w = total_demand_kw * 1000
            mdot_kg_per_s = total_demand_w / (cp_water * delta_t_k)
            
            pp.create_sink(
                net,
                junction=current_return,
                mdot_kg_per_s=mdot_kg_per_s,
                name="system_sink"
            )
            
            self.network = net
            
            # Store metadata
            self._simulation_metadata = {
                "num_consumers": len(consumers),
                "heat_source_building": source_id,
                "total_demand_kw": total_demand_kw,
                "mass_flow_kg_s": mdot_kg_per_s,
                "delta_t_k": delta_t_k,
            }
            
            print(f"  Network created: {len(net.junction)} junctions, "
                  f"{len(net.pipe)} pipes, {len(net.heat_exchanger)} heat exchangers")
            
            return net
            
        except Exception as e:
            raise NetworkCreationError(f"Failed to create DH network: {e}") from e
    
    def create_network_with_advanced_routing(
        self, 
        buildings_gdf: gpd.GeoDataFrame,
        streets_gdf: gpd.GeoDataFrame,
        plant_location: Optional[Dict] = None,
        **kwargs
    ) -> Any:
        """
        Create DH network using advanced shortest path routing.
        
        Uses advanced routing algorithms from street_final_copy_3 to create
        optimized network topology that follows street geometries.
        
        Args:
            buildings_gdf: GeoDataFrame with building data
            streets_gdf: GeoDataFrame with street geometries
            plant_location: Optional plant location dict with 'x', 'y' coordinates
            **kwargs: Additional routing options
                - max_snapping_distance: Maximum distance for building-to-street snapping (m)
                - use_virtual_nodes: Whether to use virtual nodes (default: True)
        
        Returns:
            pandapipes.Net object with optimized topology
            
        Raises:
            NetworkCreationError: If routing fails
        """
        if not ADVANCED_ROUTING_AVAILABLE:
            print("⚠️  Advanced routing not available. Falling back to radial topology.")
            return self.create_network(buildings_gdf, **kwargs)
        
        print("🔗 Creating DH network with advanced shortest path routing...")
        
        try:
            import pandas as pd

            # Ensure projected CRS
            if buildings_gdf.crs.is_geographic:
                print("  Converting to projected CRS...")
                buildings_gdf = buildings_gdf.to_crs(buildings_gdf.estimate_utm_crs())
            
            if streets_gdf.crs != buildings_gdf.crs:
                streets_gdf = streets_gdf.to_crs(buildings_gdf.crs)
            
            # Get plant location (use default if not provided)
            if plant_location is None:
                plant_x, plant_y = transform_plant_coordinates()
                plant_connection = {"plant_x": plant_x, "plant_y": plant_y}
            else:
                plant_connection = {
                    "plant_x": plant_location.get('x', plant_location.get('plant_x')),
                    "plant_y": plant_location.get('y', plant_location.get('plant_y'))
                }
            
            # Prepare building connections DataFrame
            building_id_col = "GebaeudeID" if "GebaeudeID" in buildings_gdf.columns else "building_id"
            
            connections_data = []
            for idx, building in buildings_gdf.iterrows():
                building_id = building.get(building_id_col, idx)
                centroid = building.geometry.centroid
                
                # Find nearest street point
                street_union = streets_gdf.geometry.union_all()
                nearest_geom = streets_gdf.geometry.nearest(centroid)
                nearest_street = streets_gdf.loc[nearest_geom.idxmin()]
                nearest_point_on_street = nearest_street.geometry.interpolate(
                    nearest_street.geometry.project(centroid)
                )
                
                distance_to_street = centroid.distance(nearest_point_on_street)
                
                connections_data.append({
                    "building_id": building_id,
                    "building_x": centroid.x,
                    "building_y": centroid.y,
                    "connection_point_x": nearest_point_on_street.x,
                    "connection_point_y": nearest_point_on_street.y,
                    "distance_to_street": distance_to_street,
                    "heating_load_kw": building["heating_load_kw"]
                })
            
            connections_df = pd.DataFrame(connections_data)
            
            print(f"  Prepared {len(connections_df)} building connections")
            
            # Create street network with virtual nodes
            G, virtual_nodes = create_street_network_with_virtual_nodes(
                streets_gdf,
                connections_df,
                plant_connection
            )
            
            # Find shortest paths from plant to all buildings
            paths = find_shortest_paths_from_plant(G, plant_node="PLANT")
            
            # Analyze routing
            analysis = analyze_routing_results(paths, connections_df)
            
            dual_topology = build_dual_pipe_topology(
                buildings_gdf=buildings_gdf,
                streets_gdf=streets_gdf,
                plant_connection=plant_connection,
                supply_temp=self.supply_temp_c,
                return_temp=self.return_temp_c,
                supply_pressure=self.supply_pressure_bar,
                analysis=analysis,
                connections_df=connections_df,
            )

            # Store routing information for later use
            self._routing_analysis = analysis
            self._routing_paths = paths
            self._routing_graph = G

            net = self._create_network_from_dual_topology(dual_topology)

            net.routing_metadata = {
                "analysis": analysis,
                "paths": paths,
                "virtual_nodes": virtual_nodes,
                "dual_topology": dual_topology,
            }

            self._dual_pipe_topology = dual_topology
            self.network = net
            return net
            
        except Exception as e:
            print(f"⚠️  Advanced routing failed: {e}")
            print("  Falling back to radial topology...")
            return self.create_network(buildings_gdf, **kwargs)

    def _create_network_from_dual_topology(self, topology: Dict[str, Any]):
        if not topology["junctions"]:
            raise NetworkCreationError("Dual topology contains no junctions")

        net = pp.create_empty_network(fluid="water")

        supply_temp_k = self.supply_temp_c + 273.15
        return_temp_k = self.return_temp_c + 273.15

        junction_map: Dict[int, Dict[str, Any]] = {}

        for junction in topology["junctions"]:
            coords = (junction["x"], junction["y"])
            if junction["type"] == "plant":
                supply_idx = pp.create_junction(
                    net,
                    pn_bar=self.supply_pressure_bar,
                    tfluid_k=supply_temp_k,
                    geodata=coords,
                    name="plant_supply",
                )
                return_idx = pp.create_junction(
                    net,
                    pn_bar=self.supply_pressure_bar - 0.5,
                    tfluid_k=return_temp_k,
                    geodata=coords,
                    name="plant_return",
                )
            else:
                supply_idx = pp.create_junction(
                    net,
                    pn_bar=self.supply_pressure_bar,
                    tfluid_k=supply_temp_k,
                    geodata=coords,
                    name=f"supply_{junction['id']}",
                )
                return_idx = pp.create_junction(
                    net,
                    pn_bar=self.supply_pressure_bar - 0.5,
                    tfluid_k=return_temp_k,
                    geodata=coords,
                    name=f"return_{junction['id']}",
                )

            junction_map[junction["id"]] = {
                "data": junction,
                "supply": supply_idx,
                "return": return_idx,
            }

        # Boundary conditions
        plant_supply_idx = junction_map[0]["supply"]
        plant_return_idx = junction_map[0]["return"]

        pp.create_ext_grid(
            net,
            junction=plant_supply_idx,
            p_bar=self.supply_pressure_bar,
            t_k=supply_temp_k,
            name="plant_ext_grid",
        )

        # Create pipes
        for pipe in topology["pipes"]:
            coords = pipe["coords"]
            line = LineString(coords)
            length_km = max(line.length / 1000.0, 1e-6)

            from_map = junction_map[pipe["from_junction"]]
            to_map = junction_map[pipe["to_junction"]]

            if pipe.get("type") == "return":
                from_idx = from_map["return"]
                to_idx = to_map["return"]
            else:
                from_idx = from_map["supply"]
                to_idx = to_map["supply"]

            diameter_m = pipe.get("diameter_m", self.default_diameter_m)

            pp.create_pipe_from_parameters(
                net,
                from_junction=from_idx,
                to_junction=to_idx,
                length_km=length_km,
                diameter_m=diameter_m,
                k_mm=self.pipe_roughness_mm,
                name=pipe["id"],
                geodata=coords,
            )

        total_demand_kw = 0.0
        for consumer in topology["consumers"]:
            heat_kw = float(consumer.get("heat_demand_kw", 0.0) or 0.0)
            total_demand_kw += heat_kw
            supply_idx = junction_map[consumer["junction_id"]]["supply"]
            return_idx = junction_map[consumer["junction_id"]]["return"]

            pp.create_heat_exchanger(
                net,
                from_junction=supply_idx,
                to_junction=return_idx,
                diameter_m=0.1,
                qext_w=-heat_kw * 1000,
                name=consumer["name"],
            )

        delta_t_k = supply_temp_k - return_temp_k
        cp_water = 4186  # J/(kg·K)
        total_demand_w = total_demand_kw * 1000
        if total_demand_w > 0 and delta_t_k > 0:
            mdot_kg_per_s = total_demand_w / (cp_water * delta_t_k)
        else:
            mdot_kg_per_s = 0.0

        pp.create_sink(
            net,
            junction=plant_return_idx,
            mdot_kg_per_s=mdot_kg_per_s,
            name="system_sink",
        )

        self._simulation_metadata = {
            "num_consumers": len(topology["consumers"]),
            "heat_source_building": topology["plant"].get("name", "CHP_Plant"),
            "total_demand_kw": total_demand_kw,
            "mass_flow_kg_s": mdot_kg_per_s,
            "delta_t_k": delta_t_k,
            "dual_pipe_stats": topology.get("stats", {}),
        }

        return net
    
    def run_simulation(self) -> SimulationResult:
        """
        Run pandapipes hydraulic and thermal simulation.
        
        Executes coupled hydraulic-thermal calculation to determine:
        - Pressure distribution throughout network
        - Temperature losses along pipes
        - Flow rates in each pipe segment
        - Heat exchanger performance
        
        Returns:
            SimulationResult with success status, KPIs, and metadata
        
        Raises:
            ConvergenceError: If simulation fails to converge
        """
        if self.network is None:
            raise ValueError("Network not created. Call create_network() first.")
        
        self._start_timer()
        
        try:
            print("  Running pandapipes simulation (hydraulic + thermal)...")
            pp.pipeflow(self.network, mode="all")
            
            print("  Simulation converged successfully!")
            
            # Extract KPIs
            kpis = self.extract_kpis()
            
            # Create result
            result = SimulationResult(
                success=True,
                scenario_name=self.config.get("scenario_name", "DH_scenario"),
                simulation_type=SimulationType.DISTRICT_HEATING,
                simulation_mode=SimulationMode.REAL,
                kpi=kpis,
                metadata={
                    **self._simulation_metadata,
                    "supply_temp_c": self.supply_temp_c,
                    "return_temp_c": self.return_temp_c,
                    "network_summary": self.get_network_summary(),
                },
                execution_time_s=self._get_execution_time()
            )
            
            return result
            
        except Exception as e:
            # Simulation failed
            error_msg = f"Pandapipes simulation failed: {str(e)}"
            print(f"  ❌ {error_msg}")
            
            # Return failure result
            return SimulationResult(
                success=False,
                scenario_name=self.config.get("scenario_name", "DH_scenario"),
                simulation_type=SimulationType.DISTRICT_HEATING,
                simulation_mode=SimulationMode.REAL,
                kpi={},
                metadata=self._simulation_metadata,
                error=error_msg,
                execution_time_s=self._get_execution_time()
            )
    
    def extract_kpis(self) -> Dict[str, float]:
        """
        Extract all required KPIs from simulation results.
        
        Returns dictionary with all 12 required DH KPIs:
        - Heat supply metrics
        - Hydraulic metrics (pressures, pump energy)
        - Thermal metrics (temperatures, losses)
        - Network metrics (element counts, lengths)
        
        Returns:
            Dictionary with all required KPI keys
        """
        net = self.network
        kpis = {}
        
        # --- Heat Supply Metrics ---
        if hasattr(net, 'res_heat_exchanger') and 'qext_w' in net.res_heat_exchanger.columns:
            # Total heat supplied (assuming 1 hour operation)
            total_heat_w = -net.res_heat_exchanger["qext_w"].sum()
            kpis["total_heat_supplied_mwh"] = total_heat_w / 1e6
            
            # Peak heat load
            peak_heat_w = -net.res_heat_exchanger["qext_w"].max()
            kpis["peak_heat_load_kw"] = peak_heat_w / 1000
        else:
            kpis["total_heat_supplied_mwh"] = 0.0
            kpis["peak_heat_load_kw"] = 0.0
        
        # --- Hydraulic Metrics ---
        if hasattr(net, 'res_pipe') and len(net.res_pipe) > 0:
            # Pressure drops
            pressure_drops = (net.res_pipe.p_from_bar - net.res_pipe.p_to_bar).abs()
            kpis["max_pressure_drop_bar"] = pressure_drops.max()
            kpis["avg_pressure_drop_bar"] = pressure_drops.mean()
        else:
            kpis["max_pressure_drop_bar"] = 0.0
            kpis["avg_pressure_drop_bar"] = 0.0
        
        # Pump energy (estimate if no explicit pumps)
        if hasattr(net, 'res_circ_pump_pressure') and len(net.res_circ_pump_pressure) > 0:
            # Real pumps present
            pump_power_w = 0.0
            for idx in net.res_circ_pump_pressure.index:
                mdot = net.res_circ_pump_pressure.loc[idx, 'mdot_flow_kg_per_s']
                deltap_bar = net.res_circ_pump_pressure.loc[idx, 'deltap_bar']
                # P = ṁ * Δp / ρ
                pump_power_w += (mdot * deltap_bar * 1e5) / 997  # water density
            kpis["pump_energy_kwh"] = pump_power_w / 1000  # Assuming 1 hour
        else:
            # Estimate from pressure drop and flow
            total_pressure_drop = kpis["max_pressure_drop_bar"]
            mass_flow = self._simulation_metadata.get("mass_flow_kg_s", 0)
            # Rough estimate with 75% pump efficiency
            pump_power_w = (mass_flow * total_pressure_drop * 1e5) / (997 * 0.75)
            kpis["pump_energy_kwh"] = pump_power_w / 1000
        
        # --- Thermal Metrics ---
        if hasattr(net, 'res_junction') and len(net.res_junction) > 0:
            # Temperatures (convert K to °C)
            temps_c = net.res_junction.t_k - 273.15
            kpis["min_supply_temp_c"] = temps_c.min()
            kpis["avg_supply_temp_c"] = temps_c.mean()
        else:
            kpis["min_supply_temp_c"] = self.supply_temp_c
            kpis["avg_supply_temp_c"] = self.supply_temp_c
        
        # Network heat loss (simplified estimate)
        # Real calculation would need pipe lengths and insulation
        total_pipe_length_km = net.pipe.length_km.sum() if hasattr(net, 'pipe') else 0
        # Assume ~10 W/m heat loss at delta_T = 50K
        heat_loss_w = total_pipe_length_km * 1000 * 10
        kpis["network_heat_loss_kwh"] = heat_loss_w / 1000  # Assuming 1 hour
        
        # Heat loss percentage
        if kpis["total_heat_supplied_mwh"] > 0:
            kpis["heat_loss_percentage"] = (
                kpis["network_heat_loss_kwh"] / (kpis["total_heat_supplied_mwh"] * 1000)
            ) * 100
        else:
            kpis["heat_loss_percentage"] = 0.0
        
        # --- Network Metrics ---
        kpis["num_junctions"] = len(net.junction)
        kpis["num_pipes"] = len(net.pipe) if hasattr(net, 'pipe') else 0
        kpis["num_consumers"] = len(net.heat_exchanger) if hasattr(net, 'heat_exchanger') else 0
        kpis["total_pipe_length_km"] = total_pipe_length_km
        
        return kpis
    
    def get_pressure_profile(self) -> gpd.GeoDataFrame:
        """Get pressure distribution as GeoDataFrame."""
        if not hasattr(self.network, 'res_junction'):
            return gpd.GeoDataFrame()
        
        data = []
        for idx, junction in self.network.junction.iterrows():
            if idx not in self.network.junction_geodata.index:
                continue
            
            geo = self.network.junction_geodata.loc[idx]
            res = self.network.res_junction.loc[idx]
            
            data.append({
                "junction_id": idx,
                "pressure_bar": res.p_bar,
                "geometry": Point(geo.x, geo.y)
            })
        
        return gpd.GeoDataFrame(data, crs=self.network.junction_geodata.crs)
    
    def get_temperature_profile(self) -> gpd.GeoDataFrame:
        """Get temperature distribution as GeoDataFrame."""
        if not hasattr(self.network, 'res_junction'):
            return gpd.GeoDataFrame()
        
        data = []
        for idx, junction in self.network.junction.iterrows():
            if idx not in self.network.junction_geodata.index:
                continue
            
            geo = self.network.junction_geodata.loc[idx]
            res = self.network.res_junction.loc[idx]
            name = junction.get("name", "")
            
            # Determine circuit from junction name
            circuit = "supply" if "supply" in name else "return"
            
            data.append({
                "junction_id": idx,
                "temperature_c": res.t_k - 273.15,
                "circuit": circuit,
                "geometry": Point(geo.x, geo.y)
            })
        
        return gpd.GeoDataFrame(data, crs=self.network.junction_geodata.crs)
    
    def export_results(self, output_dir: Path, format: str = "geojson") -> Dict[str, Path]:
        """Export simulation results to GeoJSON files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        if format == "geojson":
            # Export junctions
            junctions_features = []
            for idx, junction in self.network.junction.iterrows():
                if idx not in self.network.junction_geodata.index:
                    continue
                
                geo = self.network.junction_geodata.loc[idx]
                res = self.network.res_junction.loc[idx] if hasattr(self.network, 'res_junction') else None
                
                feature = {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [float(geo.x), float(geo.y)]},
                    "properties": {
                        "id": int(idx),
                        "name": str(junction.get("name", f"j{idx}")),
                        "pressure_bar": float(res.p_bar) if res is not None else 0.0,
                        "temperature_c": float(res.t_k - 273.15) if res is not None else 0.0
                    }
                }
                junctions_features.append(feature)
            
            junctions_file = output_dir / "dh_junctions.geojson"
            with open(junctions_file, 'w') as f:
                json.dump({"type": "FeatureCollection", "features": junctions_features}, f, indent=2)
            
            exported_files["junctions"] = junctions_file
            print(f"  Exported: {junctions_file}")
        
        return exported_files
    
    def get_network_summary(self) -> Dict[str, int]:
        """Get summary statistics of the network."""
        if self.network is None:
            return {}
        
        return {
            "num_junctions": len(self.network.junction),
            "num_pipes": len(self.network.pipe) if hasattr(self.network, 'pipe') else 0,
            "num_heat_exchangers": len(self.network.heat_exchanger) if hasattr(self.network, 'heat_exchanger') else 0,
            "num_sinks": len(self.network.sink) if hasattr(self.network, 'sink') else 0,
            "num_ext_grids": len(self.network.ext_grid) if hasattr(self.network, 'ext_grid') else 0,
        }

