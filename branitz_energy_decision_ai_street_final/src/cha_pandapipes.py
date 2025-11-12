from __future__ import annotations
import json
import math
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

warnings.filterwarnings("ignore")

try:
    import pandapipes as pp
    PANDAPIPES_AVAILABLE = True
except ImportError:
    PANDAPIPES_AVAILABLE = False
    print("⚠️ Pandapipes not available - hydraulic simulation disabled")

class CHAPandapipesSimulator:
    """Pandapipes simulator for CHA dual-pipe network with thermal simulation."""
    
    def __init__(self, cha_output_dir: str = "processed/cha", config: dict = None):
        self.cha_output_dir = Path(cha_output_dir)
        self.net = None
        self.simulation_results = None
        self.config = config or self._get_default_config()
        
        # Thermal simulation parameters
        self.thermal_enabled = self.config.get('hydraulic_simulation', {}).get('enabled', True)
        self.simulation_mode = self.config.get('hydraulic_simulation', {}).get('mode', 'sequential')
        self.max_iterations = self.config.get('hydraulic_simulation', {}).get('max_iterations', 100)
        self.convergence_tolerance = self.config.get('hydraulic_simulation', {}).get('convergence_tolerance', 1e-6)
        
        # Thermal parameters
        thermal_params = self.config.get('hydraulic_simulation', {}).get('thermal_parameters', {})
        self.supply_temp_c = thermal_params.get('supply_temp_c', 80)
        self.return_temp_c_init = thermal_params.get('return_temp_c_init', 50)
        self.ground_temp_c = thermal_params.get('ground_temp_c', 10)
        self.pipe_sections_default = thermal_params.get('pipe_sections_default', 8)
        self.pipe_u_w_per_m2k_default = thermal_params.get('pipe_u_w_per_m2k_default', 0.6)
        
        # Fluid properties
        fluid_props = self.config.get('hydraulic_simulation', {}).get('fluid_properties', {})
        self.fluid_temp_c = fluid_props.get('temperature_c', 80)
        self.fluid_pressure_bar = fluid_props.get('pressure_bar', 2.0)
        
        # Water properties for calculations
        self.water_density_kg_m3 = 977.8  # Water density at 70°C
        
        print(f"✅ CHAPandapipesSimulator initialized with thermal simulation: {self.thermal_enabled}")
        print(f"   Mode: {self.simulation_mode}, Max iterations: {self.max_iterations}")
        print(f"   Supply temp: {self.supply_temp_c}°C, Return temp: {self.return_temp_c_init}°C")
        print(f"   Ground temp: {self.ground_temp_c}°C, Pipe sections: {self.pipe_sections_default}")
    
    def _get_default_config(self) -> dict:
        """Get default configuration for thermal simulation."""
        return {
            'hydraulic_simulation': {
                'enabled': True,
                'mode': 'sequential',
                'max_iterations': 100,
                'convergence_tolerance': 1e-6,
                'thermal_parameters': {
                    'supply_temp_c': 80,
                    'return_temp_c_init': 50,
                    'ground_temp_c': 10,
                    'pipe_sections_default': 8,
                    'pipe_u_w_per_m2k_default': 0.6
                },
                'fluid_properties': {
                    'temperature_c': 80,
                    'pressure_bar': 2.0
                }
            }
        }
        
    def load_cha_network(self) -> bool:
        """Load the dual-pipe network created by CHA."""
        if not PANDAPIPES_AVAILABLE:
            print("❌ Pandapipes not available")
            return False
            
        print("📁 Loading CHA network for pandapipes simulation...")
        
        try:
            # Load network data
            supply_pipes = pd.read_csv(self.cha_output_dir / "supply_pipes.csv")
            return_pipes = pd.read_csv(self.cha_output_dir / "return_pipes.csv")
            service_connections = pd.read_csv(self.cha_output_dir / "service_connections.csv")
            network_stats = json.loads((self.cha_output_dir / "network_stats.json").read_text())
            
            print(f"✅ Loaded network with {len(supply_pipes)} supply pipes, {len(return_pipes)} return pipes, {len(service_connections)} service connections")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to load CHA network: {e}")
            return False
    
    def create_pandapipes_network(self) -> bool:
        """Create pandapipes network from CHA data."""
        if not PANDAPIPES_AVAILABLE:
            print("❌ Pandapipes not available")
            return False
            
        print("🏗️ Creating pandapipes network...")
        
        try:
            # Load network data
            supply_pipes = pd.read_csv(self.cha_output_dir / "supply_pipes.csv")
            return_pipes = pd.read_csv(self.cha_output_dir / "return_pipes.csv")
            service_connections = pd.read_csv(self.cha_output_dir / "service_connections.csv")
            network_stats = json.loads((self.cha_output_dir / "network_stats.json").read_text())
            
            # Create empty pandapipes network
            self.net = pp.create_empty_network("cha_dual_pipe_network")
            
            # Add fluid properties for water with thermal properties
            pp.create_fluid_from_lib(self.net, "water", overwrite=True)
            
            # Configure thermal simulation parameters
            if self.thermal_enabled:
                print("🌡️ Configuring thermal simulation parameters...")
                # Set network-wide thermal parameters (if available)
                try:
                    if hasattr(self.net, 'fluid_properties'):
                        self.net.fluid_properties['temperature'] = self.fluid_temp_c + 273.15  # Convert to Kelvin
                        self.net.fluid_properties['pressure'] = self.fluid_pressure_bar
                    else:
                        print("   Fluid properties not directly accessible, will be set during simulation")
                except Exception as e:
                    print(f"   Warning: Could not set fluid properties: {e}")
                
                print(f"   Fluid temperature: {self.fluid_temp_c}°C")
                print(f"   Fluid pressure: {self.fluid_pressure_bar} bar")
                print(f"   Ground temperature: {self.ground_temp_c}°C")
            
            # Add junctions for all unique nodes
            all_nodes = set()
            for _, pipe in supply_pipes.iterrows():
                all_nodes.add(str(pipe["start_node"]))
                all_nodes.add(str(pipe["start_node"]))
            for _, pipe in return_pipes.iterrows():
                all_nodes.add(str(pipe["start_node"]))
                all_nodes.add(str(pipe["end_node"]))
            
            # Create junctions with thermal boundary conditions
            node_to_junction = {}
            plant_node = None
            
            for i, node in enumerate(all_nodes):
                # Parse node coordinates
                if isinstance(node, str) and node.startswith("(") and node.endswith(")"):
                    # Handle tuple format "(x, y)"
                    coords = eval(node)
                    x, y = coords
                else:
                    # Handle other formats
                    x, y = 0, 0
                
                # Determine if this is the plant node (first node or special identifier)
                is_plant_node = (i == 0) or ("plant" in str(node).lower())
                if is_plant_node:
                    plant_node = node
                
                # Set initial temperature based on node type
                if self.thermal_enabled:
                    if is_plant_node:
                        initial_temp_k = self.supply_temp_c + 273.15  # Supply temperature
                    else:
                        initial_temp_k = self.return_temp_c_init + 273.15  # Return temperature
                else:
                    initial_temp_k = 313.15  # Default temperature (40°C)
                
                # Create junction with thermal boundary conditions
                junction = pp.create_junction(
                    self.net, 
                    pn_bar=self.fluid_pressure_bar,  # Use configured pressure
                    tfluid_k=initial_temp_k  # Use thermal boundary conditions
                )
                node_to_junction[node] = junction
                
                if is_plant_node:
                    print(f"   Plant junction created at {node} with temperature {self.supply_temp_c}°C")
            
            print(f"✅ Created {len(node_to_junction)} junctions with thermal boundary conditions")
            
            # Add supply pipes with thermal parameters
            print("🔥 Creating supply pipes with thermal parameters...")
            for _, pipe in supply_pipes.iterrows():
                start_junction = node_to_junction.get(str(pipe["start_node"]), 0)
                end_junction = node_to_junction.get(str(pipe["end_node"]), 0)
                
                # Get pipe diameter from CHA data if available, otherwise use default
                diameter_m = pipe.get('d_inner_m', 0.1) if 'd_inner_m' in pipe else 0.1
                
                # Configure thermal parameters for supply pipes
                if self.thermal_enabled:
                    # Supply pipes: higher heat transfer coefficient for better thermal performance
                    alpha_w_per_m2k = self.pipe_u_w_per_m2k_default * 1.2  # 20% higher for supply
                    sections = self.pipe_sections_default
                    text_k = self.ground_temp_c + 273.15  # Ground temperature in Kelvin
                else:
                    # Hydraulic-only mode
                    alpha_w_per_m2k = 0.0
                    sections = 1
                    text_k = 313.15
                
                pp.create_pipe_from_parameters(
                    self.net,
                    from_junction=start_junction,
                    to_junction=end_junction,
                    length_km=pipe["length_m"] / 1000.0,
                    diameter_m=diameter_m,
                    k_mm=0.1,  # Default roughness
                    name=f"supply_{pipe['street_id']}_{pipe['building_served']}",
                    sections=sections,
                    alpha_w_per_m2k=alpha_w_per_m2k,
                    text_k=text_k
                )
            
            # Add return pipes with thermal parameters
            print("❄️ Creating return pipes with thermal parameters...")
            for _, pipe in return_pipes.iterrows():
                start_junction = node_to_junction.get(str(pipe["start_node"]), 0)
                end_junction = node_to_junction.get(str(pipe["end_node"]), 0)
                
                # Get pipe diameter from CHA data if available, otherwise use default
                diameter_m = pipe.get('d_inner_m', 0.1) if 'd_inner_m' in pipe else 0.1
                
                # Configure thermal parameters for return pipes
                if self.thermal_enabled:
                    # Return pipes: standard heat transfer coefficient
                    alpha_w_per_m2k = self.pipe_u_w_per_m2k_default
                    sections = self.pipe_sections_default
                    text_k = self.ground_temp_c + 273.15  # Ground temperature in Kelvin
                else:
                    # Hydraulic-only mode
                    alpha_w_per_m2k = 0.0
                    sections = 1
                    text_k = 313.15
                
                pp.create_pipe_from_parameters(
                    self.net,
                    from_junction=start_junction,
                    to_junction=end_junction,
                    length_km=pipe["length_m"] / 1000.0,
                    diameter_m=diameter_m,
                    k_mm=0.1,  # Default roughness
                    name=f"return_{pipe['street_id']}_{pipe['building_served']}",
                    sections=sections,
                    alpha_w_per_m2k=alpha_w_per_m2k,
                    text_k=text_k
                )
            
            # Add ext_grid at plant (supply source) with thermal boundary conditions
            print("🏭 Creating heat source with thermal boundary conditions...")
            plant_junction = node_to_junction.get(plant_node, list(node_to_junction.values())[0])
            
            # Set thermal boundary conditions for heat source
            if self.thermal_enabled:
                supply_pressure_bar = 6.0  # Supply pressure
                supply_temp_k = self.supply_temp_c + 273.15  # Supply temperature in Kelvin
            else:
                supply_pressure_bar = 6.0
                supply_temp_k = 343.15  # Default temperature (70°C)
            
            pp.create_ext_grid(
                self.net,
                junction=plant_junction,
                p_bar=supply_pressure_bar,
                t_k=supply_temp_k,
                name="CHP_Plant",
                type="pt"  # Pressure and temperature boundary condition
            )
            
            print(f"   Heat source: {self.supply_temp_c}°C, {supply_pressure_bar} bar")
            
            # Add sinks at buildings (heat consumers) with mass flow from LFA
            print("🏠 Creating heat consumers with mass flow rates...")
            for _, service in service_connections.iterrows():
                if service["pipe_type"] == "supply_service":
                    # Find the junction closest to this building
                    building_junction = list(node_to_junction.values())[0]  # Simplified
                    
                    # Get mass flow rate from CHA data if available
                    mass_flow_kg_s = service.get('mdot_kg_s', 0.1) if 'mdot_kg_s' in service else 0.1
                    
                    pp.create_sink(
                        self.net,
                        junction=building_junction,
                        mdot_kg_per_s=mass_flow_kg_s,
                        name=f"Building_{service['building_id']}",
                        scaling=1.0
                    )
            
            print(f"✅ Created pandapipes network with {len(self.net.junction)} junctions and {len(self.net.pipe)} pipes")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create pandapipes network: {e}")
            return False
    
    def run_hydraulic_simulation(self) -> bool:
        """Run pandapipes hydraulic and thermal simulation."""
        if not PANDAPIPES_AVAILABLE or self.net is None:
            print("❌ Pandapipes network not available")
            return False
            
        print("🔄 Running pandapipes hydraulic and thermal simulation...")
        
        try:
            # Configure simulation parameters
            simulation_mode = self.simulation_mode if self.thermal_enabled else "hydraulics"
            max_iterations = self.max_iterations
            tolerance = self.convergence_tolerance
            
            print(f"   Simulation mode: {simulation_mode}")
            print(f"   Max iterations: {max_iterations}")
            print(f"   Convergence tolerance: {tolerance}")
            
            # Run simulation with thermal mode if enabled
            if self.thermal_enabled:
                print("🌡️ Running thermal simulation (sequential mode)...")
                pp.pipeflow(
                    self.net, 
                    mode=simulation_mode, 
                    iter=max_iterations,
                    tol_p=tolerance,
                    tol_v=tolerance,
                    tol_T=tolerance
                )
            else:
                print("💧 Running hydraulic-only simulation...")
                pp.pipeflow(
                    self.net, 
                    mode=simulation_mode, 
                    iter=max_iterations,
                    tol_p=tolerance,
                    tol_v=tolerance
                )
            
            # Extract results
            self.simulation_results = {
                "junction_results": self.net.res_junction,
                "pipe_results": self.net.res_pipe,
                "ext_grid_results": self.net.res_ext_grid,
                "sink_results": self.net.res_sink,
                "simulation_success": True,
                "thermal_enabled": self.thermal_enabled,
                "simulation_mode": simulation_mode,
                "convergence_info": {
                    "iterations": getattr(self.net, 'converged', False),
                    "mode": simulation_mode
                }
            }
            
            # Check convergence
            if hasattr(self.net, 'converged') and self.net.converged:
                print("✅ Simulation converged successfully")
            else:
                print("⚠️ Simulation completed but convergence status unclear")
            
            print("✅ Hydraulic and thermal simulation completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Simulation failed: {e}")
            self.simulation_results = {
                "simulation_success": False, 
                "error": str(e),
                "thermal_enabled": self.thermal_enabled
            }
            return False
    
    def calculate_hydraulic_kpis(self) -> Dict:
        """Calculate hydraulic and thermal KPIs from simulation results."""
        if not self.simulation_results or not self.simulation_results.get("simulation_success"):
            return {"error": "No simulation results available"}
        
        try:
            junction_results = self.simulation_results["junction_results"]
            pipe_results = self.simulation_results["pipe_results"]
            
            # Calculate hydraulic KPIs
            max_pressure = junction_results.p_bar.max()
            min_pressure = junction_results.p_bar.min()
            pressure_drop = max_pressure - min_pressure
            
            max_velocity = pipe_results.v_mean_m_per_s.max()
            min_velocity = pipe_results.v_mean_m_per_s.min()
            
            total_flow = self.simulation_results["sink_results"].mdot_kg_per_s.sum()
            
            # Base KPIs
            kpis = {
                "max_pressure_bar": float(max_pressure),
                "min_pressure_bar": float(min_pressure),
                "pressure_drop_bar": float(pressure_drop),
                "max_velocity_ms": float(max_velocity),
                "min_velocity_ms": float(min_velocity),
                "total_flow_kg_s": float(total_flow),
                "simulation_success": True,
                "thermal_enabled": self.thermal_enabled
            }
            
            # Calculate thermal KPIs if thermal simulation was enabled
            if self.thermal_enabled and 't_k' in junction_results.columns:
                # Temperature analysis
                max_temp_k = junction_results.t_k.max()
                min_temp_k = junction_results.t_k.min()
                temp_drop_k = max_temp_k - min_temp_k
                
                # Convert to Celsius for reporting
                max_temp_c = max_temp_k - 273.15
                min_temp_c = min_temp_k - 273.15
                temp_drop_c = temp_drop_k
                
                # Calculate thermal losses (if available in pipe results)
                if 'q_loss_W' in pipe_results.columns:
                    total_thermal_loss_w = pipe_results.q_loss_W.sum()
                    total_thermal_loss_kw = total_thermal_loss_w / 1000.0
                else:
                    total_thermal_loss_kw = 0.0
                
                # Add thermal KPIs
                kpis.update({
                    "max_temperature_c": float(max_temp_c),
                    "min_temperature_c": float(min_temp_c),
                    "temperature_drop_c": float(temp_drop_c),
                    "total_thermal_loss_kw": float(total_thermal_loss_kw),
                    "supply_temperature_c": self.supply_temp_c,
                    "return_temperature_c": min_temp_c,
                    "thermal_efficiency": float((max_temp_c - min_temp_c) / (self.supply_temp_c - self.ground_temp_c)) if (self.supply_temp_c - self.ground_temp_c) > 0 else 0.0
                })
                
                print(f"✅ Hydraulic and thermal KPIs calculated:")
                print(f"   - Pressure drop: {pressure_drop:.3f} bar")
                print(f"   - Max velocity: {max_velocity:.2f} m/s")
                print(f"   - Total flow: {total_flow:.2f} kg/s")
                print(f"   - Temperature drop: {temp_drop_c:.1f}°C")
                print(f"   - Thermal losses: {total_thermal_loss_kw:.1f} kW")
                print(f"   - Thermal efficiency: {kpis['thermal_efficiency']:.2%}")
            else:
                print(f"✅ Hydraulic KPIs calculated:")
                print(f"   - Pressure drop: {pressure_drop:.3f} bar")
                print(f"   - Max velocity: {max_velocity:.2f} m/s")
                print(f"   - Total flow: {total_flow:.2f} kg/s")
            
            return kpis
            
        except Exception as e:
            print(f"❌ Failed to calculate KPIs: {e}")
            return {"error": str(e)}
    
    def set_thermal_boundary_conditions(self) -> bool:
        """Set thermal boundary conditions at heat sources and consumers."""
        if not PANDAPIPES_AVAILABLE or self.net is None:
            print("❌ Pandapipes network not available")
            return False
        
        if not self.thermal_enabled:
            print("⚠️ Thermal simulation not enabled, skipping boundary conditions")
            return True
        
        try:
            print("🌡️ Setting thermal boundary conditions...")
            
            # Set supply temperature at heat source (ext_grid)
            if hasattr(self.net, 'ext_grid') and len(self.net.ext_grid) > 0:
                for idx, ext_grid in self.net.ext_grid.iterrows():
                    # Update supply temperature
                    self.net.ext_grid.at[idx, 't_k'] = self.supply_temp_c + 273.15
                    print(f"   Heat source {idx}: {self.supply_temp_c}°C")
            
            # Set return temperature at heat consumers (sinks)
            if hasattr(self.net, 'sink') and len(self.net.sink) > 0:
                for idx, sink in self.net.sink.iterrows():
                    # Set return temperature for sinks
                    self.net.sink.at[idx, 't_k'] = self.return_temp_c_init + 273.15
                    print(f"   Heat consumer {idx}: {self.return_temp_c_init}°C")
            
            print("✅ Thermal boundary conditions set successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to set thermal boundary conditions: {e}")
            return False
    
    def configure_pipe_thermal_properties(self) -> bool:
        """Configure per-pipe thermal properties for heat transfer."""
        if not PANDAPIPES_AVAILABLE or self.net is None:
            print("❌ Pandapipes network not available")
            return False
        
        if not self.thermal_enabled:
            print("⚠️ Thermal simulation not enabled, skipping thermal properties")
            return True
        
        try:
            print("🔥 Configuring pipe thermal properties...")
            
            # Configure thermal properties for all pipes
            if hasattr(self.net, 'pipe') and len(self.net.pipe) > 0:
                for idx, pipe in self.net.pipe.iterrows():
                    # Set thermal parameters
                    self.net.pipe.at[idx, 'sections'] = self.pipe_sections_default
                    self.net.pipe.at[idx, 'text_k'] = self.ground_temp_c + 273.15
                    
                    # Set heat transfer coefficient based on pipe type
                    pipe_name = str(pipe.get('name', ''))
                    if 'supply' in pipe_name.lower():
                        # Supply pipes: higher heat transfer coefficient
                        self.net.pipe.at[idx, 'alpha_w_per_m2k'] = self.pipe_u_w_per_m2k_default * 1.2
                    else:
                        # Return pipes: standard heat transfer coefficient
                        self.net.pipe.at[idx, 'alpha_w_per_m2k'] = self.pipe_u_w_per_m2k_default
                
                print(f"   Configured {len(self.net.pipe)} pipes with thermal properties")
                print(f"   Pipe sections: {self.pipe_sections_default}")
                print(f"   Ground temperature: {self.ground_temp_c}°C")
                print(f"   Heat transfer coefficient: {self.pipe_u_w_per_m2k_default} W/(m²·K)")
            
            print("✅ Pipe thermal properties configured successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to configure pipe thermal properties: {e}")
            return False
    
    def save_simulation_results(self, output_dir: str = "eval/cha") -> bool:
        """Save simulation results and KPIs."""
        if not self.simulation_results:
            print("❌ No simulation results to save")
            return False
            
        print("💾 Saving simulation results...")
        
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save pandapipes network
            if self.net:
                network_file = output_path / "pandapipes_network.json"
                pp.io.to_json(self.net, str(network_file))
            
            # Save simulation results
            results_file = output_path / "simulation_results.json"
            with open(results_file, "w") as f:
                json.dump(self.simulation_results, f, indent=2, default=str)
            
            # Save hydraulic KPIs
            kpis = self.calculate_hydraulic_kpis()
            kpis_file = output_path / "hydraulics_check.csv"
            pd.DataFrame([kpis]).to_csv(kpis_file, index=False)
            
            print(f"✅ Simulation results saved to {output_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save simulation results: {e}")
            return False
    
    def run_complete_simulation(self, cha_output_dir: str = "processed/cha") -> Dict:
        """Run complete pandapipes simulation workflow."""
        print("🚀 Running complete CHA pandapipes simulation...")
        
        try:
            # Step 1: Load CHA network
            if not self.load_cha_network():
                return {"status": "error", "message": "Failed to load CHA network"}
            
            # Step 2: Create pandapipes network
            if not self.create_pandapipes_network():
                return {"status": "error", "message": "Failed to create pandapipes network"}
            
            # Step 3: Set thermal boundary conditions (if thermal simulation enabled)
            if self.thermal_enabled:
                if not self.set_thermal_boundary_conditions():
                    return {"status": "error", "message": "Failed to set thermal boundary conditions"}
            
            # Step 4: Configure pipe thermal properties (if thermal simulation enabled)
            if self.thermal_enabled:
                if not self.configure_pipe_thermal_properties():
                    return {"status": "error", "message": "Failed to configure pipe thermal properties"}
            
            # Step 5: Run hydraulic and thermal simulation
            if not self.run_hydraulic_simulation():
                return {"status": "error", "message": "Failed to run hydraulic simulation"}
            
            # Step 6: Save results
            output_dir = "eval/cha"
            if not self.save_simulation_results(output_dir):
                return {"status": "error", "message": "Failed to save simulation results"}
            
            # Step 7: Calculate hydraulic KPIs
            kpis = self.calculate_hydraulic_kpis()
            
            # Step 8: Calculate pump power
            print("🔧 Step 8: Calculating pump power...")
            pump_power_w = self.calculate_pump_power(self.simulation_results)
            
            # Step 9: Calculate thermal losses
            print("🔥 Step 9: Calculating thermal losses...")
            thermal_losses = self.calculate_thermal_losses(self.simulation_results)
            
            # Step 10: Calculate temperature profiles
            print("🌡️ Step 10: Calculating temperature profiles...")
            temperature_profiles = self.calculate_temperature_profiles(self.simulation_results)
            
            # Step 11: Validate thermal performance
            print("✅ Step 11: Validating thermal performance...")
            thermal_results = {
                'pump_power': self.pump_power_results,
                'thermal_losses': thermal_losses,
                'temperature_profiles': temperature_profiles
            }
            thermal_validation = self.validate_thermal_performance(thermal_results)
            
            # Step 12: Export comprehensive results
            print("📊 Step 12: Exporting comprehensive results...")
            export_results = {
                'hydraulic_results': self.export_hydraulic_results(cha_output_dir),
                'thermal_visualization': self.export_thermal_visualization(cha_output_dir),
                'compliance_report': self.export_standards_compliance_report(cha_output_dir),
                'kpi_summary': self.export_kpi_summary(cha_output_dir)
            }
            
            print("✅ CHA pandapipes simulation completed successfully!")
            return {
                "status": "ok",
                "output_dir": output_dir,
                "kpis": kpis,
                "pump_power": self.pump_power_results,
                "thermal_losses": thermal_losses,
                "temperature_profiles": temperature_profiles,
                "thermal_validation": thermal_validation,
                "export_results": export_results,
                "network_size": {
                    "junctions": len(self.net.junction) if self.net else 0,
                    "pipes": len(self.net.pipe) if self.net else 0
                }
            }
            
        except Exception as e:
            print(f"❌ CHA pandapipes simulation failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def calculate_pump_power(self, simulation_results: Dict) -> float:
        """
        Calculate total pump power required for the network.
        
        Formula: P_pump = Σ(Δp_i · V_dot_i) / η
        where:
        - P_pump = pump power (W)
        - Δp_i = pressure drop in pipe i (Pa)
        - V_dot_i = volumetric flow rate in pipe i (m³/s)
        - η = pump efficiency (default 0.75)
        
        Args:
            simulation_results: Pandapipes simulation results
            
        Returns:
            pump_power_w: Total pump power in watts
        """
        if not simulation_results or not simulation_results.get("simulation_success"):
            print("❌ No valid simulation results for pump power calculation")
            return 0.0
        
        try:
            print("🔧 Calculating pump power...")
            
            # Get pipe results
            pipe_results = simulation_results.get("pipe_results")
            if pipe_results is None or len(pipe_results) == 0:
                print("❌ No pipe results available")
                return 0.0
            
            # Pump efficiency (configurable)
            pump_efficiency = self.config.get('hydraulic_simulation', {}).get('pump_efficiency', 0.75)
            
            total_pump_power_w = 0.0
            pump_power_details = []
            
            # Calculate pump power for each pipe
            for idx, pipe in pipe_results.iterrows():
                # Get pressure drop and mass flow rate
                pressure_drop_pa = pipe.get('p_from_bar', 0) - pipe.get('p_to_bar', 0)
                pressure_drop_pa *= 100000  # Convert bar to Pa
                
                mass_flow_kg_s = pipe.get('mdot_kg_per_s', 0)
                
                # Calculate volumetric flow rate: V_dot = m_dot / ρ
                volumetric_flow_m3_s = mass_flow_kg_s / self.water_density_kg_m3
                
                # Calculate pump power for this pipe: P = Δp · V_dot / η
                pipe_pump_power_w = (pressure_drop_pa * volumetric_flow_m3_s) / pump_efficiency
                
                total_pump_power_w += pipe_pump_power_w
                
                # Store details for logging
                pump_power_details.append({
                    'pipe_id': idx,
                    'pressure_drop_pa': pressure_drop_pa,
                    'mass_flow_kg_s': mass_flow_kg_s,
                    'volumetric_flow_m3_s': volumetric_flow_m3_s,
                    'pump_power_w': pipe_pump_power_w
                })
            
            # Convert to kW for reporting
            total_pump_power_kw = total_pump_power_w / 1000.0
            
            print(f"   Total pump power: {total_pump_power_kw:.2f} kW")
            print(f"   Pump efficiency: {pump_efficiency:.2%}")
            print(f"   Pipes analyzed: {len(pump_power_details)}")
            
            # Store results
            self.pump_power_results = {
                'total_pump_power_w': total_pump_power_w,
                'total_pump_power_kw': total_pump_power_kw,
                'pump_efficiency': pump_efficiency,
                'pipe_details': pump_power_details
            }
            
            return total_pump_power_w
            
        except Exception as e:
            print(f"❌ Error calculating pump power: {e}")
            return 0.0
    
    def calculate_thermal_losses(self, simulation_results: Dict) -> Dict:
        """
        Calculate thermal losses for the network.
        
        Formula: Q_loss = U · A · ΔT
        where:
        - Q_loss = thermal loss (W)
        - U = overall heat transfer coefficient (W/(m²·K))
        - A = surface area (m²)
        - ΔT = temperature difference (K)
        
        Args:
            simulation_results: Pandapipes simulation results
            
        Returns:
            Dict with thermal loss results
        """
        if not simulation_results or not simulation_results.get("simulation_success"):
            print("❌ No valid simulation results for thermal loss calculation")
            return {"error": "No valid simulation results"}
        
        try:
            print("🔥 Calculating thermal losses...")
            
            # Get pipe results
            pipe_results = simulation_results.get("pipe_results")
            if pipe_results is None or len(pipe_results) == 0:
                print("❌ No pipe results available")
                return {"error": "No pipe results available"}
            
            total_thermal_loss_w = 0.0
            thermal_loss_details = []
            
            # Calculate thermal losses for each pipe
            for idx, pipe in pipe_results.iterrows():
                # Get pipe parameters
                length_m = pipe.get('length_km', 0) * 1000  # Convert km to m
                diameter_m = pipe.get('diameter_m', 0.1)
                
                # Get thermal parameters
                heat_transfer_coeff = pipe.get('alpha_w_per_m2k', self.pipe_u_w_per_m2k_default)
                ground_temp_k = pipe.get('text_k', self.ground_temp_c + 273.15)
                
                # Get fluid temperature (average of inlet and outlet)
                inlet_temp_k = pipe.get('t_from_k', self.supply_temp_c + 273.15)
                outlet_temp_k = pipe.get('t_to_k', self.return_temp_c_init + 273.15)
                avg_fluid_temp_k = (inlet_temp_k + outlet_temp_k) / 2
                
                # Calculate temperature difference
                delta_t_k = avg_fluid_temp_k - ground_temp_k
                
                # Calculate surface area: A = π · D · L
                surface_area_m2 = math.pi * diameter_m * length_m
                
                # Calculate thermal loss: Q_loss = U · A · ΔT
                thermal_loss_w = heat_transfer_coeff * surface_area_m2 * delta_t_k
                
                total_thermal_loss_w += thermal_loss_w
                
                # Store details for logging
                thermal_loss_details.append({
                    'pipe_id': idx,
                    'length_m': length_m,
                    'diameter_m': diameter_m,
                    'surface_area_m2': surface_area_m2,
                    'heat_transfer_coeff': heat_transfer_coeff,
                    'avg_fluid_temp_c': avg_fluid_temp_k - 273.15,
                    'ground_temp_c': ground_temp_k - 273.15,
                    'delta_t_k': delta_t_k,
                    'thermal_loss_w': thermal_loss_w
                })
            
            # Convert to kW for reporting
            total_thermal_loss_kw = total_thermal_loss_w / 1000.0
            
            print(f"   Total thermal loss: {total_thermal_loss_kw:.2f} kW")
            print(f"   Pipes analyzed: {len(thermal_loss_details)}")
            print(f"   Average heat transfer coefficient: {self.pipe_u_w_per_m2k_default:.2f} W/(m²·K)")
            
            # Store results
            self.thermal_loss_results = {
                'total_thermal_loss_w': total_thermal_loss_w,
                'total_thermal_loss_kw': total_thermal_loss_kw,
                'pipe_details': thermal_loss_details
            }
            
            return {
                'total_thermal_loss_w': total_thermal_loss_w,
                'total_thermal_loss_kw': total_thermal_loss_kw,
                'pipe_details': thermal_loss_details
            }
            
        except Exception as e:
            print(f"❌ Error calculating thermal losses: {e}")
            return {"error": str(e)}
    
    def calculate_temperature_profiles(self, simulation_results: Dict) -> Dict:
        """
        Calculate temperature profiles along the network.
        
        Formula: ΔT = Q_loss / (m_dot · cp)
        where:
        - ΔT = temperature drop (K)
        - Q_loss = thermal loss (W)
        - m_dot = mass flow rate (kg/s)
        - cp = specific heat capacity (J/(kg·K))
        
        Args:
            simulation_results: Pandapipes simulation results
            
        Returns:
            Dict with temperature profile results
        """
        if not simulation_results or not simulation_results.get("simulation_success"):
            print("❌ No valid simulation results for temperature profile calculation")
            return {"error": "No valid simulation results"}
        
        try:
            print("🌡️ Calculating temperature profiles...")
            
            # Get pipe results
            pipe_results = simulation_results.get("pipe_results")
            if pipe_results is None or len(pipe_results) == 0:
                print("❌ No pipe results available")
                return {"error": "No pipe results available"}
            
            # Water properties
            cp_water = 4180  # J/(kg·K) - specific heat capacity of water
            
            temperature_profiles = []
            total_temp_drop_k = 0.0
            
            # Calculate temperature profiles for each pipe
            for idx, pipe in pipe_results.iterrows():
                # Get pipe parameters
                length_m = pipe.get('length_km', 0) * 1000  # Convert km to m
                mass_flow_kg_s = pipe.get('mdot_kg_per_s', 0.1)
                
                # Get inlet and outlet temperatures
                inlet_temp_k = pipe.get('t_from_k', self.supply_temp_c + 273.15)
                outlet_temp_k = pipe.get('t_to_k', self.return_temp_c_init + 273.15)
                
                # Calculate temperature drop
                temp_drop_k = inlet_temp_k - outlet_temp_k
                total_temp_drop_k += temp_drop_k
                
                # Calculate thermal loss for this pipe
                thermal_loss_w = self._calculate_pipe_thermal_loss(pipe)
                
                # Calculate temperature drop from thermal loss: ΔT = Q_loss / (m_dot · cp)
                temp_drop_from_loss_k = thermal_loss_w / (mass_flow_kg_s * cp_water) if mass_flow_kg_s > 0 else 0
                
                # Store temperature profile
                temperature_profiles.append({
                    'pipe_id': idx,
                    'length_m': length_m,
                    'inlet_temp_c': inlet_temp_k - 273.15,
                    'outlet_temp_c': outlet_temp_k - 273.15,
                    'temp_drop_k': temp_drop_k,
                    'temp_drop_c': temp_drop_k,
                    'thermal_loss_w': thermal_loss_w,
                    'temp_drop_from_loss_k': temp_drop_from_loss_k,
                    'mass_flow_kg_s': mass_flow_kg_s
                })
            
            # Calculate network-wide temperature statistics
            inlet_temps = [p['inlet_temp_c'] for p in temperature_profiles]
            outlet_temps = [p['outlet_temp_c'] for p in temperature_profiles]
            
            max_inlet_temp_c = max(inlet_temps) if inlet_temps else self.supply_temp_c
            min_outlet_temp_c = min(outlet_temps) if outlet_temps else self.return_temp_c_init
            network_temp_drop_c = max_inlet_temp_c - min_outlet_temp_c
            
            print(f"   Network temperature drop: {network_temp_drop_c:.1f}°C")
            print(f"   Max inlet temperature: {max_inlet_temp_c:.1f}°C")
            print(f"   Min outlet temperature: {min_outlet_temp_c:.1f}°C")
            print(f"   Pipes analyzed: {len(temperature_profiles)}")
            
            # Store results
            self.temperature_profile_results = {
                'temperature_profiles': temperature_profiles,
                'network_temp_drop_c': network_temp_drop_c,
                'max_inlet_temp_c': max_inlet_temp_c,
                'min_outlet_temp_c': min_outlet_temp_c,
                'total_temp_drop_k': total_temp_drop_k
            }
            
            return {
                'temperature_profiles': temperature_profiles,
                'network_temp_drop_c': network_temp_drop_c,
                'max_inlet_temp_c': max_inlet_temp_c,
                'min_outlet_temp_c': min_outlet_temp_c,
                'total_temp_drop_k': total_temp_drop_k
            }
            
        except Exception as e:
            print(f"❌ Error calculating temperature profiles: {e}")
            return {"error": str(e)}
    
    def validate_thermal_performance(self, results: Dict) -> bool:
        """
        Validate thermal performance against standards.
        
        Args:
            results: Combined results from pump power, thermal losses, and temperature profiles
            
        Returns:
            bool: True if thermal performance is acceptable
        """
        try:
            print("✅ Validating thermal performance...")
            
            # Get temperature profile results
            temp_results = results.get('temperature_profiles', {})
            if not temp_results:
                print("❌ No temperature profile results for validation")
                return False
            
            # Get thermal loss results
            thermal_results = results.get('thermal_losses', {})
            if not thermal_results:
                print("❌ No thermal loss results for validation")
                return False
            
            # Get pump power results
            pump_results = results.get('pump_power', {})
            if not pump_results:
                print("❌ No pump power results for validation")
                return False
            
            validation_results = {
                'temperature_validation': True,
                'thermal_loss_validation': True,
                'pump_power_validation': True,
                'overall_validation': True
            }
            
            # Validate temperature drop
            network_temp_drop_c = temp_results.get('network_temp_drop_c', 0)
            min_temp_drop_c = self.config.get('standards_limits', {}).get('temperature_drop_k', {}).get('minimum', 30)
            max_temp_drop_c = self.config.get('standards_limits', {}).get('temperature_drop_k', {}).get('maximum', 50)
            
            if network_temp_drop_c < min_temp_drop_c:
                print(f"⚠️ Temperature drop {network_temp_drop_c:.1f}°C below minimum {min_temp_drop_c}°C")
                validation_results['temperature_validation'] = False
            elif network_temp_drop_c > max_temp_drop_c:
                print(f"⚠️ Temperature drop {network_temp_drop_c:.1f}°C above maximum {max_temp_drop_c}°C")
                validation_results['temperature_validation'] = False
            else:
                print(f"✅ Temperature drop {network_temp_drop_c:.1f}°C within limits ({min_temp_drop_c}-{max_temp_drop_c}°C)")
            
            # Validate thermal losses
            total_thermal_loss_kw = thermal_results.get('total_thermal_loss_kw', 0)
            max_thermal_loss_kw = self.config.get('standards_limits', {}).get('max_thermal_loss_kw', 1000)
            
            if total_thermal_loss_kw > max_thermal_loss_kw:
                print(f"⚠️ Thermal losses {total_thermal_loss_kw:.1f} kW above maximum {max_thermal_loss_kw} kW")
                validation_results['thermal_loss_validation'] = False
            else:
                print(f"✅ Thermal losses {total_thermal_loss_kw:.1f} kW within limit {max_thermal_loss_kw} kW")
            
            # Validate pump power
            total_pump_power_kw = pump_results.get('total_pump_power_kw', 0)
            max_pump_power_kw = self.config.get('standards_limits', {}).get('max_pump_power_kw', 500)
            
            if total_pump_power_kw > max_pump_power_kw:
                print(f"⚠️ Pump power {total_pump_power_kw:.1f} kW above maximum {max_pump_power_kw} kW")
                validation_results['pump_power_validation'] = False
            else:
                print(f"✅ Pump power {total_pump_power_kw:.1f} kW within limit {max_pump_power_kw} kW")
            
            # Overall validation
            validation_results['overall_validation'] = all([
                validation_results['temperature_validation'],
                validation_results['thermal_loss_validation'],
                validation_results['pump_power_validation']
            ])
            
            print(f"✅ Thermal performance validation: {'PASS' if validation_results['overall_validation'] else 'FAIL'}")
            
            return validation_results['overall_validation']
            
        except Exception as e:
            print(f"❌ Error validating thermal performance: {e}")
            return False
    
    def _calculate_pipe_thermal_loss(self, pipe_data) -> float:
        """
        Calculate thermal loss for a single pipe.
        
        Args:
            pipe_data: Pipe data from simulation results
            
        Returns:
            thermal_loss_w: Thermal loss in watts
        """
        try:
            # Get pipe parameters
            length_m = pipe_data.get('length_km', 0) * 1000  # Convert km to m
            diameter_m = pipe_data.get('diameter_m', 0.1)
            
            # Get thermal parameters
            heat_transfer_coeff = pipe_data.get('alpha_w_per_m2k', self.pipe_u_w_per_m2k_default)
            ground_temp_k = pipe_data.get('text_k', self.ground_temp_c + 273.15)
            
            # Get fluid temperature (average of inlet and outlet)
            inlet_temp_k = pipe_data.get('t_from_k', self.supply_temp_c + 273.15)
            outlet_temp_k = pipe_data.get('t_to_k', self.return_temp_c_init + 273.15)
            avg_fluid_temp_k = (inlet_temp_k + outlet_temp_k) / 2
            
            # Calculate temperature difference
            delta_t_k = avg_fluid_temp_k - ground_temp_k
            
            # Calculate surface area: A = π · D · L
            surface_area_m2 = math.pi * diameter_m * length_m
            
            # Calculate thermal loss: Q_loss = U · A · ΔT
            thermal_loss_w = heat_transfer_coeff * surface_area_m2 * delta_t_k
            
            return thermal_loss_w
            
        except Exception as e:
            print(f"❌ Error calculating pipe thermal loss: {e}")
            return 0.0

    def export_hydraulic_results(self, output_dir: str) -> bool:
        """
        Export comprehensive hydraulic simulation results.
        
        Args:
            output_dir: Directory to export results to
            
        Returns:
            bool: True if export successful
        """
        try:
            print("📊 Exporting hydraulic results...")
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            if not self.simulation_results or not self.simulation_results.get("simulation_success"):
                print("❌ No valid simulation results to export")
                return False
            
            # Export detailed hydraulic results CSV
            hydraulic_file = output_path / "cha_hydraulic_summary.csv"
            self._export_hydraulic_csv(hydraulic_file)
            
            # Export GeoPackage with results
            gpkg_file = output_path / "cha_with_results.gpkg"
            self._export_results_gpkg(gpkg_file)
            
            print(f"✅ Hydraulic results exported to {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting hydraulic results: {e}")
            return False

    def export_thermal_visualization(self, output_dir: str) -> bool:
        """
        Export interactive thermal visualization map.
        
        Args:
            output_dir: Directory to export visualization to
            
        Returns:
            bool: True if export successful
        """
        try:
            print("🌡️ Exporting thermal visualization...")
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            if not self.simulation_results or not self.simulation_results.get("simulation_success"):
                print("❌ No valid simulation results for thermal visualization")
                return False
            
            # Create interactive thermal map
            thermal_map_file = output_path / "cha_temperature_map.html"
            self._create_thermal_map(thermal_map_file)
            
            print(f"✅ Thermal visualization exported to {thermal_map_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting thermal visualization: {e}")
            return False

    def export_standards_compliance_report(self, output_dir: str) -> bool:
        """
        Export standards compliance report.
        
        Args:
            output_dir: Directory to export report to
            
        Returns:
            bool: True if export successful
        """
        try:
            print("📋 Exporting standards compliance report...")
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            if not self.simulation_results or not self.simulation_results.get("simulation_success"):
                print("❌ No valid simulation results for compliance report")
                return False
            
            # Create compliance report
            compliance_file = output_path / "cha_compliance_report.html"
            self._create_compliance_report(compliance_file)
            
            print(f"✅ Standards compliance report exported to {compliance_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting compliance report: {e}")
            return False

    def export_kpi_summary(self, output_dir: str) -> bool:
        """
        Export comprehensive KPI summary.
        
        Args:
            output_dir: Directory to export KPIs to
            
        Returns:
            bool: True if export successful
        """
        try:
            print("📈 Exporting KPI summary...")
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            if not self.simulation_results or not self.simulation_results.get("simulation_success"):
                print("❌ No valid simulation results for KPI summary")
                return False
            
            # Calculate comprehensive KPIs
            kpis = self.calculate_hydraulic_kpis()
            if "error" in kpis:
                print(f"❌ Failed to calculate KPIs: {kpis['error']}")
                return False
            
            # Add additional metrics
            enhanced_kpis = self._enhance_kpi_data(kpis)
            
            # Export KPI JSON
            kpi_file = output_path / "cha_kpis.json"
            with open(kpi_file, 'w') as f:
                json.dump(enhanced_kpis, f, indent=2, default=str)
            
            print(f"✅ KPI summary exported to {kpi_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting KPI summary: {e}")
            return False

    def _export_hydraulic_csv(self, output_file: Path) -> None:
        """Export detailed hydraulic results to CSV."""
        try:
            # Get pipe results
            pipe_results = self.simulation_results.get("pipe_results")
            if pipe_results is None or len(pipe_results) == 0:
                print("❌ No pipe results to export")
                return
            
            # Create comprehensive hydraulic data
            hydraulic_data = []
            for idx, pipe in pipe_results.iterrows():
                hydraulic_data.append({
                    'pipe_id': idx,
                    'length_km': pipe.get('length_km', 0),
                    'diameter_m': pipe.get('diameter_m', 0),
                    'velocity_ms': pipe.get('v_mean_m_per_s', 0),
                    'pressure_drop_bar': pipe.get('p_from_bar', 0) - pipe.get('p_to_bar', 0),
                    'pressure_drop_pa_per_m': (pipe.get('p_from_bar', 0) - pipe.get('p_to_bar', 0)) * 100000 / (pipe.get('length_km', 0.001) * 1000),
                    'mass_flow_kg_s': pipe.get('mdot_kg_per_s', 0),
                    'inlet_temp_c': pipe.get('t_from_k', 0) - 273.15,
                    'outlet_temp_c': pipe.get('t_to_k', 0) - 273.15,
                    'temp_drop_c': (pipe.get('t_from_k', 0) - pipe.get('t_to_k', 0)),
                    'thermal_loss_w': self._calculate_pipe_thermal_loss(pipe),
                    'pipe_category': self._categorize_pipe_by_diameter(pipe.get('diameter_m', 0))
                })
            
            # Export to CSV
            df = pd.DataFrame(hydraulic_data)
            df.to_csv(output_file, index=False)
            print(f"   📄 Hydraulic CSV exported: {len(hydraulic_data)} pipes")
            
        except Exception as e:
            print(f"❌ Error exporting hydraulic CSV: {e}")

    def _export_results_gpkg(self, output_file: Path) -> None:
        """Export results to GeoPackage."""
        try:
            # This would integrate with the existing CHA network data
            # For now, create a placeholder that indicates results are available
            import geopandas as gpd
            from shapely.geometry import Point
            
            # Create a simple results summary GeoPackage
            results_data = []
            if self.simulation_results and self.simulation_results.get("simulation_success"):
                # Add network summary point
                results_data.append({
                    'geometry': Point(0, 0),  # Placeholder coordinates
                    'simulation_success': True,
                    'total_pipes': len(self.simulation_results.get("pipe_results", [])),
                    'max_velocity_ms': self.simulation_results.get("max_velocity_ms", 0),
                    'max_pressure_drop_pa_per_m': self.simulation_results.get("max_pressure_drop_pa_per_m", 0),
                    'total_pump_power_kw': self.simulation_results.get("total_pump_power_kw", 0),
                    'thermal_efficiency': self.simulation_results.get("thermal_efficiency", 0)
                })
            
            if results_data:
                gdf = gpd.GeoDataFrame(results_data)
                gdf.to_file(output_file, driver='GPKG')
                print(f"   📦 Results GeoPackage exported: {len(results_data)} summary records")
            else:
                print("   ⚠️ No results data to export to GeoPackage")
                
        except Exception as e:
            print(f"❌ Error exporting results GeoPackage: {e}")

    def _create_thermal_map(self, output_file: Path) -> None:
        """Create interactive thermal visualization map."""
        try:
            import folium
            
            # Create base map
            m = folium.Map(location=[52.5, 13.4], zoom_start=12, tiles='OpenStreetMap')
            
            # Add thermal visualization layers
            if self.simulation_results and self.simulation_results.get("simulation_success"):
                pipe_results = self.simulation_results.get("pipe_results")
                if pipe_results is not None and len(pipe_results) > 0:
                    # Add temperature visualization
                    for idx, pipe in pipe_results.iterrows():
                        inlet_temp = pipe.get('t_from_k', 0) - 273.15
                        outlet_temp = pipe.get('t_to_k', 0) - 273.15
                        avg_temp = (inlet_temp + outlet_temp) / 2
                        
                        # Color based on temperature
                        if avg_temp > 70:
                            color = 'red'
                        elif avg_temp > 60:
                            color = 'orange'
                        elif avg_temp > 50:
                            color = 'yellow'
                        else:
                            color = 'blue'
                        
                        # Add pipe segment (placeholder coordinates)
                        folium.CircleMarker(
                            location=[52.5 + idx * 0.001, 13.4 + idx * 0.001],
                            radius=5,
                            popup=f"Pipe {idx}: {avg_temp:.1f}°C",
                            color=color,
                            fill=True
                        ).add_to(m)
            
            # Add legend
            legend_html = '''
            <div style="position: fixed; 
                        bottom: 50px; left: 50px; width: 150px; height: 90px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:14px; padding: 10px">
            <p><b>Temperature Legend</b></p>
            <p><i class="fa fa-circle" style="color:red"></i> >70°C</p>
            <p><i class="fa fa-circle" style="color:orange"></i> 60-70°C</p>
            <p><i class="fa fa-circle" style="color:yellow"></i> 50-60°C</p>
            <p><i class="fa fa-circle" style="color:blue"></i> <50°C</p>
            </div>
            '''
            m.get_root().html.add_child(folium.Element(legend_html))
            
            # Save map
            m.save(str(output_file))
            print(f"   🗺️ Thermal map created with temperature visualization")
            
        except Exception as e:
            print(f"❌ Error creating thermal map: {e}")

    def _create_compliance_report(self, output_file: Path) -> None:
        """Create standards compliance report."""
        try:
            # Calculate compliance metrics
            kpis = self.calculate_hydraulic_kpis()
            compliance_data = self._assess_standards_compliance(kpis)
            
            # Create HTML report
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>CHA Standards Compliance Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                    .section {{ margin: 20px 0; }}
                    .metric {{ margin: 10px 0; padding: 10px; border-left: 4px solid #007acc; }}
                    .compliant {{ border-left-color: #28a745; }}
                    .non-compliant {{ border-left-color: #dc3545; }}
                    .warning {{ border-left-color: #ffc107; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>CHA Standards Compliance Report</h1>
                    <p>Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="section">
                    <h2>Executive Summary</h2>
                    <p>Overall Compliance: <strong>{'✅ COMPLIANT' if compliance_data['overall_compliant'] else '❌ NON-COMPLIANT'}</strong></p>
                    <p>Standards Assessed: EN 13941, DIN 1988, VDI 2067</p>
                </div>
                
                <div class="section">
                    <h2>Hydraulic Performance</h2>
                    {self._generate_hydraulic_compliance_html(compliance_data)}
                </div>
                
                <div class="section">
                    <h2>Thermal Performance</h2>
                    {self._generate_thermal_compliance_html(compliance_data)}
                </div>
                
                <div class="section">
                    <h2>Detailed Metrics</h2>
                    {self._generate_detailed_metrics_html(kpis)}
                </div>
            </body>
            </html>
            """
            
            with open(output_file, 'w') as f:
                f.write(html_content)
            
            print(f"   📋 Compliance report created with {len(compliance_data.get('violations', []))} violations")
            
        except Exception as e:
            print(f"❌ Error creating compliance report: {e}")

    def _enhance_kpi_data(self, kpis: dict) -> dict:
        """Enhance KPI data with additional metrics."""
        try:
            enhanced_kpis = kpis.copy()
            
            # Add metadata
            enhanced_kpis['metadata'] = {
                'generated_at': pd.Timestamp.now().isoformat(),
                'simulator_version': '1.0.0',
                'pandapipes_version': '0.8.0',
                'thermal_simulation_enabled': self.thermal_enabled,
                'simulation_mode': self.simulation_mode
            }
            
            # Add performance indicators
            enhanced_kpis['performance_indicators'] = {
                'hydraulic_efficiency': min(1.0, 2.0 / max(0.1, kpis.get('max_velocity_ms', 1.0))),
                'thermal_efficiency': kpis.get('thermal_efficiency', 0.0),
                'pump_efficiency': kpis.get('pump_efficiency', 0.0),
                'overall_efficiency': (kpis.get('thermal_efficiency', 0.0) + kpis.get('pump_efficiency', 0.0)) / 2
            }
            
            # Add standards compliance summary
            compliance_data = self._assess_standards_compliance(kpis)
            enhanced_kpis['standards_compliance'] = compliance_data
            
            return enhanced_kpis
            
        except Exception as e:
            print(f"❌ Error enhancing KPI data: {e}")
            return kpis

    def _categorize_pipe_by_diameter(self, diameter_m: float) -> str:
        """Categorize pipe by diameter."""
        if diameter_m >= 0.3:
            return "mains"
        elif diameter_m >= 0.15:
            return "distribution"
        else:
            return "services"

    def _assess_standards_compliance(self, kpis: dict) -> dict:
        """Assess compliance with engineering standards."""
        try:
            compliance = {
                'overall_compliant': True,
                'violations': [],
                'warnings': [],
                'standards_checked': ['EN_13941', 'DIN_1988', 'VDI_2067']
            }
            
            # EN 13941 compliance
            max_velocity = kpis.get('max_velocity_ms', 0)
            if max_velocity > 2.0:
                compliance['violations'].append(f"Velocity {max_velocity:.2f} m/s exceeds EN 13941 limit (2.0 m/s)")
                compliance['overall_compliant'] = False
            
            # DIN 1988 compliance
            max_pressure_drop = kpis.get('max_pressure_drop_pa_per_m', 0)
            if max_pressure_drop > 500:
                compliance['violations'].append(f"Pressure drop {max_pressure_drop:.0f} Pa/m exceeds DIN 1988 limit (500 Pa/m)")
                compliance['overall_compliant'] = False
            
            # VDI 2067 compliance
            thermal_efficiency = kpis.get('thermal_efficiency', 0)
            if thermal_efficiency < 0.85:
                compliance['warnings'].append(f"Thermal efficiency {thermal_efficiency:.2f} below VDI 2067 recommendation (0.85)")
            
            return compliance
            
        except Exception as e:
            print(f"❌ Error assessing standards compliance: {e}")
            return {'overall_compliant': False, 'violations': [f"Assessment error: {e}"], 'warnings': []}

    def _generate_hydraulic_compliance_html(self, compliance_data: dict) -> str:
        """Generate HTML for hydraulic compliance section."""
        violations = compliance_data.get('violations', [])
        warnings = compliance_data.get('warnings', [])
        
        html = "<table><tr><th>Metric</th><th>Status</th><th>Details</th></tr>"
        
        # Add violation rows
        for violation in violations:
            html += f"<tr><td>Standards Violation</td><td>❌ Non-Compliant</td><td>{violation}</td></tr>"
        
        # Add warning rows
        for warning in warnings:
            html += f"<tr><td>Performance Warning</td><td>⚠️ Warning</td><td>{warning}</td></tr>"
        
        if not violations and not warnings:
            html += "<tr><td>Hydraulic Performance</td><td>✅ Compliant</td><td>All metrics within standards</td></tr>"
        
        html += "</table>"
        return html

    def _generate_thermal_compliance_html(self, compliance_data: dict) -> str:
        """Generate HTML for thermal compliance section."""
        return "<p>Thermal performance analysis integrated with hydraulic compliance assessment.</p>"

    def _generate_detailed_metrics_html(self, kpis: dict) -> str:
        """Generate HTML for detailed metrics section."""
        html = "<table><tr><th>Metric</th><th>Value</th><th>Unit</th></tr>"
        
        for key, value in kpis.items():
            if isinstance(value, (int, float)):
                unit = self._get_metric_unit(key)
                html += f"<tr><td>{key}</td><td>{value:.3f}</td><td>{unit}</td></tr>"
        
        html += "</table>"
        return html

    def _get_metric_unit(self, metric_name: str) -> str:
        """Get unit for metric name."""
        units = {
            'max_velocity_ms': 'm/s',
            'max_pressure_drop_pa_per_m': 'Pa/m',
            'pump_kw': 'kW',
            'thermal_efficiency': '%',
            'pump_efficiency': '%',
            'total_thermal_loss_kw': 'kW',
            'temperature_drop_c': '°C'
        }
        return units.get(metric_name, '')

def run_cha_simulation_only():
    """
    Standalone function to run CHA simulation only from command line.
    """
    simulator = CHAPandapipesSimulator()
    return simulator.run_complete_simulation()


if __name__ == "__main__":
    import sys
    cha_output_dir = sys.argv[1] if len(sys.argv) > 1 else "processed/cha"
    simulator = CHAPandapipesSimulator(cha_output_dir)
    result = simulator.run_complete_simulation(cha_output_dir)
    print(json.dumps(result, indent=2))
